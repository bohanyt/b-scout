"""Optional local text presence detection; recognition and traversal are separate.

Coordinates use source-pixel XYXY, with exclusive right/bottom edges. Scores
are detector signals, never calibrated probabilities. No downloads are made.
"""
from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
import hashlib
import math
from pathlib import Path
from typing import Callable, Protocol

import numpy as np

Box = tuple[float, float, float, float]


@dataclass(frozen=True, slots=True)
class SpatialPolicy:
    """Explicit longest-side limit and optional overlapping source-pixel tiles.

    Each view is resized independently to the nearest multiple of 32 (at least
    32). The *effective* dimensions, rather than the requested scalar ratio,
    are used to recover source coordinates. No box-count budget is applied.
    """
    max_side: int
    tile_size: tuple[int, int] | None = None  # width, height in source pixels
    overlap: tuple[int, int] = (0, 0)
    duplicate_iou: float = 0.5
    duplicate_containment: float = 0.85

    def __post_init__(self):
        if type(self.max_side) is not int or self.max_side < 32 or self.max_side % 32:
            raise ValueError("max_side must be a positive multiple of 32, at least 32")
        if type(self.overlap) is not tuple or len(self.overlap) != 2 or any(type(v) is not int or v < 0 for v in self.overlap):
            raise ValueError("overlap must be two nonnegative integers")
        if self.tile_size is None:
            if self.overlap != (0, 0):
                raise ValueError("overlap requires tiling")
        elif (type(self.tile_size) is not tuple or len(self.tile_size) != 2
              or any(type(v) is not int or v <= 0 for v in self.tile_size)
              or any(o >= s for o, s in zip(self.overlap, self.tile_size))):
            raise ValueError("tile_size must exceed overlap on both axes")
        for value in (self.duplicate_iou, self.duplicate_containment):
            if type(value) not in (int, float) or not math.isfinite(value) or not 0 < value <= 1:
                raise ValueError("duplicate thresholds must be finite in (0,1]")


@dataclass(frozen=True, slots=True)
class FrameTiming:
    pts: int
    time_base: Fraction
    duration_pts: int | None = None

    def __post_init__(self):
        if type(self.pts) is not int or type(self.time_base) is not Fraction or self.time_base <= 0:
            raise ValueError("native integer PTS and positive Fraction time_base required")
        if self.duration_pts is not None and (type(self.duration_pts) is not int or self.duration_pts <= 0):
            raise ValueError("duration must be a positive native integer or explicit unknown")


@dataclass(frozen=True, slots=True)
class View:
    index: int
    source_xyxy: tuple[int, int, int, int]
    input_size: tuple[int, int]

    def to_source(self, box: Box) -> Box:
        left, top, right, bottom = self.source_xyxy
        iw, ih = self.input_size
        return (left + box[0] * (right-left) / iw,
                top + box[1] * (bottom-top) / ih,
                left + box[2] * (right-left) / iw,
                top + box[3] * (bottom-top) / ih)


@dataclass(frozen=True, slots=True)
class LocalDetection:
    box: Box
    score: float


class Backend(Protocol):
    def __call__(self, image: np.ndarray) -> list[LocalDetection]: ...


@dataclass(frozen=True, slots=True)
class Detection:
    box: Box
    score: float
    view_index: int
    local_index: int
    duplicates: tuple[tuple[int, int], ...] = ()
    seam_clipped: bool = False


@dataclass(frozen=True, slots=True)
class DetectionResult:
    timing: FrameTiming
    source_size: tuple[int, int]
    policy: SpatialPolicy
    views: tuple[View, ...]
    detections: tuple[Detection, ...]
    raw_candidates: tuple[Detection, ...]
    raw_count: int
    rejected_count: int
    suppressed_count: int


def _starts(length: int, tile: int, overlap: int) -> list[int]:
    if length <= tile:
        return [0]
    starts = list(range(0, length-tile+1, tile-overlap))
    if starts[-1] != length-tile:
        starts.append(length-tile)
    return starts


def plan_views(width: int, height: int, policy: SpatialPolicy) -> tuple[View, ...]:
    if type(width) is not int or type(height) is not int or min(width, height) <= 0:
        raise ValueError("positive integer source dimensions required")
    if type(policy) is not SpatialPolicy:
        raise ValueError("explicit SpatialPolicy required")
    tw, th = policy.tile_size or (width, height)
    views = []
    for top in _starts(height, th, policy.overlap[1]):
        for left in _starts(width, tw, policy.overlap[0]):
            right, bottom = min(width, left+tw), min(height, top+th)
            w, h = right-left, bottom-top
            ratio = min(1.0, policy.max_side / max(w, h))
            iw, ih = max(32, round(w*ratio/32)*32), max(32, round(h*ratio/32)*32)
            views.append(View(len(views), (left, top, right, bottom), (iw, ih)))
    return tuple(views)


def _area(box: Box) -> float:
    return max(0.0, box[2]-box[0])*max(0.0, box[3]-box[1])


def _duplicates(a: Box, b: Box, policy: SpatialPolicy) -> bool:
    inter = _area((max(a[0], b[0]), max(a[1], b[1]), min(a[2], b[2]), min(a[3], b[3])))
    aa, ab = _area(a), _area(b)
    return (inter/(aa+ab-inter) >= policy.duplicate_iou
            or inter/min(aa, ab) >= policy.duplicate_containment)


def suppress_seams(candidates: list[Detection], views: tuple[View, ...], policy: SpatialPolicy) -> tuple[Detection, ...]:
    """Greedy cross-view spatial suppression, with all suppressed references.

    Less-clipped candidates take priority, then higher scores. Same-view boxes
    are never suppressed here. All mapped candidates remain in DetectionResult. Containment covers seam-clipped
    copies. Geometry alone can merge nested text from distinct views; this is
    an explicit heuristic, not proof of semantic content equality.
    """
    kept: list[Detection] = []
    references: list[list[tuple[int, int]]] = []
    for candidate in sorted(candidates, key=lambda d: (d.seam_clipped, -d.score, -_area(d.box), d.view_index, d.local_index)):
        match = None
        for i, prior in enumerate(kept):
            if (candidate.view_index != prior.view_index
                    and _area(tuple(max(a, b) if n < 2 else min(a, b)
                                    for n, (a, b) in enumerate(zip(views[candidate.view_index].source_xyxy,
                                                                   views[prior.view_index].source_xyxy)))) > 0
                    and _duplicates(candidate.box, prior.box, policy)):
                match = i
                break
        if match is None:
            kept.append(candidate)
            references.append([])
        else:
            references[match].append((candidate.view_index, candidate.local_index))
    output = [Detection(d.box, d.score, d.view_index, d.local_index, tuple(refs), d.seam_clipped) for d, refs in zip(kept, references)]
    return tuple(sorted(output, key=lambda d: (d.box[1], d.box[0], d.view_index, d.local_index)))


def _resize(image: np.ndarray, size: tuple[int, int]) -> np.ndarray:
    import cv2  # optional: imported only on explicit detector invocation
    return cv2.resize(image, size, interpolation=cv2.INTER_LINEAR)


class TextDetector:
    """Detect a supplied BGR uint8 frame; never seek, skip frames or read text.

    Backend boxes describe the resized input with exclusive XYXY edges. Any
    backend failure propagates: the caller must report incomplete traversal,
    rather than substituting an empty complete frame. Input is copied so a
    backend cannot modify the caller's decoded pixels.
    """
    def __init__(self, backend: Backend, policy: SpatialPolicy, *, resize: Callable = _resize):
        if not callable(backend) or type(policy) is not SpatialPolicy or not callable(resize):
            raise ValueError("backend, explicit spatial policy and resize callable required")
        self.backend, self.policy, self.resize = backend, policy, resize

    def detect(self, image: np.ndarray, timing: FrameTiming) -> DetectionResult:
        if (not isinstance(image, np.ndarray) or image.dtype != np.uint8 or image.ndim != 3
                or image.shape[2] != 3 or min(image.shape[:2]) <= 0):
            raise ValueError("nonempty BGR uint8 image required")
        if type(timing) is not FrameTiming:
            raise ValueError("native FrameTiming required")
        height, width = image.shape[:2]
        views = plan_views(width, height, self.policy)
        candidates, raw, rejected = [], 0, 0
        for view in views:
            x1, y1, x2, y2 = view.source_xyxy
            prepared = self.resize(image[y1:y2, x1:x2].copy(), view.input_size)
            iw, ih = view.input_size
            if prepared.shape != (ih, iw, 3) or prepared.dtype != np.uint8:
                raise ValueError("resize returned unexpected dimensions/type")
            for index, detection in enumerate(self.backend(prepared)):
                raw += 1
                box, score = detection.box, detection.score
                if (len(box) != 4 or any(not math.isfinite(v) for v in box)
                        or not math.isfinite(score) or box[0] >= box[2] or box[1] >= box[3]):
                    rejected += 1
                    continue
                clipped = (max(0., box[0]), max(0., box[1]), min(float(iw), box[2]), min(float(ih), box[3]))
                if not _area(clipped):
                    rejected += 1
                    continue
                # Interior crop edges can truncate glyphs. Prefer another
                # view's complete candidate even when its score is lower.
                seam_clipped = ((x1 > 0 and clipped[0] <= 1)
                                or (y1 > 0 and clipped[1] <= 1)
                                or (x2 < width and clipped[2] >= iw-1)
                                or (y2 < height and clipped[3] >= ih-1))
                candidates.append(Detection(view.to_source(clipped), float(score), view.index, index,
                                            seam_clipped=seam_clipped))
        output = suppress_seams(candidates, views, self.policy)
        return DetectionResult(timing, (width, height), self.policy, views, output, tuple(candidates), raw, rejected, len(candidates)-len(output))


class PPOCRv4Backend:
    """Explicit local PP-OCRv4 DB detector on CPU. No recognition/downloads.

    Caller supplies a reviewed ONNX path and expected SHA256. Optional packages
    (OpenCV, ONNX Runtime, pyclipper) are not core imports or dependencies.
    All contours are examined; thresholds are filtering, not calibrated recall.
    """
    def __init__(self, model_path: str | Path, expected_sha256: str, *, threads: int = 4,
                 bitmap_threshold: float = .3, box_threshold: float = .5, unclip_ratio: float = 1.6):
        if (type(expected_sha256) is not str or len(expected_sha256) != 64
                or any(c not in "0123456789abcdef" for c in expected_sha256)):
            raise ValueError("expected lowercase SHA256 required")
        if type(threads) is not int or threads <= 0:
            raise ValueError("positive integer CPU thread count required")
        for threshold in (bitmap_threshold, box_threshold):
            if type(threshold) not in (float, int) or not math.isfinite(threshold) or not 0 < threshold <= 1:
                raise ValueError("detector thresholds must be in (0,1]")
        if type(unclip_ratio) not in (float, int) or not math.isfinite(unclip_ratio) or unclip_ratio <= 0:
            raise ValueError("positive unclip ratio required")
        path = Path(model_path)
        with path.open("rb") as source:
            actual = hashlib.file_digest(source, "sha256").hexdigest()
        if actual != expected_sha256:
            raise ValueError("local detector model SHA256 differs")
        import cv2
        import onnxruntime as ort
        import pyclipper
        self.cv2, self.pyclipper = cv2, pyclipper
        options = ort.SessionOptions()
        options.intra_op_num_threads, options.inter_op_num_threads = threads, 1
        self.session = ort.InferenceSession(str(path), options, providers=["CPUExecutionProvider"])
        self.name = self.session.get_inputs()[0].name
        self.bitmap_threshold, self.box_threshold, self.unclip_ratio = bitmap_threshold, box_threshold, unclip_ratio

    def __call__(self, image: np.ndarray) -> list[LocalDetection]:
        cv2 = self.cv2
        height, width = image.shape[:2]
        tensor = ((image.astype(np.float32)/255-.5)/.5).transpose(2, 0, 1)[None]
        probability = self.session.run(None, {self.name: tensor})[0][0, 0]
        if probability.ndim != 2 or not np.isfinite(probability).all():
            raise ValueError("invalid detector output map")
        ph, pw = probability.shape
        mask = cv2.dilate((probability > self.bitmap_threshold).astype(np.uint8), np.ones((2, 2), np.uint8))
        contours, _ = cv2.findContours(mask, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
        detections = []
        for contour in contours:
            rect = cv2.minAreaRect(contour)
            if min(rect[1]) < 3:
                continue
            polygon = cv2.boxPoints(rect)
            xmin, ymin = np.maximum(0, np.floor(polygon.min(axis=0))).astype(int)
            xmax, ymax = np.minimum([pw-1, ph-1], np.ceil(polygon.max(axis=0))).astype(int)
            if xmin > xmax or ymin > ymax:
                continue
            local = np.zeros((ymax-ymin+1, xmax-xmin+1), np.uint8)
            cv2.fillPoly(local, [(polygon-[xmin, ymin]).astype(np.int32)], 1)
            score = float(cv2.mean(probability[ymin:ymax+1, xmin:xmax+1], mask=local)[0])
            if score < self.box_threshold:
                continue
            perimeter, area = cv2.arcLength(polygon, True), cv2.contourArea(polygon)
            if perimeter <= 0:
                continue
            expand = self.pyclipper.PyclipperOffset()
            expand.AddPath(polygon.astype(int).tolist(), self.pyclipper.JT_ROUND, self.pyclipper.ET_CLOSEDPOLYGON)
            expanded = expand.Execute(area*self.unclip_ratio/perimeter)
            if len(expanded) != 1:
                continue
            rect = cv2.minAreaRect(np.array(expanded[0], np.float32))
            if min(rect[1]) < 5:
                continue
            points = cv2.boxPoints(rect)
            # The detector map may differ from model input dimensions.
            x1, y1 = points.min(axis=0)
            x2, y2 = points.max(axis=0)
            box = (max(0., float(x1)*width/pw), max(0., float(y1)*height/ph),
                   min(float(width), float(x2)*width/pw), min(float(height), float(y2)*height/ph))
            if box[2]-box[0] > 3 and box[3]-box[1] > 3:
                detections.append(LocalDetection(box, score))
        return detections

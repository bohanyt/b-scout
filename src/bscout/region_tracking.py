"""Conservative source-pixel content tracking, independent of detector/OCR models."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from fractions import Fraction
import hashlib
import math

import numpy as np

Box = tuple[int, int, int, int]


@dataclass(frozen=True)
class NativeTiming:
    position: int
    pts: int
    duration: int | None
    time_base: Fraction

    def __post_init__(self):
        if type(self.position) is not int or self.position < 0 or type(self.pts) is not int:
            raise ValueError("Native position and PTS must be integers")
        if self.duration is not None and (type(self.duration) is not int or self.duration <= 0):
            raise ValueError("Duration must be a positive native integer or None")
        if not isinstance(self.time_base, Fraction) or self.time_base <= 0:
            raise ValueError("time_base must be a positive Fraction")

    def record(self):
        return dict(position=self.position, pts=self.pts, duration=self.duration,
                    time_base=[self.time_base.numerator, self.time_base.denominator])


@dataclass(frozen=True)
class TrackingConfig:
    max_box_jitter: int = 8
    min_iou: float = 0.65
    pixel_delta: int = 12
    max_changed_pixels: int = 0
    context_pixels: int = 2
    max_anchor_bytes: int | None = None

    def __post_init__(self):
        for name in ("max_box_jitter", "pixel_delta", "max_changed_pixels", "context_pixels"):
            if type(getattr(self, name)) is not int or getattr(self, name) < 0:
                raise ValueError("Tracking thresholds must be nonnegative integers")
        if self.pixel_delta > 255:
            raise ValueError("pixel_delta exceeds uint8 range")
        if type(self.min_iou) not in (int, float) or not math.isfinite(self.min_iou) or not 0 < self.min_iou <= 1:
            raise ValueError("min_iou must be in (0, 1]")
        if self.max_anchor_bytes is not None and (type(self.max_anchor_bytes) is not int or self.max_anchor_bytes <= 0):
            raise ValueError("max_anchor_bytes must be positive or None")


class AnchorBudgetExceeded(ValueError):
    """Observation was rejected intact; callers must report a partial scan/gap."""


def _iou(a: Box, b: Box):
    w = max(0, min(a[2], b[2]) - max(a[0], b[0]))
    h = max(0, min(a[3], b[3]) - max(a[1], b[1]))
    intersection = w * h
    return intersection / ((a[2]-a[0])*(a[3]-a[1]) + (b[2]-b[0])*(b[3]-b[1]) - intersection)


class RegionTracker:
    """Fixed anchors resist detector jitter without crop resizing or grayscale loss.

    [] is an observed detector absence, not proof that text is visually absent.
    None is a missing observation and closes uncertain occurrences. Anchors and
    output records grow with distinct content; optional budget failure is explicit.
    """

    def __init__(self, config: TrackingConfig = TrackingConfig()):
        self.config = config
        self.contents: list[dict] = []
        self.occurrences: list[dict] = []
        self.gaps: list[dict] = []
        self._anchors: list[np.ndarray] = []
        self._active: dict[int, int] = {}  # occurrence index -> content index
        self._previous: NativeTiming | None = None
        self._shape: tuple | None = None
        self.anchor_bytes = 0
        self._finished = False

    def _near(self, a, b):
        return max(abs(x-y) for x, y in zip(a, b)) <= self.config.max_box_jitter and _iou(a, b) >= self.config.min_iou

    def _support(self, box, shape):
        p = self.config.context_pixels + self.config.max_box_jitter
        return (max(0, box[0]-p), max(0, box[1]-p), min(shape[1], box[2]+p), min(shape[0], box[3]+p))

    def _compare(self, image, content_index):
        record = self.contents[content_index]
        x1,y1,x2,y2 = record["support_xyxy"]
        patch = image[y1:y2,x1:x2]
        delta = np.max(np.abs(patch.astype(np.int16) - self._anchors[content_index].astype(np.int16)), axis=2)
        changed = int(np.count_nonzero(delta > self.config.pixel_delta))
        return changed <= self.config.max_changed_pixels, changed

    def _close(self, index, reason):
        self.occurrences[index]["close_reason"] = reason
        self._active.pop(index, None)

    def observe(self, image: np.ndarray | None, boxes: list[Box] | None,
                timing: NativeTiming, evidence_ref: str | None = None):
        """Return one assignment per input detection; retain all observed frames.

        Input pixels must be HxWx3 uint8 in one consistent channel order. PTS and
        position strictly increase. Discontinuous positions produce explicit gaps.
        Missing duration remains unknown. Budget errors do not change state.
        """
        if self._finished:
            raise ValueError("Tracker is finished")
        if not isinstance(timing, NativeTiming):
            raise ValueError("NativeTiming is required")
        previous = self._previous
        if previous and (timing.position <= previous.position or timing.pts*timing.time_base <= previous.pts*previous.time_base):
            raise ValueError("Presentation position and native time must strictly increase")
        if evidence_ref is not None and (not isinstance(evidence_ref, str) or not evidence_ref):
            raise ValueError("Evidence reference must be a nonempty string or None")
        missing = boxes is None
        checked = []
        if not missing:
            if not isinstance(image, np.ndarray) or image.dtype != np.uint8 or image.ndim != 3 or image.shape[2] != 3:
                raise ValueError("Source pixels must be HxWx3 uint8")
            if self._shape is not None and image.shape != self._shape:
                raise ValueError("Source dimensions changed; start a separate tracker")
            for box in boxes:
                if len(box) != 4 or any(type(v) is not int for v in box):
                    raise ValueError("Source XYXY boxes require four integers")
                x1,y1,x2,y2 = box
                if not (0 <= x1 < x2 <= image.shape[1] and 0 <= y1 < y2 <= image.shape[0]):
                    raise ValueError("Source box lies outside the decoded frame")
                checked.append(tuple(box))
        position_gap = previous is not None and timing.position != previous.position + 1
        timing_gap = previous is not None and previous.duration is not None and timing.pts*timing.time_base > (previous.pts+previous.duration)*previous.time_base
        unknown_duration = previous is not None and previous.duration is None
        if previous is not None and previous.duration is not None and timing.pts*timing.time_base < (previous.pts+previous.duration)*previous.time_base:
            raise ValueError("Native frame intervals overlap")
        discontinuity = position_gap or timing_gap or unknown_duration
        active = {} if discontinuity or missing else self._active
        # Resolve only mutually unique associations. A split/merge ambiguity is
        # retained as new observations, never silently assigned to a neighbour.
        edges = {i: [o for o in active if self._near(box, tuple(self.occurrences[o]["anchor_box_xyxy"]))]
                 for i, box in enumerate(checked)}
        reverse = {o: [i for i in edges if o in edges[i]] for o in active}
        associations = {i: os[0] for i, os in edges.items() if len(os) == 1 and len(reverse[os[0]]) == 1}
        plans, staged = [], []
        for i, box in enumerate(checked):
            occurrence = associations.get(i)
            content = active.get(occurrence)
            changed = None
            if content is not None:
                equal, changed = self._compare(image, content)
                if not equal:
                    content = None
            if content is None:
                # Location-bound reuse only; visually identical strings at other
                # locations remain distinct candidates, not semantic dedup.
                matches = []
                for c, record in enumerate(self.contents):
                    if self._near(box, tuple(record["anchor_box_xyxy"])):
                        equal, count = self._compare(image, c)
                        if equal:
                            matches.append((c, count))
                if len(matches) == 1:
                    content, changed = matches[0]
                else:
                    support = self._support(box, image.shape)
                    x1,y1,x2,y2 = support
                    anchor = image[y1:y2,x1:x2].copy()
                    content = len(self.contents) + len(staged)
                    staged.append((box, support, anchor))
            plans.append((i, box, occurrence, content, changed))
        required = self.anchor_bytes + sum(anchor.nbytes for _, _, anchor in staged)
        if self.config.max_anchor_bytes is not None and required > self.config.max_anchor_bytes:
            raise AnchorBudgetExceeded(f"Anchor budget exhausted: {required} > {self.config.max_anchor_bytes}; observation not consumed")
        if discontinuity or missing:
            for o in list(self._active):
                self._close(o, "observation_gap")
            self.gaps.append(dict(reason="missing_observation" if missing else "position_gap" if position_gap else "timing_gap" if timing_gap else "unknown_previous_duration",
                                  after=previous.record() if previous else None, before=timing.record(),
                                  missing_positions=[previous.position+1, timing.position + int(missing)] if position_gap else [timing.position, timing.position+1] if missing else None))
        for box, support, anchor in staged:
            c = len(self.contents)
            self.contents.append(dict(content_id=f"content-{c+1:08d}", anchor_box_xyxy=list(box),
                                      support_xyxy=list(support), anchor_sha256=hashlib.sha256(anchor.tobytes()).hexdigest(),
                                      first=timing.record(), evidence_ref=evidence_ref))
            self._anchors.append(anchor)
        self.anchor_bytes = required
        matched = {p[2] for p in plans if p[2] is not None}
        for o in list(self._active):
            if o not in matched:
                self._close(o, "ambiguous_association" if reverse.get(o) else "detector_absence")
        assignments = []
        for i, box, o, c, changed in plans:
            if o is not None and self._active.get(o) != c:
                self._close(o, "content_change")
                o = None
            if o is None:
                o = len(self.occurrences)
                self.occurrences.append(dict(occurrence_id=f"occurrence-{o+1:08d}", content_id=self.contents[c]["content_id"],
                                             anchor_box_xyxy=list(self.contents[c]["anchor_box_xyxy"]),
                                             first=timing.record(), last=timing.record(), first_evidence_ref=evidence_ref,
                                             last_evidence_ref=evidence_ref, observed_frames=0, close_reason=None))
            record = self.occurrences[o]
            record.update(last=timing.record(), end_pts_exclusive=timing.pts+timing.duration if timing.duration is not None else None,
                          last_evidence_ref=evidence_ref, last_box_xyxy=list(box),
                          observed_frames=record["observed_frames"]+1)
            self._active[o] = c
            assignments.append(dict(detection_index=i, content_id=record["content_id"], occurrence_id=record["occurrence_id"],
                                    timing=timing.record(), box_xyxy=list(box), changed_pixels_from_anchor=changed,
                                    evidence_ref=evidence_ref))
        if not missing:
            self._shape = image.shape
        self._previous = timing
        return assignments

    def finish(self):
        for o in list(self._active):
            self._close(o, "end_of_observations")
        self._finished = True
        return self.snapshot()

    def snapshot(self):
        # Copy records so consumers cannot change tracking state. Pixels stay
        # local; digest/reference records are compact but not recovery proof.
        import copy
        return dict(version="bscout-region-tracking-v1", config=asdict(self.config),
                    contents=copy.deepcopy(self.contents), occurrences=copy.deepcopy(self.occurrences),
                    gaps=copy.deepcopy(self.gaps), anchor_bytes=self.anchor_bytes,
                    observation_count=sum(o["observed_frames"] for o in self.occurrences),
                    finished=self._finished)

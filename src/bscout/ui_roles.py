"""Conservative pixel/temporal UI role candidates; no OCR or semantic truth input."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from fractions import Fraction
import math

import numpy as np

VERSION = "bscout-ui-roles-v1"
ROLES = ("persistent_hud", "transient_notice", "menu_panel", "unknown")


@dataclass(frozen=True, slots=True)
class RoleConfig:
    hud_seconds: float = 5.0
    panel_seconds: float = 0.5
    notice_max_seconds: float = 2.0
    max_sample_seconds: float = 0.1
    stable_iou: float = 0.9
    hud_max_area: float = 0.12
    panel_min_area: float = 0.15
    notice_max_area: float = 0.3
    edge_margin: float = 0.04
    flat_fraction: float = 0.65
    min_edge_fraction: float = 0.005
    min_row_bands: int = 3
    boundary_pixel_delta: float = 24.0

    def __post_init__(self):
        for key, value in asdict(self).items():
            if type(value) not in (int, float) or not math.isfinite(value) or value <= 0:
                raise ValueError(f"Invalid role threshold: {key}")
        for key in ("stable_iou", "hud_max_area", "panel_min_area", "notice_max_area",
                    "edge_margin", "flat_fraction", "min_edge_fraction"):
            if getattr(self, key) > 1:
                raise ValueError(f"Invalid role fraction: {key}")
        if type(self.min_row_bands) is not int:
            raise ValueError("Row-band threshold must be an integer")


@dataclass(frozen=True, slots=True)
class RoleSample:
    """Scalar pixel measurements from measure_sample; holds no source image."""
    position: int
    pts: int
    duration_pts: int
    time_base: Fraction
    image_size: tuple[int, int]
    box_xyxy: tuple[int, int, int, int] | None
    flat_fraction: float | None
    edge_fraction: float | None
    row_bands: int | None
    evidence_ref: str
    comparison_box_xyxy: tuple[int, int, int, int] | None = None
    pixel_signature: tuple[float, ...] | None = None

    def __post_init__(self):
        if any(type(v) is not int for v in (self.position, self.pts, self.duration_pts)) or self.position < 0 or self.duration_pts <= 0:
            raise ValueError("Invalid measured native position/timing")
        if not isinstance(self.time_base, Fraction) or self.time_base <= 0:
            raise ValueError("Measured time base must be a positive Fraction")
        if len(self.image_size) != 2 or any(type(v) is not int or v < 2 for v in self.image_size):
            raise ValueError("Invalid measured source dimensions")
        if not isinstance(self.evidence_ref, str) or not self.evidence_ref:
            raise ValueError("Evidence reference required")
        if self.comparison_box_xyxy is None:
            if self.pixel_signature is not None:
                raise ValueError("Pixel signature requires a fixed comparison box")
        else:
            b = self.comparison_box_xyxy
            w, h = self.image_size
            if len(b) != 4 or any(type(v) is not int for v in b) or not (0 <= b[0] < b[2] <= w and 0 <= b[1] < b[3] <= h) or min(b[2]-b[0], b[3]-b[1]) < 4:
                raise ValueError("Invalid fixed comparison box")
            if self.pixel_signature is None or len(self.pixel_signature) != 16 or any(type(v) not in (int, float) or not math.isfinite(v) or not 0 <= v <= 255 for v in self.pixel_signature):
                raise ValueError("Invalid native-pixel spatial signature")
        values = (self.flat_fraction, self.edge_fraction, self.row_bands)
        if self.box_xyxy is None:
            if any(v is not None for v in values):
                raise ValueError("Absent observation cannot carry region features")
        else:
            b = self.box_xyxy
            w, h = self.image_size
            if len(b) != 4 or any(type(v) is not int for v in b) or not (0 <= b[0] < b[2] <= w and 0 <= b[1] < b[3] <= h) or min(b[2]-b[0], b[3]-b[1]) < 2:
                raise ValueError("Invalid measured source box")
            if any(type(v) not in (int, float) or not math.isfinite(v) or not 0 <= v <= 1 for v in values[:2]):
                raise ValueError("Measured pixel fractions must be finite and in [0,1]")
            if type(self.row_bands) is not int or self.row_bands < 0:
                raise ValueError("Invalid measured row bands")

    @property
    def start(self):
        return self.pts * self.time_base

    @property
    def end(self):
        return (self.pts + self.duration_pts) * self.time_base


def measure_sample(*, image, box_xyxy, position, pts, duration_pts, time_base, evidence_ref, comparison_box_xyxy=None):
    """Measure every crop pixel. None box means detector absence, not proven absence.

    image is a source-sized uint8 RGB/BGR array (channel order is immaterial to
    channel-mean gradients). Boxes are source-pixel XYXY, end-exclusive. Images
    are neither resized nor retained. Text and manual role labels are not inputs.
    """
    if not isinstance(image, np.ndarray) or image.dtype != np.uint8 or image.ndim != 3 or image.shape[2] != 3:
        raise ValueError("Expected source-sized uint8 three-channel image")
    height, width = image.shape[:2]
    if min(height, width) < 2:
        raise ValueError("Image too small")
    if any(type(v) is not int for v in (position, pts, duration_pts)) or position < 0 or duration_pts <= 0:
        raise ValueError("Invalid native position/timing")
    tb = Fraction(time_base)
    if tb <= 0 or not isinstance(evidence_ref, str) or not evidence_ref:
        raise ValueError("Positive time base and evidence reference required")
    flat = edge = bands = None
    box = None
    if box_xyxy is not None:
        box = tuple(box_xyxy)
        if len(box) != 4 or any(type(v) is not int for v in box):
            raise ValueError("Box must contain four source-pixel integers")
        x1, y1, x2, y2 = box
        if not (0 <= x1 < x2 <= width and 0 <= y1 < y2 <= height) or min(x2-x1, y2-y1) < 2:
            raise ValueError("Box outside source or too small for gradients")
        gray = image[y1:y2, x1:x2].mean(axis=2, dtype=np.float32)
        dx = np.abs(np.diff(gray, axis=1))
        dy = np.abs(np.diff(gray, axis=0))
        count = dx.size + dy.size
        flat = float((np.count_nonzero(dx <= 8) + np.count_nonzero(dy <= 8)) / count)
        edge = float((np.count_nonzero(dx > 24) + np.count_nonzero(dy > 24)) / count)
        # Disjoint horizontal gradient bands are a layout cue, not text reading.
        active = np.mean(dy, axis=1) > 8
        bands = int(np.count_nonzero(active & ~np.r_[False, active[:-1]]))
    comparison = signature = None
    if comparison_box_xyxy is not None:
        comparison = tuple(comparison_box_xyxy)
        if len(comparison) != 4 or any(type(v) is not int for v in comparison):
            raise ValueError("Comparison box must contain four integers")
        x1, y1, x2, y2 = comparison
        if not (0 <= x1 < x2 <= width and 0 <= y1 < y2 <= height) or min(x2-x1, y2-y1) < 4:
            raise ValueError("Invalid fixed comparison geometry")
        crop = image[y1:y2, x1:x2]
        # All native pixels contribute to 16 spatial mean cells. This explicit
        # feature reduction does not skip decoded frames or resize source images.
        signature = tuple(float(cell.mean()) for row in np.array_split(crop, 4, axis=0)
                          for cell in np.array_split(row, 4, axis=1))
    return RoleSample(position, pts, duration_pts, tb, (width, height), box,
                      flat, edge, bands, evidence_ref, comparison, signature)


def _iou(a, b):
    inter = max(0, min(a[2], b[2])-max(a[0], b[0])) * max(0, min(a[3], b[3])-max(a[1], b[1]))
    aa = (a[2]-a[0])*(a[3]-a[1])
    bb = (b[2]-b[0])*(b[3]-b[1])
    return inter/(aa+bb-inter)


def classify(samples, *, candidate_id, occurrence_id, config=RoleConfig(), include_observations=False):
    """Label one tracked region occurrence; never merge/delete its evidence.

    Include surrounding detected-absence samples when available. Distinct
    appearances must be passed separately. No ordering repair or gap filling.
    """
    samples = tuple(samples)
    if not candidate_id or not occurrence_id or not samples:
        raise ValueError("IDs and at least one observation required")
    if not all(isinstance(s, RoleSample) for s in samples):
        raise ValueError("Expected measured RoleSamples")
    if any(b.position <= a.position or b.start < a.end for a, b in zip(samples, samples[1:])):
        raise ValueError("Observations must have increasing positions and nonoverlapping native timing")
    if len({s.image_size for s in samples}) != 1 or len({s.time_base for s in samples}) != 1:
        raise ValueError("Changing image size/time base requires separate classification")
    present = [s for s in samples if s.box_xyxy is not None]
    gaps = [{"after_position": a.position, "before_position": b.position,
             "start_pts": a.pts+a.duration_pts, "end_pts": b.pts,
             "missing_positions": b.position-a.position-1}
            for a, b in zip(samples, samples[1:])
            if b.position != a.position+1 or b.start != a.end]
    too_long = [s.position for s in samples if s.end-s.start > Fraction(str(config.max_sample_seconds))]
    dense = not gaps and not too_long
    total = sum((s.end-s.start for s in samples), Fraction())
    visible = sum((s.end-s.start for s in present), Fraction())
    transitions = sum((a.box_xyxy is None) != (b.box_xyxy is None) for a, b in zip(samples, samples[1:]))
    runs = sum(s.box_xyxy is not None and (i == 0 or samples[i-1].box_xyxy is None)
               for i, s in enumerate(samples))
    features = {"sample_count": len(samples), "present_count": len(present),
                "observed_seconds": float(total), "visible_seconds": float(visible),
                "span_seconds": float(samples[-1].end-samples[0].start),
                "occupancy": float(visible/total), "dense_coverage": dense,
                "gaps": gaps, "oversized_sample_positions": too_long,
                "presence_transitions": transitions, "presence_runs": runs,
                "bracketed": bool(present and samples[0].box_xyxy is None and samples[-1].box_xyxy is None)}
    reasons = []
    eligible = []
    if not present:
        reasons.append("no_detected_region")
    else:
        width, height = samples[0].image_size
        boxes = [s.box_xyxy for s in present]
        stability = min(_iou(boxes[0], b) for b in boxes)
        areas = [(b[2]-b[0])*(b[3]-b[1])/(width*height) for b in boxes]
        margins = [min(b[0]/width, b[1]/height, (width-b[2])/width, (height-b[3])/height) for b in boxes]
        # Worst observations make conflicting/changing evidence conservative.
        flat = min(s.flat_fraction for s in present)
        edge = min(s.edge_fraction for s in present)
        rows = min(s.row_bands for s in present)
        features.update(min_anchor_iou=stability, min_area_fraction=min(areas), max_area_fraction=max(areas),
                        max_edge_margin=max(margins), min_flat_fraction=flat,
                        min_edge_fraction=edge, min_row_bands=rows)
        if not dense:
            reasons.append("sparse_or_gapped_observations")
        if len(present) == 1:
            reasons.append("single_frame_semantics_unconfirmed_event_retained")
        if runs != 1:
            reasons.append("multiple_appearances_require_separate_occurrences")
        if stability < config.stable_iou:
            reasons.append("unstable_geometry")
        if not features["bracketed"]:
            reasons.append("appearance_boundaries_censored")
        if float(visible) < config.hud_seconds:
            reasons.append("insufficient_observed_duration_for_hud")
        comparison_iou = min((_iou(s.box_xyxy, s.comparison_box_xyxy) for s in present), default=0) if all(s.comparison_box_xyxy is not None for s in present) else None
        features["min_comparison_iou"] = comparison_iou
        boundary_delta = None
        if features["bracketed"] and runs == 1:
            first = next(i for i, s in enumerate(samples) if s.box_xyxy is not None)
            last = max(i for i, s in enumerate(samples) if s.box_xyxy is not None)
            pairs = ((samples[first-1], samples[first]), (samples[last], samples[last+1]))
            if all(a.pixel_signature is not None and b.pixel_signature is not None and
                   a.comparison_box_xyxy == b.comparison_box_xyxy for a, b in pairs):
                boundary_delta = min(float(np.mean(np.abs(np.asarray(a.pixel_signature)-b.pixel_signature))) for a, b in pairs)
        features["min_boundary_pixel_delta"] = boundary_delta
        if comparison_iou is not None and comparison_iou < config.stable_iou:
            reasons.append("comparison_roi_unrelated_to_candidate")
        if boundary_delta is None:
            reasons.append("visual_appearance_boundaries_unverified")
        elif boundary_delta < config.boundary_pixel_delta:
            reasons.append("detector_absence_without_visual_change")
        usable = dense and runs == 1 and stability >= config.stable_iou and edge >= config.min_edge_fraction
        if usable and visible >= Fraction(str(config.hud_seconds)) and features["occupancy"] >= 0.9 and max(areas) <= config.hud_max_area and max(margins) <= config.edge_margin:
            eligible.append("persistent_hud")
        if usable and visible >= Fraction(str(config.panel_seconds)) and min(areas) >= config.panel_min_area and flat >= config.flat_fraction and rows >= config.min_row_bands:
            eligible.append("menu_panel")
        # No minimum duration: a bracketed one-frame event can be a notice
        # candidate. It is retained even when cues are insufficient to label it.
        if usable and comparison_iou is not None and comparison_iou >= config.stable_iou and boundary_delta is not None and boundary_delta >= config.boundary_pixel_delta and features["bracketed"] and visible <= Fraction(str(config.notice_max_seconds)) and max(areas) <= config.notice_max_area and min(margins) > config.edge_margin and flat >= config.flat_fraction:
            eligible.append("transient_notice")
    if len(eligible) == 1:
        role = eligible[0]
        reasons.append(f"rule_supported:{role}")
    elif eligible:
        role = "unknown"
        reasons.append("conflicting_role_rules")
    else:
        role = "unknown"
        reasons.append("no_role_rule_supported")
    def evidence(s):
        return {"position": s.position, "pts": s.pts, "duration_pts": s.duration_pts,
                "box_xyxy": s.box_xyxy, "ref": s.evidence_ref}
    representatives = {0, len(samples)-1}
    if present:
        representatives.update((next(i for i, s in enumerate(samples) if s.box_xyxy is not None),
                                max(i for i, s in enumerate(samples) if s.box_xyxy is not None)))
    result = {"version": VERSION, "candidate_id": candidate_id, "occurrence_id": occurrence_id,
            "role": role, "candidate_only": True, "eligible_roles": eligible,
            "reasons": reasons, "features": features, "configuration": asdict(config),
            "observation_interval": {"start_pts": samples[0].pts, "end_pts": samples[-1].pts+samples[-1].duration_pts,
                                     "time_base": str(samples[0].time_base)},
            "candidate_interval": {"start_pts": present[0].pts, "end_pts": present[-1].pts+present[-1].duration_pts,
                                   "time_base": str(present[0].time_base)} if present else None,
            "interval_semantics": "Observation interval includes context; candidate interval bounds detected presence and may span multiple runs or gaps, flagged in features.",
            "evidence_count": len(samples),
            "evidence": [evidence(samples[i]) for i in sorted(representatives)],
            "evidence_scope": "First/last observed and present references; complete trace belongs to caller occurrence_id.",
            "limitations": ["Pixel geometry and timing do not establish UI semantics.",
                            "Detector absence can be a miss; notice boundaries remain candidates.",
                            "No probability calibration, OCR, content deduplication, or retention gate."]}

    if include_observations:
        result["observations"] = [evidence(s) for s in samples]
    return result

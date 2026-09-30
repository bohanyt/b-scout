"""Offline B diagnostics against frozen truth, independent of candidate generation.

Only this evaluator reads annotation events. Traversal positions are mapped with
independently decoded generator IDs; they are never treated as generator ordinals.
Evidence ``verified`` is the caller's source-bound recovery/asset verification
receipt. This helper checks that receipt's metadata, not files or C packet rules.
"""
from __future__ import annotations

from collections import Counter
from collections.abc import Mapping
from copy import deepcopy
import math


def _integer(value):
    return isinstance(value, int) and not isinstance(value, bool)


def _sha256(value):
    return (isinstance(value, str) and len(value) == 64
            and all(c in "0123456789abcdefABCDEF" for c in value))


def _region(value):
    if (not isinstance(value, (list, tuple)) or len(value) != 4
            or not all(_integer(v) for v in value)
            or min(value[:2]) < 0 or min(value[2:]) <= 0):
        raise ValueError("Expected source-pixel region_xywh with positive area")
    return tuple(value)


def _area(region):
    return region[2] * region[3]


def _intersection(a, b):
    return (max(0, min(a[0] + a[2], b[0] + b[2]) - max(a[0], b[0]))
            * max(0, min(a[1] + a[3], b[1] + b[3]) - max(a[1], b[1])))


def _spatial_match(a, b):
    intersection = _intersection(a, b)
    return (intersection / min(_area(a), _area(b)) >= 0.8
            and intersection / _area(a) >= 0.25)


def _evidence_records(evidence):
    records = []
    if isinstance(evidence, Mapping):
        for position, value in evidence.items():
            values = value if isinstance(value, list) else [value]
            for record in values:
                record = deepcopy(record)
                record.setdefault("position", int(position))
                records.append(record)
    else:
        records = deepcopy(list(evidence))
    return records


def _evidence_failure(record, known_timing):
    if not known_timing:
        return "native_timing_unavailable"
    if record.get("verified") is not True:
        return "source_bound_recovery_unverified"
    identity = record.get("identity")
    if (not isinstance(identity, (list, tuple)) or len(identity) != 4
            or not _sha256(identity[0]) or not _integer(identity[1])
            or not _integer(identity[2]) or not _integer(identity[3])):
        return "canonical_identity_unavailable"
    if not _sha256(record.get("native_sha256")):
        return "native_digest_unavailable"
    assets = record.get("assets")
    if not isinstance(assets, list) or not assets:
        return "retained_assets_unavailable"
    for asset in assets:
        if (not isinstance(asset, Mapping) or not asset.get("path")
                or not _sha256(asset.get("sha256"))
                or not _integer(asset.get("bytes")) or asset["bytes"] <= 0
                or not isinstance(asset.get("kind"), str) or not asset["kind"]):
            return "retained_asset_metadata_incomplete"
    return None


def _append_unique_evidence(target, records, seen_positions):
    """Store one representative per position; global evidence retains assets."""
    for record in records:
        position = record["position"]
        if position not in seen_positions:
            seen_positions.add(position)
            target.append(deepcopy(record))


def _candidate_kind(trigger):
    if trigger in ("initial_structure", "regional_change"):
        return "state"
    if trigger == "structural_inspection":
        return "structural_inspection"
    return "unclassified"


def _recall_metrics(matches, candidate_key="candidate_ids", usable_key="usable_candidate_ids"):
    candidate_count = sum(bool(m[candidate_key]) for m in matches)
    usable_count = sum(bool(m[usable_key]) for m in matches)
    return {"truth_occurrences": len(matches),
            "matched_occurrences": candidate_count,
            "usable_evidence_occurrences": usable_count,
            "candidate_recall": candidate_count / len(matches) if matches else None,
            "usable_evidence_recall": usable_count / len(matches) if matches else None,
            "candidate_miss_ids": [m["truth_id"] for m in matches if not m[candidate_key]],
            "usable_evidence_miss_ids": [m["truth_id"] for m in matches if not m[usable_key]]}


def evaluate_fixture(fixture, candidates, evidence, generator_ids, harness_region,
                     *, coverage_duration=None, known_timing=True,
                     allow_persistent_hud=False):
    """Return raw, JSON-compatible B matching and metrics without mutating input.

    ``fixture`` is one frozen annotation fixture. ``generator_ids`` maps integer
    traversal positions to independently read integer generator IDs. Candidates
    contain id, region_xywh, start_position, end_position_exclusive and explicit
    evidence_positions. Evidence is a list of records or a position-keyed mapping.
    Records contain position, canonical identity, native_sha256, verified and
    assets [{path, sha256, bytes, kind}].

    Candidate recall measures spatial/temporal localization; evidence recall also
    requires a verified representative inside truth and inside its candidate.
    Full-frame and effectively-full-clip candidates do not count by default. A
    candidate spanning both clip boundaries within one frame is effectively
    full-clip when the clip has at least four frames.
    Spatial matching also requires at least 25% of the candidate area to lie in
    truth, so an almost-fullscreen region cannot pass for a small popup. A
    persistent full-clip truth gets separate continuity/initial-observation
    diagnostics, which do not relax strict interval criteria. Boundary tolerance
    is one generator frame, including first and last events. Shared matches are
    explicit; this evaluator does not invent a visual split between annotations.
    Each truth's evidence list holds one representative per traversal position;
    every candidate ID/boundary and the complete global evidence inventory remain.
    Trigger, observation_of, occurrence and close_reason are preserved verbatim.
    Only explicit initial_structure/regional_change triggers are classed as state
    candidates; structural_inspection identifies an observation window without
    asserting a new appearance/content boundary. Recalls report localization of
    observations against annotations, not semantic or visual-boundary detection.

    ``coverage_duration`` must come from observed native PTS/traversal coverage in
    seconds (a float or Fraction), never nominal FPS or the generator schedule.
    When omitted, per-minute rates are null. ``known_timing=False`` permits raw
    generator-ID candidate diagnostics but makes timed usable evidence unavailable.
    ``allow_persistent_hud`` is an explicit product-policy opt-in, default false.
    It only allows full-clip candidates for the frozen ``persistent_hud`` truth
    occurrence when candidate area is below half the source frame and verified
    representative evidence is present. It never permits full-frame candidates.
    """
    clip_frames = len(fixture["pts"])
    width, height = fixture["width"], fixture["height"]
    full_frame = (0, 0, width, height)
    harness = _region(harness_region)
    ids = dict(generator_ids)
    if any(not _integer(k) or k < 0 or not _integer(v)
           or not 0 <= v < clip_frames for k, v in ids.items()):
        raise ValueError("Generator ID map must contain valid integer positions and IDs")
    ordered = sorted(ids)
    if any(b != a + 1 or ids[b] != ids[a] + 1
           for a, b in zip(ordered, ordered[1:])):
        raise ValueError("Generator ID map must be contiguous, monotonic and one-to-one")
    duration = None
    if known_timing and coverage_duration is not None:
        duration = float(coverage_duration)
        if not math.isfinite(duration) or duration <= 0:
            raise ValueError("Native coverage duration must be positive finite seconds")

    records = _evidence_records(evidence)
    record_results = []
    records_by_position = {}
    for record in records:
        position = record.get("position")
        if not _integer(position):
            raise ValueError("Evidence position must be an integer traversal reference")
        failure = _evidence_failure(record, known_timing)
        if position not in ids:
            failure = "generator_identity_unavailable"
        result = {"position": position, "generator_id": ids.get(position),
                  "identity": deepcopy(record.get("identity")),
                  "native_sha256": record.get("native_sha256"),
                  "assets": deepcopy(record.get("assets", [])),
                  "usable": failure is None, "unavailable_reason": failure}
        record_results.append(result)
        records_by_position.setdefault(position, []).append(result)

    truths = list(fixture["events"])
    truth_ids = [event["id"] for event in truths]
    if len(set(truth_ids)) != len(truth_ids):
        raise ValueError("Truth occurrence IDs must be unique")
    truth_matches = {event["id"]: {"truth_id": event["id"], "tier": event["tier"],
                    "start": event["start"], "end_exclusive": event["end_exclusive"],
                    "candidate_ids": [], "usable_candidate_ids": [],
                    "evidence": [], "matched_boundaries": [],
                    "temporal_rejections": []} for event in truths}
    kinds = ("state", "structural_inspection", "unclassified")
    for match in truth_matches.values():
        for kind in kinds:
            match[f"{kind}_candidate_ids"] = []
            match[f"usable_{kind}_candidate_ids"] = []
    persistent = {event["id"]: {"truth_id": event["id"],
                  "continuity_candidate_ids": [], "initial_observation_candidate_ids": [],
                  "evidence": [], "counts_toward_strict_recall": False}
                  for event in truths if event["start"] == 0
                  and event["end_exclusive"] == clip_frames
                  and _area(_region(event["region_xywh"])) < width * height * 0.5}
    truth_evidence_positions = {truth_id: set() for truth_id in truth_matches}
    persistent_evidence_positions = {truth_id: set() for truth_id in persistent}
    results, durations, seen = [], [], set()
    for candidate in candidates:
        candidate_id = candidate["id"]
        if candidate_id in seen:
            raise ValueError("Candidate IDs must be unique")
        seen.add(candidate_id)
        trigger = candidate.get("trigger")
        if trigger is not None and not isinstance(trigger, str):
            raise ValueError("Candidate trigger must be a string or unavailable")
        kind = _candidate_kind(trigger)
        region = _region(candidate["region_xywh"])
        start, end = candidate["start_position"], candidate["end_position_exclusive"]
        if not _integer(start) or not _integer(end) or start < 0 or end <= start:
            raise ValueError("Candidate interval must be nonempty integer traversal positions")
        if region[0] + region[2] > width or region[1] + region[3] > height:
            raise ValueError("Candidate region lies outside the source frame")
        durations.append(end - start)
        positions = candidate.get("evidence_positions", [])
        if not all(_integer(p) for p in positions):
            raise ValueError("Candidate evidence positions must be integers")
        mapped = all(p in ids for p in range(start, end))
        generator_start = ids[start] if mapped else None
        generator_end = ids[end - 1] + 1 if mapped else None
        harness_only = _intersection(region, harness) == _area(region)
        rejection = None
        if not mapped:
            rejection = "generator_mapping_incomplete"
        elif region == full_frame:
            rejection = "whole_frame"
        elif ((generator_start == 0 and generator_end == clip_frames)
              or (clip_frames >= 4 and generator_start <= 1
                  and generator_end >= clip_frames - 1)):
            rejection = "whole_clip"
        available = [r for p in dict.fromkeys(positions) if start <= p < end
                     for r in records_by_position.get(p, []) if r["usable"]]
        row = {"id": candidate_id, "region_xywh": list(region),
               "start_position": start, "end_position_exclusive": end,
               "generator_start": generator_start, "generator_end_exclusive": generator_end,
               "duration_frames": end - start, "harness_only": harness_only,
               "rejection_reason": rejection, "truth_ids": [], "usable_truth_ids": [],
               "persistent_hud_exception_truth_ids": [],
               "trigger": trigger, "candidate_kind": kind,
               "observation_of": deepcopy(candidate.get("observation_of")),
               "occurrence": deepcopy(candidate.get("occurrence")),
               "close_reason": deepcopy(candidate.get("close_reason")),
               "temporal_rejections": [], "raw_signals": deepcopy(candidate.get("raw_signals")),
               "evidence_positions": list(positions)}
        for event in truths:
            if harness_only or not mapped or not _spatial_match(region, _region(event["region_xywh"])):
                continue
            inside = [r for r in available
                      if event["start"] <= r["generator_id"] < event["end_exclusive"]]
            if event["id"] in persistent:
                diagnostic = persistent[event["id"]]
                if generator_start == 0 and generator_end == clip_frames and region != full_frame:
                    diagnostic["continuity_candidate_ids"].append(candidate_id)
                elif generator_start <= 1 and region != full_frame:
                    diagnostic["initial_observation_candidate_ids"].append(candidate_id)
                _append_unique_evidence(diagnostic["evidence"], inside,
                                        persistent_evidence_positions[event["id"]])
            ds, de = generator_start - event["start"], generator_end - event["end_exclusive"]
            match = truth_matches[event["id"]]
            hud_exception = (allow_persistent_hud and rejection == "whole_clip"
                             and event["id"] == "persistent_hud"
                             and event["id"] in persistent
                             and _area(region) < width * height * 0.5 and bool(inside))
            if (rejection and not hud_exception) or abs(ds) > 1 or abs(de) > 1:
                # Only overlapping intervals are localization/overreach diagnostics.
                if generator_start < event["end_exclusive"] and generator_end > event["start"]:
                    rejected = {"candidate_id": candidate_id, "start_delta_frames": ds,
                                "end_delta_frames": de, "reason": rejection or "boundary_overreach"}
                    match["temporal_rejections"].append(rejected)
                    row["temporal_rejections"].append(dict(rejected, truth_id=event["id"]))
                continue
            # Tolerance alone must never turn an adjacent non-overlapping interval into a match.
            if generator_start >= event["end_exclusive"] or generator_end <= event["start"]:
                continue
            row["truth_ids"].append(event["id"])
            match["candidate_ids"].append(candidate_id)
            match[f"{kind}_candidate_ids"].append(candidate_id)
            if hud_exception:
                row["persistent_hud_exception_truth_ids"].append(event["id"])
            match["matched_boundaries"].append({"candidate_id": candidate_id,
                                               "trigger": trigger, "candidate_kind": kind,
                                               "start_delta_frames": ds,
                                               "end_delta_frames": de,
                                               "generator_start": generator_start,
                                               "generator_end_exclusive": generator_end,
                                               "persistent_hud_exception": hud_exception,
                                               "intersection_over_candidate_area":
                                               _intersection(region, _region(event["region_xywh"])) / _area(region)})
            if inside:
                row["usable_truth_ids"].append(event["id"])
                match["usable_candidate_ids"].append(candidate_id)
                match[f"usable_{kind}_candidate_ids"].append(candidate_id)
                _append_unique_evidence(match["evidence"], inside,
                                        truth_evidence_positions[event["id"]])
        results.append(row)

    metrics = {}
    for tier in ("easy", "challenge"):
        matches = [m for m in truth_matches.values() if m["tier"] == tier]
        metrics[tier] = _recall_metrics(matches)
        metrics[tier]["by_candidate_kind"] = {
            kind: _recall_metrics(matches, f"{kind}_candidate_ids", f"usable_{kind}_candidate_ids")
            for kind in kinds}
    ordinary = [r for r in results if not r["harness_only"]]
    noise = [r["id"] for r in ordinary if not r["truth_ids"]]
    histogram = Counter(durations)
    overreach = [r["id"] for r in ordinary if r["temporal_rejections"]]
    return {"fixture_id": fixture["id"], "split": fixture.get("split"),
            "metric_policy": {"spatial_intersection_over_min_area": 0.8,
                              "minimum_intersection_over_candidate_area": 0.25,
                              "boundary_tolerance_frames": 1,
                              "effectively_full_clip_boundary_tolerance_frames": 1,
                              "effectively_full_clip_minimum_frames": 4,
                              "full_frame_rejected": True,
                              "full_clip_rejected_by_default": True,
                              "allow_persistent_hud": bool(allow_persistent_hud),
                              "persistent_diagnostics_count_toward_strict_recall": False,
                              "recall_interpretation": "localized_observation_coverage",
                              "candidate_kind_basis": "explicit_detector_trigger",
                              "state_triggers": ["initial_structure", "regional_change"],
                              "structural_inspection_asserts_new_boundary": False,
                              "recall_asserts_semantic_or_visual_boundary_detection": False},
            "known_timing": known_timing,
            "timed_evidence_status": "available" if known_timing else "native_timing_unavailable",
            "coverage_duration_seconds": duration,
            "candidate_count": len(results), "non_harness_candidate_count": len(ordinary),
            "candidate_counts_by_trigger": dict(sorted(Counter(r["trigger"] or "unspecified"
                                                               for r in results).items())),
            "non_harness_candidate_counts_by_trigger": dict(sorted(Counter(r["trigger"] or "unspecified"
                                                                           for r in ordinary).items())),
            "candidates_per_video_minute": len(ordinary) * 60 / duration if duration else None,
            "harness_only_candidate_ids": [r["id"] for r in results if r["harness_only"]],
            "false_or_noise_candidate_ids": noise, "false_or_noise_candidate_count": len(noise),
            "false_or_noise_candidates_per_video_minute": len(noise) * 60 / duration if duration else None,
            "candidate_duration_frames": {"minimum": min(durations) if durations else None,
                                          "maximum": max(durations) if durations else None,
                                          "histogram": {str(k): histogram[k] for k in sorted(histogram)},
                                          "one_frame_count": histogram[1]},
            "temporal_overreach_candidate_ids": overreach,
            "rejected_candidate_ids": [r["id"] for r in results
                                       if r["rejection_reason"] and not r["truth_ids"]],
            "persistent_hud_exception_candidate_ids": [r["id"] for r in results
                                                        if r["persistent_hud_exception_truth_ids"]],
            "shared_candidate_matches": [{"candidate_id": r["id"], "truth_ids": r["truth_ids"],
                                          "usable_truth_ids": r["usable_truth_ids"]}
                                         for r in results if len(r["truth_ids"]) > 1],
            "metrics": metrics, "truth_matches": list(truth_matches.values()),
            "persistent_truth_diagnostics": list(persistent.values()),
            "candidates": results, "evidence_frame_count": len(records),
            "usable_evidence_frame_count": sum(r["usable"] for r in record_results),
            "evidence": record_results,
            "generator_mapping": {"mapped_frame_count": len(ids), "truth_frame_count": clip_frames,
                                  "complete": set(ids.values()) == set(range(clip_frames))}}

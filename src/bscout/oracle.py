"""Independent checked-ID timing, survival, lossless and seek-path verifier."""
from __future__ import annotations

from fractions import Fraction
from pathlib import Path
import random
import numpy as np
from .common import sha256
from .corpus import load_corpus, planes_for
from .frames import native_planes, read_id
from .ledger import ledger, rows, select_video, presented, recover


def nearest(value: Fraction) -> int:
    """Nearest integer, exact ties away from zero (including negative PTS)."""
    sign = -1 if value < 0 else 1
    v = abs(value)
    return sign * ((2*v.numerator + v.denominator) // (2*v.denominator))


def timing_check(truth_pts, decoded_pts, decoded_tb):
    expected = Fraction(truth_pts, 60000)
    ticks = expected / decoded_tb
    rounded = nearest(ticks)
    error = Fraction(decoded_pts) * decoded_tb - expected
    if decoded_pts != rounded:
        raise ValueError(f"PTS mismatch: expected {rounded}, emitted {decoded_pts}")
    if abs(error) > decoded_tb / 2:
        raise ValueError("Declared nearest tick bound exceeded")
    return {"exact": ticks.denominator == 1, "error_seconds": [error.numerator, error.denominator],
            "bound_seconds": [(decoded_tb/2).numerator, (decoded_tb/2).denominator]}


def survival(spec, fixture, index, frame, event):
    expected = planes_for(spec, fixture, index)
    absent = planes_for(spec, fixture, index, omit=event["id"])
    decoded = native_planes(frame)[0]
    x, y, w, h = event["region_xywh"]
    signal, observed, error = [], [], []
    for p in range(3):
        div = 1 if p == 0 else 2
        region = np.s_[y//div:(y+h)//div, x//div:(x+w)//div]
        e, b, d = (a[p][region].astype(np.float64) for a in (expected, absent, decoded))
        signal.append((e-b).ravel())
        observed.append((d-b).ravel())
        error.append((d-e).ravel())
    signal, observed, error = map(np.concatenate, (signal, observed, error))
    power = float(np.dot(signal, signal))
    if power == 0:
        raise ValueError("Annotated event has zero counterfactual pixel signal")
    projection = float(np.dot(signal, observed)/power)
    normalized_rmse = float(np.sqrt(np.dot(error, error)/power))
    survives = projection >= 0.5 and normalized_rmse <= 0.5
    return {"projection": projection, "normalized_rmse": normalized_rmse,
            "status": "survived" if survives else "degraded"}


def verify_fixture(spec, fixture, media, ledger_path):
    import av
    source = Path(media) / fixture["filename"]
    before = sha256(source)
    trailer = ledger(source, ledger_path)
    entries = list(rows(ledger_path))
    header = next((r for r in entries if r["type"] == "header"), None)
    frame_rows = [r for r in entries if r["type"] == "frame"]
    if header is None:
        raise ValueError("Fixture ledger failed to open")
    no_timing = fixture["name"] == "no_timing"
    if not no_timing and trailer["status"] != "complete":
        raise ValueError(f"Fixture ledger incomplete: {trailer}")
    if len(frame_rows) != len(fixture["pts"]):
        raise ValueError("Fixture frame count changed after encoding")
    seen, timing_results = [], []
    previous_pts = None
    metrics = {e["id"]: [] for e in fixture["events"]}
    lossless_mismatches = 0
    with av.open(str(source), options={"ignore_editlist": "0"}) as container:
        stream = select_video(container)
        for frame in presented(container, stream):
            i = read_id(frame, spec["harness"])
            # ID, never decode ordinal, selects generator truth. Strict ordering
            # subsequently exposes drops, duplicates and presentation reorder.
            if not 0 <= i < len(fixture["pts"]):
                raise ValueError("Frame-ID outside frozen truth")
            if seen and i <= seen[-1]:
                raise ValueError("Frame-ID mapping not monotonic one-to-one")
            seen.append(i)
            if not no_timing:
                if frame.pts is None:
                    raise ValueError("Known-timing fixture emitted unknown PTS")
                timing_results.append(timing_check(fixture["pts"][i], frame.pts, frame.time_base))
                if previous_pts is not None and frame.pts <= previous_pts:
                    raise ValueError("Known fixture timing is not strictly monotonic one-to-one")
                previous_pts = frame.pts
            elif frame.pts is not None:
                raise ValueError("Raw H264 unexpectedly has known timing; review fixture contract")
            if fixture["name"] == "lossless":
                if not all(np.array_equal(a, b) for a, b in
                           zip(native_planes(frame)[0], planes_for(spec, fixture, i))):
                    lossless_mismatches += 1
            for event in fixture["events"]:
                if event["start"] <= i < event["end_exclusive"]:
                    metrics[event["id"]].append(survival(spec, fixture, i, frame, event))
    if seen != list(range(len(fixture["pts"]))):
        raise ValueError("ID mapping missing generator frames")
    events = []
    for event in fixture["events"]:
        values = metrics[event["id"]]
        if len(values) != event["end_exclusive"]-event["start"]:
            raise ValueError("Annotated event frame missing")
        degraded = sum(v["status"] == "degraded" for v in values)
        if event["tier"] == "easy" and degraded:
            raise ValueError(f"Easy event erased/degraded: {event['id']}")
        events.append({"id": event["id"], "tier": event["tier"], "frames": len(values),
                       "degraded_frames": degraded, "status": "degraded" if degraded else "survived",
                       "minimum_projection": min(v["projection"] for v in values),
                       "maximum_normalized_rmse": max(v["normalized_rmse"] for v in values)})
    if lossless_mismatches:
        raise ValueError("Lossless YUV pixel truth mismatch")
    if fixture["audio_before_video"] and header["selected_stream_index"] != 1:
        raise ValueError("Audio-before-video selected wrong stream")
    keys = [r["pts"] for r in frame_rows if r["key_frame"] and r["pts"] is not None]
    # FFmpeg AVPictureType numeric values: I=1, P=2, B=3.
    b_frames = sum(r["pict_type"] in ("3", "B") for r in frame_rows)
    if fixture["name"] in {"main60", "main30"}:
        gop = fixture["encoder"]["gop"]
        if not b_frames or not frame_rows[gop]["key_frame"]:
            raise ValueError("Required long GOP/B-frame structure absent")
        event_by_id = {e["id"]: e for e in fixture["events"]}
        if frame_rows[event_by_id["one_b_phase"]["start"]]["pict_type"] not in ("3", "B"):
            raise ValueError("Annotated B-frame phase is not B")
    targets = {0, len(frame_rows)-1}
    for e in fixture["events"]:
        targets.update(range(e["start"], e["end_exclusive"]))
    targets.update(i-1 for i, row in enumerate(frame_rows) if row["key_frame"] and i)
    targets.update(random.Random(fixture["seed"]).sample(range(len(frame_rows)), 12))
    recovery = []
    if not no_timing:
        for i in sorted(targets):
            _, proof = recover(source, frame_rows[i], header, keys)
            recovery.append({"generator_id": seen[i], **proof})
        # Prove absent canonical known targets fail, never select a neighbor.
        missing = dict(frame_rows[-1])
        missing["pts"] += 100000000
        missing["identity"] = [before, header["selected_stream_index"], missing["pts"], 0]
        try:
            recover(source, missing, header, keys)
        except ValueError as exc:
            if "never emitted" not in str(exc):
                raise
        else:
            raise ValueError("Absent exact known target falsely recovered")
    elif trailer["status"] != "diagnostic" or trailer["timing"]["missing"] != len(seen):
        raise ValueError("Unknown-timing input falsely reported healthy")
    unchanged = sha256(source) == before
    if not unchanged:
        raise ValueError("Oracle modified source")
    return {"id": fixture["id"], "status": "pass", "frames": len(seen),
            "mapping": "checked luma frame-ID -> frozen generator index; monotonic bijection",
            "timing": {"status": "unknown" if no_timing else "pass", "rule": spec["rounding"],
                       "exact_frames": sum(v["exact"] for v in timing_results),
                       "rounded_frames": sum(not v["exact"] for v in timing_results),
                       "max_abs_error_seconds": max((abs(Fraction(*v["error_seconds"])) for v in timing_results),
                                                    default=Fraction(0)).__float__()},
            "origins": {k: header[k] for k in ("container_start", "stream_start", "first_presented_pts",
                                               "origin_pts", "first_presented_time_base")},
            "selected_stream_index": header["selected_stream_index"], "b_frames": b_frames,
            "key_pts": keys, "PTS_behavior": trailer["timing"], "ledger_status": trailer["status"],
            "survival": events, "lossless_pixel_exact": lossless_mismatches == 0
            if fixture["name"] == "lossless" else None,
            "recovery_count": len(recovery), "recovery": recovery,
            "skips": ["exact seek recovery unavailable: raw H264 emits no PTS"] if no_timing else [],
            "T2": [{"generator_id": seen[i], "native_sha256": frame_rows[i]["native_sha256"]}
                   for i in sorted(targets)],
            "T3": {"media_sha256": before, "ledger_sha256": sha256(ledger_path)},
            "resources": trailer, "source_unchanged": unchanged}


def verify(media, out, corpus="corpus-v1", split="all", progress=None):
    spec, truth, frozen = load_corpus(corpus)
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    results = []
    for fixture in truth["fixtures"]:
        if split != "all" and fixture["split"] != split:
            continue
        if progress:
            progress(fixture["id"])
        try:
            result = verify_fixture(spec, fixture, Path(media), out / (fixture["id"]+".jsonl"))
        except Exception as exc:
            result = {"id": fixture["id"], "status": "fail", "error": f"{type(exc).__name__}: {exc}"}
        results.append(result)
    return {"version": "bscout-oracle-v1", "corpus": corpus, "T1": frozen, "fixtures": results}

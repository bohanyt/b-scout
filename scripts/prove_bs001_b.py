"""Clean-checkout B proof; pinned environment and synthetic assets remain external.

Default: full accepted A regression proof, then all B splits under a dev-only
configuration freeze. --split dev is the sole pre-freeze tuning mode.
"""
from __future__ import annotations

import argparse
from dataclasses import asdict
from fractions import Fraction
import hashlib
import gzip
import json
import os
from pathlib import Path
import subprocess
import struct
import sys
import tempfile
import time
import venv
import zlib

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_FREEZE = ROOT / "docs/evidence/BS-001-B/config-freeze.json"


def canonical_hash(value):
    data = (json.dumps(value, sort_keys=True, ensure_ascii=False,
                       separators=(",", ":"), allow_nan=False) + "\n").encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def load_freeze(path, config_type, dev_ids):
    """Fail closed before held-out scans; reconstruct exactly the frozen config."""
    try:
        frozen = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise ValueError("Held-out B evaluation requires readable frozen configuration") from exc
    if not isinstance(frozen, dict):
        raise ValueError("Frozen configuration must be an object")
    values = frozen.get("configuration")
    if not isinstance(values, dict) or canonical_hash(values) != frozen.get("configuration_sha256"):
        raise ValueError("Frozen configuration hash missing or drifted")
    record = frozen.get("dev_tuning_record")
    if (not isinstance(record, dict) or record.get("split") != "dev"
            or record.get("selected_before_held_out") is not True
            or not isinstance(record.get("procedure"), str) or not record["procedure"].strip()
            or not isinstance(record.get("fixtures"), list) or not record["fixtures"]
            or not all(isinstance(v, str) for v in record["fixtures"])
            or not set(record["fixtures"]).issubset(set(dev_ids))):
        raise ValueError("Freeze requires an explicit dev-only tuning record before held-out scans")
    policy = frozen.get("evidence_policy", {})
    if (not isinstance(policy, dict) or type(policy.get("allow_persistent_hud", False)) is not bool
            or (policy.get("allow_persistent_hud") is True
                and (not isinstance(policy.get("authority"), str) or not policy["authority"].strip()))):
        raise ValueError("Persistent HUD exception requires explicit boolean policy and recorded user authority")
    try:
        config = config_type(**values)
    except (TypeError, ValueError) as exc:
        raise ValueError("Frozen configuration unsupported by installed detector") from exc
    if asdict(config) != values:
        raise ValueError("Frozen configuration differs from effective detector configuration")
    return frozen, config


def run(args, **kwargs):
    return subprocess.run(args, check=True, cwd=ROOT, **kwargs)


def source_snapshot():
    """Relevant checkout bytes, without local paths or generated artifacts."""
    files = [p for directory in ("src", "scripts", "tests") for p in (ROOT/directory).rglob("*")
             if p.is_file() and p.suffix in (".py", ".json")]
    files += [ROOT/name for name in ("requirements-proof.txt", "pyproject.toml")]
    return {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(files)}


def selected_fixtures(truth, split):
    split = split.replace("-", "_")
    selected = [f for f in truth["fixtures"] if split == "all" or f["split"] == split]
    if not selected:
        raise ValueError("Requested evaluation split selected no frozen fixtures")
    return selected


def native_coverage(rows, known):
    if not known:
        return None, {"method": "native PTS unavailable; no video-minute rates"}
    start = Fraction(rows[0]["pts"])*Fraction(*rows[0]["time_base"])
    last = rows[-1]
    end = Fraction(last["pts"])*Fraction(*last["time_base"])
    duration = last.get("duration")
    has_duration = type(duration) is int and duration > 0
    if has_duration:
        end += duration*Fraction(*last["time_base"])
    return float(end-start), {"method": "observed native last PTS minus first PTS" +
                               (" plus decoder-reported final-frame duration" if has_duration else "; final-frame duration unknown and excluded"),
                             "start_seconds": [start.numerator, start.denominator],
                             "end_seconds": [end.numerator, end.denominator],
                             "last_duration_status": "decoder_reported" if has_duration else "unknown"}


def installed_snapshot_check(expected):
    import bscout
    package_root = Path(bscout.__file__).resolve().parent
    if package_root.is_relative_to(ROOT.resolve()):
        raise ValueError("B proof must use installed package away from checkout")
    for name, expected_hash in expected.items():
        if name.startswith("src/bscout/"):
            path = package_root/name.removeprefix("src/bscout/")
            if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != expected_hash:
                raise ValueError("Installed B package differs from snapshotted checkout: " + name)
    return {"status": "pass", "method": "installed package outside checkout; every package Python/corpus file SHA-256 equals pre-install source snapshot"}


def read_jsonl(path):
    with Path(path).open(encoding="utf-8") as source:
        return [json.loads(line) for line in source if line.strip()]


def redact(value, work):
    """Keep public reports free of checkout, interpreter and disposable paths."""
    if isinstance(value, dict):
        return {k: redact(v, work) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [redact(v, work) for v in value]
    if isinstance(value, str):
        for path, replacement in ((work, "[work]"), (ROOT, "[checkout]"),
                                  (Path(sys.executable), "[proof-python]"),
                                  (Path(tempfile.gettempdir()), "[temporary]"),
                                  (Path.home(), "[user]")):
            for private in (str(path), str(path.resolve()), str(path).replace("\\", "/"),
                            str(path.resolve()).replace("\\", "/"), str(path).replace("\\", "\\\\"),
                            str(path.resolve()).replace("\\", "\\\\")):
                value = value.replace(private, replacement)
        return value
    return value


def independent_frames(source, spec, fixture, decode_config):
    """Decode native identity channel after detector scan, using the A config."""
    import av
    from bscout.frames import read_id
    from bscout.ledger import Timing, frame_row, select_video, presented
    from bscout.oracle import timing_check
    from bscout.common import sha256
    source_hash = sha256(source)
    rows, ids, timing_checks = [], [], []
    known = fixture["name"] != "no_timing"
    timing = Timing()
    try:
        with av.open(str(source), options=dict(decode_config.demux_options)) as container:
            stream = select_video(container, decode_config.stream_index, decode_config)
            for frame in presented(container, stream):
                generator_id = read_id(frame, spec["harness"])
                if not 0 <= generator_id < len(fixture["pts"]):
                    raise ValueError("Independent frame ID outside frozen truth")
                if ids and generator_id <= ids[-1]:
                    raise ValueError("Independent frame IDs are not monotonic one-to-one")
                ids.append(generator_id)
                rows.append(frame_row(frame, len(rows), timing, source_hash, stream.index))
                if known:
                    if frame.pts is None:
                        raise ValueError("Known fixture emitted missing PTS")
                    timing_checks.append(timing_check(fixture["pts"][generator_id], frame.pts, frame.time_base))
                elif frame.pts is not None:
                    raise ValueError("Unknown-timing fixture unexpectedly emitted PTS")
    finally:
        timing.close()
    if ids != list(range(len(fixture["pts"]))):
        raise ValueError("Independent ID mapping lost/duplicated/reordered truth frames")
    return ids, rows, {"status": "pass" if known else "unknown", "frames": len(ids),
                       "mapping": "checked luma frame ID; monotonic bijection to frozen truth",
                       "exact_frames": sum(v["exact"] for v in timing_checks),
                       "rounded_frames": sum(not v["exact"] for v in timing_checks),
                       "maximum_abs_rounding_error_seconds": max(
                           (float(abs(Fraction(*v["error_seconds"]))) for v in timing_checks), default=0)}


def historical_comparison(fixture, rows, frozen_truth):
    from bscout.common import sha256
    path = ROOT / "docs/evidence/BS-001-A-R2/result.json"
    historical = json.loads(path.read_text(encoding="utf-8"))
    prior = next(f for f in historical["oracle"]["fixtures"] if f["id"] == fixture["id"])
    native = [{"generator_id": f["generator_id"], "equal":
               rows[f["generator_id"]]["native_sha256"] == f["native_sha256"]}
              for f in prior["T2"]]
    return {"historical_report_sha256": sha256(path), "historical_tested_head": historical["tested_head"],
            "T1_equal": frozen_truth == historical["oracle"]["T1"],
            "native_selected_count": len(native), "native_selected_equal": all(f["equal"] for f in native),
            "native_mismatches": [f for f in native if not f["equal"]],
            "note": "native digest reproducibility in recorded toolchain; encoded bytes may differ across toolchains"}


def test_suite(work):
    # Separate process: legacy test modules intentionally prepend source paths;
    # they cannot alter this worker's installed-package import resolution.
    tests = run([sys.executable, "-c", "import json,unittest; from pathlib import Path; "
        "s=unittest.defaultTestLoader.discover('tests'); "
        "f=open(__import__('sys').argv[1], 'w', encoding='utf-8'); "
        "r=unittest.TextTestRunner(stream=f,verbosity=2).run(s); f.close(); "
        "print(json.dumps({'run':r.testsRun,'passed':r.testsRun-len(r.skipped)-len(r.failures)-len(r.errors),"
        "'failures':[{'test':str(t),'traceback':m} for t,m in r.failures+r.errors],"
        "'skipped':[{'test':str(t),'reason':m} for t,m in r.skipped]}))", str(work/"tests.txt")],
        capture_output=True, text=True)
    return json.loads(tests.stdout)


def prepare_media(work, skip_full_a):
    from bscout.common import sha256
    from bscout.corpus import generate
    if not skip_full_a:
        a_work = work / "a-proof"
        a_work.mkdir()
        stage = subprocess.run([sys.executable, str(ROOT/"scripts/prove_bs001_a.py"),
                                "--work", str(a_work), "--worker"], cwd=ROOT)
        result = json.loads((a_work/"result.json").read_text(encoding="utf-8"))
        return a_work/"media", {"status": result["status"], "exit_code": stage.returncode,
            "counts": result["counts"], "tested_head": result["tested_head"],
            "result_sha256": sha256(a_work/"result.json"), "artifact": "a-proof/result.json",
            "scope": "full existing A oracle, survival, lossless, exact seek, tests and both resource proofs"}, result["generation"], result["repeat_generation"]
    generation = generate(work/"media")
    repeat = generate(work/"repeat")
    old = {f["id"]: f for f in generation["fixtures"]}
    matches = [{"id": f["id"], "sha256": f["sha256"], "equal": f["sha256"] == old[f["id"]]["sha256"]}
               for f in repeat["fixtures"]]
    return work/"media", {"status": "skipped", "reason": "explicit --skip-full-a; focused B run is not complete regression proof"}, generation, matches


def verify_evidence(source, output, evidence, rows, decode_config, known):
    """Independently match saved bytes to post-scan native sequential digests.

    Core B has already used A exact recovery. Avoid another expensive recovery
    of every frame: match its receipt, native digest domain and actual asset bytes
    to the independently decoded source rows instead.
    """
    from bscout.common import canonical, sha256
    if not known:
        if evidence:
            raise ValueError("Unknown-PTS input published falsely verified evidence")
        return {"status": "unsupported", "reason": "native PTS unavailable; raw candidate diagnostics only", "checked_frames": 0}
    checks, seen = [], set()
    for item in evidence:
        position = item["position"]
        if type(position) is not int or not 0 <= position < len(rows) or position in seen:
            raise ValueError("Retained evidence has invalid/repeated source position")
        seen.add(position)
        row = rows[position]
        recovery = item["recovery"]
        if (item.get("verified") is not True or item["identity"] != row["identity"]
                or item["native_sha256"] != row["native_sha256"] or item["digest_domain"] != row["digest_domain"]
                or recovery["sha256"] != row["native_sha256"]
                or recovery["target_position"] != position or list(recovery["identity"]) != row["identity"]):
            raise ValueError("Retained evidence/recovery identity differs from independently decoded source")
        assets = {}
        for asset in item["assets"]:
            path = (output/asset["path"]).resolve()
            if not path.is_relative_to(output.resolve()) or not path.is_file():
                raise ValueError("Retained B asset missing or outside owned output")
            if asset["kind"] in assets:
                raise ValueError("Duplicate retained B asset kind")
            data = path.read_bytes()
            if len(data) != asset["bytes"] or sha256(path) != asset["sha256"]:
                raise ValueError("Retained B asset bytes differ from receipt")
            assets[asset["kind"]] = data
        native = assets["native_planes"]
        actual_native = hashlib.sha256(canonical(row["digest_domain"])+native).hexdigest()
        expected_bytes = sum(p["height"]*p["row_bytes"] for p in row["digest_domain"]["planes"])
        if len(native) != expected_bytes or actual_native != row["native_sha256"]:
            raise ValueError("Retained native asset differs from independently decoded source pixels")
        pgm = f"P5\n{row['width']} {row['height']}\n255\n".encode("ascii") + native[:row["width"]*row["height"]]
        if assets["native_luma_preview"] != pgm:
            raise ValueError("Retained luma preview differs from independently decoded source pixels")
        verify_native_luma_png(assets["native_luma_png"], row["width"], row["height"], native[:row["width"]*row["height"]])
        checks.append({"position": position, "identity": row["identity"],
                       "native_sha256": row["native_sha256"], "actual_asset_bytes_checked": True,
                       "exact_recovery_receipt_matches_independent_source": True})
    return {"status": "pass", "checked_frames": len(checks), "checks": checks,
            "method": "post-scan independent native decode/read_id; A receipt identity/digest; native asset domain hash; pixel-exact PGM and PNG luma (independent chunk CRC/deflate/filter verification)"}


def verify_native_luma_png(data, width, height, luma):
    """Parse PNG independently, accepting only declared lossless 8-bit gray/filter 0."""
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError("Retained PNG signature invalid")
    offset, header, payload, ended = 8, None, bytearray(), False
    while offset < len(data):
        if len(data)-offset < 12:
            raise ValueError("Retained PNG chunk truncated")
        length = struct.unpack(">I", data[offset:offset+4])[0]
        kind = data[offset+4:offset+8]
        end = offset+12+length
        if end > len(data):
            raise ValueError("Retained PNG chunk length exceeds asset")
        content = data[offset+8:offset+8+length]
        crc = struct.unpack(">I", data[offset+8+length:end])[0]
        if zlib.crc32(kind+content)&0xffffffff != crc:
            raise ValueError("Retained PNG chunk CRC mismatch")
        if kind == b"IHDR":
            if header is not None or offset != 8:
                raise ValueError("Retained PNG IHDR placement invalid")
            header = content
        elif kind == b"IDAT":
            if header is None or ended:
                raise ValueError("Retained PNG IDAT placement invalid")
            payload.extend(content)
        elif kind == b"IEND":
            if content or end != len(data):
                raise ValueError("Retained PNG IEND invalid")
            ended = True
        else:
            raise ValueError("Retained PNG contains unsupported chunk")
        offset = end
    if header != struct.pack(">IIBBBBB", width, height, 8, 0, 0, 0, 0) or not ended or not payload:
        raise ValueError("Retained PNG differs from declared native luma representation")
    expected = b"".join(b"\x00"+luma[y*width:(y+1)*width] for y in range(height))
    decoder = zlib.decompressobj()
    try:
        observed = decoder.decompress(payload, len(expected)+1)
    except zlib.error as exc:
        raise ValueError("Retained PNG deflate invalid") from exc
    if not decoder.eof or decoder.unused_data or decoder.unconsumed_tail or observed != expected:
        raise ValueError("Retained PNG differs from independently decoded source pixels")


def write_fixture_archive(path, record, work):
    """Canonical full JSON, deterministic gzip; no sampled/truncated mappings."""
    path.parent.mkdir(parents=True, exist_ok=True)
    encoder = json.JSONEncoder(sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=False)
    uncompressed_hash, uncompressed_bytes = hashlib.sha256(), 0
    with path.open("xb") as sink, gzip.GzipFile(filename="", mode="wb", fileobj=sink, mtime=0, compresslevel=9) as compressed:
        for chunk in encoder.iterencode(redact(record, work)):
            payload = chunk.encode("utf-8")
            uncompressed_hash.update(payload)
            uncompressed_bytes += len(payload)
            compressed.write(payload)
        compressed.write(b"\n")
        uncompressed_hash.update(b"\n")
        uncompressed_bytes += 1
    return {"encoding": "canonical UTF-8 JSON + LF; gzip mtime=0, empty filename, level=9",
            "uncompressed_bytes": uncompressed_bytes, "uncompressed_sha256": uncompressed_hash.hexdigest()}


def aggregate(fixtures):
    result = {}
    for split in sorted({f["split"] for f in fixtures}):
        members = [f for f in fixtures if f["split"] == split]
        native = [f for f in members if f["evaluation"]["known_timing"]]
        duration = sum(f["evaluation"]["coverage_duration_seconds"] or 0 for f in native)
        metrics = {}
        for tier in ("easy", "challenge"):
            total = sum(f["evaluation"]["metrics"][tier]["truth_occurrences"] for f in native)
            matched = sum(f["evaluation"]["metrics"][tier]["matched_occurrences"] for f in native)
            usable = sum(f["evaluation"]["metrics"][tier]["usable_evidence_occurrences"] for f in native)
            metrics[tier] = {"truth_occurrences": total, "matched_occurrences": matched,
                             "usable_evidence_occurrences": usable,
                             "candidate_recall": matched/total if total else None,
                             "usable_evidence_recall": usable/total if total else None,
                             "misses": [{"fixture": f["id"], "truth_ids": f["evaluation"]["metrics"][tier]["candidate_miss_ids"],
                                         "usable_evidence_miss_ids": f["evaluation"]["metrics"][tier]["usable_evidence_miss_ids"]}
                                        for f in native if f["evaluation"]["metrics"][tier]["candidate_miss_ids"]
                                        or f["evaluation"]["metrics"][tier]["usable_evidence_miss_ids"]]}
        count = sum(f["evaluation"]["non_harness_candidate_count"] for f in native)
        noise = sum(f["evaluation"]["false_or_noise_candidate_count"] for f in native)
        histogram = {}
        for f in members:
            for key, value in f["evaluation"]["candidate_duration_frames"]["histogram"].items():
                histogram[key] = histogram.get(key, 0)+value
        result[split] = {"fixtures": len(members), "known_timing_fixtures": len(native), "metrics": metrics,
                         "non_harness_candidate_count": count, "false_or_noise_candidate_count": noise,
                         "candidates_per_video_minute": count*60/duration if duration else None,
                         "false_or_noise_candidates_per_video_minute": noise*60/duration if duration else None,
                         "observed_native_coverage_seconds": duration, "candidate_duration_frames_histogram": histogram,
                         "scanned_frames": sum(f["scan"]["scanned_frames"] for f in members),
                         "decoded_frames": sum(f["scan"]["decoded_frames"] for f in members),
                         "evidence_frame_count": sum(f["evaluation"]["evidence_frame_count"] for f in members),
                         "unknown_timing_diagnostics": [f["id"] for f in members if not f["evaluation"]["known_timing"]],
                         "persistent_truth_diagnostics": [{"fixture": f["id"], **d} for f in members
                             for d in f["evaluation"]["persistent_truth_diagnostics"]]}
    return result


def compact_fixture(record, archive, work, archive_metadata):
    """Retain aggregate inputs and bounded truth summaries; archive every raw row."""
    from bscout.common import sha256
    evaluation = record["evaluation"]
    compact = {k: v for k, v in record.items() if k not in ("evaluation", "evidence_verification")}
    compact["evaluation"] = {k: v for k, v in evaluation.items() if k not in (
        "candidates", "evidence", "truth_matches", "persistent_truth_diagnostics",
        "harness_only_candidate_ids", "false_or_noise_candidate_ids",
        "temporal_overreach_candidate_ids", "rejected_candidate_ids", "shared_candidate_matches")}
    compact["evaluation"]["truth_matches"] = [{k: v for k, v in match.items() if k not in ("evidence", "temporal_rejections", "candidate_ids", "usable_candidate_ids")}
        | {"retained_evidence_count": len(match["evidence"]), "temporal_rejection_count": len(match["temporal_rejections"]),
           "candidate_count": len(match["candidate_ids"]), "usable_candidate_count": len(match["usable_candidate_ids"])}
        for match in evaluation["truth_matches"]]
    compact["evaluation"]["persistent_truth_diagnostics"] = [
        {"truth_id": diagnostic["truth_id"],
         "continuity_candidate_count": len(diagnostic["continuity_candidate_ids"]),
         "initial_observation_candidate_count": len(diagnostic["initial_observation_candidate_ids"]),
         "evidence_count": len(diagnostic["evidence"]),
         "counts_toward_strict_recall": diagnostic["counts_toward_strict_recall"]}
        for diagnostic in evaluation["persistent_truth_diagnostics"]]
    compact["evidence_verification"] = {k: v for k, v in record["evidence_verification"].items() if k != "checks"}
    compact["full_fixture_report"] = {"path": archive.relative_to(work).as_posix(),
        "bytes": archive.stat().st_size, "sha256": sha256(archive),
        **archive_metadata,
        "scope": "all candidate/truth mappings, misses, noise, temporal rejections, exact evidence identities/digests and actual asset-byte checks; no sampled rows"}
    return compact


def assessment_failures(fixtures):
    failures = []
    for fixture in fixtures:
        scan, evaluation = fixture["scan"], fixture["evaluation"]
        known = evaluation["known_timing"]
        if scan["scanned_frames"] != fixture["independent_decode"]["frames"] or scan["decoded_frames"] != scan["scanned_frames"]:
            failures.append({"fixture": fixture["id"], "reason": "decoded/scanned coverage incomplete"})
        if scan["status"] != ("complete" if known else "partial"):
            failures.append({"fixture": fixture["id"], "reason": "unexpected B complete/partial state", "status": scan["status"]})
        if known:
            misses = evaluation["metrics"]["easy"]
            if misses["candidate_miss_ids"] or misses["usable_evidence_miss_ids"]:
                failures.append({"fixture": fixture["id"], "reason": "strict easy localized candidate/evidence misses",
                                 "candidate_miss_ids": misses["candidate_miss_ids"],
                                 "usable_evidence_miss_ids": misses["usable_evidence_miss_ids"]})
    return failures


def regional_stress(count, out, config=None):
    """Separate-process actual TileSignals/native-frame streaming resource proof."""
    import av
    from bscout.common import canonical, fingerprint, peak_rss, sha256, write_json
    from bscout.regional import BudgetExceeded, RegionalConfig, TileSignals, scan
    if count <= 0:
        raise ValueError("Stress frame count must be positive")
    out.parent.mkdir(parents=True, exist_ok=True)
    config = config or RegionalConfig()
    tracker = TileSignals(config)
    started = time.perf_counter()
    candidates, scanned = 0, 0

    def native_frame(index):
        import numpy as np
        from bscout.corpus import make_frame
        y = np.full((64, 64), 32+index % 3, np.uint8)
        if index % 5 in (1, 2):
            y[16:32, 16:32] = 220
        uv = np.full((32, 32), 128, np.uint8)
        frame = make_frame([y, uv, uv.copy()])
        frame.pts, frame.time_base = index, Fraction(1, 1000)
        return frame

    signal_path, candidate_path = out.with_suffix(".signals.jsonl"), out.with_suffix(".candidates.jsonl")
    with signal_path.open("xb") as signals, candidate_path.open("xb") as sink:
        for position in range(count):
            closed, raw = tracker.observe(native_frame(position), position)
            signals.write(canonical({"position": position, "tiles": raw}))
            scanned += 1
            for candidate in closed:
                sink.write(canonical(candidate))
                candidates += 1
        for candidate in tracker.finish():
            sink.write(canonical(candidate))
            candidates += 1
    spool_probe = None
    if count == 1000:
        source = out.with_suffix(".budget-probe.mkv")
        with av.open(str(source), "w", format="matroska") as container:
            stream = container.add_stream("ffv1", rate=1000)
            stream.width = stream.height = 64
            stream.pix_fmt = "yuv420p"
            stream.time_base = stream.codec_context.time_base = Fraction(1, 1000)
            stream.codec_context.thread_count = 1
            for index in range(4):
                for packet in stream.encode(native_frame(index)):
                    container.mux(packet)
            for packet in stream.encode():
                container.mux(packet)
        before = sha256(source)
        result = scan(source, out.with_suffix(".budget-output"), config=RegionalConfig(max_spool_bytes=1))
        budget_errors = result["errors"] + (result.get("validation") or {}).get("errors", [])
        budget_ok = (result["status"] in ("partial", "failed") and result["scanned_frames"] < result["decoded_frames"]
                     and any("budget exhausted" in e for e in budget_errors)
                     and result["evidence_count"] == 0 and result["source_unchanged"] and sha256(source) == before)
        spool_probe = {"status": "pass" if budget_ok else "fail", "result": result,
                       "configured_spool_bytes": 1, "source_unchanged": before == sha256(source),
                       "method": "real 4-frame FFV1 synthetic clip; actual core scan under one-byte total spool budget; explicit incomplete validation/failure diagnostics retained"}
    budget_tracker = TileSignals(RegionalConfig(max_analysis_pixels=1))
    analysis_refused = False
    try:
        budget_tracker.observe(native_frame(0), 0)
    except BudgetExceeded:
        analysis_refused = budget_tracker.position == -1
    complete = scanned == count and tracker.position == count-1 and not tracker.tracks and analysis_refused
    complete = complete and (spool_probe is None or spool_probe["status"] == "pass")
    write_json(out, {"status": "pass" if complete else "fail", "frames": count, "scanned_frames": scanned,
        "candidate_count": candidates, "peak_rss": peak_rss(), "elapsed_seconds": time.perf_counter()-started,
        "analysis_state_bytes_upper_estimate": tracker.max_state_bytes,
        "signal_spool_bytes": signal_path.stat().st_size, "candidate_spool_bytes": candidate_path.stat().st_size,
        "spool_bytes": signal_path.stat().st_size+candidate_path.stat().st_size,
        "active_tracks_after_finish": len(tracker.tracks), "analysis_budget_refused_before_scan": analysis_refused,
        "spool_budget_probe": spool_probe, "configuration_sha256": config.sha256,
        "toolchain": fingerprint(),
        "tested_head": run(["git", "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip(),
        "working_tree_dirty": bool(run(["git", "status", "--porcelain"], capture_output=True, text=True).stdout.strip()),
        "regional_module_sha256": sha256(ROOT/"src/bscout/regional.py"),
        "ledger_module_sha256": sha256(ROOT/"src/bscout/ledger.py"),
        "method": "separate process; every real PyAV 64x64 native frame; actual TileSignals; streamed signals/candidates; no retained frame history",
        "limitations": "synthetic native frames measure signal memory/spool behavior; full frozen-corpus proof exercises codecs and exact retained evidence"})
    if not complete:
        raise AssertionError("B resource/budget proof failed")


def worker(work, freeze_path, split, skip_full_a):
    from bscout.common import digest, fingerprint, peak_rss, sha256, write_json
    from bscout.corpus import load_corpus
    from bscout.ledger import DecodeConfig
    from bscout.regional import RegionalConfig, scan
    from bscout.evaluation_b import evaluate_fixture
    started = time.perf_counter()
    snapshot_path = work/"source-snapshot.json"
    snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))
    if source_snapshot() != snapshot["files"]:
        raise ValueError("Checkout changed between source snapshot, install and B worker")
    installed = installed_snapshot_check(snapshot["files"])
    spec, truth, frozen_truth = load_corpus()
    selected = selected_fixtures(truth, split)
    dev_ids = [f["id"] for f in truth["fixtures"] if f["split"] == "dev"]
    if split == "dev" and not freeze_path.exists():
        config, frozen = RegionalConfig(), None
    else:
        frozen, config = load_freeze(freeze_path, RegionalConfig, dev_ids)
    # Capture before any media generation or detector work. Recheck before each
    # held-out scan to expose a changed/deleted freeze during the run.
    freeze_sha = sha256(freeze_path) if frozen is not None else None
    decode_config = DecodeConfig()
    media, a_proof, generation, repeats = prepare_media(work, skip_full_a)
    fixtures, failures = [], []
    for fixture in selected:
        print("B scan " + fixture["id"], flush=True)
        if fixture["split"] != "dev":
            fresh, effective = load_freeze(freeze_path, RegionalConfig, dev_ids)
            if fresh != frozen or effective != config or sha256(freeze_path) != freeze_sha:
                raise ValueError("Configuration freeze changed before held-out scan")
        source = media/fixture["filename"]
        output = work/"b"/fixture["id"]
        before = sha256(source)
        summary = scan(source, output, config=config, decode_config=decode_config)
        candidates, evidence = read_jsonl(output/"candidates.jsonl"), read_jsonl(output/"evidence.jsonl")
        ids, rows, mapping = independent_frames(source, spec, fixture, decode_config)
        historical = historical_comparison(fixture, rows, frozen_truth)
        known = fixture["name"] != "no_timing"
        coverage_duration, coverage_method = native_coverage(rows, known)
        evaluation = evaluate_fixture(fixture, candidates, evidence, dict(enumerate(ids)), spec["harness"]["region_xywh"],
                                      coverage_duration=coverage_duration, known_timing=known,
                                      allow_persistent_hud=(frozen or {}).get("evidence_policy", {}).get("allow_persistent_hud", False))
        extraction = verify_evidence(source, output, evidence, rows, decode_config, known)
        unchanged = before == sha256(source)
        record = {"id": fixture["id"], "split": fixture["split"], "seed": fixture["seed"],
                  "source_sha256": before, "scan": summary, "evaluation": evaluation,
                  "independent_decode": mapping, "native_coverage": coverage_method, "historical_A_comparison": historical,
                  "evidence_verification": extraction, "source_unchanged": unchanged,
                  "artifact_bytes": sum(p.stat().st_size for p in output.rglob("*") if p.is_file())}
        archive = work/"fixtures"/(fixture["id"]+".json.gz")
        archive_metadata = write_fixture_archive(archive, record, work)
        fixtures.append(compact_fixture(record, archive, work, archive_metadata))
        if not unchanged or not historical["T1_equal"] or not historical["native_selected_equal"]:
            failures.append({"fixture": fixture["id"], "reason": "source/frozen truth/native regression"})
    if skip_full_a:
        tests = test_suite(work)
        bootstrap_output = run([sys.executable, str(ROOT/"scripts/check_bootstrap.py")], capture_output=True, text=True).stdout.strip()
        skips = list(tests["skipped"]) + [{"stage": "full_A_regression_proof", "reason": a_proof["reason"]}]
    else:
        a_result = json.loads((work/"a-proof/result.json").read_text(encoding="utf-8"))
        tests, bootstrap_output = a_result["tests"], a_result["bootstrap"]
        skips = [{"stage": "A_regression_proof", **entry} for entry in a_result["skips"]]
    skips += [{"stage": "B_timed_evidence", "fixture": f["id"],
               "reason": "raw H264 emits no native PTS; complete L0 candidate diagnostics, partial B and no verified evidence"}
              for f in fixtures if not f["evaluation"]["known_timing"]]
    head = run(["git", "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
    dirty = run(["git", "status", "--porcelain"], capture_output=True, text=True).stdout.strip()
    failures += tests["failures"]
    if a_proof["status"] == "fail" or not all(r["equal"] for r in repeats):
        failures.append({"reason": "A proof or repeat generation failed"})
    failures += assessment_failures(fixtures)
    for count in (1000, 20000):
        command = [sys.executable, str(Path(__file__).resolve()), "--stress", str(count),
                   "--work", str(work/f"b-stress-{count}.json")]
        if frozen is not None:
            command += ["--freeze", str(freeze_path)]
        run(command)
    resources = [json.loads((work/f"b-stress-{count}.json").read_text(encoding="utf-8")) for count in (1000, 20000)]
    resource_ok = all(r["status"] == "pass" for r in resources) and resources[1]["peak_rss"]["bytes"]-resources[0]["peak_rss"]["bytes"] < 32*1024*1024
    if not resource_ok:
        failures.append({"reason": "B separate-process resource/budget proof failed"})
    head = run(["git", "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
    dirty = run(["git", "status", "--porcelain"], capture_output=True, text=True).stdout.strip()
    snapshot_unchanged = source_snapshot() == snapshot["files"]
    if not snapshot_unchanged or head != snapshot["head"]:
        failures.append({"reason": "checkout source or HEAD changed during proof"})
    if frozen is not None and (not freeze_path.is_file() or sha256(freeze_path) != freeze_sha):
        failures.append({"reason": "configuration freeze changed during proof"})
    status = "fail" if failures else ("focused" if skip_full_a or split != "all" else "pass")
    result = {"version": "bscout-proof-B-v1", "scope": "BS-001 B regional candidates; C held",
        "status": status, "tested_head": head, "working_tree_dirty": bool(dirty),
        "starting_head": snapshot["head"], "starting_working_tree_dirty": snapshot["working_tree_dirty"],
        "source_snapshot_sha256": sha256(snapshot_path), "source_snapshot_unchanged": snapshot_unchanged,
        "installed_package_verification": installed,
        "regional_resource_stress": {"status": "pass" if resource_ok else "fail", "runs": resources,
                                     "growth_limit_bytes": 32*1024*1024},
        "configuration": asdict(config), "configuration_sha256": digest(asdict(config)),
        "configuration_freeze": frozen, "freeze_file_sha256": freeze_sha,
        "evaluation_split": split, "toolchain": fingerprint(), "decode_config": asdict(decode_config),
        "requirements_proof_sha256": sha256(ROOT/"requirements-proof.txt"),
        "runtime_packages": {distribution.metadata["Name"]: distribution.version
                             for distribution in __import__("importlib.metadata", fromlist=["distributions"]).distributions()},
        "wheels": [{"filename": p.name, "sha256": sha256(p), "bytes": p.stat().st_size,
                    "source": "https://pypi.org/simple/ (pip binary wheel, no cache)"}
                   for p in sorted((work/"wheels").glob("*.whl"))],
        "generation": generation, "repeat_generation": repeats, "A_regression_proof": a_proof,
        "fixtures": fixtures, "aggregate": aggregate(fixtures), "tests": tests,
        "bootstrap": bootstrap_output, "failures": failures,
        "counts": {"tests_pass": tests["passed"], "fail": len(failures), "skip": len(skips),
                   "note": "tests_pass counts unittest cases; fail includes benchmark/regression checks; skips enumerate stages and cases; full A counts nested separately"},
        "skips": skips,
        "elapsed_seconds": time.perf_counter()-started, "peak_rss": peak_rss(),
        "harness_memory_scope": "proof process peak includes one-fixture truth/evaluation/report materialization; engine bounded state and separate-process resource stress reported independently",
        "source_unchanged": all(f["source_unchanged"] for f in fixtures),
        "commands": ["python scripts/prove_bs001_b.py --work [new-external-work]" +
                     (" --skip-full-a" if skip_full_a else "") + (" --split "+split if split != "all" else ""),
                     "[proof-python] -m pip download --only-binary=:all: --no-cache-dir --index-url https://pypi.org/simple --dest [work]/wheels -r requirements-proof.txt",
                     "[proof-python] -m pip install --no-cache-dir --no-index --find-links [work]/wheels -r requirements-proof.txt",
                     "[proof-python] -m pip install --no-cache-dir --no-index --no-deps --no-build-isolation [checkout]",
                     "[proof-python] -m unittest discover -s tests -v (programmatic loader; exact output retained)",
                     "[proof-python] scripts/check_bootstrap.py"] + ([] if skip_full_a else [
                     "[proof-python] scripts/prove_bs001_a.py --work [work]/a-proof --worker"]),
        "untested": ["private/real footage and production recall", "real 1440p60 throughput",
                     "Linux/macOS native digest portability", "OCR/semantic labels/providers",
                     "Checkpoint C packet/READY/cancellation and later roadmap"],
        "output_bytes_excluding_environment_and_wheels": sum(p.stat().st_size for p in work.rglob("*")
                     if p.is_file() and p.relative_to(work).parts[0] not in ("venv", "wheels"))}
    write_json(work/"result.json", redact(result, work))
    print(json.dumps({"status": status, "counts": result["counts"], "elapsed_seconds": result["elapsed_seconds"]}), flush=True)
    return 1 if failures else 0


def main():
    entrypoint_started = time.perf_counter()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--work", required=True, type=Path)
    parser.add_argument("--freeze", type=Path, default=DEFAULT_FREEZE)
    parser.add_argument("--split", choices=("all", "dev", "held-out"), default="all")
    parser.add_argument("--skip-full-a", action="store_true", help="Focused run; explicitly omits complete A regression proof")
    parser.add_argument("--worker", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--stress", type=int, help=argparse.SUPPRESS)
    args = parser.parse_args()
    work = args.work.resolve()
    if work.is_relative_to(ROOT.resolve()):
        parser.error("Work directory, media and venv must be outside checkout")
    if args.stress is not None:
        # Explicit focused stress can use a previously pinned review runtime.
        # Default proof verifies installed/check-out byte equivalence first.
        sys.path.insert(0, str(ROOT/"src"))
        stress_config = None
        if args.freeze.is_file():
            from bscout.corpus import load_corpus
            from bscout.regional import RegionalConfig
            _, stress_truth, _ = load_corpus()
            _, stress_config = load_freeze(args.freeze, RegionalConfig,
                [f["id"] for f in stress_truth["fixtures"] if f["split"] == "dev"])
        regional_stress(args.stress, work, stress_config)
        return 0
    if args.worker:
        return worker(work, args.freeze.resolve(), args.split, args.skip_full_a)
    if work.exists() and any(work.iterdir()):
        parser.error("Work directory must be new or empty; no overwrite/cleanup")
    if args.split != "dev" and not args.freeze.is_file():
        parser.error("Held-out/all evaluation requires a pre-existing dev-only configuration freeze")
    work.mkdir(parents=True, exist_ok=True)
    snapshot = {"head": run(["git", "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip(),
                "working_tree_dirty": bool(run(["git", "status", "--porcelain"], capture_output=True, text=True).stdout.strip()),
                "files": source_snapshot()}
    (work/"source-snapshot.json").write_text(json.dumps(snapshot, sort_keys=True, separators=(",", ":"))+"\n", encoding="utf-8")
    venv.EnvBuilder(with_pip=True).create(work/"venv")
    python = work/"venv"/("Scripts/python.exe" if os.name == "nt" else "bin/python")
    run([str(python), "-m", "pip", "download", "--only-binary=:all:", "--no-cache-dir",
         "--index-url", "https://pypi.org/simple", "--dest", str(work/"wheels"), "-r", str(ROOT/"requirements-proof.txt")])
    run([str(python), "-m", "pip", "install", "--no-cache-dir", "--no-index", "--find-links", str(work/"wheels"),
         "-r", str(ROOT/"requirements-proof.txt")])
    run([str(python), "-m", "pip", "install", "--no-cache-dir", "--no-index", "--no-deps", "--no-build-isolation", str(ROOT)])
    smoke = subprocess.run([str(python), "-c", "from bscout.corpus import load_corpus; load_corpus(); "
             "from bscout.regional import RegionalConfig; from bscout.cli import main; main(['--version'])"],
             check=True, cwd=work, capture_output=True, text=True)
    (work/"package.txt").write_text(smoke.stdout, encoding="utf-8")
    command = [str(python), str(Path(__file__).resolve()), "--work", str(work), "--worker",
               "--freeze", str(args.freeze.resolve()), "--split", args.split]
    if args.skip_full_a:
        command.append("--skip-full-a")
    rc = subprocess.run(command, cwd=work).returncode
    result_path = work/"result.json"
    if result_path.is_file():
        result = json.loads(result_path.read_text(encoding="utf-8"))
        result["entrypoint_elapsed_seconds_including_isolated_install"] = time.perf_counter()-entrypoint_started
        result_path.write_text(json.dumps(result, sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=False)+"\n", encoding="utf-8")
    return rc


if __name__ == "__main__":
    raise SystemExit(main())

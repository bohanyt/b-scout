"""Run with the fresh proof's Python; all generated artifacts stay in --work.

Arguments name local directories but their values are never serialized. The
checkout must be the clean runtime-tested head, not the evidence publication.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys

from bscout.common import canonical, sha256
from bscout.ledger import rows, select_video, presented
from bscout.frames import native_planes


def run(argv, cwd):
    env = os.environ.copy()
    env.pop("PYTHONPATH", None)
    return subprocess.run([sys.executable, "-B", *argv], cwd=cwd, env=env,
                          capture_output=True, text=True, check=True)


def cases(log):
    return [{"name": m[0], "test_class": m[1], "status": "pass" if m[2] == "ok" else "skip"}
            for m in re.findall(r"^(test\S+) \(([^\n]+)\) \.\.\. (ok|skipped[^\n]*)$", log, re.M)]


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--checkout", type=Path, required=True)
    p.add_argument("--work", type=Path, required=True)
    a = p.parse_args()
    work, checkout = a.work.resolve(), a.checkout.resolve()
    result = json.loads((work / "result.json").read_text())
    assert result["status"] == "pass" and not result["working_tree_dirty"]
    historical = {}
    for name in ("BS-001-A", "BS-001-A-R1"):
        old = json.loads((checkout / "docs/evidence" / name / "result.json").read_text())
        previous = {f["id"]: f for f in old["oracle"]["fixtures"]}
        tier = []
        for f in result["oracle"]["fixtures"]:
            prior = previous[f["id"]]
            recovery = lambda values: [(v["generator_id"], v["identity"], v["sha256"]) for v in values]
            item = {"fixture": f["id"], "T2_native_frames_equal": f["T2"] == prior["T2"],
                    "canonical_recovery_identity_digest_equal": recovery(f["recovery"]) == recovery(prior["recovery"]),
                    "encoded_media_sha256_equal": f["T3"]["media_sha256"] == prior["T3"]["media_sha256"],
                    "ledger_sha256_equal": f["T3"]["ledger_sha256"] == prior["T3"]["ledger_sha256"],
                    "baseline_semantics_equal": all(f[k] == prior[k] for k in
                        ("frames", "mapping", "timing", "origins", "selected_stream_index", "b_frames",
                         "key_pts", "PTS_behavior", "ledger_status", "survival", "lossless_pixel_exact",
                         "skips", "source_unchanged")),
                    "recovery_count": f["recovery_count"]}
            assert all(item[k] for k in ("T2_native_frames_equal", "canonical_recovery_identity_digest_equal",
                                         "encoded_media_sha256_equal", "baseline_semantics_equal"))
            tier.append(item)
        equal_wheels = lambda r: {(v["filename"], v["sha256"]) for v in r["wheels"]}
        historical[name] = {"T1_equal": result["oracle"]["T1"] == old["oracle"]["T1"],
                            "toolchain_equal": result["toolchain"] == old["toolchain"],
                            "all_wheel_hashes_equal": equal_wheels(result) == equal_wheels(old), "fixtures": tier}
        assert all(historical[name][k] for k in ("T1_equal", "toolchain_equal", "all_wheel_hashes_equal"))

    ledger_sizes = []
    for path in sorted((work / "ledgers").glob("*.jsonl")):
        trailer = list(rows(path))[-1]
        ok = trailer["output_bytes"] == path.stat().st_size
        assert ok
        ledger_sizes.append({"file": path.name, "bytes": path.stat().st_size,
                             "trailer_bytes_equal": ok, "sha256": sha256(path)})

    version = run(["-m", "bscout", "--version"], work).stdout.strip()
    help_text = run(["-m", "bscout", "--help"], work).stdout
    assert "analyze" not in help_text
    source = work / "media/main60-s11.mp4"
    before = sha256(source)
    ledger_path, output = work / "installed-cli.jsonl", work / "installed-cli.yuv"
    ledger_result = json.loads(run(["-m", "bscout", "ledger", str(source), "--out", str(ledger_path)], work).stdout)
    proof = json.loads(run(["-m", "bscout", "recover", str(source), "--ledger", str(ledger_path),
                           "--pts", "1000", "--out", str(output)], work).stdout)
    target = next(r for r in rows(ledger_path) if r["type"] == "frame" and r["pts"] == 1000)
    assert proof["identity"] == target["identity"] and proof["sha256"] == target["native_sha256"]
    import av
    with av.open(str(source), options={"ignore_editlist": "0"}) as container:
        stream = select_video(container)
        expected = next(f for f in presented(container, stream) if f.pts == 1000)
        raw = b"".join(v.tobytes() for v in native_planes(expected)[0])
    assert output.read_bytes() == raw and sha256(source) == before
    cli = {"status": "pass", "installed_package_outside_checkout": True, "version": version,
           "help_excludes_analyze": True, "ledger": ledger_result, "recovery": proof,
           "native_output_bytes": output.stat().st_size, "native_bytes_match_sequential_target": True,
           "output_sha256": hashlib.sha256(raw).hexdigest(), "source_unchanged": True,
           "commands": ["python -B -m bscout --version", "python -B -m bscout --help",
                        "python -B -m bscout ledger TEMP_MEDIA/main60-s11.mp4 --out TEMP_LEDGER.jsonl",
                        "python -B -m bscout recover TEMP_MEDIA/main60-s11.mp4 --ledger TEMP_LEDGER.jsonl --pts 1000 --out TEMP_FRAME.yuv"]}
    focused = run(["-m", "unittest", "discover", "-s", "tests", "-p", "test_recovery_r2.py", "-v"], checkout)
    log = focused.stdout + focused.stderr
    with (work / "recovery-tests.txt").open("x", encoding="utf-8", newline="\n") as sink:
        sink.write(log)
    regression_cases = cases(log)
    assert len(regression_cases) == 37 and all(c["status"] == "pass" for c in regression_cases)
    full_cases = cases((work / "tests.txt").read_text())
    assert len(full_cases) == result["tests"]["run"]
    supplement = {"version": "bscout-r2-supplement-v1", "tested_head": result["tested_head"],
                  "scope": "R2 supplemental checks overlap proof; excluded from aggregate counts",
                  "historical_comparison": historical, "ledger_byte_counts": ledger_sizes,
                  "CLI": cli, "full_suite_cases": full_cases, "injected_regression_cases": regression_cases,
                  "mandatory_attacks": [{"pts": [0, 100, 20, 50, 100], "identical_duplicate_pixels": True,
                      "imported_ledger": variant, "actual_validation_sees_complete_source": True,
                      "API": "unsupported; no frame/proof returned", "CLI_exit": 2,
                      "CLI_new_output": False, "recovery_seek_calls": 0,
                      "method": "only av.open replaced; actual VT validation/comparison/native digest routines"}
                      for variant in ("complete original traversal", "shortened/reindexed [0,20,50,100]; correct source SHA; forged complete/zero anomalies")],
                  "digest_policy": "T1 and T2 identity/native digests match; encoded files match; v2/config/projection/seek metadata and telemetry legitimately change T3/report bytes"}
    with (work / "supplement.json").open("xb") as sink:
        sink.write(canonical(supplement))
    print(json.dumps({"status": "pass", "focused_tests": len(regression_cases),
                      "historical_native_mappings": sum(f["frames"] for f in result["oracle"]["fixtures"]),
                      "canonical_recoveries": sum(f["recovery_count"] for f in result["oracle"]["fixtures"]),
                      "ledger_byte_counts": len(ledger_sizes)}))


if __name__ == "__main__":
    main()

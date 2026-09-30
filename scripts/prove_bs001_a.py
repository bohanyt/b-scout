"""One clean-checkout entrypoint. All environments/media stay in a new temp work dir."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import venv

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))


def run(args, **kwargs):
    return subprocess.run(args, check=True, cwd=ROOT, **kwargs)


def stress(count, out):
    import av
    from bscout.ledger import Timing, frame_row
    from bscout.common import canonical, peak_rss, write_json
    frame = av.VideoFrame(8, 8, "yuv420p")
    from fractions import Fraction
    frame.time_base = Fraction(1, 1000)
    for p in frame.planes:
        p.update(bytes(p.buffer_size))
    t = Timing()
    started = time.perf_counter()
    try:
        with out.with_suffix(".jsonl").open("xb") as sink:
            for i in range(count):
                frame.pts = i
                sink.write(canonical(frame_row(frame, i, t, "0"*64, 0)))
        write_json(out, {"frames": count, "peak_rss": peak_rss(),
                         "elapsed_seconds": time.perf_counter()-started,
                         "output_bytes": out.with_suffix(".jsonl").stat().st_size,
                         "method": "separate process; real PyAV native frames; streamed rows; disk-backed PTS; no list"})
    finally:
        t.close()


def worker(work):
    from bscout.common import fingerprint, peak_rss, sha256, write_json
    from bscout.corpus import generate
    from bscout.oracle import verify
    from bscout.ledger import ledger
    import unittest
    started = time.perf_counter()
    print("Generating frozen corpus-v1 (dev and held-out)", flush=True)
    generation = generate(work/"media")
    # Independent second generation proves byte-repeatability in this toolchain.
    from bscout.corpus import load_corpus, encode
    spec, truth, _ = load_corpus()
    repeat = work/"repeat"
    repeat.mkdir()
    repeat_results = []
    for fixture in truth["fixtures"]:
        path = repeat/fixture["filename"]
        encode(spec, fixture, path)
        repeat_results.append({"id": fixture["id"], "sha256": sha256(path),
                               "equal": sha256(path) == sha256(work/"media"/fixture["filename"])})
    print("Running ID/timing/survival/lossless/random-access oracle", flush=True)
    oracle = verify(work/"media", work/"ledgers", progress=lambda s: print("Oracle "+s, flush=True))
    errors = []
    for name in ("truncated.mp4", "damaged.mp4", "unsupported.mp4"):
        result = ledger(work/"media"/name, work/"ledgers"/(name+".jsonl"))
        errors.append({"fixture": name, "pass": result["status"] != "complete" and result["source_unchanged"],
                       "diagnostic": result})
    print("Running bootstrap and Checkpoint A tests", flush=True)
    with (work/"tests.txt").open("w", encoding="utf-8", newline="\n") as sink:
        suite = unittest.defaultTestLoader.discover(str(ROOT/"tests"))
        tests = unittest.TextTestRunner(stream=sink, verbosity=2).run(suite)
    bootstrap = run([sys.executable, str(ROOT/"scripts/check_bootstrap.py")], capture_output=True, text=True)
    print(bootstrap.stdout.strip(), flush=True)
    for n in (1000, 20000):
        run([sys.executable, str(Path(__file__).resolve()), "--stress", str(n), "--work", str(work/f"stress-{n}.json")])
    resources = [json.loads((work/f"stress-{n}.json").read_text()) for n in (1000, 20000)]
    resource_ok = resources[1]["peak_rss"]["bytes"]-resources[0]["peak_rss"]["bytes"] < 32*1024*1024
    wheels = [{"filename": p.name, "sha256": sha256(p), "bytes": p.stat().st_size,
               "source": "https://pypi.org/simple/ (pip binary wheel, no cache)"}
              for p in sorted((work/"wheels").glob("*.whl"))]
    failures = len(tests.failures)+len(tests.errors)
    failures += sum(f["status"] == "fail" for f in oracle["fixtures"])
    failures += sum(not f["pass"] for f in errors) + int(not resource_ok)
    failures += sum(not f["equal"] for f in repeat_results)
    skips = [{"test": str(t), "reason": reason} for t, reason in tests.skipped]
    skips += [{"fixture": f["id"], "reason": s} for f in oracle["fixtures"] for s in f.get("skips", [])]
    head = run(["git", "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
    dirty = run(["git", "status", "--porcelain"], capture_output=True, text=True).stdout.strip()
    result = {"version": "bscout-proof-v1", "scope": "BS-001 Checkpoint A only; B/C held",
              "tested_head": head, "working_tree_dirty": bool(dirty),
              "status": "pass" if failures == 0 else "fail", "toolchain": fingerprint(), "wheels": wheels,
              "generation": generation, "repeat_generation": repeat_results, "oracle": oracle, "negative_inputs": errors,
              "tests": {"run": tests.testsRun, "passed": tests.testsRun-len(tests.skipped)-len(tests.failures)-len(tests.errors),
                        "failures": [{"test": str(t), "traceback": msg} for t,msg in tests.failures+tests.errors],
                        "skipped": [{"test": str(t), "reason": reason} for t,reason in tests.skipped]},
              "bootstrap": bootstrap.stdout.strip(),
              "resource_stress": {"status": "pass" if resource_ok else "fail", "runs": resources,
                                  "growth_limit_bytes": 32*1024*1024},
              "counts": {"pass": tests.testsRun-len(tests.skipped)-len(tests.failures)-len(tests.errors)
                         +sum(f["status"] == "pass" for f in oracle["fixtures"])
                         +sum(f["pass"] for f in errors)+sum(f["equal"] for f in repeat_results)+int(resource_ok)+1,
                         "fail": failures, "skip": len(skips)}, "skips": skips,
              "untested": ["real media duplicate/non-monotonic PTS (injected logic tested)",
                           "Linux/macOS/native-plane digest portability", "HDR/10-bit/rotation/SAR/interlacing",
                           "mid-stream format changes, MPEG-TS wrap, NLE edit-list interpretation",
                           "private footage and real 1440p60 throughput", "Python versions other than recorded runtime",
                           "production detector/packet, cancellation/budgets, B/C and later roadmap"],
              "elapsed_seconds": time.perf_counter()-started, "peak_rss": peak_rss(),
              "output_bytes": {"media_and_ledgers": sum(p.stat().st_size for sub in
                  ("media", "ledgers") for p in (work/sub).rglob("*") if p.is_file()),
                  "all_proof_artifacts_excluding_venv_wheels_result": sum(p.stat().st_size for p in work.rglob("*")
                      if p.is_file() and p.relative_to(work).parts[0] not in ("venv", "wheels"))},
              "source_unchanged": all(f.get("source_unchanged",False) for f in oracle["fixtures"])
              and all(f["diagnostic"]["source_unchanged"] for f in errors)}
    write_json(work/"result.json", result)
    print(json.dumps({"status": result["status"], "counts": result["counts"],
                      "elapsed_seconds": result["elapsed_seconds"]}), flush=True)
    return 0 if failures == 0 else 1


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--work", type=Path, required=True)
    p.add_argument("--worker", action="store_true", help=argparse.SUPPRESS)
    p.add_argument("--stress", type=int, help=argparse.SUPPRESS)
    a = p.parse_args()
    if a.stress:
        stress(a.stress, a.work)
        return 0
    if a.worker:
        return worker(a.work)
    work = a.work.resolve()
    if work.is_relative_to(ROOT.resolve()):
        p.error("Work directory and venv must be outside repository")
    if work.exists() and any(work.iterdir()):
        p.error("Work directory must be new or empty; no overwrite/cleanup")
    work.mkdir(parents=True, exist_ok=True)
    start = time.perf_counter()
    venv.EnvBuilder(with_pip=True).create(work/"venv")
    python = work/"venv"/("Scripts/python.exe" if os.name == "nt" else "bin/python")
    run([str(python), "-m", "pip", "download", "--only-binary=:all:", "--no-cache-dir",
         "--index-url", "https://pypi.org/simple", "--dest", str(work/"wheels"),
         "-r", str(ROOT/"requirements-proof.txt")])
    run([str(python), "-m", "pip", "install", "--no-cache-dir", "--no-index", "--find-links", str(work/"wheels"),
         "-r", str(ROOT/"requirements-proof.txt")])
    run([str(python), "-m", "pip", "install", "--no-cache-dir", "--no-index", "--no-deps", "--no-build-isolation", str(ROOT)])
    # Prove the installed wheel works away from source; corpus data must ship.
    package = subprocess.run([str(python), "-c", "from bscout.corpus import load_corpus; load_corpus(); from bscout.cli import main; main(['--version'])"],
                             check=True, cwd=work, capture_output=True, text=True)
    (work/"package.txt").write_text(package.stdout, encoding="utf-8")
    rc = subprocess.run([str(python), str(Path(__file__).resolve()), "--work", str(work), "--worker"], cwd=ROOT).returncode
    print(f"Total entrypoint elapsed including isolated install: {time.perf_counter()-start:.3f}s", flush=True)
    return rc


if __name__ == "__main__":
    raise SystemExit(main())

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


def vt_stress(count, out):
    """Exercise the actual VT core through an injected, streaming media boundary.

    The external bytes identify a synthetic source, not encoded media. av.open is
    the only patched operation; full validation, SQLite inserts/lookups, digest
    comparisons, anchor selection and seek verification execute in the core.
    Fixed-corpus oracle results separately prove the real codec/seek path.
    """
    import av
    from fractions import Fraction
    from types import SimpleNamespace
    from unittest.mock import patch
    from bscout.common import peak_rss, sha256, write_json
    from bscout.ledger import DecodeConfig, recover, validate_traversal

    out.parent.mkdir(parents=True, exist_ok=True)
    source = out.with_suffix(".synthetic.bin")
    with source.open("xb") as sink:
        sink.write(b"B-Scout R2 streaming resource injection\n" + str(count).encode("ascii"))
    original = sha256(source)
    tb, gop = Fraction(1, 1000), 100
    observed = {"validation_opens": 0, "seek_calls": 0,
                "validation_frames": 0, "seek_frames": 0,
                "validation_flush_packets": 0, "seek_flush_packets": 0}

    def native_frame(index):
        frame = av.VideoFrame(8, 8, "yuv420p")
        frame.pts, frame.time_base = index, tb
        frame.key_frame = index % gop == 0
        for plane in frame.planes:
            plane.update(bytes([index % 251]) * plane.buffer_size)
        return frame

    class Packet:
        is_corrupt = False

        def __init__(self, index, seeked):
            self.index, self.seeked = index, seeked

        def decode(self):
            category = "seek" if self.seeked else "validation"
            if self.index is None:
                observed[category + "_flush_packets"] += 1
                return
            observed[category + "_frames"] += 1
            yield native_frame(self.index)

    class Streams:
        def __init__(self, stream):
            self.video = (stream,)

        def __len__(self):
            return 1

    class Container:
        def __init__(self):
            codec = SimpleNamespace(name="r2-injected-native", thread_count=0,
                thread_type=None, options={}, color_range=0, color_primaries=0,
                color_trc=0, colorspace=0)
            self.stream = SimpleNamespace(index=0, time_base=tb, start_time=0,
                duration=count, frames=count, codec_context=codec)
            self.streams = Streams(self.stream)
            self.format = SimpleNamespace(name="r2-injected-streaming")
            self.start_time, self.duration = 0, count * 1000
            self.start, self.seeked = 0, False

        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return False

        def seek(self, offset, *, stream, backward, any_frame):
            if stream is not self.stream or not backward or any_frame:
                raise AssertionError("Resource seam requires backward keyframe seek")
            self.start = max(0, (offset // gop) * gop)
            self.seeked = True
            observed["seek_calls"] += 1

        def demux(self, stream):
            if stream is not self.stream:
                raise AssertionError("Resource seam stream mismatch")
            if not self.seeked:
                observed["validation_opens"] += 1
            for index in range(self.start, count):
                yield Packet(index, self.seeked)
            # Explicit EOF/decoder-flush packet; no frame list in the seam.
            yield Packet(None, self.seeked)

    started = time.perf_counter()
    with patch("av.open", side_effect=lambda *args, **kwargs: Container()):
        validation_start = time.perf_counter()
        vt = validate_traversal(source, config=DecodeConfig())
        try:
            validation_seconds = time.perf_counter() - validation_start
            owned_directory = Path(vt.temporary_directory)
            table_bytes = vt.table_bytes
            if vt.trailer["presented_frames"] != count or not owned_directory.is_dir():
                raise AssertionError("Resource VT did not retain full owned traversal")
            lookup_start = time.perf_counter()
            lookup_count = 0
            # Streamed lookups across the whole table; no retained row/key list.
            for ordinal in range(count):
                row = vt.entry(ordinal)
                if row["ordinal"] != ordinal or row["pts"] != ordinal:
                    raise AssertionError("Resource VT lookup mismatch")
                lookup_count += 1
            lookup_seconds = time.perf_counter() - lookup_start
            recovery_start = time.perf_counter()
            recovered, decoded_forward = 0, 0
            for ordinal in (0, count // 2, count - 1):
                identity = vt.identity(ordinal)
                frame, proof = recover(source, vt, identity)
                if frame.pts != ordinal or tuple(proof["identity"]) != tuple(identity):
                    raise AssertionError("Resource VT recovery mismatch")
                recovered += 1
                decoded_forward += proof["decoded_forward"]
            recovery_seconds = time.perf_counter() - recovery_start
        finally:
            vt.close()
    cleanup = not owned_directory.exists()
    unchanged = sha256(source) == original
    complete = (observed["validation_opens"] == 1
                and observed["validation_frames"] == count
                and observed["validation_flush_packets"] == 1
                and observed["seek_calls"] == recovered == 3
                and lookup_count == count and table_bytes > 0 and cleanup and unchanged)
    write_json(out, {"status": "pass" if complete else "fail", "frames": count,
        "peak_rss": peak_rss(), "elapsed_seconds": time.perf_counter()-started,
        "validation_seconds": validation_seconds, "lookup_seconds": lookup_seconds,
        "recovery_seconds": recovery_seconds, "table_bytes": table_bytes,
        "lookup_count": lookup_count, "recovery_count": recovered,
        "decoded_forward": decoded_forward, "observed_media_boundary": observed,
        "temporary_table_removed_after_close": cleanup, "source_unchanged": unchanged,
        "method": "separate process; only av.open injected; streaming real PyAV native frames; "
                  "actual full core VT validation/SQLite lookup/anchor/aligned recovery; no frame list",
        "limitations": "injected media boundary measures VT resource/lifecycle behavior; "
                       "fixed-corpus oracle independently proves encoded-media seek recovery"})
    if not complete:
        raise AssertionError("VT resource/lifecycle proof failed")


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
    for n in (1000, 20000):
        run([sys.executable, str(Path(__file__).resolve()), "--vt-stress", str(n),
             "--work", str(work/f"vt-stress-{n}.json")])
    vt_resources = [json.loads((work/f"vt-stress-{n}.json").read_text()) for n in (1000, 20000)]
    vt_resource_ok = (all(r["status"] == "pass" for r in vt_resources) and
        vt_resources[1]["peak_rss"]["bytes"]-vt_resources[0]["peak_rss"]["bytes"] < 32*1024*1024)
    validation_reuse_ok = all(f.get("validation_passes") == 1 for f in oracle["fixtures"])
    wheels = [{"filename": p.name, "sha256": sha256(p), "bytes": p.stat().st_size,
               "source": "https://pypi.org/simple/ (pip binary wheel, no cache)"}
              for p in sorted((work/"wheels").glob("*.whl"))]
    failures = len(tests.failures)+len(tests.errors)
    failures += sum(f["status"] == "fail" for f in oracle["fixtures"])
    failures += sum(not f["pass"] for f in errors) + int(not resource_ok) + int(not vt_resource_ok)
    failures += int(not validation_reuse_ok)
    failures += sum(not f["equal"] for f in repeat_results)
    skips = [{"test": str(t), "reason": reason} for t, reason in tests.skipped]
    skips += [{"fixture": f["id"], "reason": s} for f in oracle["fixtures"] for s in f.get("skips", [])]
    head = run(["git", "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
    dirty = run(["git", "status", "--porcelain"], capture_output=True, text=True).stdout.strip()
    result = {"version": "bscout-proof-v2", "scope": "BS-001 Checkpoint A R2 only; B/C held",
              "tested_head": head, "working_tree_dirty": bool(dirty),
              "status": "pass" if failures == 0 else "fail", "toolchain": fingerprint(), "wheels": wheels,
              "generation": generation, "repeat_generation": repeat_results, "oracle": oracle, "negative_inputs": errors,
              "tests": {"run": tests.testsRun, "passed": tests.testsRun-len(tests.skipped)-len(tests.failures)-len(tests.errors),
                        "failures": [{"test": str(t), "traceback": msg} for t,msg in tests.failures+tests.errors],
                        "skipped": [{"test": str(t), "reason": reason} for t,reason in tests.skipped]},
              "bootstrap": bootstrap.stdout.strip(),
              "resource_stress": {"status": "pass" if resource_ok else "fail", "runs": resources,
                                  "growth_limit_bytes": 32*1024*1024},
              "vt_resource_stress": {"status": "pass" if vt_resource_ok else "fail", "runs": vt_resources,
                                     "growth_limit_bytes": 32*1024*1024},
              "validation_reuse": {"status": "pass" if validation_reuse_ok else "fail",
                                   "rule": "one full VT validation per fixture, reused for every recovery",
                                   "fixture_validation_passes": {f["id"]: f.get("validation_passes")
                                                                 for f in oracle["fixtures"]}},
              "counts": {"pass": tests.testsRun-len(tests.skipped)-len(tests.failures)-len(tests.errors)
                         +sum(f["status"] == "pass" for f in oracle["fixtures"])
                         +sum(f["pass"] for f in errors)+sum(f["equal"] for f in repeat_results)
                         +int(resource_ok)+int(vt_resource_ok)+int(validation_reuse_ok)+1,
                         "fail": failures, "skip": len(skips)}, "skips": skips,
              "untested": ["real encoded media duplicate/non-monotonic PTS (full-source media-open injection tested)",
                           "hostile same-process code and undetectable source modify-and-restore races; stable read-only local source assumed",
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
    p.add_argument("--vt-stress", type=int, help=argparse.SUPPRESS)
    a = p.parse_args()
    if a.stress:
        stress(a.stress, a.work)
        return 0
    if a.vt_stress:
        vt_stress(a.vt_stress, a.work)
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

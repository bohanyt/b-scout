"""Checkpoint A logic; optional media tests skip explicitly without runtime deps."""
from fractions import Fraction
import importlib.util
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from bscout.common import canonical, digest, safe_output
from bscout.cli import parser

HAS_RUNTIME = bool(importlib.util.find_spec("av") and importlib.util.find_spec("numpy"))
if HAS_RUNTIME:
    import av
    import numpy as np
    from bscout.corpus import load_corpus, make_frame, planes_for, encode
    from bscout.frames import native_digest, native_planes, read_id
    from bscout.ledger import Timing, frame_row, ledger, rows, recover, presented
    from bscout.oracle import nearest, timing_check, survival


class ContractTests(unittest.TestCase):
    def test_canonical_is_semantic_utf8_lf_and_no_nan(self):
        self.assertEqual(digest({"b": 2, "a": "é"}), digest({"a": "é", "b": 2}))
        self.assertTrue(canonical({"a": "é"}).endswith(b"\n"))
        self.assertIn("é".encode(), canonical({"a": "é"}))
        with self.assertRaises(ValueError):
            canonical(float("nan"))

    def test_output_source_and_hardlink_fail_before_write(self):
        import os
        with tempfile.TemporaryDirectory() as d:
            source = Path(d) / "source"
            source.write_bytes(b"read only")
            with self.assertRaises(ValueError):
                safe_output(source, source)
            alias = Path(d) / "alias"
            os.link(source, alias)
            with self.assertRaises(ValueError):
                safe_output(source, alias)
            self.assertEqual(source.read_bytes(), b"read only")

    def test_no_production_analyze_command(self):
        self.assertNotIn("analyze", parser().format_help())
        self.assertIn("recover", parser().format_help())


@unittest.skipUnless(HAS_RUNTIME, "Checkpoint A media tests require pinned av/numpy; run proof entrypoint")
class TemporalTests(unittest.TestCase):
    def injected_recovery(self, directory, pts):
        from bscout.common import sha256
        from bscout.ledger import VERSION
        source = Path(directory) / "synthetic.bin"
        source.write_bytes(b"synthetic injected source")
        frames, entries = [], []
        timing = Timing()
        header = {"type": "header", "version": VERSION, "source_sha256": sha256(source),
                  "selected_stream_index": 0, "first_presented_pts": pts[0],
                  "first_presented_time_base": [1, 1000]}
        try:
            for i, p in enumerate(pts):
                f = av.VideoFrame(8, 8, "yuv420p")
                f.pts, f.time_base = p, Fraction(1, 1000)
                for plane in f.planes:
                    plane.update(bytes(plane.buffer_size))
                frames.append(f)
                entries.append(frame_row(f, i, timing, header["source_sha256"], 0))
            trailer = {"type": "trailer", "version": VERSION,
                       "status": "diagnostic" if any(timing.counts.values()) else "complete",
                       "presented_frames": len(pts), "timing": dict(timing.counts),
                       "errors": [], "source_unchanged": True}
        finally:
            timing.close()
        # Explicit keyframes reproduce the reviewer's seek anchors.
        for entry in entries:
            entry["key_frame"] = entry["pts"] in (0, 20, 50)
        path = Path(directory) / "ledger.jsonl"
        path.write_bytes(b"".join(canonical(r) for r in [header, *entries, trailer]))
        keys = [r["pts"] for r in entries if r["key_frame"] and r["pts"] is not None]
        return source, path, frames, entries, header, keys

    def test_r1_identical_pixels_later_duplicate_never_recovers_first(self):
        from unittest.mock import patch
        from types import SimpleNamespace
        with tempfile.TemporaryDirectory() as d:
            source, path, frames, entries, header, keys = self.injected_recovery(d, [0,100,20,50,100])
            self.assertEqual(entries[1]["native_sha256"], entries[4]["native_sha256"])
            self.assertNotEqual(entries[1]["identity"], entries[4]["identity"])
            # If reached, this exact suffix would return the wrong identical-pixel occurrence.
            with patch("av.open") as opened, patch("bscout.ledger.select_video",
                    return_value=SimpleNamespace(time_base=Fraction(1,1000))), \
                    patch("bscout.ledger.presented", return_value=iter(frames[2:])):
                with self.assertRaisesRegex(ValueError, "unsupported.*non-monotonic"):
                    recover(source, entries[1], header, keys, ledger_path=path)
                opened.assert_not_called()

    def test_recovery_rejects_nearby_timing_anomalies_in_entire_ledger(self):
        from unittest.mock import patch
        for pts in ([0,100,100], [0,100,20], [0,100,None], [None,100,200], [0,100,200,100]):
            with self.subTest(pts=pts), tempfile.TemporaryDirectory() as d:
                source, path, _, entries, header, keys = self.injected_recovery(d, pts)
                with patch("av.open") as opened:
                    with self.assertRaisesRegex(ValueError, "unsupported"):
                        recover(source, entries[1], header, keys, ledger_path=path)
                    opened.assert_not_called()

    def test_recovery_api_cannot_bypass_validation_with_header_only(self):
        from unittest.mock import patch
        with tempfile.TemporaryDirectory() as d:
            source, _, _, entries, header, keys = self.injected_recovery(d, [0,100,20,50,100])
            header["exact_recovery"] = {"status": "supported"}
            with patch("av.open") as opened:
                with self.assertRaisesRegex(ValueError, "complete validated ledger"):
                    recover(source, entries[1], header, keys)
                opened.assert_not_called()

    def test_recovery_recomputes_safety_instead_of_trusting_declared_status(self):
        from unittest.mock import patch
        with tempfile.TemporaryDirectory() as d:
            source, path, _, entries, header, keys = self.injected_recovery(d, [0,100,20,50,100])
            records = list(rows(path))
            records[-1].update(status="complete", timing={"missing":0,"duplicate":0,"non_monotonic":0},
                               exact_recovery={"status":"supported"})
            for row in records[1:-1]:
                row["timing_flags"] = []
                row["same_pts_ordinal"] = 0
                row["identity"][-1] = 0
            path.write_bytes(b"".join(canonical(r) for r in records))
            with patch("av.open") as opened:
                with self.assertRaisesRegex(ValueError, "unsupported"):
                    recover(source, entries[1], header, keys, ledger_path=path)
                opened.assert_not_called()

    def test_recovery_incomplete_or_unrelated_ledger_rejected(self):
        from unittest.mock import patch
        with tempfile.TemporaryDirectory() as d:
            source, path, _, entries, header, keys = self.injected_recovery(d, [0,100,200])
            records = list(rows(path))
            for changed in (records[:-1], [*records, records[-1]],
                            [dict(header, source_sha256="0"*64), *records[1:]]):
                path.write_bytes(b"".join(canonical(r) for r in changed))
                with patch("av.open") as opened:
                    with self.assertRaises(ValueError):
                        recover(source, entries[1], header, keys, ledger_path=path)
                    opened.assert_not_called()

    def test_recovery_supported_seek_missing_target_and_native_digest(self):
        from unittest.mock import patch, MagicMock
        from types import SimpleNamespace
        with tempfile.TemporaryDirectory() as d:
            source, path, frames, entries, header, keys = self.injected_recovery(d, [0,100,200])
            container = MagicMock()
            container.__enter__.return_value = container
            with patch("av.open", return_value=container), patch("bscout.ledger.select_video",
                    return_value=SimpleNamespace(time_base=Fraction(1,1000))), \
                    patch("bscout.ledger.presented", side_effect=lambda *a: iter(frames)):
                frame, proof = recover(source, entries[1], header, keys, ledger_path=path)
                self.assertIs(frame, frames[1])
                self.assertEqual(proof["identity"], entries[1]["identity"])
                self.assertTrue(container.seek.call_args.kwargs["backward"])
                bad = dict(entries[1], native_sha256="0"*64)
                with self.assertRaisesRegex(ValueError, "native digest mismatch"):
                    recover(source, bad, header, keys, ledger_path=path)
                missing = dict(entries[1], pts=150)
                missing["identity"] = [header["source_sha256"],0,150,0]
                with self.assertRaisesRegex(ValueError, "never emitted"):
                    recover(source, missing, header, keys, ledger_path=path)

    def test_cli_rejects_r1_without_writing_recovery_output(self):
        from bscout.cli import main
        from unittest.mock import patch
        import io
        with tempfile.TemporaryDirectory() as d:
            source, path, _, _, _, _ = self.injected_recovery(d, [0,100,20,50,100])
            output, error = Path(d)/"recovered.yuv", io.StringIO()
            with patch("sys.stderr", error), patch("av.open") as opened:
                self.assertEqual(main(["recover", str(source), "--ledger", str(path),
                                       "--pts", "100", "--out", str(output)]), 2)
                opened.assert_not_called()
            self.assertIn("unsupported", error.getvalue())
            self.assertFalse(output.exists())

    def test_recovery_rejects_unsafe_timing_emitted_after_seek(self):
        from unittest.mock import patch, MagicMock
        from types import SimpleNamespace
        with tempfile.TemporaryDirectory() as d:
            source, path, _, entries, header, keys = self.injected_recovery(d, [0,100,200])
            for emitted in ([0,None,100], [0,0,100], [50,20,100]):
                container = MagicMock()
                container.__enter__.return_value = container
                frames = [SimpleNamespace(pts=p, time_base=Fraction(1,1000)) for p in emitted]
                with self.subTest(emitted=emitted), patch("av.open", return_value=container), \
                        patch("bscout.ledger.select_video", return_value=SimpleNamespace(time_base=Fraction(1,1000))), \
                        patch("bscout.ledger.presented", return_value=iter(frames)):
                    with self.assertRaisesRegex(ValueError, "unsafe seek-path timing"):
                        recover(source, entries[1], header, keys, ledger_path=path)

    def test_failure_ledger_does_not_expose_source_path(self):
        with tempfile.TemporaryDirectory(prefix="bscout private diagnostic ") as d:
            source = Path(d)/"nonmedia.mp4"
            source.write_bytes(b"synthetic unsupported input")
            output = Path(d)/"diagnostic.jsonl"
            result = ledger(source, output)
            self.assertEqual(result["status"], "failed")
            self.assertTrue(result["source_unchanged"])
            self.assertNotIn(str(source), output.read_text(encoding="utf-8"))
            self.assertNotIn("bscout private diagnostic", output.read_text(encoding="utf-8"))
            self.assertIn("[source]", " ".join(result["errors"]))

    def test_concealed_corruption_is_rejected(self):
        from types import SimpleNamespace
        for packet_bad, frame_bad in ((True, False), (False, True)):
            packet = SimpleNamespace(is_corrupt=packet_bad,
                                     decode=lambda: [SimpleNamespace(is_corrupt=frame_bad)])
            container = SimpleNamespace(demux=lambda stream: [packet])
            with self.assertRaisesRegex(ValueError, "corrupt"):
                list(presented(container, None))

    def test_frozen_corpus_and_splits(self):
        spec, truth, frozen = load_corpus()
        self.assertEqual(len(truth["fixtures"]), 16)
        self.assertTrue(set(spec["dev_seeds"]).isdisjoint(spec["held_out_seeds"]))
        self.assertEqual(digest(truth), frozen["annotations"])

    def test_nearest_exact_ties_signed_and_bound(self):
        for value, expected in [(Fraction(1, 2), 1), (Fraction(-1, 2), -1),
                                (Fraction(3, 2), 2), (Fraction(49, 100), 0)]:
            self.assertEqual(nearest(value), expected)
        self.assertTrue(timing_check(1000, 1000, Fraction(1, 60000))["exact"])
        result = timing_check(1001, 17, Fraction(1, 1000))
        self.assertFalse(result["exact"])
        with self.assertRaises(ValueError):
            timing_check(1001, 16, Fraction(1, 1000))

    def test_pts_missing_duplicate_and_regression_identity(self):
        timing = Timing()
        try:
            results = [timing.observe(p) for p in (None, 10, 10, 20, 10, None)]
            self.assertEqual([r[0] for r in results], [None, 0, 1, 0, 2, None])
            self.assertEqual(timing.first, 10)
            self.assertEqual(timing.counts, {"missing": 2, "duplicate": 2, "non_monotonic": 1})
            f = av.VideoFrame(8, 8, "yuv420p")
            f.pts = None
            for plane in f.planes:
                plane.update(bytes(plane.buffer_size))
            row = frame_row(f, 99, timing, "0"*64, 1)
            self.assertIsNone(row["identity"])
            self.assertIsNone(row["pts"])
            self.assertIsNone(row["best_effort_timestamp"])
        finally:
            timing.close()

    def test_digest_ignores_native_row_padding_includes_dimensions(self):
        f = av.VideoFrame(854, 480, "yuv420p")
        for plane in f.planes:
            plane.update(bytes(plane.buffer_size))
        before, _ = native_digest(f)
        for plane in f.planes:
            array = np.zeros((plane.height, plane.line_size), np.uint8)
            array[:, plane.width:] = 255
            plane.update(array)
        self.assertEqual(native_digest(f)[0], before)
        for plane in f.planes:
            array = np.zeros((plane.height, plane.line_size), np.uint8)
            array[0, 0] = 1
            plane.update(array)
        self.assertNotEqual(native_digest(f)[0], before)

    def test_checked_id_and_corrupted_bit_rejected(self):
        spec, truth, _ = load_corpus()
        f = truth["fixtures"][0]
        planes = planes_for(spec, f, 42)
        self.assertEqual(read_id(make_frame(planes), spec["harness"]), 42)
        planes[0][:16, :16] = 235 - planes[0][:16, :16] + 16
        with self.assertRaises(ValueError):
            read_id(make_frame(planes), spec["harness"])

    def test_erased_easy_survival_is_degraded(self):
        spec, truth, _ = load_corpus()
        f = truth["fixtures"][0]
        e = next(e for e in f["events"] if e["id"] == "one_b_phase")
        erased = make_frame(planes_for(spec, f, 1, omit=e["id"]))
        self.assertEqual(survival(spec, f, 1, erased, e)["status"], "degraded")

    def test_actual_unicode_spaced_lossless_path_and_exact_recovery(self):
        spec, truth, _ = load_corpus()
        f = dict(next(f for f in truth["fixtures"] if f["name"] == "lossless"))
        f["pts"] = [0, 1000, 2000]
        with tempfile.TemporaryDirectory(prefix="bscout path é ไทย ") as d:
            source = Path(d) / "vid é ไทย.mkv"
            output = Path(d) / "ledger.jsonl"
            encode(spec, f, source)
            self.assertEqual(ledger(source, output)["status"], "complete")
            entries = list(rows(output))
            header = entries[0]
            target = [r for r in entries if r["type"] == "frame"][1]
            frame, result = recover(source, target, header, [0], ledger_path=output)
            self.assertEqual(result["sha256"], target["native_sha256"])
            self.assertTrue(all(np.array_equal(a,b) for a,b in zip(native_planes(frame)[0], planes_for(spec,f,1))))
            with self.assertRaises(ValueError):
                ledger(source, source)
            bad = dict(target, pts=333)
            bad["identity"] = [header["source_sha256"], 0, 333, 0]
            with self.assertRaisesRegex(ValueError, "never emitted"):
                recover(source, bad, header, [0], ledger_path=output)
            unknown = dict(target, pts=None, identity=None)
            with self.assertRaisesRegex(ValueError, "unknown timing"):
                recover(source, unknown, header, [0], ledger_path=output)

    def test_symlink_source_rejected_where_supported(self):
        import os
        with tempfile.TemporaryDirectory() as d:
            source, alias = Path(d)/"source", Path(d)/"alias"
            source.write_bytes(b"source")
            try:
                os.symlink(source, alias)
            except OSError as exc:
                self.skipTest(f"OS cannot create symlinks: {type(exc).__name__}, winerror={getattr(exc,'winerror',None)}")
            with self.assertRaises(ValueError):
                ledger(source, alias)
            self.assertEqual(source.read_bytes(), b"source")


if __name__ == "__main__":
    unittest.main()

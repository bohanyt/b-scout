"""R2 injected media proofs: only av.open is replaced; the core actually validates.

The synthetic container exposes every source frame, including a final flush
packet, before seeking. Its seek operation changes presentation output to the
chosen suffix. Real PyAV native frames/digests exercise the trusted core.
These are injected boundary regressions, not anomalous encoded-media proof.
"""
from contextlib import redirect_stderr, redirect_stdout
from copy import deepcopy
from dataclasses import FrozenInstanceError
from fractions import Fraction
import gc
import importlib.util
import io
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
HAS_RUNTIME = bool(importlib.util.find_spec("av") and importlib.util.find_spec("numpy"))
if HAS_RUNTIME:
    import av
    from bscout.cli import main
    from bscout.common import canonical, sha256
    from bscout.ledger import (DecodeConfig, ValidatedTraversal, compare_ledger,
                              recover, rows, validate_traversal)


def native_frame(pts, *, value=0, key=False, tb=Fraction(1, 1000), width=8):
    frame = av.VideoFrame(width, 8, "yuv420p")
    frame.pts, frame.time_base, frame.key_frame = pts, tb, key
    for plane in frame.planes:
        plane.update(bytes([value % 256]) * plane.buffer_size)
    return frame


class CorruptFrame:
    is_corrupt = True

    def __init__(self, frame):
        self.frame = frame

    def __getattr__(self, name):
        return getattr(self.frame, name)


class Streams(list):
    @property
    def video(self):
        return [s for s in self if s.type == "video"]


class FakeMedia:
    """One source/configuration seam with full traversal and post-seek output."""
    def __init__(self, pts=(0, 100, 200), *, count="actual", stream_index=0,
                 identical=False, seek_frames=None, on_validation=None,
                 on_recovery=None, on_recovery_close=None, packet_bad=False, decode_error=False):
        self.frames = [native_frame(p, value=0 if identical else i,
                                    key=(p in (0, 20, 50)))
                       for i, p in enumerate(pts)]
        self.count = len(self.frames) if count == "actual" else count
        self.stream_index = stream_index
        self.seek_frames = seek_frames
        self.on_validation, self.on_recovery = on_validation, on_recovery
        self.on_recovery_close = on_recovery_close
        self.packet_bad, self.decode_error = packet_bad, decode_error
        self.opened, self.seek_calls = [], []

    def open(self, *args, **kwargs):
        container = FakeContainer(self)
        container.open_kwargs = kwargs
        self.opened.append(container)
        return container


class FakeContainer:
    def __init__(self, media):
        self.media, self.after_seek = media, False
        self.full_seen, self.seek_seen, self.flush_seen = [], [], False
        codec = SimpleNamespace(name="synthetic", thread_count=0, thread_type=None,
                                options={}, color_range=None, color_primaries=None,
                                color_trc=None, colorspace=None)
        video = SimpleNamespace(index=media.stream_index, type="video",
                                codec_context=codec, time_base=Fraction(1, 1000),
                                start_time=0, duration=None, frames=media.count)
        self.streams = Streams([video])
        self.format = SimpleNamespace(name="synthetic-injected")
        self.start_time, self.duration = 0, None

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    def close(self):
        if self.after_seek and self.media.on_recovery_close is not None:
            self.media.on_recovery_close()

    def seek(self, offset, **kwargs):
        self.after_seek = True
        self.media.seek_calls.append((offset, kwargs))

    def demux(self, stream):
        frames = (self.media.frames if not self.after_seek or self.media.seek_frames is None
                  else self.media.seek_frames)
        # The final frame exists only in the final flush packet.
        for i, frame in enumerate(frames):
            flush = i == len(frames) - 1
            def decode(frame=frame, flush=flush):
                if self.media.decode_error:
                    raise ValueError("synthetic decode failure")
                if flush:
                    self.flush_seen = True
                seen = self.seek_seen if self.after_seek else self.full_seen
                seen.append(frame.pts)
                callback = self.media.on_recovery if self.after_seek else self.media.on_validation
                if callback is not None:
                    callback()
                return [frame]
            yield SimpleNamespace(is_corrupt=self.media.packet_bad, decode=decode,
                                  size=0 if flush else 1, pts=None if flush else frame.pts,
                                  dts=None if flush else frame.pts)


@unittest.skipUnless(HAS_RUNTIME, "R2 media tests require pinned av/numpy; run proof entrypoint")
class RecoveryR2Tests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="bscout-r2-synthetic-")
        self.addCleanup(self.temp.cleanup)
        self.source = Path(self.temp.name) / "source é ไทย.bin"
        self.source.write_bytes(b"synthetic complete source bytes")
        self.ledger_path = Path(self.temp.name) / "ledger.jsonl"

    def validate(self, media, *, output=True, config=None):
        kwargs = {"ledger_out": self.ledger_path} if output else {}
        if config is not None:
            kwargs["config"] = config
        with patch("av.open", side_effect=media.open):
            vt = validate_traversal(self.source, **kwargs)
        self.addCleanup(vt.close)
        return vt

    def write_records(self, records, path=None):
        (path or self.ledger_path).write_bytes(b"".join(canonical(r) for r in records))

    def cli(self, media, *, pts=100, output=None, ordinal=0):
        output = output or Path(self.temp.name) / "recovered.yuv"
        stdout, stderr = io.StringIO(), io.StringIO()
        with patch("av.open", side_effect=media.open), redirect_stdout(stdout), redirect_stderr(stderr):
            code = main(["recover", str(self.source), "--ledger", str(self.ledger_path),
                         "--pts", str(pts), "--same-pts-ordinal", str(ordinal), "--out", str(output)])
        return code, stdout.getvalue(), stderr.getvalue(), output

    def test_full_duplicate_identical_pixels_api_and_cli_reject_before_seek(self):
        media = FakeMedia([0, 100, 20, 50, 100], identical=True)
        media.seek_frames = media.frames[2:]
        vt = self.validate(media)
        self.assertEqual(media.opened[0].full_seen, [0, 100, 20, 50, 100])
        self.assertTrue(media.opened[0].flush_seen)
        first, later = vt.entry(1), vt.entry(4)
        self.assertEqual(first["native_sha256"], later["native_sha256"])
        self.assertNotEqual(first["identity"], later["identity"])
        with patch("av.open", side_effect=media.open), self.assertRaisesRegex(ValueError, "unsupported|unsafe"):
            recover(self.source, vt, first["identity"], ledger_path=self.ledger_path)
        code, stdout, stderr, output = self.cli(media)
        self.assertEqual(code, 2)
        self.assertEqual(stdout, "")
        self.assertFalse(output.exists())
        self.assertIn("unsupported", stderr)
        self.assertFalse(media.seek_calls)
        self.assertEqual(media.opened[-1].full_seen, [0, 100, 20, 50, 100])

    def test_shortened_self_consistent_duplicate_attack_api_and_cli_reject(self):
        media = FakeMedia([0, 100, 20, 50, 100], identical=True)
        media.seek_frames = media.frames[2:]
        vt = self.validate(media)
        records = list(rows(self.ledger_path))
        subset = [deepcopy(records[i + 1]) for i in (0, 2, 3, 4)]
        for i, row in enumerate(subset):
            row.update(ordinal=i, same_pts_ordinal=0, timing_flags=[])
            row["identity"][-1] = 0
        trailer = deepcopy(records[-1])
        trailer.update(status="complete", presented_frames=4,
                       timing={"missing": 0, "duplicate": 0, "non_monotonic": 0})
        trailer["exact_recovery"]["status"] = "supported"
        self.write_records([records[0], *subset, trailer])
        self.assertEqual(records[0]["source_sha256"], sha256(self.source))
        with self.assertRaises(ValueError):
            compare_ledger(vt, self.ledger_path)
        with patch("av.open", side_effect=media.open), self.assertRaises(ValueError):
            recover(self.source, vt, vt.identity(100), ledger_path=self.ledger_path)
        code, stdout, _, output = self.cli(media)
        self.assertEqual(code, 2)
        self.assertEqual(stdout, "")
        self.assertFalse(output.exists())
        self.assertFalse(media.seek_calls)
        self.assertEqual(media.opened[-1].full_seen, [0, 100, 20, 50, 100])

    def test_safe_source_middle_and_tail_omissions_with_fixed_counts_reject(self):
        vt = self.validate(FakeMedia())
        original = list(rows(self.ledger_path))
        for remove in (2, 3):
            with self.subTest(remove=remove):
                changed = deepcopy(original)
                del changed[remove]
                for i, row in enumerate(changed[1:-1]):
                    row["ordinal"] = i
                changed[-1]["presented_frames"] = 2
                self.write_records(changed)
                with self.assertRaises(ValueError):
                    compare_ledger(vt, self.ledger_path)

    def test_inserted_reordered_extra_or_missing_record_rejects(self):
        vt = self.validate(FakeMedia())
        original = list(rows(self.ledger_path))
        cases = [original[:-1], [*original, original[-1]],
                 [original[0], original[2], original[1], *original[3:]],
                 [original[0], original[1], original[1], *original[2:]],
                 original[1:], [*original[:-1], {"type": "unknown"}, original[-1]]]
        for changed in cases:
            with self.subTest(types=[r["type"] for r in changed]):
                self.write_records(changed)
                with self.assertRaises(ValueError):
                    compare_ledger(vt, self.ledger_path)

    def test_all_frame_semantics_are_cross_checked(self):
        vt = self.validate(FakeMedia())
        original = list(rows(self.ledger_path))
        mutations = {"key_frame": True, "ordinal": 9, "same_pts_ordinal": 1,
                     "time_base": [1, 999], "pts": 101, "native_sha256": "0" * 64,
                     "width": 9, "height": 9, "pix_fmt": "gray", "digest_domain": {},
                     "identity": ["0" * 64, 0, 100, 0], "timing_flags": ["duplicate_pts"]}
        for key, value in mutations.items():
            with self.subTest(field=key):
                changed = deepcopy(original)
                changed[2][key] = value
                self.write_records(changed)
                with self.assertRaises(ValueError):
                    compare_ledger(vt, self.ledger_path)

    def test_foreign_source_stream_header_and_legacy_version_reject(self):
        vt = self.validate(FakeMedia())
        original = list(rows(self.ledger_path))
        for key, value in {"source_sha256": "0" * 64, "selected_stream_index": 1,
                           "source_bytes": 1, "version": "bscout-ledger-v1",
                           "first_presented_pts": 5, "first_presented_time_base": [1, 999],
                           "toolchain": {"foreign": True}}.items():
            with self.subTest(field=key):
                changed = deepcopy(original)
                changed[0][key] = value
                self.write_records(changed)
                with self.assertRaises(ValueError):
                    compare_ledger(vt, self.ledger_path)

    def test_binding_fields_cannot_be_removed_or_forged(self):
        vt = self.validate(FakeMedia())
        original = list(rows(self.ledger_path))
        # Every generated header field is required, including configuration,
        # projection/domain versions and resolved stream/toolchain provenance.
        for field in original[0]:
            with self.subTest(missing=field):
                changed = deepcopy(original)
                del changed[0][field]
                self.write_records(changed)
                with self.assertRaises(ValueError):
                    compare_ledger(vt, self.ledger_path)
        for field in original[0]:
            if any(word in field for word in ("config", "projection", "domain")):
                with self.subTest(forged=field):
                    changed = deepcopy(original)
                    changed[0][field] = {"stale": True}
                    self.write_records(changed)
                    with self.assertRaises(ValueError):
                        compare_ledger(vt, self.ledger_path)
        for field in original[0]["decode_binding"]:
            with self.subTest(stale_binding=field):
                changed = deepcopy(original)
                changed[0]["decode_binding"][field] = {"stale": True}
                self.write_records(changed)
                with self.assertRaises(ValueError):
                    compare_ledger(vt, self.ledger_path)

    def test_forged_completion_counts_and_boolean_integer_substitution_reject(self):
        vt = self.validate(FakeMedia())
        original = list(rows(self.ledger_path))
        mutations = {"status": "diagnostic", "presented_frames": 99,
                     "timing": {"missing": False, "duplicate": False, "non_monotonic": False},
                     "source_unchanged": 1, "errors": ["forged"],
                     "decode_eof": False, "validation_passes": 0, "projection_sha256": "0" * 64,
                     "exact_recovery": {"status": "supported"}}
        for key, value in mutations.items():
            with self.subTest(field=key):
                changed = deepcopy(original)
                changed[-1][key] = value
                self.write_records(changed)
                with self.assertRaises(ValueError):
                    compare_ledger(vt, self.ledger_path)

    def test_documented_run_local_telemetry_may_differ(self):
        media = FakeMedia()
        vt = self.validate(media)
        records = list(rows(self.ledger_path))
        records[-1].update(elapsed_seconds=9876.5, peak_rss={"method": "synthetic telemetry", "bytes": 1},
                           output_bytes=1, output_bytes_before_trailer=2, traversal_table_bytes=3)
        self.write_records(records)
        compare_ledger(vt, self.ledger_path)
        for field in ("elapsed_seconds", "peak_rss", "output_bytes", "output_bytes_before_trailer",
                      "traversal_table_bytes"):
            records[-1].pop(field, None)
        self.write_records(records)
        compare_ledger(vt, self.ledger_path)
        with patch("av.open", side_effect=media.open):
            _, proof = recover(self.source, vt, vt.identity(100), ledger_path=self.ledger_path)
        self.assertEqual(proof["identity"], vt.entry(1)["identity"])

    def test_unknown_fields_and_missing_frame_fields_reject(self):
        vt = self.validate(FakeMedia())
        original = list(rows(self.ledger_path))
        for record in (0, 1, -1):
            changed = deepcopy(original)
            changed[record]["validated"] = True
            self.write_records(changed)
            with self.subTest(record=record), self.assertRaises(ValueError):
                compare_ledger(vt, self.ledger_path)
        for key in original[1]:
            changed = deepcopy(original)
            del changed[1][key]
            self.write_records(changed)
            with self.subTest(missing=key), self.assertRaises(ValueError):
                compare_ledger(vt, self.ledger_path)

    def test_timing_anomalies_anywhere_make_recovery_unsupported(self):
        for pts in ([0, 100, 100], [0, 100, 20], [0, 100, None],
                    [None, 100, 200], [0, 100, 200, 100], [200, 100, 300]):
            with self.subTest(pts=pts):
                media = FakeMedia(pts, identical=True)
                vt = self.validate(media, output=False)
                self.assertEqual(vt.trailer["presented_frames"], len(pts))
                with patch("av.open", side_effect=media.open), self.assertRaisesRegex(ValueError, "unsupported|unsafe"):
                    recover(self.source, vt, vt.identity(100))
                self.assertFalse(media.seek_calls)

    def test_compatible_frame_time_base_required_source_wide(self):
        media = FakeMedia()
        media.frames[-1].time_base = Fraction(1, 999)
        vt = self.validate(media)
        with patch("av.open", side_effect=media.open), self.assertRaises(ValueError):
            recover(self.source, vt, vt.identity(100))
        self.assertFalse(media.seek_calls)

    def test_unavailable_counts_do_not_invent_failure_available_mismatch_diagnoses(self):
        for count in (0, None):
            with self.subTest(count=count):
                media = FakeMedia(count=count)
                vt = self.validate(media, output=False)
                self.assertEqual(vt.trailer["status"], "complete")
                with patch("av.open", side_effect=media.open):
                    recover(self.source, vt, vt.identity(100))
        media = FakeMedia(count=4)
        vt = self.validate(media, output=False)
        self.assertNotEqual(vt.trailer["status"], "complete")
        self.assertTrue(vt.trailer["errors"])
        with self.assertRaises(ValueError):
            recover(self.source, vt, vt.identity(100))

    def test_plain_dict_boolean_table_and_unminted_handle_reject(self):
        vt = self.validate(FakeMedia())
        forged = object.__new__(ValidatedTraversal)
        for handle in ({"validated": True}, vt.header, True, self.ledger_path, forged):
            with self.subTest(handle=type(handle).__name__), self.assertRaises((ValueError, TypeError)):
                recover(self.source, handle, vt.identity(100))
        with self.assertRaises((ValueError, TypeError)):
            ValidatedTraversal()

    def test_legacy_direct_api_cannot_grant_trust(self):
        vt = self.validate(FakeMedia())
        with self.assertRaises((TypeError, ValueError)):
            recover(self.source, vt.entry(1), vt.header, [0], ledger_path=self.ledger_path)

    def test_closed_vt_and_public_copy_mutations_reject_or_do_not_change_authority(self):
        media = FakeMedia()
        vt = self.validate(media)
        header, entry, trailer = vt.header, vt.entry(1), vt.trailer
        header["source_sha256"] = "0" * 64
        entry["native_sha256"] = "0" * 64
        trailer["status"] = "failed"
        with patch("av.open", side_effect=media.open):
            _, proof = recover(self.source, vt, vt.identity(100))
        self.assertEqual(proof["sha256"], vt.entry(1)["native_sha256"])
        vt.close()
        for operation in (lambda: recover(self.source, vt, proof["identity"]),
                          lambda: compare_ledger(vt, self.ledger_path), lambda: vt.entry(1)):
            with self.assertRaises((ValueError, TypeError)):
                operation()

    def test_absent_identity_and_unsupported_occurrence_are_distinct_pre_seek_errors(self):
        media = FakeMedia()
        vt = self.validate(media)
        with self.assertRaisesRegex(ValueError, "absent|not found"):
            recover(self.source, vt, vt.identity(150))
        with self.assertRaisesRegex(ValueError, "occurrence|ordinal|unsupported"):
            recover(self.source, vt, vt.identity(100, 1))
        for identity in (["0" * 64, 0, 100, 0], [vt.header["source_sha256"], 1, 100, 0],
                         {"pts": 100}, [vt.header["source_sha256"], 0, True, 0]):
            with self.assertRaises((ValueError, TypeError)):
                recover(self.source, vt, identity)
        self.assertFalse(media.seek_calls)

    def test_immutable_configuration_and_recovery_selected_stream_mismatch(self):
        config = DecodeConfig()
        with self.assertRaises((FrozenInstanceError, AttributeError)):
            config.thread_count = 2
        for kwargs in ({"hardware": True}, {"thread_count": 2}, {"thread_type": "AUTO"},
                       {"err_detect": "ignore_err"}, {"demux_options": (("ignore_editlist", "1"),)}):
            with self.subTest(config=kwargs), self.assertRaises((ValueError, TypeError)):
                DecodeConfig(**kwargs)
        vt = self.validate(FakeMedia())
        with self.assertRaisesRegex(ValueError, "config|stream"):
            recover(self.source, vt, vt.identity(100), config=DecodeConfig(stream_index=1))

    def test_resolved_nonzero_video_stream_reuses_identical_decoder_options(self):
        media = FakeMedia(stream_index=1)
        vt = self.validate(media)
        self.assertEqual(vt.header["selected_stream_index"], 1)
        with patch("av.open", side_effect=media.open):
            _, proof = recover(self.source, vt, vt.identity(100), config=DecodeConfig(stream_index=1))
        self.assertEqual(proof["identity"][1], 1)
        self.assertEqual(media.opened[0].open_kwargs, media.opened[1].open_kwargs)
        for container in media.opened:
            codec = container.streams.video[0].codec_context
            self.assertEqual(codec.thread_count, 1)
            self.assertEqual(codec.thread_type, "SLICE")
            self.assertEqual(codec.options["err_detect"], "explode")

    def test_source_mutation_after_validation_rejects_before_seek(self):
        media = FakeMedia()
        vt = self.validate(media)
        self.source.write_bytes(b"different synthetic source")
        with patch("av.open", side_effect=media.open), self.assertRaisesRegex(ValueError, "Source|source"):
            recover(self.source, vt, vt.identity(100))
        self.assertFalse(media.seek_calls)
        # An observed changed source invalidates the handle even if restored.
        self.source.write_bytes(b"synthetic complete source bytes")
        with self.assertRaisesRegex(ValueError, "invalidated|closed"):
            recover(self.source, vt, [sha256(self.source), 0, 100, 0])

    def test_source_mutation_during_validation_cannot_make_recoverable_vt(self):
        media = FakeMedia(on_validation=lambda: self.source.write_bytes(b"changed during validation"))
        vt = self.validate(media)
        self.assertFalse(vt.trailer["source_unchanged"])
        self.assertNotEqual(vt.trailer["status"], "complete")
        with self.assertRaises(ValueError):
            recover(self.source, vt, vt.identity(100))
        self.assertFalse(media.seek_calls)

    def test_source_mutation_during_recovery_api_and_cli_withhold_success(self):
        media = FakeMedia()
        vt = self.validate(media)
        media.on_recovery = lambda: self.source.write_bytes(b"changed during recovery")
        with patch("av.open", side_effect=media.open), self.assertRaisesRegex(ValueError, "Source|source"):
            recover(self.source, vt, vt.identity(100))
        self.source.write_bytes(b"synthetic complete source bytes")
        code, stdout, stderr, output = self.cli(media)
        self.assertEqual(code, 2)
        self.assertEqual(stdout, "")
        self.assertFalse(output.exists())
        self.assertNotIn(str(self.source), stderr)

    def test_source_post_check_includes_recovery_container_close(self):
        media = FakeMedia()
        vt = self.validate(media)
        identity = vt.identity(100)
        media.on_recovery_close = lambda: self.source.write_bytes(b"changed when closing decoder")
        with patch("av.open", side_effect=media.open), self.assertRaisesRegex(ValueError, "Source|source"):
            recover(self.source, vt, identity)
        self.source.write_bytes(b"synthetic complete source bytes")
        code, stdout, _, output = self.cli(media)
        self.assertEqual(code, 2)
        self.assertEqual(stdout, "")
        self.assertFalse(output.exists())

    def test_seek_suffix_must_match_contiguous_vt_positions(self):
        media = FakeMedia()
        vt = self.validate(media)
        a, b, c = media.frames
        cases = {"drop": [a, c], "extra": [a, native_frame(50), b],
                 "repeat": [a, a, b], "reverse": [b, a, c],
                 "overshoot": [c], "unknown": [a, native_frame(None), b],
                 "wrong_tb": [a, native_frame(100, value=1, tb=Fraction(1, 999))],
                 "wrong_digest": [a, native_frame(100, value=99)],
                 "wrong_representation": [a, native_frame(100, value=1, width=10)],
                 "corrupt": [a, CorruptFrame(b)]}
        for case, frames in cases.items():
            with self.subTest(case=case):
                media.seek_frames = frames
                with patch("av.open", side_effect=media.open), self.assertRaises(ValueError):
                    recover(self.source, vt, vt.identity(200 if case == "reverse" else 100))

    def test_present_target_not_emitted_is_seek_failure_not_absent_identity(self):
        media = FakeMedia(seek_frames=[])
        vt = self.validate(media)
        with patch("av.open", side_effect=media.open), self.assertRaisesRegex(ValueError, "never emitted|EOF|seek"):
            recover(self.source, vt, vt.identity(100))
        self.assertEqual(len(media.seek_calls), 1)

    def test_decode_exceptions_and_corruption_never_make_complete_authority(self):
        for kwargs in ({"packet_bad": True}, {"decode_error": True}):
            with self.subTest(failure=kwargs):
                media = FakeMedia(**kwargs)
                vt = self.validate(media, output=False)
                self.assertNotEqual(vt.trailer["status"], "complete")
                with self.assertRaises(ValueError):
                    recover(self.source, vt, [sha256(self.source), 0, 100, 0])
        media = FakeMedia()
        media.frames[-1] = CorruptFrame(media.frames[-1])
        vt = self.validate(media, output=False)
        self.assertNotEqual(vt.trailer["status"], "complete")

    def test_seek_decode_exception_cli_preserves_existing_file(self):
        media = FakeMedia()
        self.validate(media)
        media.seek_frames = [media.frames[0], CorruptFrame(media.frames[1])]
        code, stdout, _, output = self.cli(media)
        self.assertEqual(code, 2)
        self.assertFalse(output.exists())
        self.assertEqual(stdout, "")
        output.write_bytes(b"existing output must survive")
        code, _, _, _ = self.cli(media, output=output)
        self.assertEqual(code, 2)
        self.assertEqual(output.read_bytes(), b"existing output must survive")

    def test_safe_source_ledger_omission_cli_validates_full_source_and_leaves_no_output(self):
        media = FakeMedia()
        self.validate(media)
        records = list(rows(self.ledger_path))
        del records[2]
        records[2]["ordinal"] = 1
        records[-1]["presented_frames"] = 2
        self.write_records(records)
        code, stdout, _, output = self.cli(media, pts=200)
        self.assertEqual(code, 2)
        self.assertEqual(stdout, "")
        self.assertFalse(output.exists())
        self.assertEqual(media.opened[-1].full_seen, [0, 100, 200])
        self.assertFalse(media.seek_calls)

    def test_cli_publication_failure_cleans_only_owned_pending_artifact(self):
        media = FakeMedia()
        self.validate(media)
        sentinel = Path(self.temp.name) / "unrelated.txt"
        sentinel.write_bytes(b"preserve unrelated files")
        with patch("bscout.cli.os.link", side_effect=OSError("synthetic publication failure")):
            code, stdout, _, output = self.cli(media)
        self.assertEqual(code, 2)
        self.assertEqual(stdout, "")
        self.assertFalse(output.exists())
        self.assertFalse(list(Path(self.temp.name).glob(".bscout-recovery-*")))
        self.assertEqual(sentinel.read_bytes(), b"preserve unrelated files")

    def test_windows_publication_error_redacts_repr_paths_and_cleans_pending_file(self):
        media = FakeMedia()
        self.validate(media)
        attempted = []
        def denied(src, dst):
            attempted.extend((Path(src), Path(dst)))
            # OSError's two filename reprs double Windows backslashes. This is
            # the actual exception shape emitted by a failed os.link call.
            raise PermissionError(13, "synthetic denied", str(src), None, str(dst))
        with patch("bscout.cli.os.link", side_effect=denied):
            code, stdout, stderr, output = self.cli(media)
        self.assertEqual(code, 2)
        self.assertEqual(stdout, "")
        message = json.loads(stderr)["error"]
        self.assertIn("PermissionError", message)
        self.assertEqual(len(attempted), 2)
        for path in (self.source, self.ledger_path, output, *attempted, Path(self.temp.name)):
            for private in (str(path), str(path.resolve())):
                self.assertNotIn(private, message)
                self.assertNotIn(repr(private), message)
                self.assertNotIn(private, stderr)
                self.assertNotIn(repr(private), stderr)
        self.assertFalse(output.exists())
        self.assertFalse(attempted[0].exists())
        self.assertFalse(list(Path(self.temp.name).glob(".bscout-recovery-*")))
        self.assertTrue(self.source.exists())
        self.assertTrue(self.ledger_path.exists())

    def test_missing_source_and_imported_ledger_api_diagnostics_omit_local_paths(self):
        missing_source = Path(self.temp.name) / "absent source é ไทย.bin"
        with self.assertRaises(ValueError) as failure:
            validate_traversal(missing_source)
        for private in (str(missing_source), str(missing_source.resolve()), str(Path(self.temp.name))):
            self.assertNotIn(private, str(failure.exception))
            self.assertNotIn(repr(private), str(failure.exception))
        media = FakeMedia()
        vt = self.validate(media)
        missing_ledger = Path(self.temp.name) / "absent ledger é ไทย.jsonl"
        for operation in (lambda: compare_ledger(vt, missing_ledger),
                          lambda: recover(self.source, vt, vt.identity(100), ledger_path=missing_ledger)):
            with self.assertRaises(ValueError) as failure:
                operation()
            for private in (str(missing_ledger), str(missing_ledger.resolve()), str(Path(self.temp.name))):
                self.assertNotIn(private, str(failure.exception))
                self.assertNotIn(repr(private), str(failure.exception))
        self.assertFalse(media.seek_calls)

    def test_pending_cleanup_failure_rolls_back_only_newly_published_output(self):
        media = FakeMedia()
        self.validate(media)
        unrelated = Path(self.temp.name) / "unrelated.txt"
        unrelated.write_bytes(b"keep unrelated output")
        original_unlink = Path.unlink
        denied_pending = []
        def deny_pending(path, *args, **kwargs):
            if path.name.startswith(".bscout-recovery-"):
                denied_pending.append(path)
                raise PermissionError(13, "synthetic persistent cleanup denial", str(path))
            return original_unlink(path, *args, **kwargs)
        with patch.object(Path, "unlink", deny_pending):
            code, stdout, stderr, output = self.cli(media)
        self.assertEqual(code, 2)
        self.assertEqual(stdout, "")
        self.assertFalse(output.exists())
        self.assertEqual(unrelated.read_bytes(), b"keep unrelated output")
        self.assertTrue(denied_pending)
        self.assertIn("PermissionError", stderr)
        # The synthetic persistent denial may leave its owned pending file.
        # It cannot justify leaving a final success artifact or deleting others.
        self.assertTrue(self.source.exists())
        self.assertTrue(self.ledger_path.exists())

    def test_valid_api_and_cli_recover_actual_seek_without_caller_authority(self):
        media = FakeMedia()
        vt = self.validate(media)
        compare_ledger(vt, self.ledger_path)
        with patch("av.open", side_effect=media.open):
            frame, proof = recover(self.source, vt, vt.identity(100))
        self.assertIs(frame, media.frames[1])
        self.assertEqual(proof["identity"], vt.entry(1)["identity"])
        self.assertEqual(proof["sha256"], vt.entry(1)["native_sha256"])
        offset, args = media.seek_calls[-1]
        self.assertTrue(args["backward"])
        self.assertFalse(args["any_frame"])
        self.assertLess(offset, 100)
        code, stdout, _, output = self.cli(media)
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(stdout)["identity"], vt.entry(1)["identity"])
        self.assertEqual(output.stat().st_size, 96)

    def test_valid_seek_may_begin_at_any_traversal_position_at_or_before_target(self):
        media = FakeMedia()
        vt = self.validate(media)
        media.seek_frames = media.frames[1:]
        with patch("av.open", side_effect=media.open):
            frame, proof = recover(self.source, vt, vt.identity(200))
        self.assertIs(frame, media.frames[-1])
        self.assertEqual(proof["first_emitted_pts"], 100)

    def test_cli_source_output_and_ledger_output_aliases_preserve_source(self):
        media = FakeMedia()
        self.validate(media)
        before = self.source.read_bytes()
        for output in (self.source, self.ledger_path):
            with self.subTest(alias=output.name):
                code, stdout, _, _ = self.cli(media, output=output)
                self.assertEqual(code, 2)
                self.assertEqual(stdout, "")
        self.assertEqual(self.source.read_bytes(), before)
        self.assertFalse(media.seek_calls)

    def test_one_full_validation_reused_for_many_seek_recoveries(self):
        media = FakeMedia()
        vt = self.validate(media)
        with patch("av.open", side_effect=media.open):
            for pts in (0, 100, 200, 100):
                _, proof = recover(self.source, vt, vt.identity(pts), ledger_path=self.ledger_path)
                self.assertEqual(proof["identity"], list(vt.identity(pts)))
        self.assertEqual(len(media.opened), 5)
        self.assertEqual(media.opened[0].full_seen, [0, 100, 200])
        self.assertTrue(all(not container.full_seen for container in media.opened[1:]))
        self.assertEqual(len(media.seek_calls), 4)

    def test_disk_table_lookup_and_explicit_context_gc_cleanup(self):
        media = FakeMedia(range(0, 100000, 100))
        vt = self.validate(media, output=False)
        directory = Path(vt.temporary_directory)
        self.assertTrue(directory.is_dir())
        self.assertGreater(vt.table_bytes, 1000)
        self.assertEqual(vt.entry(999)["pts"], 99900)
        with patch("av.open", side_effect=media.open):
            _, proof = recover(self.source, vt, vt.identity(99900))
        self.assertEqual(proof["identity"], vt.entry(999)["identity"])
        vt.close()
        vt.close()
        self.assertFalse(directory.exists())
        with patch("av.open", side_effect=FakeMedia().open):
            with validate_traversal(self.source) as context_vt:
                context_dir = Path(context_vt.temporary_directory)
        self.assertFalse(context_dir.exists())
        with patch("av.open", side_effect=FakeMedia().open):
            collected = validate_traversal(self.source)
        collected_dir = Path(collected.temporary_directory)
        del collected
        gc.collect()
        self.assertFalse(collected_dir.exists())


if __name__ == "__main__":
    unittest.main()

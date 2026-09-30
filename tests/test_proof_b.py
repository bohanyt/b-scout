"""Fail-closed B held-out configuration and public-report boundaries."""
from dataclasses import dataclass
import importlib.util
import json
import hashlib
import gzip
import struct
import zlib
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/"src"))
SPEC = importlib.util.spec_from_file_location("proof_b", ROOT/"scripts/prove_bs001_b.py")
proof = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(proof)


@dataclass(frozen=True)
class SyntheticConfig:
    version: str = "fixture-only-v1"
    threshold: int = 3


class FreezeTests(unittest.TestCase):
    def record(self):
        config = {"version": "fixture-only-v1", "threshold": 3}
        return {"configuration": config, "configuration_sha256": proof.canonical_hash(config),
                "dev_tuning_record": {"split": "dev", "fixtures": ["synthetic-dev"],
                                      "procedure": "choose using dev only", "selected_before_held_out": True}}

    def check_record(self, record):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/"frozen.json"
            path.write_text(json.dumps(record), encoding="utf-8")
            return proof.load_freeze(path, SyntheticConfig, ["synthetic-dev"])

    def test_explicit_frozen_configuration_reconstructs_exactly(self):
        frozen, config = self.check_record(self.record())
        self.assertEqual(config, SyntheticConfig())
        self.assertEqual(frozen, self.record())

    def test_missing_or_invalid_freeze_is_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/"missing.json"
            with self.assertRaisesRegex(ValueError, "requires readable"):
                proof.load_freeze(path, SyntheticConfig, ["synthetic-dev"])
            path.write_text("{", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "requires readable"):
                proof.load_freeze(path, SyntheticConfig, ["synthetic-dev"])

    def test_configuration_hash_drift_is_refused(self):
        record = self.record()
        record["configuration"]["threshold"] = 9
        with self.assertRaisesRegex(ValueError, "drifted"):
            self.check_record(record)

    def test_implicit_defaults_and_unknown_configuration_fields_are_refused(self):
        for mutate in (lambda c: c.pop("threshold"), lambda c: c.update(extra=1)):
            record = self.record()
            mutate(record["configuration"])
            record["configuration_sha256"] = proof.canonical_hash(record["configuration"])
            with self.assertRaises(ValueError):
                self.check_record(record)

    def test_heldout_or_incomplete_tuning_record_is_refused(self):
        changes = ({"split": "held-out"}, {"fixtures": ["synthetic-held-out"]},
                   {"fixtures": []}, {"procedure": ""}, {"selected_before_held_out": False})
        for change in changes:
            with self.subTest(change=change):
                record = self.record()
                record["dev_tuning_record"].update(change)
                with self.assertRaisesRegex(ValueError, "dev-only"):
                    self.check_record(record)

    def test_public_report_redacts_workspace_and_temp_paths_recursively(self):
        with tempfile.TemporaryDirectory() as directory:
            value = {"diagnostic": [str(ROOT/"tests"), str(Path(directory)/"media")],
                     "normal": "assets/frame.pgm"}
            result = proof.redact(value, Path(directory))
            self.assertEqual(result["diagnostic"], ["[checkout]\\tests", "[work]\\media"]
                             if __import__("os").name == "nt" else ["[checkout]/tests", "[work]/media"])
            self.assertEqual(result["normal"], "assets/frame.pgm")

    def test_hud_exception_requires_explicit_policy_and_authority(self):
        record = self.record()
        record["evidence_policy"] = {"allow_persistent_hud": True, "authority": "User explicitly approved regional HUD exception"}
        self.check_record(record)
        for policy in ({"allow_persistent_hud": "true"}, {"allow_persistent_hud": True}):
            record["evidence_policy"] = policy
            with self.assertRaisesRegex(ValueError, "recorded user authority"):
                self.check_record(record)


class SplitAndCoverageTests(unittest.TestCase):
    def test_held_out_hyphen_selects_canonical_frozen_split(self):
        truth = {"fixtures": [{"id": "dev", "split": "dev"}, {"id": "test", "split": "held_out"}]}
        self.assertEqual([f["id"] for f in proof.selected_fixtures(truth, "held-out")], ["test"])
        with self.assertRaisesRegex(ValueError, "no frozen fixtures"):
            proof.selected_fixtures({"fixtures": []}, "all")

    def test_native_coverage_includes_only_decoder_reported_final_duration(self):
        rows = [{"pts": 30, "time_base": [1, 100]}, {"pts": 35, "time_base": [1, 100], "duration": 2}]
        seconds, receipt = proof.native_coverage(rows, True)
        self.assertEqual(seconds, 0.07)
        self.assertEqual(receipt["last_duration_status"], "decoder_reported")
        rows[-1]["duration"] = None
        seconds, receipt = proof.native_coverage(rows, True)
        self.assertEqual(seconds, 0.05)
        self.assertEqual(receipt["last_duration_status"], "unknown")
        self.assertIsNone(proof.native_coverage(rows, False)[0])


class EvidenceByteTests(unittest.TestCase):
    def png(self, luma):
        def chunk(kind, data):
            return struct.pack(">I", len(data))+kind+data+struct.pack(">I", zlib.crc32(kind+data)&0xffffffff)
        return b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB",2,2,8,0,0,0,0)) + chunk(
            b"IDAT", zlib.compress(b"\x00"+luma[:2]+b"\x00"+luma[2:])) + chunk(b"IEND", b"")

    def fixture(self, directory):
        from bscout.common import canonical
        native = bytes([16, 32, 64, 128, 128, 128])
        domain = {"domain": "bscout-native-planes-v1", "width": 2, "height": 2, "pix_fmt": "yuv420p",
                  "planes": [{"plane": 0, "width": 2, "height": 2, "row_bytes": 2, "sample_storage_bytes": 1},
                             {"plane": 1, "width": 1, "height": 1, "row_bytes": 1, "sample_storage_bytes": 1},
                             {"plane": 2, "width": 1, "height": 1, "row_bytes": 1, "sample_storage_bytes": 1}]}
        identity = ["0"*64, 0, 10, 0]
        row = {"identity": identity, "native_sha256": hashlib.sha256(canonical(domain)+native).hexdigest(),
               "digest_domain": domain, "width": 2, "height": 2}
        output = Path(directory)
        paths = [("native_planes", "frame.yuv", native), ("native_luma_preview", "frame.pgm", b"P5\n2 2\n255\n"+native[:4]),
                 ("native_luma_png", "frame.png", self.png(native[:4]))]
        assets = []
        for kind, name, data in paths:
            (output/name).write_bytes(data)
            assets.append({"kind": kind, "path": name, "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()})
        item = {"position": 0, "identity": identity, "native_sha256": row["native_sha256"],
                "digest_domain": domain, "verified": True, "assets": assets,
                "recovery": {"identity": identity, "target_position": 0, "sha256": row["native_sha256"]}}
        return output, item, row

    def test_saved_native_and_preview_bytes_match_independent_source_domain(self):
        with tempfile.TemporaryDirectory() as directory:
            output, item, row = self.fixture(directory)
            result = proof.verify_evidence(output/"unused-source", output, [item], [row], None, True)
            self.assertEqual(result["status"], "pass")
            self.assertEqual(result["checked_frames"], 1)

    def test_self_consistent_replaced_assets_are_rejected_against_source(self):
        for kind in ("native_planes", "native_luma_preview", "native_luma_png"):
            with self.subTest(kind=kind), tempfile.TemporaryDirectory() as directory:
                output, item, row = self.fixture(directory)
                asset = next(a for a in item["assets"] if a["kind"] == kind)
                path = output/asset["path"]
                changed = self.png(bytes([1,2,3,4])) if kind == "native_luma_png" else path.read_bytes()[:-1]+b"\x00"
                path.write_bytes(changed)
                asset["sha256"] = hashlib.sha256(changed).hexdigest()
                with self.assertRaisesRegex(ValueError, "independently decoded source pixels"):
                    proof.verify_evidence(output/"unused-source", output, [item], [row], None, True)

    def test_png_corrupt_chunk_is_rejected(self):
        data = bytearray(self.png(bytes([1,2,3,4])))
        data[-1] ^= 1
        with self.assertRaisesRegex(ValueError, "CRC mismatch"):
            proof.verify_native_luma_png(data, 2, 2, bytes([1,2,3,4]))

    def test_full_archive_is_losslessly_reproducible_and_has_canonical_digest(self):
        record = {"candidates": [{"id": f"candidate-{i}", "signals": [i, i+1]} for i in range(30)]}
        with tempfile.TemporaryDirectory() as directory:
            work = Path(directory)
            first, second = work/"first.json.gz", work/"second.json.gz"
            receipt = proof.write_fixture_archive(first, record, work)
            proof.write_fixture_archive(second, record, work)
            self.assertEqual(first.read_bytes(), second.read_bytes())
            payload = gzip.decompress(first.read_bytes())
            self.assertEqual(json.loads(payload), record)
            self.assertEqual(len(payload), receipt["uncompressed_bytes"])
            self.assertEqual(hashlib.sha256(payload).hexdigest(), receipt["uncompressed_sha256"])


if __name__ == "__main__":
    unittest.main()

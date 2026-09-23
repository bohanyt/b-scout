"""Contract/guardrail tests; intentionally do not pretend to test video detection."""
import copy
import importlib.util
from pathlib import Path
import unittest

from jsonschema import Draft202012Validator, ValidationError

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("bootstrap", ROOT / "scripts/check_bootstrap.py")
bootstrap = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bootstrap)


class BootstrapTests(unittest.TestCase):
    def setUp(self):
        self.manifest = bootstrap.load_json(ROOT / "examples/manifest.example.json")
        self.event = bootstrap.load_json(ROOT / "examples/event.example.json")
        self.validator = Draft202012Validator(bootstrap.load_json(ROOT / "schemas/event.schema.json"))

    def test_examples_are_explicitly_unmeasured(self):
        self.assertTrue(self.manifest["example"])
        self.assertEqual(self.manifest["status"], "partial")
        self.assertIsNone(self.manifest["coverage"]["scanned_frames"])
        self.validator.validate(self.event)
        bootstrap.validate_pair(self.manifest, self.event)

    def test_illustrative_five_frame_interval_is_not_rounded(self):
        self.assertEqual(self.event["end_exclusive"]["frame_index"] - self.event["start"]["frame_index"], 5)
        duration = (self.event["end_exclusive"]["pts"] - self.event["start"]["pts"]) / 60000
        self.assertAlmostEqual(duration, 5 / 60)

    def test_missing_event_id_fails_schema(self):
        del self.event["event_id"]
        with self.assertRaises(ValidationError):
            self.validator.validate(self.event)

    def test_unknown_semantic_label_fails_schema(self):
        self.event["kind"] = "guaranteed_boss_reveal"
        with self.assertRaises(ValidationError):
            self.validator.validate(self.event)

    def test_end_before_start_fails(self):
        self.event["end_exclusive"]["pts"] = self.event["start"]["pts"]
        with self.assertRaises(ValueError):
            bootstrap.validate_pair(self.manifest, self.event)

    def test_source_mismatch_fails(self):
        self.event["source_id"] = "different-file"
        with self.assertRaises(ValueError):
            bootstrap.validate_pair(self.manifest, self.event)

    def test_context_outside_source_fails(self):
        self.event["context"]["start_pts"] = -1
        with self.assertRaises(ValueError):
            bootstrap.validate_pair(self.manifest, self.event)

    def test_unsafe_paths_are_rejected(self):
        for path in ("../secret", "/tmp/secret", "C:/secret", "frames\\secret", "frames/../secret", "https://example.com/a"):
            with self.subTest(path=path):
                self.assertFalse(bootstrap.safe_relative_path(path))
        self.assertTrue(bootstrap.safe_relative_path("frames/E0001.png"))

    def test_missing_evidence_ref_fails(self):
        self.event["context"]["asset_ids"] = ["absent-frame"]
        with self.assertRaises(ValueError):
            bootstrap.validate_pair(self.manifest, self.event)

    def test_best_frame_outside_interval_fails(self):
        self.event["best_frame"] = {"asset_id": "absent-frame", "frame_index": 126, "pts": 126000}
        with self.assertRaisesRegex(ValueError, "outside event"):
            bootstrap.validate_pair(self.manifest, self.event)

    def test_example_cannot_claim_complete(self):
        self.manifest["status"] = "complete"
        with self.assertRaises(ValueError):
            bootstrap.validate_pair(self.manifest, self.event)

    def test_scanned_more_than_decoded_fails(self):
        self.manifest["coverage"].update(decoded_frames=10, scanned_frames=11)
        with self.assertRaises(ValueError):
            bootstrap.validate_pair(self.manifest, self.event)

    def test_distinct_occurrences_can_share_content(self):
        second = copy.deepcopy(self.event)
        self.event["content_id"] = second["content_id"] = "same-panel-text"
        second.update(event_id="EXAMPLE-E0002", occurrence=2)
        second["start"] = {"frame_index": 180, "pts": 180000}
        second["end_exclusive"] = {"frame_index": 185, "pts": 185000}
        for record in (self.event, second):
            self.validator.validate(record)
            bootstrap.validate_pair(self.manifest, record)
        self.assertNotEqual(self.event["event_id"], second["event_id"])


if __name__ == "__main__":
    unittest.main()

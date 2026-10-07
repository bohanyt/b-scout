"""Truth/evidence matching tests; no optional decoder dependencies required."""
from copy import deepcopy
from fractions import Fraction
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from bscout.evaluation_b import evaluate_fixture


HASH = "a" * 64
REGION = [32, 32, 16, 16]
HARNESS = [0, 0, 80, 16]


def event(event_id, start, end, region=REGION, tier="easy"):
    return {"id": event_id, "start": start, "end_exclusive": end,
            "region_xywh": list(region), "tier": tier, "content_id": "synthetic"}


def fixture(events):
    return {"id": "synthetic", "split": "dev", "width": 128, "height": 96,
            "pts": [9000, 9100, 9200, 9300, 9400, 10000, 10700, 10800, 10900, 11000],
            "rate": [999, 1], "events": events}


def candidate(candidate_id, start, end, region=REGION, positions=None):
    return {"id": candidate_id, "start_position": start,
            "end_position_exclusive": end, "region_xywh": list(region),
            "evidence_positions": [start, end - 1] if positions is None else positions,
            "raw_signals": {"pixel_delta": 193.5}}


def evidence(position, **changes):
    result = {"position": position, "identity": [HASH, 0, 9000 + position * 100, 0],
              "native_sha256": HASH, "verified": True,
              "assets": [{"path": "frames/synthetic.ppm", "sha256": HASH,
                          "bytes": 41, "kind": "full_frame"}]}
    result.update(changes)
    return result


class EvaluationBTests(unittest.TestCase):
    def evaluate(self, events, candidates, records, **kwargs):
        return evaluate_fixture(fixture(events), candidates, records,
                                {i: i for i in range(10)}, HARNESS, **kwargs)

    def test_first_last_one_frame_and_raw_values_survive(self):
        result = self.evaluate([event("first", 0, 1), event("last", 9, 10)],
                               [candidate("first", 0, 1), candidate("last", 9, 10)],
                               [evidence(0), evidence(9)])
        self.assertEqual(result["metrics"]["easy"]["usable_evidence_recall"], 1)
        self.assertEqual(result["candidate_duration_frames"]["one_frame_count"], 2)
        self.assertEqual(result["candidates"][0]["raw_signals"]["pixel_delta"], 193.5)
        self.assertEqual(result["truth_matches"][1]["evidence"][0]["identity"], evidence(9)["identity"])

    def test_candidate_and_evidence_recall_are_separate(self):
        result = self.evaluate([event("short", 3, 4)], [candidate("candidate", 3, 4)], [])
        self.assertEqual(result["metrics"]["easy"]["candidate_recall"], 1)
        self.assertEqual(result["metrics"]["easy"]["usable_evidence_recall"], 0)
        self.assertEqual(result["metrics"]["easy"]["usable_evidence_miss_ids"], ["short"])
        self.assertEqual(result["false_or_noise_candidate_count"], 0)
        self.assertEqual(result["truth_matches"][0]["matched_boundaries"][0]["start_delta_frames"], 0)

    def test_only_explicit_candidate_representatives_count(self):
        result = self.evaluate([event("short", 3, 4)],
                               [candidate("candidate", 3, 4, positions=[])], [evidence(3)])
        self.assertEqual(result["metrics"]["easy"]["usable_evidence_recall"], 0)

    def test_shared_evidence_is_compact_without_dropping_candidate_mappings(self):
        candidates = [candidate(f"tile-{i}", 3, 4) for i in range(200)]
        result = self.evaluate([event("short", 3, 4)], candidates, [evidence(3)])
        match = result["truth_matches"][0]
        self.assertEqual(len(match["evidence"]), 1)
        self.assertEqual(match["evidence"][0]["position"], 3)
        self.assertEqual(match["candidate_ids"], [c["id"] for c in candidates])
        self.assertEqual(match["usable_candidate_ids"], [c["id"] for c in candidates])
        self.assertEqual(len(match["matched_boundaries"]), 200)
        self.assertEqual(result["evidence_frame_count"], 1)

    def test_explicit_trigger_metadata_and_kind_metrics_are_preserved(self):
        state = candidate("state", 3, 4)
        state.update(trigger="regional_change", occurrence=2, close_reason="content_change")
        initial = candidate("initial", 0, 1)
        initial.update(trigger="initial_structure", occurrence=1, close_reason="absence")
        inspection = candidate("inspection", 7, 8)
        inspection.update(trigger="structural_inspection", observation_of="state-long-run",
                          occurrence=2, close_reason="fixed_observation_window")
        result = self.evaluate([event("state_truth", 3, 4), event("inspection_truth", 7, 8)],
                               [state, initial, inspection], [evidence(3), evidence(7)])
        by_id = {r["id"]: r for r in result["candidates"]}
        for name, source in (("state", state), ("initial", initial), ("inspection", inspection)):
            for field in ("trigger", "observation_of", "occurrence", "close_reason"):
                self.assertEqual(by_id[name][field], source.get(field))
        self.assertEqual(result["candidate_counts_by_trigger"],
                         {"initial_structure": 1, "regional_change": 1, "structural_inspection": 1})
        matches = {m["truth_id"]: m for m in result["truth_matches"]}
        self.assertEqual(matches["state_truth"]["state_candidate_ids"], ["state"])
        self.assertEqual(matches["state_truth"]["usable_state_candidate_ids"], ["state"])
        self.assertEqual(matches["inspection_truth"]["structural_inspection_candidate_ids"], ["inspection"])
        self.assertEqual(matches["inspection_truth"]["usable_structural_inspection_candidate_ids"], ["inspection"])
        metrics = result["metrics"]["easy"]
        self.assertEqual(metrics["candidate_recall"], 1)
        self.assertEqual(metrics["by_candidate_kind"]["state"]["candidate_recall"], 0.5)
        self.assertEqual(metrics["by_candidate_kind"]["structural_inspection"]["usable_evidence_recall"], 0.5)
        self.assertFalse(result["metric_policy"]["structural_inspection_asserts_new_boundary"])
        self.assertFalse(result["metric_policy"]["recall_asserts_semantic_or_visual_boundary_detection"])

    def test_inspection_coverage_does_not_become_inferred_state_boundary(self):
        inspection = candidate("inspection", 0, 2)
        inspection.update(trigger="structural_inspection", observation_of="unchanged-run",
                          occurrence=1, close_reason="fixed_observation_window")
        result = self.evaluate([event("first", 0, 1), event("adjacent_same_pixels", 1, 2)],
                               [inspection], [evidence(0), evidence(1)])
        self.assertEqual(result["metrics"]["easy"]["usable_evidence_recall"], 1)
        self.assertEqual(result["metrics"]["easy"]["by_candidate_kind"]["state"]["candidate_recall"], 0)
        self.assertEqual(result["metrics"]["easy"]["by_candidate_kind"]["structural_inspection"]["candidate_recall"], 1)
        self.assertEqual(result["shared_candidate_matches"][0]["candidate_id"], "inspection")
        for match in result["truth_matches"]:
            self.assertEqual(match["state_candidate_ids"], [])
            self.assertEqual(match["structural_inspection_candidate_ids"], ["inspection"])
        self.assertEqual(result["candidates"][0]["occurrence"], 1)

    def test_missing_or_unrecognized_trigger_remains_unclassified(self):
        missing = candidate("missing", 3, 4)
        custom = candidate("custom", 3, 4)
        custom.update(trigger="synthetic_custom_signal", observation_of="source-reference", occurrence=9)
        result = self.evaluate([event("short", 3, 4)], [missing, custom], [evidence(3)])
        match = result["truth_matches"][0]
        self.assertEqual(match["unclassified_candidate_ids"], ["missing", "custom"])
        self.assertEqual(match["usable_unclassified_candidate_ids"], ["missing", "custom"])
        self.assertEqual(match["state_candidate_ids"], [])
        self.assertEqual(result["candidates"][1]["trigger"], "synthetic_custom_signal")
        self.assertEqual(result["candidate_counts_by_trigger"],
                         {"synthetic_custom_signal": 1, "unspecified": 1})

    def test_kind_evidence_recall_stays_separate_when_assets_missing(self):
        state = candidate("state", 3, 4)
        state["trigger"] = "regional_change"
        inspection = candidate("inspection", 7, 8)
        inspection["trigger"] = "structural_inspection"
        result = self.evaluate([event("state_truth", 3, 4), event("inspection_truth", 7, 8)],
                               [state, inspection], [])
        for kind in ("state", "structural_inspection"):
            self.assertEqual(result["metrics"]["easy"]["by_candidate_kind"][kind]["candidate_recall"], 0.5)
            self.assertEqual(result["metrics"]["easy"]["by_candidate_kind"][kind]["usable_evidence_recall"], 0)

    def test_persistent_diagnostic_evidence_is_unique_per_position(self):
        candidates = [candidate(f"continuity-{i}", 0, 10) for i in range(100)]
        candidates.append(candidate("initial", 0, 1))
        result = self.evaluate([event("persistent_hud", 0, 10)], candidates,
                               [evidence(0), evidence(9)], allow_persistent_hud=True)
        self.assertEqual(len(result["truth_matches"][0]["evidence"]), 2)
        diagnostic = result["persistent_truth_diagnostics"][0]
        self.assertEqual([r["position"] for r in diagnostic["evidence"]], [0, 9])
        self.assertEqual(len(diagnostic["continuity_candidate_ids"]), 100)
        self.assertEqual(diagnostic["initial_observation_candidate_ids"], ["initial"])

    def test_evidence_must_be_inside_truth_and_candidate(self):
        result = self.evaluate([event("short", 3, 4)],
                               [candidate("candidate", 2, 4)], [evidence(2), evidence(4)])
        self.assertEqual(result["metrics"]["easy"]["candidate_recall"], 1)
        self.assertEqual(result["metrics"]["easy"]["usable_evidence_recall"], 0)

    def test_exact_tolerance_and_overreach(self):
        result = self.evaluate([event("three", 4, 7)],
                               [candidate("allowed", 3, 8), candidate("too_early", 2, 7)],
                               [evidence(3), evidence(4), evidence(6), evidence(7)])
        self.assertEqual(result["truth_matches"][0]["candidate_ids"], ["allowed"])
        self.assertEqual(result["temporal_overreach_candidate_ids"], ["too_early"])
        self.assertEqual(result["truth_matches"][0]["temporal_rejections"][0]["start_delta_frames"], -2)

    def test_nonoverlapping_adjacent_candidate_never_matches(self):
        result = self.evaluate([event("short", 3, 4)], [candidate("adjacent", 4, 5)], [evidence(4)])
        self.assertEqual(result["metrics"]["easy"]["candidate_recall"], 0)

    def test_whole_clip_and_whole_frame_are_rejected(self):
        result = self.evaluate([event("short", 3, 4)],
                               [candidate("whole_clip", 0, 10),
                                candidate("whole_frame", 3, 4, [0, 0, 128, 96])],
                               [evidence(0), evidence(3), evidence(9)])
        self.assertEqual(result["metrics"]["easy"]["candidate_recall"], 0)
        self.assertEqual(result["rejected_candidate_ids"], ["whole_clip", "whole_frame"])
        self.assertEqual(result["false_or_noise_candidate_count"], 2)

    def test_persistent_truth_has_diagnostics_not_localization_exemption(self):
        result = self.evaluate([event("persistent", 0, 10)],
                               [candidate("continuity", 0, 10), candidate("initial", 0, 1)],
                               [evidence(0), evidence(9)])
        self.assertEqual(result["metrics"]["easy"]["candidate_recall"], 0)
        diagnostic = result["persistent_truth_diagnostics"][0]
        self.assertEqual(diagnostic["continuity_candidate_ids"], ["continuity"])
        self.assertEqual(diagnostic["initial_observation_candidate_ids"], ["initial"])
        self.assertFalse(diagnostic["counts_toward_strict_recall"])
        self.assertTrue(diagnostic["evidence"])

    def test_nearly_full_clip_cannot_evade_rejection_with_boundary_tolerance(self):
        result = self.evaluate([event("persistent_hud", 0, 10)],
                               [candidate("near_full_clip", 1, 9)], [evidence(1), evidence(8)])
        self.assertEqual(result["metrics"]["easy"]["candidate_recall"], 0)
        self.assertEqual(result["candidates"][0]["rejection_reason"], "whole_clip")
        self.assertFalse(result["metric_policy"]["allow_persistent_hud"])

    def test_explicit_persistent_hud_policy_requires_localized_verified_evidence(self):
        events = [event("persistent_hud", 0, 10)]
        candidates = [candidate("hud", 0, 10)]
        result = self.evaluate(events, candidates, [evidence(0), evidence(9)], allow_persistent_hud=True)
        self.assertEqual(result["metrics"]["easy"]["usable_evidence_recall"], 1)
        self.assertEqual(result["persistent_hud_exception_candidate_ids"], ["hud"])
        self.assertEqual(result["rejected_candidate_ids"], [])
        self.assertTrue(result["truth_matches"][0]["matched_boundaries"][0]["persistent_hud_exception"])
        self.assertTrue(result["metric_policy"]["allow_persistent_hud"])
        for records in ([], [evidence(0, verified=False)]):
            with self.subTest(records=records):
                result = self.evaluate(events, candidates, records, allow_persistent_hud=True)
                self.assertEqual(result["metrics"]["easy"]["candidate_recall"], 0)
        unrelated = self.evaluate([event("other_persistent", 0, 10)], candidates,
                                  [evidence(0)], allow_persistent_hud=True)
        self.assertEqual(unrelated["metrics"]["easy"]["candidate_recall"], 0)
        whole_frame = self.evaluate(events, [candidate("global", 0, 10, [0, 0, 128, 96])],
                                    [evidence(0)], allow_persistent_hud=True)
        self.assertEqual(whole_frame["metrics"]["easy"]["candidate_recall"], 0)

    def test_two_visually_identical_adjacent_truths_report_shared_candidate(self):
        result = self.evaluate([event("first", 0, 1), event("phase", 1, 2)],
                               [candidate("shared", 0, 2)], [evidence(0), evidence(1)])
        self.assertEqual(result["metrics"]["easy"]["usable_evidence_recall"], 1)
        self.assertEqual(result["shared_candidate_matches"], [
            {"candidate_id": "shared", "truth_ids": ["first", "phase"],
             "usable_truth_ids": ["first", "phase"]}])

    def test_reopen_occurrences_with_deduplicated_assets_remain_separate(self):
        records = [evidence(3), evidence(7)]
        result = self.evaluate([event("open", 3, 4), event("reopen", 7, 8)],
                               [candidate("open", 3, 4), candidate("reopen", 7, 8)], records)
        self.assertEqual(result["metrics"]["easy"]["usable_evidence_recall"], 1)
        self.assertEqual([m["usable_candidate_ids"] for m in result["truth_matches"]],
                         [["open"], ["reopen"]])
        self.assertNotEqual(result["truth_matches"][0]["evidence"][0]["identity"],
                            result["truth_matches"][1]["evidence"][0]["identity"])

    def test_harness_only_is_excluded_but_harness_overlap_is_not(self):
        result = self.evaluate([], [candidate("harness", 2, 3, [0, 0, 16, 16]),
                                    candidate("mixed", 2, 3, [0, 8, 16, 16]),
                                    candidate("noise", 2, 3)], [])
        self.assertEqual(result["harness_only_candidate_ids"], ["harness"])
        self.assertEqual(result["false_or_noise_candidate_ids"], ["mixed", "noise"])
        self.assertEqual(result["candidate_count"], 3)
        self.assertEqual(result["non_harness_candidate_count"], 2)

    def test_small_contained_tile_matches_but_small_intersection_does_not(self):
        result = self.evaluate([event("panel", 2, 3, [24, 24, 48, 32])],
                               [candidate("contained", 2, 3), candidate("edge", 2, 3, [64, 48, 16, 16])],
                               [evidence(2)])
        self.assertEqual(result["truth_matches"][0]["candidate_ids"], ["contained"])
        self.assertEqual(result["false_or_noise_candidate_ids"], ["edge"])

    def test_nearly_whole_frame_does_not_match_small_truth(self):
        result = self.evaluate([event("small", 2, 3)],
                               [candidate("giant", 2, 3, [0, 16, 128, 80])], [evidence(2)])
        self.assertEqual(result["metrics"]["easy"]["candidate_recall"], 0)
        self.assertEqual(result["false_or_noise_candidate_ids"], ["giant"])

    def test_native_observed_duration_is_only_rate_denominator(self):
        result = self.evaluate([], [candidate("noise", 0, 1)], [], coverage_duration=Fraction(3, 2))
        self.assertEqual(result["candidates_per_video_minute"], 40)
        self.assertEqual(result["false_or_noise_candidates_per_video_minute"], 40)
        unspecified = self.evaluate([], [candidate("noise", 0, 1)], [])
        self.assertIsNone(unspecified["candidates_per_video_minute"])

    def test_unknown_timing_only_allows_raw_candidate_diagnostics(self):
        result = self.evaluate([event("short", 3, 4)], [candidate("candidate", 3, 4)],
                               [evidence(3)], known_timing=False, coverage_duration=3)
        self.assertEqual(result["metrics"]["easy"]["candidate_recall"], 1)
        self.assertEqual(result["metrics"]["easy"]["usable_evidence_recall"], 0)
        self.assertEqual(result["timed_evidence_status"], "native_timing_unavailable")
        self.assertIsNone(result["coverage_duration_seconds"])

    def test_unverified_missing_identity_digest_and_assets_do_not_count(self):
        for changes in ({"verified": False}, {"identity": None}, {"native_sha256": "bad"},
                        {"assets": []}, {"assets": [{"path": "frame.ppm", "bytes": 0}]}):
            with self.subTest(changes=changes):
                result = self.evaluate([event("short", 3, 4)], [candidate("candidate", 3, 4)],
                                       [evidence(3, **changes)])
                self.assertEqual(result["metrics"]["easy"]["usable_evidence_recall"], 0)
                self.assertIsNotNone(result["evidence"][0]["unavailable_reason"])

    def test_generator_ids_do_not_assume_traversal_ordinal(self):
        result = evaluate_fixture(fixture([event("short", 3, 4)]),
                                  [candidate("candidate", 13, 14)], [evidence(13)],
                                  {i + 10: i for i in range(10)}, HARNESS)
        self.assertEqual(result["metrics"]["easy"]["usable_evidence_recall"], 1)
        self.assertEqual(result["candidates"][0]["generator_start"], 3)
        self.assertEqual(result["truth_matches"][0]["evidence"][0]["generator_id"], 3)

    def test_gapped_repeated_or_reversed_mapping_is_explicit_failure(self):
        for mapping in ({0: 0, 2: 2}, {0: 0, 1: 2}, {0: 0, 1: 0}, {0: 1, 1: 0}):
            with self.subTest(mapping=mapping), self.assertRaisesRegex(ValueError, "contiguous"):
                evaluate_fixture(fixture([]), [], [], mapping, HARNESS)
        result = evaluate_fixture(fixture([event("short", 3, 4)]),
                                  [candidate("candidate", 3, 4)], [], {0: 0}, HARNESS)
        self.assertEqual(result["candidates"][0]["rejection_reason"], "generator_mapping_incomplete")
        self.assertFalse(result["generator_mapping"]["complete"])

    def test_easy_and_challenge_misses_and_no_input_mutation(self):
        source = fixture([event("easy", 2, 3), event("challenge", 7, 8, tier="challenge")])
        candidates = [candidate("easy", 2, 3)]
        records = {2: evidence(2)}
        snapshot = deepcopy((source, candidates, records))
        result = evaluate_fixture(source, iter(candidates), records, {i: i for i in range(10)}, HARNESS)
        self.assertEqual(result["metrics"]["easy"]["candidate_recall"], 1)
        self.assertEqual(result["metrics"]["challenge"]["candidate_miss_ids"], ["challenge"])
        self.assertEqual((source, candidates, records), snapshot)
        json.dumps(result)


if __name__ == "__main__":
    unittest.main()

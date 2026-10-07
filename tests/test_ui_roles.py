"""Synthetic role contracts; these are not a semantic detection benchmark."""
from dataclasses import replace
from fractions import Fraction
from pathlib import Path
import sys
import unittest

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from bscout.ui_roles import RoleConfig, classify, measure_sample


class RoleTests(unittest.TestCase):
    def image(self, box):
        image = np.full((200, 320, 3), 30, np.uint8)
        if box is not None:
            x1, y1, x2, y2 = box
            image[y1:y2, x1:x2] = 90
            for y in range(y1+4, y2-2, 9):
                image[y:y+2, x1+2:x2-2] = 210
        return image

    def samples(self, box, count, *, lead=0, tail=0):
        return [measure_sample(image=self.image(box if lead <= p < lead+count else None),
                              box_xyxy=box if lead <= p < lead+count else None,
                              position=p, pts=p*256, duration_pts=256,
                              time_base=Fraction(1, 15360), evidence_ref=f"synthetic:{p}", comparison_box_xyxy=box)
                for p in range(lead+count+tail)]

    def result(self, samples, **kwargs):
        return classify(samples, candidate_id="candidate", occurrence_id="occurrence", **kwargs)

    def test_long_edge_geometry_is_hud_candidate(self):
        r = self.result(self.samples((0, 0, 100, 30), 300))
        self.assertEqual(r["role"], "persistent_hud")
        self.assertEqual(r["features"]["visible_seconds"], 5)
        self.assertTrue(r["candidate_only"])
        self.assertNotIn("probability", r)

    def test_short_edge_geometry_abstains(self):
        r = self.result(self.samples((0, 0, 100, 30), 60))
        self.assertEqual(r["role"], "unknown")
        self.assertIn("insufficient_observed_duration_for_hud", r["reasons"])

    def test_large_structured_flat_panel(self):
        r = self.result(self.samples((65, 40, 255, 160), 30))
        self.assertEqual(r["role"], "menu_panel")
        self.assertGreaterEqual(r["features"]["min_row_bands"], 3)

    def test_bracketed_one_frame_notice_retains_native_evidence(self):
        r = self.result(self.samples((140, 70, 190, 110), 1, lead=1, tail=1))
        self.assertEqual(r["role"], "transient_notice")
        self.assertEqual(r["features"]["present_count"], 1)
        self.assertEqual(r["evidence"][1]["duration_pts"], 256)
        self.assertEqual(r["observation_interval"], {"start_pts": 0, "end_pts": 768, "time_base": "1/15360"})

    def test_detector_dropout_without_pixel_removal_abstains(self):
        box=(140, 70, 190, 110)
        samples=[measure_sample(image=self.image(box), box_xyxy=box if p==1 else None,
                                comparison_box_xyxy=box, position=p, pts=p*256,
                                duration_pts=256, time_base="1/15360", evidence_ref=f"synthetic:{p}")
                 for p in range(3)]
        r=self.result(samples)
        self.assertEqual(r["role"], "unknown")
        self.assertIn("detector_absence_without_visual_change",r["reasons"])

    def test_unrelated_comparison_roi_cannot_prove_notice(self):
        box=(140,70,190,110);other=(20,20,70,60)
        samples=[]
        for p in range(3):
            image=self.image(box)
            x1,y1,x2,y2=other
            image[y1:y2,x1:x2]=200 if p==1 else 0
            samples.append(measure_sample(image=image,box_xyxy=box if p==1 else None,
                                           comparison_box_xyxy=other,position=p,pts=p*256,
                                           duration_pts=256,time_base="1/15360",evidence_ref=f"synthetic:{p}"))
        r=self.result(samples)
        self.assertGreaterEqual(r["features"]["min_boundary_pixel_delta"],24)
        self.assertEqual(r["role"],"unknown")
        self.assertIn("comparison_roi_unrelated_to_candidate",r["reasons"])

    def test_context_interval_and_candidate_interval_are_distinct(self):
        r=self.result(self.samples((140,70,190,110),1,lead=2,tail=2))
        self.assertEqual(r["observation_interval"]["start_pts"],0)
        self.assertEqual(r["observation_interval"]["end_pts"],1280)
        self.assertEqual(r["candidate_interval"],{"start_pts":512,"end_pts":768,"time_base":"1/15360"})
        self.assertIsNone(self.result(self.samples(None,3))["candidate_interval"])

    def test_no_pixel_boundary_evidence_abstains(self):
        samples=self.samples((140, 70, 190, 110),1,lead=1,tail=1)
        samples=[replace(s,comparison_box_xyxy=None,pixel_signature=None) for s in samples]
        r=self.result(samples)
        self.assertEqual(r["role"],"unknown")
        self.assertIn("visual_appearance_boundaries_unverified",r["reasons"])

    def test_unbracketed_one_frame_unknown_not_discarded(self):
        r = self.result(self.samples((140, 70, 190, 110), 1))
        self.assertEqual(r["role"], "unknown")
        self.assertEqual(len(r["evidence"]), 1)

    def test_contradictory_panel_and_notice_abstains(self):
        r = self.result(self.samples((70, 50, 250, 150), 30, lead=1, tail=1))
        self.assertEqual(r["role"], "unknown")
        self.assertEqual(r["eligible_roles"], ["menu_panel", "transient_notice"])
        self.assertIn("conflicting_role_rules", r["reasons"])

    def test_missing_position_cannot_prove_persistence(self):
        samples = self.samples((0, 0, 100, 30), 302)
        del samples[100]
        r = self.result(samples)
        self.assertEqual(r["role"], "unknown")
        self.assertEqual(r["features"]["gaps"][0]["missing_positions"], 1)

    def test_time_gap_even_with_adjacent_positions(self):
        samples = self.samples((65, 40, 255, 160), 31)
        samples[-1] = replace(samples[-1], pts=samples[-1].pts+256)
        r = self.result(samples)
        self.assertEqual(r["role"], "unknown")
        self.assertFalse(r["features"]["dense_coverage"])

    def test_sparse_duration_intervals_do_not_fake_dense_coverage(self):
        samples = [replace(s, pts=s.position*15360, duration_pts=15360)
                   for s in self.samples((0, 0, 100, 30), 6)]
        r = self.result(samples)
        self.assertEqual(r["role"], "unknown")
        self.assertEqual(r["features"]["oversized_sample_positions"], list(range(6)))

    def test_multiple_appearances_cannot_be_combined(self):
        samples = self.samples((140, 70, 190, 110), 10, lead=1, tail=1)
        samples[5] = measure_sample(image=self.image(None), box_xyxy=None, position=5,
                                  pts=5*256, duration_pts=256, time_base="1/15360", evidence_ref="synthetic:gap")
        r = self.result(samples)
        self.assertEqual(r["role"], "unknown")
        self.assertEqual(r["features"]["presence_runs"], 2)

    def test_geometry_change_is_not_persistent(self):
        samples = self.samples((0, 0, 100, 30), 300)
        samples[-1] = measure_sample(image=self.image((100, 0, 200, 30)), box_xyxy=(100, 0, 200, 30),
                                    position=299, pts=299*256, duration_pts=256,
                                    time_base="1/15360", evidence_ref="synthetic:moved")
        r = self.result(samples)
        self.assertEqual(r["role"], "unknown")
        self.assertIn("unstable_geometry", r["reasons"])

    def test_uniform_background_rectangle_has_no_ui_structure(self):
        samples = [measure_sample(image=np.full((200, 320, 3), 30, np.uint8),
                                  box_xyxy=(65, 40, 255, 160), position=p, pts=p,
                                  duration_pts=1, time_base="1/60", evidence_ref=f"synthetic:{p}")
                   for p in range(30)]
        self.assertEqual(self.result(samples)["role"], "unknown")

    def test_absence_only_has_unknown_with_evidence(self):
        r = self.result(self.samples(None, 3))
        self.assertEqual(r["role"], "unknown")
        self.assertEqual(r["evidence_count"], 3)

    def test_compact_default_and_explicit_complete_trace(self):
        import json
        samples = self.samples((0, 0, 100, 30), 600)
        short = self.result(samples[:300])
        long = self.result(samples)
        self.assertEqual(len(long["evidence"]), 2)
        self.assertEqual(long["evidence_count"], 600)
        self.assertNotIn("observations", long)
        self.assertLess(abs(len(json.dumps(long))-len(json.dumps(short))), 100)
        full = self.result(samples, include_observations=True)
        self.assertEqual(len(full["observations"]), 600)
        self.assertEqual(full["role"], long["role"])

    def test_direct_sample_construction_cannot_bypass_validation(self):
        s = self.samples((0, 0, 100, 30), 1)[0]
        for bad in ({"flat_fraction": float("nan")}, {"edge_fraction": 2},
                    {"duration_pts": 0}, {"row_bands": -1}, {"box_xyxy": (-1, 0, 5, 5)},
                    {"evidence_ref": ""}, {"time_base": "1/60"}):
            with self.assertRaises(ValueError):
                replace(s, **bad)

    def test_order_timing_shape_and_input_validation(self):
        samples = self.samples((0, 0, 100, 30), 2)
        for bad in (samples[::-1], [samples[0], samples[0]],
                    [samples[0], replace(samples[1], image_size=(321, 200))]):
            with self.assertRaises(ValueError):
                self.result(bad)
        with self.assertRaises(ValueError):
            measure_sample(image=self.image(None), box_xyxy=(-1, 0, 5, 5), position=0,
                           pts=0, duration_pts=1, time_base="1/60", evidence_ref="ref")
        with self.assertRaises(ValueError):
            self.result([])
        for bad in ({"hud_seconds": float("nan")}, {"stable_iou": 2}, {"min_row_bands": 1.5}):
            with self.assertRaises(ValueError):
                RoleConfig(**bad)


if __name__ == "__main__":
    unittest.main()

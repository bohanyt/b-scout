"""Synthetic adversarial tests; no private footage or fixtures."""
from fractions import Fraction
import unittest

import numpy as np

from bscout.region_tracking import AnchorBudgetExceeded, NativeTiming, RegionTracker, TrackingConfig


class RegionTrackingTests(unittest.TestCase):
    def setUp(self):
        self.image = np.zeros((80, 120, 3), np.uint8)
        self.image[25:28, 35:43] = (40, 180, 240)
        self.box = (30, 20, 60, 40)

    def time(self, i, duration=7):
        return NativeTiming(i, 100+i*7, duration, Fraction(1, 1000))

    def observe(self, tracker, i, image=None, boxes=None):
        return tracker.observe(self.image if image is None else image, [self.box] if boxes is None else boxes, self.time(i), f"frame:{i}")

    def test_box_jitter_uses_original_source_coordinates(self):
        tracker = RegionTracker()
        ids = [self.observe(tracker, i, boxes=[(30+i%3-1,20,60+i%3-1,40)])[0] for i in range(9)]
        self.assertEqual(len({a['content_id'] for a in ids}), 1)
        self.assertEqual(len({a['occurrence_id'] for a in ids}), 1)
        self.assertEqual(tracker.finish()['occurrences'][0]['observed_frames'], 9)

    def test_changed_glyph_at_new_box_edge_is_not_ignored(self):
        tracker = RegionTracker()
        a = self.observe(tracker, 0)[0]
        changed = self.image.copy()
        changed[25:28, 61:64] = 255
        b = self.observe(tracker, 1, changed, [(34,20,64,40)])[0]
        self.assertNotEqual(a['content_id'], b['content_id'])

    def test_equal_mean_spatial_swap_and_one_frame_content(self):
        tracker = RegionTracker()
        a = self.observe(tracker, 0)[0]
        swapped = self.image.copy()
        swapped[25:28,35:43] = 0
        swapped[30:33,35:43] = (40,180,240)
        self.assertEqual(self.image.sum(), swapped.sum())
        b = self.observe(tracker, 1, swapped)[0]
        c = self.observe(tracker, 2)[0]
        self.assertNotEqual(a['content_id'], b['content_id'])
        self.assertEqual(a['content_id'], c['content_id'])
        self.assertEqual(len({x['occurrence_id'] for x in [a,b,c]}), 3)
        self.assertEqual(tracker.occurrences[1]['observed_frames'], 1)

    def test_color_change_with_same_grayscale_mean(self):
        tracker = RegionTracker()
        red = self.image.copy()
        blue = self.image.copy()
        red[25:28,35:43] = (255,0,0)
        blue[25:28,35:43] = (0,0,255)
        a = self.observe(tracker, 0, red)[0]
        b = self.observe(tracker, 1, blue)[0]
        self.assertNotEqual(a['content_id'], b['content_id'])

    def test_single_pixel_high_contrast_change(self):
        tracker = RegionTracker()
        a = self.observe(tracker, 0)[0]
        changed = self.image.copy()
        changed[26,40] = 0
        b = self.observe(tracker, 1, changed)[0]
        self.assertNotEqual(a['content_id'], b['content_id'])

    def test_exact_mode_retains_low_contrast_single_pixel_change(self):
        tracker = RegionTracker(TrackingConfig(pixel_delta=0))
        a = self.observe(tracker,0)[0]
        changed = self.image.copy()
        changed[26,40,0] += 1
        b = self.observe(tracker,1,changed)[0]
        self.assertNotEqual(a['content_id'],b['content_id'])
        self.assertEqual(tracker.occurrences[0]['observed_frames'],1)

    def test_fixed_anchor_prevents_accumulated_noise_drift(self):
        tracker = RegionTracker(TrackingConfig(pixel_delta=12))
        original = np.full_like(self.image, 40)
        ids = [self.observe(tracker, i, original+i*5)[0]['content_id'] for i in range(5)]
        self.assertEqual(ids[0], ids[2])
        self.assertNotEqual(ids[0], ids[3])

    def test_absence_reopen_reuses_content_separate_occurrence(self):
        tracker = RegionTracker()
        first = self.observe(tracker, 0)[0]
        self.observe(tracker, 1, boxes=[])
        last = self.observe(tracker, 2)[0]
        self.assertEqual(first['content_id'], last['content_id'])
        self.assertNotEqual(first['occurrence_id'], last['occurrence_id'])
        self.assertEqual(tracker.occurrences[0]['close_reason'], 'detector_absence')
        self.assertEqual(tracker.gaps, [])

    def test_missing_observation_is_explicit_gap(self):
        tracker = RegionTracker()
        self.observe(tracker, 0)
        tracker.observe(None, None, self.time(1))
        self.observe(tracker, 2)
        self.assertEqual(tracker.occurrences[0]['close_reason'], 'observation_gap')
        self.assertEqual(tracker.gaps[0]['reason'], 'missing_observation')
        self.assertEqual(tracker.gaps[0]['missing_positions'], [1,2])
        self.assertEqual(len(tracker.occurrences), 2)

    def test_position_gap_and_native_duration_unknown(self):
        tracker = RegionTracker()
        self.observe(tracker, 0)
        tracker.observe(self.image,[self.box],self.time(4, None))
        out = tracker.finish()
        self.assertEqual(out['gaps'][0]['missing_positions'],[1,4])
        self.assertEqual(out['occurrences'][0]['last']['pts'],100)
        self.assertEqual(out['occurrences'][1]['last']['duration'],None)
        self.assertEqual(out['occurrences'][1]['last']['time_base'],[1,1000])

    def test_native_timestamp_gap_even_with_contiguous_positions(self):
        tracker = RegionTracker()
        self.observe(tracker,0)
        tracker.observe(self.image,[self.box],NativeTiming(1,1000,7,Fraction(1,1000)))
        self.assertEqual(tracker.gaps[0]['reason'],'timing_gap')
        self.assertIsNone(tracker.gaps[0]['missing_positions'])
        self.assertEqual(len(tracker.occurrences),2)

    def test_unknown_duration_does_not_assert_native_continuity(self):
        tracker = RegionTracker()
        tracker.observe(self.image,[self.box],self.time(0,None))
        self.observe(tracker,1)
        self.assertEqual(tracker.gaps[0]['reason'],'unknown_previous_duration')
        self.assertIsNone(tracker.occurrences[0]['end_pts_exclusive'])
        self.assertEqual(len(tracker.occurrences),2)

    def test_overlapping_native_intervals_are_rejected(self):
        tracker = RegionTracker()
        self.observe(tracker,0)
        before = tracker.snapshot()
        with self.assertRaises(ValueError):
            tracker.observe(self.image,[self.box],NativeTiming(1,101,7,Fraction(1,1000)))
        self.assertEqual(tracker.snapshot(),before)

    def test_simultaneous_nearby_different_content_does_not_merge(self):
        tracker = RegionTracker()
        self.image[25:28,70:78] = 255
        boxes = [self.box,(65,20,95,40)]
        first = self.observe(tracker,0,boxes=boxes)
        last = self.observe(tracker,1,boxes=boxes[::-1])
        self.assertEqual(first[0]['occurrence_id'],last[1]['occurrence_id'])
        self.assertNotEqual(first[0]['content_id'],first[1]['content_id'])

    def test_detector_split_ambiguity_does_not_drop_detections(self):
        tracker = RegionTracker()
        self.observe(tracker,0)
        out = self.observe(tracker,1,boxes=[self.box,(31,20,61,40)])
        self.assertEqual(len(out),2)
        self.assertEqual(tracker.occurrences[0]['close_reason'],'ambiguous_association')
        self.assertEqual(len(tracker.occurrences),3)

    def test_large_motion_exceeds_jitter_and_is_retained(self):
        tracker = RegionTracker()
        a = self.observe(tracker,0)[0]
        b = self.observe(tracker,1,boxes=[(50,20,80,40)])[0]
        self.assertNotEqual(a['occurrence_id'],b['occurrence_id'])
        self.assertNotEqual(a['content_id'],b['content_id'])

    def test_budget_rejection_is_transactional_and_explicit(self):
        tracker = RegionTracker(TrackingConfig(max_anchor_bytes=6500))
        self.observe(tracker,0)
        before = tracker.snapshot()
        changed = self.image.copy()
        changed[26,40] = 0
        with self.assertRaises(AnchorBudgetExceeded):
            self.observe(tracker,1,changed)
        self.assertEqual(tracker.snapshot(),before)
        self.observe(tracker,2)
        self.assertEqual(tracker.gaps[0]['reason'],'position_gap')

    def test_no_duration_minimum_or_anchor_limit_by_default(self):
        tracker = RegionTracker()
        for i in range(40):
            image = self.image.copy()
            image[26,40] = i*5
            self.observe(tracker,i,image)
        self.assertIsNone(tracker.config.max_anchor_bytes)
        self.assertGreater(len(tracker.contents),10)
        self.assertEqual(sum(o['observed_frames'] for o in tracker.occurrences),40)

    def test_validation_and_snapshot_isolation(self):
        tracker = RegionTracker()
        self.observe(tracker,0)
        bad = [(0,0,121,80)]
        with self.assertRaises(ValueError):
            self.observe(tracker,1,boxes=bad)
        with self.assertRaises(ValueError):
            self.observe(tracker,0)
        out = tracker.snapshot()
        out['contents'][0]['anchor_box_xyxy'][0] = 999
        self.assertEqual(tracker.contents[0]['anchor_box_xyxy'][0],30)
        tracker.finish()
        with self.assertRaises(ValueError):
            self.observe(tracker,1)
        with self.assertRaises(ValueError):
            TrackingConfig(pixel_delta=256)
        with self.assertRaises(ValueError):
            NativeTiming(0,0,0,Fraction(1,60))


if __name__ == '__main__':
    unittest.main()

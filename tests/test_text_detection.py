"""Synthetic spatial mapping, seam retention, and optional-adapter contracts."""
from fractions import Fraction
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import numpy as np
from bscout.text_detection import (Detection, FrameTiming, LocalDetection, PPOCRv4Backend,
                                  SpatialPolicy, TextDetector, plan_views, suppress_seams)


def resize_stub(image, size):
    return np.zeros((size[1], size[0], 3), np.uint8)


class TextDetectionTests(unittest.TestCase):
    def test_explicit_policy_validation(self):
        for kwargs in (dict(max_side=0), dict(max_side=33), dict(max_side=True),
                       dict(max_side=960, overlap=(1, 0)),
                       dict(max_side=960, tile_size=(100, 100), overlap=(100, 0)),
                       dict(max_side=960, tile_size=(0, 100)),
                       dict(max_side=960, duplicate_iou=float("nan"))):
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                SpatialPolicy(**kwargs)

    def test_rounded_dimensions_use_separate_exact_axes(self):
        policy = SpatialPolicy(960)
        view, = plan_views(1001, 577, policy)
        self.assertEqual(view.input_size, (960, 544))
        self.assertEqual(view.to_source((0., 0., 960., 544.)), (0., 0., 1001., 577.))
        box = view.to_source((240., 136., 720., 408.))
        self.assertEqual(box, (250.25, 144.25, 750.75, 432.75))

    def test_tiles_cover_every_pixel_and_anchor_last_edges(self):
        views = plan_views(113, 79, SpatialPolicy(64, tile_size=(64, 48), overlap=(16, 12)))
        coverage = np.zeros((79, 113), np.uint16)
        for v in views:
            x1, y1, x2, y2 = v.source_xyxy
            coverage[y1:y2, x1:x2] += 1
            self.assertEqual(v.to_source((0, 0, *v.input_size)), tuple(map(float, v.source_xyxy)))
        self.assertTrue((coverage >= 1).all())
        self.assertGreater(coverage.max(), 1)
        self.assertEqual(views[-1].source_xyxy, (49, 31, 113, 79))
        self.assertEqual(len({v.source_xyxy for v in views}), len(views))

    def test_small_and_thin_source_views_do_not_disappear(self):
        for shape in ((1, 1), (13, 77), (91, 9)):
            view, = plan_views(*shape, SpatialPolicy(960, tile_size=(100, 100), overlap=(16, 16)))
            self.assertEqual(view.to_source((0, 0, *view.input_size)), (0., 0., *map(float, shape)))
            self.assertGreaterEqual(min(view.input_size), 32)

    def test_source_clip_invalid_rejections_and_unknown_duration(self):
        backend = lambda image: [LocalDetection((-10., -10., 100., 100.), .8),
                                 LocalDetection((1000., 0., 1001., 5.), .7),
                                 LocalDetection((0., 0., float("nan"), 1.), .2),
                                 LocalDetection((5., 1., 1., 2.), .1)]
        timing = FrameTiming(-3, Fraction(1, 90000))
        result = TextDetector(backend, SpatialPolicy(64), resize=resize_stub).detect(np.zeros((17, 33, 3), np.uint8), timing)
        self.assertEqual(result.timing, timing)
        self.assertEqual(result.detections[0].box, (0., 0., 33., 17.))
        self.assertEqual((result.raw_count, result.rejected_count, result.suppressed_count), (4, 3, 0))
        self.assertIsNone(result.timing.duration_pts)

    def test_seam_iou_and_clipped_containment_keep_provenance(self):
        policy = SpatialPolicy(64, tile_size=(64, 64), overlap=(32, 0))
        views = plan_views(96, 64, policy)
        boxes = [Detection((40., 10., 60., 20.), .9, 0, 0),
                 Detection((41., 10., 61., 20.), .8, 1, 0),
                 Detection((48., 10., 60., 20.), .7, 1, 1)]
        kept = suppress_seams(boxes, views, policy)
        self.assertEqual(len(kept), 1)
        self.assertEqual(kept[0].duplicates, ((1, 0), (1, 1)))
        self.assertEqual(kept[0].box, boxes[0].box)

    def test_complete_box_beats_high_score_seam_fragment_and_raw_is_recoverable(self):
        calls = []
        def backend(image):
            calls.append(1)
            return ([LocalDetection((50., 10., 64., 20.), .99)] if len(calls) == 1
                    else [LocalDetection((18., 10., 38., 20.), .7)])
        policy = SpatialPolicy(64, tile_size=(64, 64), overlap=(32, 0))
        result = TextDetector(backend, policy, resize=resize_stub).detect(np.zeros((64, 96, 3), np.uint8), FrameTiming(1, Fraction(1, 60)))
        self.assertEqual(len(result.detections), 1)
        self.assertEqual(result.detections[0].box, (50., 10., 70., 20.))
        self.assertEqual(result.detections[0].duplicates, ((0, 0),))
        self.assertEqual(len(result.raw_candidates), 2)
        self.assertTrue(result.raw_candidates[0].seam_clipped)
        self.assertFalse(result.raw_candidates[1].seam_clipped)
        self.assertEqual(result.raw_candidates[0].score, .99)

    def test_adjacent_text_and_same_view_candidates_are_retained(self):
        policy = SpatialPolicy(64, tile_size=(64, 64), overlap=(32, 0))
        views = plan_views(96, 64, policy)
        boxes = [Detection((35., 10., 45., 20.), .9, 0, 0),
                 Detection((46., 10., 56., 20.), .8, 1, 0),
                 Detection((35., 10., 45., 20.), .7, 0, 1)]
        self.assertEqual(len(suppress_seams(boxes, views, policy)), 3)

    def test_nonoverlapping_views_never_suppress(self):
        policy = SpatialPolicy(64, tile_size=(64, 64))
        views = plan_views(128, 64, policy)
        boxes = [Detection((60., 1., 68., 8.), .9, 0, 0), Detection((60., 1., 68., 8.), .8, 1, 0)]
        self.assertEqual(len(suppress_seams(boxes, views, policy)), 2)

    def test_no_global_candidate_cap(self):
        boxes = [LocalDetection((float(i%32), float(i//32), float(i%32+1), float(i//32+1)), .7) for i in range(2048)]
        result = TextDetector(lambda image: boxes, SpatialPolicy(64), resize=resize_stub).detect(np.zeros((64, 64, 3), np.uint8), FrameTiming(5, Fraction(1, 60), 1))
        self.assertEqual(len(result.detections), 2048)
        self.assertEqual(result.raw_count, 2048)

    def test_one_frame_calls_preserve_native_timing_and_input(self):
        image = np.full((32, 32, 3), 77, np.uint8)
        def mutate_backend(prepared):
            prepared[:] = 0
            return [LocalDetection((1., 2., 5., 6.), .7)]
        detector = TextDetector(mutate_backend, SpatialPolicy(32), resize=lambda image, size: image)
        for pts, base, duration in ((7, Fraction(1001, 60000), 1), (9200, Fraction(1, 15360), 256)):
            result = detector.detect(image, FrameTiming(pts, base, duration))
            self.assertEqual(result.timing, FrameTiming(pts, base, duration))
            self.assertEqual(len(result.detections), 1)
            self.assertTrue((image == 77).all())

    def test_backend_failure_propagates_and_resize_is_checked(self):
        def fail(image):
            raise RuntimeError("bounded invocation failed")
        with self.assertRaisesRegex(RuntimeError, "bounded invocation failed"):
            TextDetector(fail, SpatialPolicy(32), resize=resize_stub).detect(np.zeros((32, 32, 3), np.uint8), FrameTiming(1, Fraction(1, 60)))
        with self.assertRaisesRegex(ValueError, "resize returned"):
            TextDetector(lambda image: [], SpatialPolicy(32), resize=lambda image, size: image[:1]).detect(np.zeros((32, 32, 3), np.uint8), FrameTiming(1, Fraction(1, 60)))

    def test_bad_image_timing_and_native_values_rejected(self):
        detector = TextDetector(lambda image: [], SpatialPolicy(32), resize=resize_stub)
        for image in (np.zeros((0, 2, 3), np.uint8), np.zeros((2, 2), np.uint8), np.zeros((2, 2, 3), np.float32)):
            with self.assertRaises(ValueError):
                detector.detect(image, FrameTiming(1, Fraction(1, 60)))
        for args in ((1.0, Fraction(1, 60)), (1, .1), (1, Fraction(0)), (1, Fraction(1, 60), 0)):
            with self.assertRaises(ValueError):
                FrameTiming(*args)

    def test_optional_imports_absent_on_module_import(self):
        code = "import sys; from bscout.text_detection import TextDetector; assert not any(x in sys.modules for x in ('cv2','onnxruntime','pyclipper'))"
        result = subprocess.run([sys.executable, "-c", "import sys; sys.path.insert(0, " + repr(str(ROOT/"src")) + "); " + code], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_local_backend_output_map_scale_and_bgr_normalization(self):
        backend = PPOCRv4Backend.__new__(PPOCRv4Backend)
        polygon = np.array([[1, 2], [8, 2], [8, 10], [1, 10]], np.float32)
        class Session:
            def run(self, outputs, inputs):
                self.tensor = inputs["input"]
                return [np.full((1, 1, 16, 16), .8, np.float32)]
        class Offset:
            def AddPath(self, *args): pass
            def Execute(self, amount): return [polygon.tolist()]
        backend.session = Session()
        backend.name = "input"
        backend.bitmap_threshold, backend.box_threshold, backend.unclip_ratio = .3, .5, 1.6
        backend.pyclipper = SimpleNamespace(PyclipperOffset=Offset, JT_ROUND=1, ET_CLOSEDPOLYGON=2)
        backend.cv2 = SimpleNamespace(
            RETR_LIST=0, CHAIN_APPROX_SIMPLE=0,
            dilate=lambda mask, kernel: mask,
            findContours=lambda *args: ([polygon], None),
            minAreaRect=lambda contour: ((4., 6.), (7., 8.), 0.),
            boxPoints=lambda rect: polygon.copy(),
            fillPoly=lambda *args: None,
            mean=lambda *args, **kwargs: (.8, 0., 0., 0.),
            arcLength=lambda *args: 30., contourArea=lambda poly: 56.,
        )
        image = np.zeros((32, 64, 3), np.uint8)
        image[:, :, 1], image[:, :, 2] = 127, 255
        detection, = backend(image)
        self.assertEqual(detection.box, (4., 4., 32., 20.))
        self.assertEqual(backend.session.tensor.shape, (1, 3, 32, 64))
        self.assertEqual(backend.session.tensor.dtype, np.float32)
        np.testing.assert_allclose(backend.session.tensor[0, :, 0, 0], [-1., 127/255*2-1, 1.], atol=1e-7)

    def test_model_hash_is_checked_before_optional_import_or_inference(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td)/"synthetic.onnx"
            path.write_bytes(b"synthetic invalid model")
            with self.assertRaisesRegex(ValueError, "SHA256 differs"):
                PPOCRv4Backend(path, "0"*64)
        for kwargs in (dict(threads=0), dict(bitmap_threshold=0), dict(unclip_ratio=float("inf"))):
            with self.assertRaises(ValueError):
                PPOCRv4Backend("unused", "0"*64, **kwargs)


if __name__ == "__main__":
    unittest.main()

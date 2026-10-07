# Optional text presence adapter

`bscout.text_detection` is a standalone candidate component. It does not alter
native traversal, the regional baseline, OCR recognition, or the CLI. Importing
it requires the project's NumPy runtime; OpenCV, ONNX Runtime and pyclipper load
only when the caller explicitly invokes the optional local adapter. No model
or dependency is downloaded. Supply a reviewed local model and its SHA256.

```python
from fractions import Fraction
from bscout.text_detection import (
    FrameTiming, PPOCRv4Backend, SpatialPolicy, TextDetector,
)

backend = PPOCRv4Backend("reviewed-detector.onnx", expected_sha256=model_sha256)
policy = SpatialPolicy(max_side=1600)
# Generic overlapping source-pixel tiles can instead be selected explicitly:
# policy = SpatialPolicy(960, tile_size=(960, 960), overlap=(192, 192))
detector = TextDetector(backend, policy)
result = detector.detect(
    decoded_bgr_uint8,
    FrameTiming(native_pts, Fraction(time_base_num, time_base_den), native_duration),
)
for candidate in result.detections:
    print(candidate.box, candidate.score, candidate.duplicates)
```

The caller supplies each decoded presentation frame with its original integer
PTS and rational time-base. Duration is a native positive integer or `None`
when unknown. This module neither traverses nor drops frames, and it does not
infer timing from FPS. A failed backend invocation raises; callers must report
incomplete coverage instead of treating failure as an empty successful frame.
A one-frame candidate is returned immediately with no duration requirement.

`SpatialPolicy` is mandatory. `max_side` is a multiple of 32, at least 32;
full-frame mode processes one view. Tiled mode covers the complete image and
anchors the final crop at each source edge. Every view is resized independently
with linear interpolation to the nearest multiple of 32, with a minimum 32 per
axis. This can slightly enlarge a small view or one axis. The result records
all effective `input_size` values and source crop XYXY boxes so rounding is
visible. No truth annotations or region hints enter the policy or backend.
Spatial resizing can miss small text; tiling costs extra model calls.

Coordinates are floating-point source pixels, XYXY with exclusive right and
bottom edges, suitable for outward-rounded array crops. The custom backend
contract is `backend(resized_bgr_uint8) -> list[LocalDetection]`; its boxes use
that resized input's coordinate system. Per-axis effective ratios and crop
origins recover source coordinates. Boxes are clipped to their source view;
nonfinite, reversed or empty boxes are rejected and counted. The decoded input
is copied before handing it to the backend. Scores are uncalibrated detector
signals; they do not establish text correctness or semantic content equality.

The PP-OCRv4 backend uses BGR normalization `(pixel/255 - .5)/.5`, CPU inference,
DB bitmap threshold `.3`, box score threshold `.5`, unclip ratio `1.6`, a 2x2
dilation, and contour size filters. All contours are examined, without a global
candidate cap. Geometry follows DB-style minimum-area rectangles and polygon
offsetting; it is not a full PaddleOCR pipeline and does not read text. Model
output-map dimensions are mapped explicitly to input dimensions. Changing
thresholds, color conventions, model or preprocessing requires separate
validation; no general recall guarantee follows from these defaults.

Seam suppression considers overlapping views only. Same-view boxes remain.
It prefers boxes away from interior crop edges, then higher detector scores and
larger areas. IoU at least `.5` or smaller-box containment at least `.85` marks
a duplicate. Defaults are adjustable in the policy and are geometry heuristics:
a nested distinct text region can be suppressed. `result.raw_candidates`
retains every valid mapped box, score, crop view and local index, while each
kept candidate lists suppressed `(view_index, local_index)` references.
`seam_clipped` reports proximity within one model-input pixel of an interior
crop edge; it is a useful preference, not proof that a glyph was truncated.
`raw_count`, `rejected_count` and `suppressed_count` make reductions explicit.
No count cap or temporal minimum is imposed. Outputs grow with image tile count
and detector candidates; overlap does not guarantee recovery of arbitrary long
text. Retain raw candidates when later OCR or review needs the alternate crop.

Run synthetic contracts with:

```text
python -m unittest discover -s tests -p test_text_detection.py -v
```

These tests verify source mapping, complete tile coverage, edges, duplicate
provenance, complete-box preference, uncapped candidate retention, optional
imports, model hash checking and error propagation. They are not a real-video
recall benchmark. Real evaluation must disclose exact windows, native timing,
manual annotation scope, false candidates, model/preprocessing and CPU cost.
This component has no semantic roles, content tracking or evidence writer.

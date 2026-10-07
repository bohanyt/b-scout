# Region content and occurrence tracking

`bscout.region_tracking.RegionTracker` is an optional in-memory component for
source-pixel detections. It does not run a detector, OCR, speech model or network
request. Existing regional indexing behavior is unchanged.

```python
from fractions import Fraction
import numpy as np
from bscout.region_tracking import NativeTiming, RegionTracker, TrackingConfig

tracker = RegionTracker(TrackingConfig(max_anchor_bytes=16 * 1024 * 1024))
pixels = np.zeros((80, 120, 3), dtype=np.uint8)
pixels[25:28, 35:43] = (40, 180, 240)
assignments = tracker.observe(
    pixels, [(30, 20, 60, 40)],
    NativeTiming(position=0, pts=100, duration=7, time_base=Fraction(1, 1000)),
    evidence_ref="source-frame:0",
)
records = tracker.finish()
```

Supply every decoded presentation position and the original integer PTS,
positive integer duration when known, and rational time base. Pixels must be
source-sized `HxWx3 uint8`, with consistent channel order. XYXY boxes are
half-open: `[x1, y1, x2, y2)`. Convert inclusive detector endpoints explicitly.
Do not normalize timestamps, resize patches, skip presentation frames or infer
missing durations when adapting a decoder. Different source dimensions require
a separate tracker.

The spatial gate requires IoU at least `0.65` and every box edge within eight
source pixels of the fixed initial box. Association must be mutually unique;
ambiguous detector splits/merges create separate occurrences. The initial box
never drifts. Its visual support expands by `max_box_jitter + context_pixels`
(default ten pixels), clipped to the source. Every associated incoming box lies
inside that fixed support, including newly exposed edge glyphs.

Content comparison uses the same source coordinates and all three channels.
For each pixel, it measures the largest absolute channel difference from the
fixed anchor. Defaults allow channel differences up to twelve levels, but zero
pixels above that threshold. A single higher-contrast changed pixel therefore
splits content. Anchors never update during an occurrence, so repeated small
changes cannot indefinitely evade the initial reference. Set `pixel_delta=0`
for exact source-pixel equality; compression noise can then increase fragments.
Raising `pixel_delta` or `max_changed_pixels` can merge real glyph changes.
These thresholds are configuration values, not calibrated probabilities.

An observed empty detection list `[]` closes occurrences with
`detector_absence`; this is not proof that the visible region disappeared.
`boxes=None` records a missing-observation gap. Noncontiguous positions and
known native timestamp gaps close occurrences and emit gap records. An unknown
previous duration also creates an explicit gap instead of asserting native
continuity. Overlapping native intervals are rejected before state changes.
Gap `missing_positions` ranges are half-open; `None` means the native temporal
uncertainty does not establish missing presentation positions.

One-frame content is immediately retained. Returning content can reuse a
location-bound content ID after absence or a content change, while each new
appearance receives its own occurrence ID. Equal-looking regions elsewhere
remain separate candidates. Historical content matching must be unique; multiple
possible anchors produce a new content candidate. These IDs describe visual
candidates and observed appearances, not recognized text or editorial events.

`observe()` returns an assignment for every input detection in input order,
including its native timing and optional evidence reference. Occurrence records
hold first/last native timing, observed detection count, initial/last boxes,
first/last references, close reason and native `end_pts_exclusive` (unknown when
last duration is unknown). Content records hold support geometry, initial
native timing, a patch digest and a reference. No full decoded frames or evidence
assets appear in the snapshot. Reference strings are opaque; the component does
not open paths or follow links from footage. Digests are not native-frame
recovery proof. The snapshot is a diagnostic/intermediate catalog, not a compact retrieval
export. Rich timing and comparison records can exceed a prior compact catalog
even when there are fewer occurrences. A separate export adapter must preserve
every occurrence while providing a compact index and selected evidence on demand.
`snapshot()` copies output records; `finish()` closes remaining
occurrences and prevents further observations.

There is no default global content cap, minimum event length or temporal grace
period. Distinct anchor patches and records remain in memory, growing with
content and appearances. `max_anchor_bytes` optionally bounds committed pixel
anchors; it does not bound total process memory, temporary comparisons, staging
patches or record storage. `AnchorBudgetExceeded` rejects the whole observation
without consuming it. A caller must stop and report partial coverage, or retry
with an explicit changed budget. Continuing at another position records a gap.
No anchors are evicted and no detections silently dropped. Long recordings need
a separately reviewed persistence strategy; matching new content currently
searches stored anchors and can become costly.

Synthetic validation covers jitter, changed edge glyphs, equal-mean spatial
swaps, channel-only changes, single-pixel/high-contrast and one-frame changes,
fixed-anchor drift, absence/reopen, missing/unknown timing, timestamp and position
gaps, overlap rejection, ambiguous association and transactional budget failure.
Run `python -m unittest discover -s tests -p test_region_tracking.py -v` with
this checkout's `src` on `PYTHONPATH`.

Source alignment removes a crop-resizing failure mode. Animated backgrounds,
cursor movement, detector misses and box changes beyond the spatial gate still
fragment appearances. Low-contrast changes below configured thresholds can
merge. Neither the targeted tests nor reduced candidate counts establish a
passing detection benchmark, real short-event recall or semantic equality.

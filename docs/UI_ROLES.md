# Conservative UI role candidates

`bscout.ui_roles` is an offline, model-free component. It classifies a supplied tracked source-pixel region as `persistent_hud`, `transient_notice`, `menu_panel`, or `unknown`. These are rule-supported candidates, not confirmed interface semantics or calibrated probabilities. It performs no OCR, speech processing, model download, cloud call, or source-file write. It is not connected to the indexing CLI.

Pass every available presentation-frame observation for one occurrence to `measure_sample`, then `classify`. The caller supplies a source-sized three-channel `uint8` NumPy image, original integer PTS and duration, positive rational time base, presentation position, source-pixel XYXY end-exclusive box, and an evidence reference. A `None` box records detector absence; it does not prove that an interface element disappeared. Preserve original native timing. RGB and BGR use the same channel-mean features.

```python
from fractions import Fraction
from bscout.ui_roles import classify, measure_sample

# source_image is a decoded source-sized uint8 image, not a resized thumbnail.
observation = measure_sample(
    image=source_image, box_xyxy=(12, 0, 120, 30),
    position=0, pts=522, duration_pts=256,
    time_base=Fraction(1, 15360), evidence_ref="source:pts:522",
)
result = classify(
    [observation], candidate_id="region-1", occurrence_id="appearance-1",
)
assert result["role"] == "unknown"
assert result["evidence_count"] == 1
```

`measure_sample` examines every crop pixel and retains scalar measurements, not the image. `RoleSample` validates native timing, geometry, finite feature fractions and references even when constructed directly. Its measurements should come from the factory. For notice-boundary evidence, also supply `comparison_box_xyxy`: the same fixed source-pixel region in visible and surrounding absent observations. Its IoU with every visible candidate box must meet `stable_iou`; a same-but-unrelated region cannot support notice boundaries. The factory computes 16 spatial cell means from all pixels in that region without resizing the source. Neither API accepts OCR text or a manual semantic label. The caller remains responsible for correct source dimensions, detection association and source-bound evidence references; validation cannot certify those facts.

The features are observable quantities:

| Feature | Measurement |
|---|---|
| Coverage | Native duration sum, native interval span, exact adjacent positions and PTS endpoints; missing observations are reported as gaps |
| Presence | Duration-weighted occupancy, presence transitions, distinct presence runs, surrounding detected-absence samples |
| Geometry | Minimum IoU against the first visible box, minimum/maximum source-area fraction, distance from image edges |
| Visual boundaries | Minimum mean absolute difference between fixed-ROI 4x4 native-pixel cell means at appearance and disappearance |
| Flatness | Fraction of adjacent channel-mean pixel differences at most 8 on the 0-255 scale |
| Structure | Fraction of adjacent differences greater than 24, and disjoint horizontal bands whose mean vertical difference exceeds 8 |

Default rules require contiguous observations, no observation interval longer than 0.1 seconds, one presence run, anchor IoU at least 0.9, and edge fraction at least 0.005. The interval ceiling is an explicit classification evidence requirement; a lower-frame-rate source can therefore return `unknown`. It never removes its events.

- `persistent_hud`: at least 5 observed visible seconds, occupancy at least 0.9, area at most 0.12, and distance to the nearest image edge at most 0.04 in every visible observation. This supports persistence only within the observed interval.
- `menu_panel`: at least 0.5 observed visible seconds, area at least 0.15, flatness at least 0.65, and at least 3 horizontal structure bands in every visible observation.
- `transient_notice`: detected absence before and after a single presence run, visible duration at most 2 seconds, area at most 0.3, interior placement beyond the 0.04 edge margin, flatness at least 0.65, and pixel-signature difference at least 24 at both boundaries in the same supplied comparison ROI. Missing visual boundary evidence or identical pixels during a detector dropout cause abstention. There is no minimum visible duration or frame count: a bracketed one-frame event can be a notice candidate.
- `unknown`: no supported rule, missing/sparse coverage, unstable geometry, multiple appearances, or competing rules. A brief large panel can satisfy menu and notice cues simultaneously, so it abstains.

`RoleConfig` exposes these thresholds. Effective configuration, features, eligible roles, reasons, IDs, separately named observation and candidate intervals, and source evidence references appear in every result. Reasons such as censored boundaries or short duration can remain even when a different rule supports a candidate. Pixel values are heuristic measurements; changing a threshold requires separate evaluation.

`observation_interval` includes all supplied context observations, including detected-absence brackets. `candidate_interval` bounds first/last detected presence and is `None` for absence-only input. Multiple runs or gaps can lie inside either interval and are explicitly flagged; neither interval asserts semantic occurrence truth.

The default result references only the first/last observed and first/last visible samples (at most four references), plus the complete observation count and the caller-owned `occurrence_id`. For a long stable input this keeps the classification record compact. Request `include_observations=True` for a separate complete per-sample trace under `observations`. The caller must retain its full occurrence evidence; this summary does not filter, cap, merge or delete observations. Coverage-gap diagnostics can grow with the number of gaps. The component consumes the supplied sequence and uses linear time/state; it is not a whole-video streaming index.

Classify repeated appearances separately. An unrelated background change or different pixels does not prove a notice; the boundary signature can miss changes within a cell that preserve its mean, causing abstention without deleting the event. A missing detection may fragment an occurrence, and a content replacement may look like an absence in an upstream association. The classifier does not repair tracking, deduplicate content, read text, infer intent, or gate event retention. A single unbracketed frame remains evidence with an `unknown` role. Short windows cannot prove enduring HUD behavior or complete notice boundaries. Small radial menus, image-rich menus, central HUD elements, world scenery and irregular layouts may be missed or confused. Manual labels and supplied evaluation regions must remain separate from predictions; conditional tests on hand-localized panels do not establish automatic localization quality.

Run the synthetic contracts with `python -m unittest discover -s tests -p test_ui_roles.py -v`. These cover timing gaps, sparse duration intervals, changing geometry, contradictory cues, one-frame events, direct-construction validation and compact output. They verify implementation behavior, not real-world semantic detection accuracy. Real footage evaluation and private annotations belong outside the public repository.

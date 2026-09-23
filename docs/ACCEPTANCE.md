# Acceptance and evidence

## Gate A — bootstrap only

Schemas parse, illustrative records validate, relative documentation links resolve, negative contract cases fail, no raw assets/secrets are committed, and CURRENT/handoff agree that the analyzer is not implemented. This gate establishes repository readiness only.

## Gate B — first native-frame baseline (BS-001)

Generate deterministic synthetic footage and ground-truth intervals before tuning. Keep generation code, not private footage, in git. Include 30/60 FPS, non-zero PTS origin and a VFR case. Run at multiple phase offsets, including events straddling aggregation/chunk boundaries.

Required easy fixtures: high-contrast overlays visible for 1, 3, and 5 frames, new text in the same panel, close/reopen identical content, persistent HUD over moving background, and a popup partially overlapping HUD. Each annotated easy occurrence must retain a candidate and an evidence frame inside the ground-truth interval. A single event covering the whole video is not a pass: enforce temporal localization and inspect candidate duration/distribution. Exact interval boundaries should be within one source-frame duration on these deterministic fixtures.

Challenge fixtures: small/low-contrast text, slow fade/scale, full-screen effects, camera motion, flashing numbers, and an immediate alt-tab-like scene transition. Publish missed events and false positives; challenge results are not assumed perfect. Re-extraction must match the selected source frame, not merely a nearby keyframe.

Safety/robustness: source SHA unchanged; no source/output collision or path escape; no-audio video; paths with spaces/Unicode; corrupt/unsupported input; cancellation; explicit incomplete state on decode failure; bounded memory/output queue and visible budget exhaustion. No provider call/model download in the first task.

## Gate C — text/UI enrichment

Benchmark detector and recognition separately. Measure event-level recall, usable-evidence recall, text recognition errors, duplicate occurrences, false candidates per minute, and HUD-only false events. Compare with a simple periodic sampler and the L0 baseline on the same held-out annotations. Do not select a model solely using its published image-inference timing.

Unknown OCR is retained as a reviewable candidate. Show results by event duration/size/contrast, not only an average. Recall denominator must list the reviewed source intervals; sparse sampling is not a valid missing-event ground truth. Manually frame-step the annotated short clips and perform an independent review where possible.

## Gate D — actual intended workflow

On a consented private real-video sample, verify popup recovery, full-res readability, repeat handling, silent gameplay overview, audio offset, seek accuracy, and preservation of source timestamps. Test Windows runtime separately from Linux CI. Obtain measured elapsed time, decoded/scanned counts, throughput (video seconds / wall seconds), peak RAM/VRAM, output bytes, and provider usage.

Drag/drop must use an in-place input path; large-file scanning cannot freeze the UI or upload raw video. Confirm Drive packet retrieval by a second reader using its actual image files and checksums. No agent can approve image readability by reading JSON alone.

## Reporting

Every result records exact git head, configuration/model versions, fixture generator seed, source/annotation digests, commands, hardware/runtime, completed/failed/skipped stages, and known misses. Engine throughput, coverage and recall are distinct. A 100% result on easy synthetic fixtures is not a universal 100% recall claim.

No production numeric recall or real-time speed target is declared achieved by this bootstrap. Release scope depends on measured Gates B-D and user acceptance.

# BS-001 Checkpoint B — regional candidates and retained evidence

Key: `BSCOUT-BS001-B-REGIONAL-CANDIDATES-20260930-V1`
CT: `BSCOUT-CT-20260930-B`.
Status: **ACTIVE / READY TO CLAIM**.
Lineage: Issue #2, `agent/bs-001-native-frame-baseline`, existing DRAFT PR #3 only.

## 1. Authority and prerequisite

Checkpoint A is accepted at exact head `25df7fb3c73ce0659ddc65f7426c4148cf5548dd` by independent receipt 5905383751 and CT disposition 5905427945.

Before claiming B, fresh-read AGENTS, CURRENT, CT ROLE/PROTOCOL, Issue #1/current comments, full V7 handoff, Issue #2/ALL comments, parent `docs/tasks/BS-001-native-frame-baseline.md`, this FULL packet, ARCHITECTURE, ACCEPTANCE, PACKET_SPEC, PRIVACY, ROADMAP and bootstrap-readiness audit. Fresh-check refs/PR/claims/exact heads.

Reuse A's frozen corpus, canonical source identity, native PTS/time-base semantics, ValidatedTraversal and exact evidence extraction. Do not regress or bypass accepted A.

## 2. Ownership and branch reconciliation

Exactly one B implementation worker claims Issue #2 before source writes. Reuse only `agent/bs-001-native-frame-baseline` and existing DRAFT PR #3. No replacement remote branch/PR.

If fresh main is ahead only by coordination documentation, integrate it into the implementation branch with a normal non-force `[skip ci]` merge. Preserve accepted implementation history. Never reset or force-push away A.

## 3. B1 — every-frame regional signals

Run an inexpensive L0 signal path on **every decoded presented frame** in presentation order.

Implement regional/tile classical-CV diagnostics sufficient to detect small localized visual changes. Whole-frame hashes/averages alone are not sufficient. At minimum preserve spatial mapping from analysis regions back to source pixels and retain raw signal values needed to audit why a frame/region became a candidate.

Use short-term change plus a longer/stable reference or an equivalently justified design so slow/local changes are not erased merely because consecutive frames are similar. Edge/structural change may supplement pixel deltas. Do not perform OCR, text recognition or semantic classification.

No silent downsampling may erase the one-frame truth fixtures. If an analysis scale is used, document exact mapping and demonstrate easy-event coverage.

## 4. B2 — candidate construction and occurrence semantics

Build localized regional candidate intervals from L0 signals using native A frame identities/timestamps.

Requirements:
- preserve one-frame candidates;
- no fixed minimum duration that deletes short evidence;
- no universal candidate/event-count cap;
- do not merge distinct contents merely because they occupy the same region;
- a same-region content replacement must be independently candidate-able;
- closing and reopening identical visual content is a new occurrence;
- persistent HUD is not a blanket exclusion;
- a popup overlapping HUD must remain detectable;
- candidate intervals use source-native timing/identity and remain temporally localized.

Thresholds/configuration must be explicit and versioned. Tune/select using dev fixtures only. Freeze the final B configuration before the final held-out evaluation; do not post-hoc retune on held-out failures.

## 5. B3 — retained representative evidence

For every candidate selected for evidence, retain an exact source-frame reference and representative regional/full-frame evidence sufficient for review.

Evidence extraction must use the accepted A source-bound exact-recovery path. Prove that the selected evidence identity/native digest matches the referenced source frame, not merely a nearby keyframe.

For every required easy annotated occurrence, at least one retained evidence frame must lie inside the ground-truth interval. Evidence/candidate localization for deterministic easy fixtures should be within one source-frame duration at boundaries.

Keep repeated occurrences separate even when their image bytes/content IDs deduplicate. No OCR text, invented labels or semantic interpretation.

## 6. B4 — bounded cache/spool and no silent drops

Do not retain unbounded full-resolution decoded history in RAM. Use bounded low-resolution state/rings and source references, plus bounded/disk-backed metadata or spool where required.

Under pressure, processing may slow or spill to disk. It must not silently skip presented frames. A configured budget exhaustion or decode failure must return explicit partial/failure diagnostics for the B run rather than a false complete result. C later owns production packet/cancellation/READY state.

Record peak RSS method, spool/cache bytes, candidate/evidence bytes and cleanup/lifecycle behavior. Preserve source SHA.

## 7. B5 — corpus evaluation

Evaluate **both dev and held-out seeds** using the frozen corpus truth. Final held-out evaluation uses the frozen B configuration.

Required easy cases include:
- high-contrast 1-frame overlay;
- 3-frame overlay;
- 5-frame overlay;
- new/different content in the same panel/region;
- close/reopen identical content;
- persistent HUD over moving background;
- popup partially overlapping HUD;
- required phase/boundary placements already present in corpus truth.

Every annotated easy occurrence must yield a localized candidate and an evidence frame inside its interval. A candidate that effectively spans the full clip/video does not satisfy this requirement.

Challenge cases include the corpus's small/low-contrast, slow fade/scale, full-screen effects, camera/motion, flashing-number and transition-style stressors. Challenge misses/noise are reported honestly; perfect challenge recall is not required unless later evidence justifies that threshold.

## 8. B6 — metrics and raw evaluation output

Publish per-fixture and aggregate metrics separated by dev vs held-out:
- easy occurrence recall;
- usable retained-evidence recall;
- misses with exact truth IDs/intervals;
- candidate count and candidates per video minute;
- candidate duration distribution, including one-frame candidates;
- candidate temporal overreach/localization;
- challenge misses and noisy/false candidates;
- evidence frame counts and identities;
- decoded/scanned presented-frame counts;
- elapsed time, peak RSS method, spool/cache/output bytes.

Do not represent B raw signal/evaluation diagnostics as the draft 0.1 event schema if that would clip raw signal magnitudes to [0,1], invent semantic fields or fabricate unknown timestamps. C owns explicit packet/schema evolution.

## 9. B7 — safety and regression proof

Preserve A source immutability and exact timing/identity behavior. Test paths with spaces/Unicode, no-audio behavior and relevant corrupt/unsupported/decode-failure paths touched by B.

Run A regression suites/proof sufficient to show B did not regress accepted temporal/extraction guarantees. Do not silently weaken A tests to make B pass.

Add focused B tests for one-frame survival through candidate grouping, same-region replacement, reopen occurrence, HUD overlap, whole-video-overreach rejection, boundary/phase behavior, held-out freeze discipline and bounded queue/spool behavior.

## 10. Durable completion evidence

Before releasing the B claim publish under `docs/evidence/BS-001-B/` (or a clearly versioned successor path):
- exact starting/base/tested/final heads and branch/PR;
- changed paths and configuration version;
- dev tuning procedure and frozen held-out configuration identity;
- per-fixture truth/candidate/evidence mapping;
- all misses/noise/candidate-rate/duration metrics;
- exact evidence identities/digests and extraction checks;
- pass/fail/skip counts and reasons;
- explicit untested list;
- elapsed/resource/spool/output measurements and method;
- source-immutability result;
- exact reproducible commands;
- exact-head GitHub Actions absence.

Keep historical A/R1/R2 evidence intact.

## 11. Hard exclusions

No Checkpoint C packet writer/READY/checksum semantics, schema migration, OCR/text detector/recognizer, ML/model download, Groq/provider calls, speech, Tauri/UI, Drive, MCP, editor automation, private/user footage, release or merge.

Do not add a universal event cap, fixed minimum duration, nominal-FPS timestamps, frame_index/FPS timing, semantic labels or network dependency.

## 12. Completion and review gate

Leave PR #3 DRAFT/unmerged. Post one complete B completion/handoff to Issue #2, RELEASE the B claim and STOP.

CT then dispatches one independent exact-head B reviewer. Reviewer top-level outcome must be exactly one of:
- `ACCEPT_CHECKPOINT_B`
- `NEEDS_FIX`
- `BLOCKED_EVIDENCE`

Checkpoint C remains HELD until CT records an accepted B disposition. No self-acceptance or auto-start of C.

END_OF_BSCOUT_B_PACKET key=BSCOUT-BS001-B-REGIONAL-CANDIDATES-20260930-V1 sections=12

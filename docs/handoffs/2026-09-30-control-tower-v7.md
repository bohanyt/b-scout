# B-Scout Control Tower handoff V7

Key: `BSCOUT-CT-HANDOFF-20260930-V7`
Date: 2026-09-30
State: **CHECKPOINT A ACCEPTED / CHECKPOINT B ACTIVE / READY TO CLAIM**.
This supersedes V6 as the active handoff.

## 1. Authority

CT: BSCOUT-CT-20260930-B, explicitly transferred by the user in Issue #1 comment 5902177064. CT owns continuity, evidence gates and sequencing. User retains product/privacy/cost/major-UX decisions plus implementation merge/release and final product acceptance.

## 2. Canonical read order

Read AGENTS, CURRENT, CT ROLE/PROTOCOL, Issue #1/current comments, this FULL V7 through its end marker, Issue #2/ALL comments, parent BS-001 packet, active B packet, linked ARCHITECTURE/ACCEPTANCE/PACKET_SPEC/PRIVACY/ROADMAP/bootstrap audit, then fresh refs/claims/PR/evidence.

## 3. Checkpoint A accepted baseline

Independent R2 reviewer receipt 5905383751 returned ACCEPT_CHECKPOINT_A against exact head 25df7fb3c73ce0659ddc65f7426c4148cf5548dd. CT recorded acceptance in 5905427945.

Reviewer independently reran 101 pass / 0 fail / 3 accepted skips, reproduced source-bound attack testing, and found both demonstrated occurrence-identity attacks resolved. Accepted A establishes frozen synthetic truth, independent frame identity, native timing/digest semantics, source-bound ValidatedTraversal authority, and exact seek recovery for the bounded A contract.

Acceptance is A only. It is not detector recall, full BS-001, Windows product support, merge/release authorization, or packet/READY acceptance.

## 4. Implementation lineage

Single remote implementation branch: `agent/bs-001-native-frame-baseline`. Existing DRAFT PR #3 only. Accepted A head: 25df7fb3c73ce0659ddc65f7426c4148cf5548dd. PR remains DRAFT/unmerged.

Do not create a competing branch/PR or reset accepted implementation to main. Coordination-only main commits may be integrated by normal non-force merge with `[skip ci]` when needed.

## 5. Checkpoint B objective

B implements every-presented-frame regional classical-CV signals and turns them into localized candidate intervals with retained exact evidence. It reuses A timing/identity/extraction and evaluates the frozen dev + held-out corpus.

B must preserve one-frame transients, same-region content replacement, close/reopen occurrences and popup/HUD overlap. Persistent HUD and moving gameplay are challenge/negative context, not blanket masks. Whole-screen-only change metrics are insufficient.

## 6. B evidence standard

For every required easy ground-truth occurrence, B must retain a localized candidate and at least one evidence frame inside the occurrence interval. A candidate spanning the whole video is failure evidence, not a pass. Deterministic easy boundaries should be within one source-frame duration.

Report all easy misses, challenge misses, false/noise candidates, candidate rate, candidate-duration distribution, evidence counts and resource use. Held-out evaluation must use a frozen/versioned configuration selected before the final held-out run.

Evidence re-extraction must resolve to A canonical source identity/native digest, not a nearby keyframe. Raw signal diagnostics remain raw; do not force them into draft packet schema ranges or fabricate unknown timestamps.

## 7. B boundedness and failure behavior

No silent frame dropping. Keep bounded RAM and bounded/disk-backed queues/spool as needed. If a configured budget or decode path cannot complete, surface explicit partial/failure evidence rather than silently omitting frames. C later owns production packet state/READY/cancellation contracts.

## 8. B exclusions

No OCR/text recognition, semantic/editorial labels, ML/model downloads, provider calls, Tauri/UI, Drive, MCP, production packet/READY writer, schema migration, B-to-C auto-activation, private/user footage, merge or release.

Checkpoint C remains HELD. BS-002 onward remains held.

## 9. Worker model and proof

One local Sol 6.1 High lead may own B; Fast and same-model/same-effort subagents are allowed with non-overlapping scopes. Post a fresh B claim in Issue #2 before source writes. Keep PR #3 DRAFT.

Run focused candidate/evidence tests and complete local regression proof without GitHub Actions. Use `[skip ci]`, verify exact pushed heads have zero runs, publish new B evidence, release claim and STOP for independent exact-head review.

## 10. Next gate

Independent B reviewer returns one top-level outcome: ACCEPT_CHECKPOINT_B, NEEDS_FIX, or BLOCKED_EVIDENCE. Only CT acceptance of B may activate C.

END_OF_BSCOUT_CT_HANDOFF key=BSCOUT-CT-HANDOFF-20260930-V7 sections=10

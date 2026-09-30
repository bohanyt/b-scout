# Current state

Updated: 2026-09-30. State: **BS-001 CHECKPOINT A ACCEPTED / CHECKPOINT B ACTIVE**.
Active evidence gate: **Checkpoint B — regional candidates and retained evidence — READY TO CLAIM**.

## Authority and accepted A baseline

- Active Control Tower: **BSCOUT-CT-20260930-B**, transferred by the user in Issue #1 comment 5902177064.
- Independent R2 acceptance review: Issue #2 comment 5905383751.
- CT A acceptance disposition: Issue #2 comment 5905427945.
- Accepted exact A implementation head: **25df7fb3c73ce0659ddc65f7426c4148cf5548dd** on `agent/bs-001-native-frame-baseline` / DRAFT PR #3.
- PR #3 remains open, DRAFT and unmerged. Acceptance does not authorize merge or release.
- A proof reproduced independently: **101 pass / 0 fail / 3 accepted skips**. Both demonstrated occurrence-identity attacks are resolved for the accepted Checkpoint-A contract.

Read AGENTS, this file, CT ROLE/PROTOCOL, Issue #1/current comments, full handoff V7, Issue #2/ALL comments, parent `docs/tasks/BS-001-native-frame-baseline.md`, active `docs/tasks/BS-001-B-regional-candidates.md`, and linked architecture/acceptance/packet/privacy/roadmap/audit docs. Fresh refs/claims/evidence override snapshots.

## Checkpoint B activation

Checkpoint B is now authorized on the SAME implementation lineage. Its job is inexpensive every-presented-frame regional-change signals, localized candidate intervals, same-region content-change/reopen evidence, bounded cache/spool behavior, and actual representative evidence on both dev and held-out synthetic truth.

Easy one-/three-/five-frame and other required easy occurrences must retain a temporally localized candidate and evidence frame inside the ground-truth interval. Whole-video candidates do not count. No fixed minimum duration or global event cap may silently remove one-frame evidence.

Use native A identities/timing/extraction. No OCR or invented semantic labels. B raw diagnostic/evaluation output is not forced into the draft 0.1 event schema when that would clip raw signals or fabricate unknown timing; C owns packet/schema evolution.

Dev data may be used for tuning. Freeze/version the B configuration before the final held-out evaluation and report held-out results without post-hoc threshold tuning.

## Lineage and ownership

- Existing implementation branch only: `agent/bs-001-native-frame-baseline`.
- Existing DRAFT PR #3 only; no replacement PR/branch.
- No active B worker claim at this publication.
- If main is ahead only by CT documentation, the B worker may integrate it by a normal non-force `[skip ci]` merge before source writes. Never reset the accepted implementation branch to main.
- One bounded B worker claims Issue #2 before source writes, implements B only, runs local proof, publishes durable evidence, releases the claim and stops for independent B review.

## Held work and limits

Checkpoint C remains **HELD** until B is independently reviewed and CT records the disposition. BS-002 OCR and later roadmap work remain held.

No GitHub Actions dispatch/rerun or workflow/settings workaround. Use local proof, applicable `[skip ci]`, and verify exact-head run absence. No user/private media, transcripts, credentials, machine-specific paths or private links in this public repository. No implementation merge or release without explicit user authorization.

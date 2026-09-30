# Current state

Updated: 2026-09-30. State: **CHECKPOINT A IMPLEMENTED / TESTED; NOT ACCEPTED**.
Active evidence gate: **BS-001 A R2 source-bound recovery correction — DESIGN SELECTED / READY TO CLAIM**.

## Authority and read order

Active Control Tower: **BSCOUT-CT-20260930-B**, user-authorized transfer in [Issue #1 comment 5902177064](https://github.com/bohanyt/b-scout/issues/1#issuecomment-5902177064). User retains product/privacy/cost/major-UX and implementation-merge/release authority.

Read AGENTS, this file, [CT role](docs/control-tower/ROLE.md), [protocol](docs/control-tower/PROTOCOL.md), Issue #1 with current comments, full [handoff V6](docs/handoffs/2026-09-30-control-tower-v6.md), Issue #2 with all comments, the [parent A/B/C packet](docs/tasks/BS-001-native-frame-baseline.md), and the [active R2 correction packet](docs/tasks/BS-001-A-R2-source-bound-recovery.md). Then fresh-check refs, claims and evidence.

V5 and older preimplementation/ready-to-redispatch paragraphs are historical snapshots. This state and the R2 packet supersede their dispatch/ownership status, not the parent acceptance requirements.

## Implemented and tested, not yet accepted

The implementation exists on **agent/bs-001-native-frame-baseline / DRAFT PR #3**, not on main. Current implementation head at reconciliation: **ce4ef9c4fa574fd34f95154b7a555eb4bc80f332**. PR #3 is open, draft and unmerged. Main before this documentation publication was e35e3e6a6990a96e7c3efd2c0a23da24a5630c2b. Publication SHA belongs in Issue #1, not self-referentially here.

A's synthetic corpus, frame-ID oracle, native-time ledger, native-plane digests, survival/lossless proof and seek harness are implemented. Windows/Python 3.11.9 synthetic proof was independently reproduced: **70 pass / 0 fail / 3 accepted skips**, 3,360 ID-mapped frames, 2,880 supported fixed-corpus seek recoveries and 480 lossless frames. These are scoped test/runtime observations, NOT acceptance of the recovery contract, detector recall, or Windows product support.

Latest independent verdict: **NEEDS_FIX**, [Issue #2 comment 5903733062](https://github.com/bohanyt/b-scout/issues/2#issuecomment-5903733062). A self-consistent shortened/reindexed ledger with the correct source SHA can still make API/CLI report the wrong duplicate-PTS occurrence. Internal ledger consistency is not proof of the complete source traversal.

## Selected correction and ownership

R2 selects one core-generated, source/configuration-bound **ValidatedTraversal**, built by a full sequential decode to EOF/flush. Caller JSON is a cross-check only. Real seek-back/decode-forward remains required and is checked against that trusted traversal. Validate once and reuse within the process; no authenticated persisted cache/key management in A.

Read the complete [R2 packet](docs/tasks/BS-001-A-R2-source-bound-recovery.md) before work. This is a selected design, not an implemented fix or an acceptance verdict.

Implementation claim 5902356966 and correction claim 5903287424 are released. Old claim 5806413667 remains superseded. **No R2 worker is running or claimed at this publication.** One local Sol 6.1 High lead may claim R2; Fast and same-model/same-effort subagents are allowed. One writer per file/scope; one remote branch and existing DRAFT PR #3 only.

Do not reset the implementation branch to main or repeat the original blank-branch redispatch. Fetch/read fresh main authority; a normal non-force merge of coordination-only main into the implementation branch is allowed if needed, with [skip ci] and preserved implementation history. No implementation merge into main is authorized.

## Next evidence gate and held work

One R2 correction worker: implement the packet, reproduce both identity attacks through real core validation, run clean-checkout proof, preserve historical evidence, publish exact heads/results, release claim, STOP. Then one independent exact-head rereviewer; only CT disposition of accepted evidence may activate B.

**B/C and BS-002 onward remain HELD.** No detector/packet/READY/OCR/provider/UI/Drive/MCP work. No user/private media, transcripts, paths, links or credentials in this public repo. No Actions dispatch/rerun or workflow/settings workaround. Use local proof, applicable [skip ci], and verify exact-head run absence. Skipped CI is not green CI. No merge/release without explicit user authorization.

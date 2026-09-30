# B-Scout Control Tower handoff V6

Key: `BSCOUT-CT-HANDOFF-20260930-V6`
Date: 2026-09-30
State: **A IMPLEMENTED / TESTED / NEEDS_FIX; R2 DESIGN SELECTED / READY TO CLAIM**.
This supersedes V5 as the active handoff. [CURRENT](../../CURRENT.md) remains canonical concise state.

## 1. Authority

CT: BSCOUT-CT-20260930-B, explicitly transferred by the user in Issue #1 comment 5902177064. CT owns continuity, evidence gates and sequencing across the whole roadmap, not default implementation. User retains product/privacy/cost/major-UX and implementation merge/release authority. A handoff alone does not transfer CT authority.

## 2. Read order

Read AGENTS, CURRENT, CT ROLE/PROTOCOL, Issue #1 and current comments, this FULL handoff through its end marker, Issue #2 and all comments, parent BS-001 packet, active [R2 packet](../tasks/BS-001-A-R2-source-bound-recovery.md), linked ARCHITECTURE/ACCEPTANCE/PACKET_SPEC/PRIVACY/ROADMAP/audit docs, then fresh refs/claims/PRs/exact-head evidence. Read files from fresh main for authority and pinned implementation heads for code. Fresh evidence overrides snapshots.

## 3. Product and roadmap boundaries

Local-first, read-only source processing; high-recall transient events including one frame; native timestamps; occurrence history independent of asset dedupe; observations separate from OCR/editorial meaning; Python engine/CLI before thin desktop UX. BS-001 A is the current gate. B regional signals/evidence and C production packet/full Gate B remain held. BS-002 OCR, BS-003 optional speech, BS-004 desktop, BS-005 delivery, BS-006 AI/MCP remain planned. CT responsibility continues beyond BS-001.

## 4. Actual implementation lineage

Exactly one remote implementation branch: agent/bs-001-native-frame-baseline. Exactly one DRAFT PR #3, open and unmerged. Head at reconciliation: ce4ef9c4fa574fd34f95154b7a555eb4bc80f332. Main before this docs-only V6 publication: e35e3e6a6990a96e7c3efd2c0a23da24a5630c2b. Publication hash is recorded in Issue #1.

Do not delete/replace/reset this branch or create a competing PR. The original initial-fast-forward instruction applied before implementation existed; it is not permission to reset the now-implemented branch. Incorporating coordination-only main via a normal non-force merge is allowed when needed; use [skip ci] and test the final integrated implementation head. No implementation merge into main.

## 5. Evidence history

All IDs below are Issue #2 comments unless stated otherwise:

- 5806205721: independent pre-build Opus review; no architecture blocker; A-only oracle/timing/seek requirements.
- 5806347830: CT incorporation; stronger parent packet remains binding.
- 5902132762: stale claim 5806413667 superseded.
- 5902356966 / 5902662946: first implementation claim/completion; claim released; final fc42cdfd9364927d98020a817436fce6ba8ce21b; 62/0/3 proof.
- 5902689680 / 5902916741: review dispatch / NEEDS_FIX; local post-seek duplicate counter can mislabel a later occurrence.
- 5902991245: CT R1 correction dispatch; fail-closed design allowed.
- 5903287424 / 5903455800: R1 claim/completion; released; tested 6371454745af601f60cf841998b67647dbc0848b; final ce4ef9c4fa574fd34f95154b7a555eb4bc80f332; 70/0/3 proof.
- 5903471324 / 5903733062: rereview dispatch / NEEDS_FIX; shortened self-consistent ledger still bypasses the source-wide identity requirement.

The last review independently reproduced 70 passing stock checks, three acceptable skips, 3,360 frame-ID mappings, 2,880 fixed-corpus recoveries and 480 lossless frames. The new identity attack is outside that stock suite. Passing stock tests do not close it.

## 6. Current blocker and consultation

Actual source PTS [0,100,20,50,100]; malicious/incomplete ledger [0,20,50,100] relabels the later identical-pixel 100 as occurrence zero. Correct source SHA plus a consistent trailer cannot prove all source frames were listed. API and CLI false success are reproduced in 5903733062.

The owner supplied a read-only Opus recovery-model consultation. It recommends a full core decode, in-process ValidatedTraversal, source/config binding and caller-ledger cross-check only. It is not a checkpoint acceptance or new runtime proof. Some pasted passages are truncated; the consultant disclosed partial reading of older comments. The R2 packet records CT's complete operational interpretation separately; missing prose is not treated as reviewed authority.

## 7. R2 design selected, not implemented

Implement the [complete R2 packet](../tasks/BS-001-A-R2-source-bound-recovery.md): shared immutable decoder config; core-owned bounded traversal table from actual EOF/flush decode; full semantic comparison of imported ledger; recovery target/anchor/time-base/digest from traversal, not caller fields; seek-path alignment and source pre/post checks; accurate failure/no-output behavior; both original and shortened-ledger regressions. Reuse one traversal per fixture. Keep source JSON and any cross-process cache untrusted. No MAC/key management or production cache in A.

T1 stays frozen; T2 equality is checked for identical encoded bytes. Encoded media should remain equal under unchanged pins/settings. Ledger/report hashes and new proof metadata may change; do not force all T3 bytes to match. Hash checkpoints do not prove immunity to adversarial concurrent writes; document the stable local-source/trusted-process assumption.

## 8. Ownership and immediate dispatch

No active implementation claim at publication. R1 claims are released; R2 is READY TO CLAIM, not RUNNING. One local Sol 6.1 High lead may implement the whole R2 correction. Fast is allowed. Subagents are allowed only with the same model/effort; avoid overlapping writers. Internal subreviews do not replace final independent acceptance.

A worker posts a bounded Issue #2 claim before source writes, reuses PR #3, runs local proof, publishes new docs/evidence/BS-001-A-R2 evidence, releases claim and stops. CT then dispatches an independent exact-head rereviewer. B remains held until CT records the accepted verdict; merge/release remains user-authorized.

## 9. Limits and durable continuity

No GitHub Actions dispatch/rerun or workflow/settings workaround. Local proof only, applicable [skip ci], exact-head run absence verified. No private/user footage, screenshots, transcripts, credentials, machine-specific paths or private links in public GitHub. Preserve prior evidence; temporary media is disposable only when reproducible. No provider/model/UI/Drive/MCP expansion. Unknown timing remains diagnostic, not fabricated. The two no-PTS raw-H264 recovery skips and environment-dependent symlink skip were accepted; do not invent broader platform/throughput support. F2 bootstrap historical sentinel remains deferred; validate V6's marker explicitly during CT publication.

## 10. Successor / worker entry prompts

Successor CT: receive explicit user transfer, then fresh-read the order above, record transfer in Issue #1 and reconcile whether R2 has advanced. Do not redispatch the original blank A task. Manage the smallest remaining source-bound recovery evidence gate, then continue the entire roadmap as accepted evidence permits. Do not merge/release without user authorization.

R2 worker: act as one local Sol 6.1 High bounded correction lead; Fast/same-model subagents allowed. Fresh-read CURRENT and docs/tasks/BS-001-A-R2-source-bound-recovery.md IN FULL through its end marker plus its read list. Claim Issue #2, reuse agent/bs-001-native-frame-baseline / DRAFT PR #3, implement source-bound traversal authority and all required regression proof, preserve truth/history, release claim and STOP before B.

END_OF_BSCOUT_CT_HANDOFF key=BSCOUT-CT-HANDOFF-20260930-V6 sections=10

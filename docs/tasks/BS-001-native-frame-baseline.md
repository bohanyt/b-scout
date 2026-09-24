# BS-001 — offline native-frame baseline

Issue: [#2](https://github.com/bohanyt/b-scout/issues/2). Implementation owner: **unassigned** at this publication. Current dispatch: **checkpoint A only, READY / UNCLAIMED**. A packet is not a launched worker.

## Objective and unchanged parent acceptance

Build the first offline Python engine/CLI slice from a local, read-only video to timestamped regional-change candidates and actual evidence in a validated portable packet. This proves temporal handling on synthetic fixtures, not general UI recognition or real-video recall. The full parent task still requires [Gate B](../ACCEPTANCE.md), [architecture](../ARCHITECTURE.md), and [packet semantics](../PACKET_SPEC.md).

The CT has divided delivery into review checkpoints **inside this same issue and lineage**. A/B/C are checkpoint labels, not new roadmap milestones or permission to create replacement issues/PRs. A worker must stop after its dispatched checkpoint. Completing A does not close BS-001.

## Read, claim, and lineage

Read AGENTS, CURRENT, CT ROLE/PROTOCOL, issue #1, the full current handoff selected by CURRENT, issue #2/comments, this packet, ARCHITECTURE, ACCEPTANCE, PACKET_SPEC, and the [readiness audit](../audits/2026-09-24-bootstrap-readiness.md). V1 is historical, not the active handoff.

Fresh-check main, task claims, branches and PRs. Claim **in issue #2** before source writes with worker identity, checkpoint, exact base, lineage, proof and exclusions. Suggested branch: `agent/bs-001-native-frame-baseline`, one DRAFT PR to main. Reuse any existing task lineage; corrections stay on it. Do not force-push, merge, release, or self-promote to CT.

No GitHub Actions dispatch/rerun. Use local/container tests and `[skip ci]` on applicable push/PR commits; inspect workflow triggers before publishing. No workflow/settings changes as a workaround. Skipped checks are not green CI.

## Checkpoint A — fixture oracle and native-time ledger (ACTIVE)

Smallest gate: prove that independently specified short events and source-frame identities survive fixture encoding/decoding, **before any detector can be tuned to them**.

Deliver:

1. Minimal Python package/CLI entry point with version/help and explicit fixture/probe/ledger commands. Do not advertise `analyze` as implemented if it is not. Use an existing reviewed decoder; pin exact runtime/toolchain versions and record provenance/licenses. No source/model copying without review.
2. Deterministic synthetic generator plus independent annotations: 30/60 FPS, VFR and non-zero PTS origin; known 1/3/5-frame overlays at multiple phase offsets, including one-second-boundary cases. Include persistent HUD/moving background, same-position content replacement, identical content reopening, and HUD overlap. Encode challenge variants or identify each still-missing challenge fixture; full Gate B cannot pass with silently omitted cases.
3. Sequential presentation-order decode ledger with selected stream, source identity, frame index, original integer PTS/rational time-base, dimensions and explicit errors/discontinuities/end uncertainty. Preserve the actual muxed/decoded time base; do not derive source time from nominal FPS or silently reset non-zero origin.
4. Validate encoded fixtures against the generator's independent frame/annotation schedule. Account for muxer time-base rescaling explicitly. Select oracle frames from the known 1/3/5-frame intervals and prove repeat extraction yields the same decoded pixels under the same declared conversion. This is **oracle-frame recovery**, not detection/evidence recall.
5. Tests for no-audio inputs, spaced/Unicode paths, unsupported/corrupt input, missing/invalid timing and source/output collision. Source SHA must be unchanged; generated media stays ignored. Stream/spool the ledger or prove bounded memory; record frame counts, elapsed time, output bytes and memory measurement method. Never report a detector scan count as complete when only decoding ran.

Annotation truth must not be inferred from detector output or from the decoder under test alone. Use an independent schedule and a separately explainable rescaling/pixel check. Do not invent final-frame duration or hide an unavailable measurement; record the limitation and reject unsupported completion claims.

**Stop after A:** publish exact head, proof commands, fixture/annotation digests and timing/extraction comparisons; leave PR DRAFT, release the implementation claim, and await CT exact-head review. No regional detector, tracking, production packet/READY writer, OCR, speech, UI or later roadmap work in this checkpoint. Standalone diagnostic metadata is not a production evidence packet.

## Checkpoint B — regional candidates and retained evidence (HELD)

Activate only after CT accepts A's evidence and explicitly dispatches B on the same lineage. Implement inexpensive regional-change signals, conservative `visual_change_candidate` intervals, same-region content-change/reopened occurrence handling, bounded cache and actual representative evidence inside each event. Preserve one-frame events and source time; do not use one-second summaries, blanket HUD masks or global caps as retention gates.

Evaluate against A's frozen annotations. Easy 1/3/5-frame occurrences must retain actual evidence inside ground truth, with temporal boundaries within one source-frame duration. A whole-video candidate is not localized success. Report challenge misses, noise/candidate rate, duration distribution and resource cost. No OCR or invented semantic labels.

## Checkpoint C — runtime packet integrity and full Gate B (HELD)

Activate only by CT dispatch after B review. Implement production packet writer/validator/evaluator, bounded event shards and visible partial/cancelled/failure states. Resolve any draft schema extension explicitly with provenance and compatibility tests. Cover readiness audit P1-P6/F3 with isolated real-temporary-asset regressions: actual bytes/digests, mandatory-stage status, frame/PTS ledger consistency, duplicate paths, invalid characters, symlink/path escapes, source/output aliasing, and honest unknown timing/input metadata.

Verify write-last READY semantics and checksum inventory, including missing/tampered assets and interrupted writes. No READY for a failed/incomplete requested scope. Test cancellation, decoder failure, queue/output budget exhaustion, no-audio and Unicode paths, repeatability and source SHA preservation. Measure elapsed time, decoded/scanned counts, output size and peak memory; publish all easy/challenge misses and localization/noise results. A schema-only pass cannot substitute for these checks.

Full BS-001 deliverables remain: usable local-video analysis CLI; deterministic corpus/evaluator; every-presented-frame source-time-preserving scan; regional candidates/occurrences; exact representative evidence; portable validated packet; complete safety and measurement report. All of Gate B remains required. Windows and private real-video acceptance are separate later evidence, not implied by Linux success.

## Exclusions for all BS-001 checkpoints

No paid/network/provider calls, credentials, model-weight downloads, OCR/text-model integration, semantic/editorial labels, Tauri UI, Drive upload, MCP, editor automation, user/proprietary footage in git, automatic source uploads, or auto-activation of BS-002. Reviewed toolchain/runtime dependencies may be installed for the dispatched scope with exact versions and provenance. No global event cap or minimum duration silently deleting evidence. No real-time or zero-miss promise.

## Exact-head review packet

The CT dispatches one read-only reviewer against the worker's recorded checkpoint/head. Fresh-check task authority and newer results; read the changed source plus the checkpoint's tests and acceptance. For A, independently inspect oracle independence, PTS/rescaling/non-zero-origin/VFR behavior, exact extraction, error accounting, source safety and bounded resources. Re-run the named proof where supported; label unsupported environments as untested.

Return `ACCEPT_CHECKPOINT_A`, `NEEDS_FIX`, or `BLOCKED_EVIDENCE`, with exact base/head, findings and concrete smallest corrections. Acceptance is only of A, not full Gate B, merge, Windows or production recall. Do not create a competing branch, modify source, become CT or start B. Corrections return to the same worker lineage. Equivalent checkpoint-specific review applies to B/C when dispatched; do not pre-approve later work.

## Ready-to-claim worker prompt

```text
Act as the ONE bounded BS-001 checkpoint A implementation worker for
bohanyt/b-scout, not Control Tower. Read AGENTS.md, CURRENT.md, CT ROLE and
PROTOCOL, issue #1, the FULL current handoff through its end marker, issue #2
and comments, and docs/tasks/BS-001-native-frame-baseline.md plus linked
acceptance/architecture/packet/audit documents. Fresh-check main, claims,
branches and PRs. Claim checkpoint A in issue #2 before source writes.
Implement ONLY the active A scope: synthetic truth fixtures, native PTS
ledger and exact oracle-frame recovery. Use/reuse the single BS-001 branch
and DRAFT PR. Do not implement B/C or later milestones. No Actions runs,
paid/provider calls, model downloads or private media. Record exact toolchain
provenance, head, commands, fixture digests, results, limits and next blocker.
Stop after A, publish the handoff, release the claim and leave the PR draft.
No merge/release authority; corrections stay on the same lineage.
```

## Completion record

Each checkpoint reports exact base/head, branch/PR, changed files, dependency provenance, environment, commands/results, fixture seeds/digests, failures/skips/untested behavior, performance/memory method and next smallest blocker. The CT decides the next checkpoint and maintains CURRENT/handoff; workers must not replace canonical state with optimistic completion. A pending execution channel does not count as an active owner.

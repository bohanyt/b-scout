# BS-001 — offline native-frame baseline

Issue: [#2](https://github.com/bohanyt/b-scout/issues/2). Owner: unassigned. Next implementation slice; do not start later roadmap work.

## Objective

Produce a reproducible first slice from local video to timestamped candidate/evidence packet. This proves temporal handling, not general UI recognition. Start with a synthetic ground-truth corpus, then build the baseline against it. No user footage is required.

## Read and claim

AGENTS, CURRENT, CT issue #1, bootstrap handoff, this packet, ARCHITECTURE, PACKET_SPEC, ACCEPTANCE. Fresh-check main and existing claims/PRs. Claim here before writes. Suggested branch `agent/bs-001-native-frame-baseline`, one DRAFT PR to main; reuse an existing branch/PR. No merge authority.

## Deliverables

- Minimal Python package and CLI with explicit version/help and a local-video analysis command. Source stays read-only. Use a reviewed existing decode library/build rather than writing a codec; record exact dependencies/licenses.
- Deterministic synthetic video/annotation generator with moving background, persistent HUD, 1/3/5-frame panels, same-position text replacements and reopened content. Include phase offsets/chunk boundaries, 30/60 FPS and VFR/non-zero-origin timing cases.
- Source probe and sequential presentation-frame loop with exact PTS/time-base, dimensions, frame accounting and gap/error reporting.
- Inexpensive region-change baseline and candidate interval tracking. Store conservative kinds, not invented tutorial/boss labels. No minimum-duration rule that discards brief candidates.
- Bounded metadata/cache and exact representative frame extraction; evidence must be from the event interval, not approximate seeking. Source references allow later context extraction.
- Packet writer/validator with safe paths, identity/checksum inventory, partial statuses, and completion marker semantics. Expand the draft schemas through an explicit reviewed change if needed.
- Evaluator/report for easy and challenge fixtures, plus reproducible tests and smoke commands. A full-video event is not a localized detection success.

## Acceptance

Meet Gate B in [../ACCEPTANCE.md](../ACCEPTANCE.md). Easy 1/3/5-frame occurrences must have actual retained evidence; record boundary error and all misses. Challenge cases and precision/noise are measured, not hidden. Test unsupported/corrupt media, no audio, source/output collisions, cancellation, safe paths and repeatability. Log elapsed time, frame counts, output bytes and peak memory. Do not claim Windows compatibility from Linux CI alone.

## Scope exclusions

No network/provider calls, API credentials, model-weight downloads, OCR/text-model integration, semantic labeling, Tauri UI, Drive upload, MCP or editor automation. System/toolchain dependencies may be installed for tests with their provenance recorded; paid APIs and model acquisition are not part of this dispatch.

## Completion

Update docs only for demonstrated facts. Return exact base/head and PR, file list, environment, test commands/results, fixture recall/misses/localization/noise report, limitations and next smallest blocker. Keep fixture media generated/ignored, not committed. Release the issue claim and leave the PR draft for independent review.

# Current state

Updated: 2026-09-30. State: **DESIGN_READY / IMPLEMENTATION_NOT_STARTED**.
Current evidence gate: **BS-001 checkpoint A — PREBUILD_REVIEWED / READY FOR REDISPATCH**.

## Canonical pointers and authority

- Primary Control Tower: **BSCOUT-CT-20260924-A**, explicitly authorized by the user; transfer record: issue #1 comment `5805761944`.
- User retains product, privacy/cost, major UX, implementation-merge/release, and final-acceptance authority.
- [CT role](docs/control-tower/ROLE.md), [protocol](docs/control-tower/PROTOCOL.md), and [coordination issue #1](https://github.com/bohanyt/b-scout/issues/1).
- Current handoff: [BSCOUT-CT-HANDOFF-20260930-V5](docs/handoffs/2026-09-30-control-tower-v5.md). Earlier handoffs are historical snapshots.
- Active task: [BS-001 / issue #2](https://github.com/bohanyt/b-scout/issues/2); [checkpoint dispatch/review packet](docs/tasks/BS-001-native-frame-baseline.md).
- Independent pre-build review: issue #2 comment `5806205721`, key `BSCOUT-PREBUILD-OPUS-20260924-V1`.
- CT incorporation of that review: issue #2 comment `5806347830`.

## Reconciled repository state

Fresh check on 2026-09-30:

- `main` = `1f9c53b3bf205d80628244bd7ce715535a99d5ef` before this V5 publication.
- Branch `agent/bs-001-native-frame-baseline` exists but points to the exact same commit as `main`.
- No pull requests exist.
- Checkpoint-A worker claim comment `5806413667` exists, but there is no implementation commit, no PR, no completion/handoff comment, and no exact-head runtime evidence after that claim.
- Therefore the claim is treated by CT as **stale/unfulfilled**, not as active implementation ownership.
- Keep/reuse the existing branch name for the next worker; do not create a competing lineage.

## What exists

Bootstrap/governance/product/architecture/privacy/acceptance/roadmap documentation, draft packet schemas, illustrative records, bootstrap checks, the bootstrap-readiness audit, and the pre-build-reviewed checkpoint-A task packet.

The pre-build review found no architecture blocker. A→B→C remains the approved engineering order. Checkpoint A has the stronger oracle/timing/seek/reproducibility requirements already incorporated in the task packet.

## What does not exist

No implementation of the runtime synthetic corpus, decoder/ledger engine, oracle verifier, regional detector, packet runtime, OCR/Groq adapter, desktop UI, Drive exporter, MCP server, or validated real-video recall/speed.

No BS-001 checkpoint has passed runtime review.

## Next action

Redispatch **one** checkpoint-A implementation worker using the existing branch `agent/bs-001-native-frame-baseline` and one DRAFT PR.

The worker must fresh-read issue #2, V5, and the task packet; post a new claim that explicitly supersedes stale claim `5806413667`; implement A only; run proof in its own temporary compute environment; persist reproducible source/tests/specs/annotations/pins/commands/results to GitHub; leave the PR DRAFT; then release the claim.

Checkpoint B and C remain held until CT exact-head review accepts A.

## Operating limits

GitHub is the durable bus between one-shot GPT/Claude agents. Do not rely on chat cache or persistent worker filesystem state.

No user/private media, transcripts, machine-specific private paths, or private project links in this public repository.

No GitHub Actions dispatch/rerun for current work. Use local/cloud proof, applicable `[skip ci]` commits, and verify no workflow run started. Skipped CI is not green CI.

No paid/provider calls, model downloads, OCR/Groq/Tauri/Drive/MCP scope in checkpoint A. No implementation merge or release without explicit user authorization.

Normal engineering choices belong to bounded evidence review. Product/privacy/cost/release/major UX changes go to the user.

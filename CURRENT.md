# Current state

Updated: 2026-09-24. State: **DESIGN_READY / IMPLEMENTATION_NOT_STARTED**.
Current evidence gate: **BS-001 checkpoint A — READY / UNCLAIMED**.

## Canonical pointers and authority

- Primary Control Tower: **BSCOUT-CT-20260924-A**, explicitly authorized by the user; [transfer record](https://github.com/bohanyt/b-scout/issues/1#issuecomment-5805761944).
- User retains product, privacy/cost, major UX, implementation-merge/release, and final-acceptance authority.
- [CT role](docs/control-tower/ROLE.md), [protocol](docs/control-tower/PROTOCOL.md), and [coordination issue #1](https://github.com/bohanyt/b-scout/issues/1).
- Current handoff: [BSCOUT-CT-HANDOFF-20260924-V3](docs/handoffs/2026-09-24-control-tower-v3.md). V1/V2 are historical snapshots.
- Active task: [BS-001 / issue #2](https://github.com/bohanyt/b-scout/issues/2); [checkpoint dispatch and review packet](docs/tasks/BS-001-native-frame-baseline.md).
- [Pinned bootstrap-readiness audit](docs/audits/2026-09-24-bootstrap-readiness.md). Publication heads belong in issue #1, not self-referentially here.

## What exists and what was tested

Product/architecture/privacy/acceptance/roadmap documentation, draft packet schemas and illustrative records, bootstrap checks, governance, and bounded task packets exist. The CT reran **13 bootstrap unit tests successfully** using six Git-blob-verified files from the audited main revision in Linux / Python 3.13.5 / jsonschema 4.26.0. Two schema definitions and their two examples also validated.

Six additional readiness probes exposed limits of the intentionally bootstrap-only validator and schema. These are requirements for the later runtime validator, not proof of a working or broken scanner. The audit records reproduction steps, exact inputs, and limitations. The full bootstrap documentation-link/entry-point command and Windows/Python 3.11 were not run in that audit.

## What does not exist

No video scanner, detector, OCR/Groq adapter, synthetic-video runtime corpus, desktop UI, Drive exporter, MCP server, or validated real-video recall/speed. Example JSON is authored documentation, not analysis output. No runtime checkpoint of BS-001 has passed.

## Ownership and next action

Implementation owner: **none**. Implementation branch / PR: **none** at this snapshot. No external worker was launched: the CT session had repository coordination and a local test container, but no successfully discovered worker-launch channel. A published dispatch is not a running worker or claim. Fresh-check issue #2 and PRs before claiming.

**Activate only checkpoint A within issue #2:** deterministic synthetic truth fixtures, reviewed decoder dependency/provenance, native presentation-frame PTS ledger, and exact oracle-frame re-extraction. Stop for CT review at an exact head. Suggested lineage remains `agent/bs-001-native-frame-baseline` and one DRAFT PR; create it only after a real worker claims.

Checkpoint B (regional-change candidates/evidence) and checkpoint C (runtime packet integrity/full Gate B evaluation) remain held until explicitly dispatched by the CT. They continue on the same BS-001 lineage. Checkpoint A is not detection recall or full BS-001 acceptance. After accepted evidence the CT may advance ordinary engineering without asking the user again; implementation merge and release still need explicit authorization.

## Direction and operating limits

Independent public, local-first footage scout; generic footage with sparse-speech gameplay as the first demanding use case. Preserve one-frame evidence and source timestamps. Python engine/CLI first; thin Tauri drag/drop desktop remains the intended destination. Groq, private Drive delivery, and MCP are later bounded gates, not additions to BS-001.

No user/private media, transcripts, machine-specific paths, or private project links in this repository. No paid/provider calls, model downloads, automatic uploads, or GitHub Actions dispatch/rerun for the current work. Use local proof; include `[skip ci]` on applicable push/PR commits and verify no workflow run was started. Skipped CI is not passing CI. Do not change workflow settings as a workaround.

Decoder choice, region scales/thresholds, OCR runtime/models, resource budgets, Windows packaging, and numerical recall/speed targets remain evidence-dependent. Normal implementation details belong to bounded engineering review; product/privacy/cost/release/major UX changes go to the user.

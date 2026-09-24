# Current state

Updated: 2026-09-24. State: **DESIGN_READY / IMPLEMENTATION_NOT_STARTED**.

## Canonical pointers

- Primary Control Tower: originating B-Scout design conversation; user retains product/release authority.
- Control Tower role: [docs/control-tower/ROLE.md](docs/control-tower/ROLE.md).
- Coordination: [issue #1](https://github.com/bohanyt/b-scout/issues/1).
- Next bounded task: [BS-001 / issue #2](https://github.com/bohanyt/b-scout/issues/2).
- Current CT handoff: [BSCOUT-CT-HANDOFF-20260924-V2](docs/handoffs/2026-09-24-control-tower-v2.md).
- Bootstrap handoff V1 remains historical context only.
- Active implementation owner: **none**. Implementation branch / PR: **none**.

## What exists

Root onboarding and governance, product/UX direction, multi-rate architecture, packet specification and draft schemas, illustrative records, bootstrap validation tests, a durable Control Tower/project-manager role, and a detailed BS-001 dispatch. Exact publication head and test evidence belong in issue #1; do not embed a self-referential HEAD here.

## What does not exist

No scanner, text/UI detector, OCR adapter, Groq adapter, synthetic video benchmark, desktop UI, Drive exporter, MCP server, or validated real-video recall/speed results. Example JSON is authored documentation, not analysis output.

## Agreed direction

Independent public project named B-Scout; local in-place video processing; generic footage with sparse-speech gameplay as the first test; event evidence for humans and AI; optional Groq speech transcription; eventual drag-and-drop desktop experience; portable packet export for Drive or local agents.

## Current engineering choices

Python engine/CLI first, thin Tauri desktop shell later. These are the selected bootstrap design, not a claim of packaged support. Text detector/model, inference runtime, thresholds, final frame sizes/rates, and decoder integration must be benchmarked. No numerical speed or recall target has passed.

## Control Tower operating state

The replacement Control Tower, once explicitly authorized by the user, is expected to continue B-Scout as the project's technical PM across milestones: reconcile current evidence, choose the next bounded gate, create/split/defer task issues, dispatch/review workers, manage correction loops, update canonical state, and advance the roadmap. BS-001 is only the current gate, not the limit of the CT role. See [ROLE.md](docs/control-tower/ROLE.md) and the current V2 handoff.

## Next action

The CT should dispatch or review one BS-001 worker: synthetic truth set + source-time-preserving decode + inexpensive region-change baseline + packet writer/evaluator. No UI, Groq, OCR model, cloud upload, or MCP in that task. See [dispatch](docs/tasks/BS-001-native-frame-baseline.md).

After BS-001 is accepted, the CT decides whether BS-002 is ready or whether a correction/research gate is required first. Workers do not auto-advance the roadmap.

## Known risks

Tiny or low-contrast UI can evade cheap gates; animated HUD creates noise; averaging/scene boundaries can erase short events; inaccurate seek/PTS handling mislabels frames; packets may expose private data; a JSON file alone does not let an agent see images that are inaccessible. See the architecture, acceptance, and privacy documents before changing any of these boundaries.

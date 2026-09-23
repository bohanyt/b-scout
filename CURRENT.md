# Current state

Updated: 2026-09-24. State: **DESIGN_READY / IMPLEMENTATION_NOT_STARTED**.

## Canonical pointers

- Primary Control Tower: originating B-Scout design conversation; user retains release authority.
- Coordination: [issue #1](https://github.com/bohanyt/b-scout/issues/1).
- Next bounded task: [BS-001 / issue #2](https://github.com/bohanyt/b-scout/issues/2).
- Handoff: [BSCOUT-CT-HANDOFF-20260924-V1](docs/handoffs/2026-09-24-bootstrap.md).
- Active implementation owner: **none**. Implementation branch / PR: **none**.

## What exists

Root onboarding and governance, product/UX direction, multi-rate architecture, packet specification and draft schemas, illustrative records, bootstrap validation tests, and a detailed BS-001 dispatch. Exact publication head and test evidence belong in issue #1; do not embed a self-referential HEAD here.

## What does not exist

No scanner, text/UI detector, OCR adapter, Groq adapter, synthetic video benchmark, desktop UI, Drive exporter, MCP server, or validated real-video recall/speed results. Example JSON is authored documentation, not analysis output.

## Agreed direction

Independent public project named B-Scout; local in-place video processing; generic footage with sparse-speech gameplay as the first test; event evidence for humans and AI; optional Groq speech transcription; eventual drag-and-drop desktop experience; portable packet export for Drive or local agents.

## Current engineering choices

Python engine/CLI first, thin Tauri desktop shell later. These are the selected bootstrap design, not a claim of packaged support. Text detector/model, inference runtime, thresholds, final frame sizes/rates, and decoder integration must be benchmarked. No numerical speed or recall target has passed.

## Next action

One worker implements BS-001: synthetic truth set + source-time-preserving decode + inexpensive region-change baseline + packet writer/evaluator. No UI, Groq, OCR model, cloud upload, or MCP in that task. See [dispatch](docs/tasks/BS-001-native-frame-baseline.md).

## Known risks

Tiny or low-contrast UI can evade cheap gates; animated HUD creates noise; averaging/scene boundaries can erase short events; inaccurate seek/PTS handling mislabels frames; packets may expose private data; a JSON file alone does not let an agent see images that are inaccessible. See the architecture, acceptance, and privacy documents before changing any of these boundaries.

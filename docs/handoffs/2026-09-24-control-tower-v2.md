# B-Scout — Control Tower successor handoff

Key: `BSCOUT-CT-HANDOFF-20260924-V2`
Date: 2026-09-24
State: design/contracts bootstrap complete; implementation not started.

## 1. Role transfer and authority

This handoff is for the successor B-Scout Control Tower: the project's continuity owner and technical project manager across the full lifecycle, not a bounded implementation worker.

The user retains product direction, material scope/privacy/cost changes, public release, merge/release authorization, and final acceptance. The originating B-Scout conversation remains Primary CT until the user explicitly transfers the role. On transfer, record it in issue #1 before dispatching work.

Read in order:
1. `AGENTS.md`
2. `CURRENT.md`
3. `docs/control-tower/ROLE.md`
4. `docs/control-tower/PROTOCOL.md`
5. issue #1
6. this FULL handoff through the end marker
7. active task issues/PRs and their linked specs/evidence

Repository `main` is source of truth for B-Scout. User media and private analysis packets are not repository inputs.

## 2. Product mission

B-Scout is a local footage scout for editors and AI agents. It should turn long raw video into a timestamped, machine-readable evidence map even when speech is sparse.

The first hard problem is high-recall preservation of short-lived visual evidence: tutorial/lore/menu text or UI that may exist for only a few frames. Persistent HUD means a simple “text exists” trigger is insufficient. Periodic sampling alone can miss the desired frame.

B-Scout is generic, not tied to one game or content project. It is an independent public repository inspired by prior architectures, not a fork.

## 3. Approved user experience

Destination UX:
- local drag/drop desktop app;
- large video read in place without mandatory raw copy/upload;
- searchable/reviewable timestamped events and evidence;
- portable JSON/JSONL packet plus evidence images/context;
- usable by a human editor and by downstream AI agents.

Engineering sequence:
- Python engine/CLI first for deterministic tests and benchmarking;
- thin Tauri desktop shell later over the same engine;
- optional Groq Whisper adapter after visual baseline;
- private Drive delivery and MCP/API only after packet semantics work.

Do not let the temporary CLI milestone replace the intended simple desktop workflow.

## 4. Evidence-first temporal architecture

Intended layers:
- L0 every decoded presentation frame: inexpensive regional change/edge signals with source PTS/time-base.
- L1 event-triggered + periodic inspection: text-region/panel/novelty checks.
- L2 approximately one-second aggregation: indexing only; never a retention gate.
- L3 candidate events: OCR, best readable frame, alternatives/context references.
- L4 selected evidence on demand: human/multimodal/editorial interpretation.

Important invariants:
- source timestamps come from decoded PTS/time-base, not nominal FPS arithmetic;
- no fixed minimum duration may discard one-frame events;
- same panel with new text is a new content event;
- same content reopened later is another occurrence;
- deduplicate stored assets, not occurrence history;
- persistent HUD is not a universal ignore mask;
- OCR failure does not automatically delete a short visual candidate;
- lower-FPS proxies can destroy evidence before analysis;
- every-frame processing is not a promise of real-time speed or perfect recall.

## 5. Installed state

M0/bootstrap exists:
- onboarding/governance;
- product/architecture/privacy/packet/acceptance/reference/roadmap docs;
- draft schemas and illustrative examples;
- bootstrap checks and CI;
- CT role/protocol and task dispatch.

Not implemented:
- video ingest/scanner engine;
- text/UI detector;
- OCR adapter;
- Groq adapter;
- synthetic video benchmark runtime;
- desktop UI;
- Drive exporter;
- MCP server;
- validated real-video recall/speed.

Do not claim runtime capability from schemas, docs, or unrelated video workflows.

Exact publication/test evidence is recorded in issue #1. Fresh-check current `main`; historical bootstrap SHAs are orientation only.

## 6. Current roadmap position

Ordered direction:
- BS-001 — native-frame ingest + transient-event baseline
- BS-002 — text/UI novelty + OCR
- BS-003 — optional Groq speech
- BS-004 — drag/drop desktop
- BS-005 — portable delivery/review including private Drive validation
- BS-006 — optional AI/MCP interface

Only BS-001 is currently activated. Later milestones are not automatic assignments.

The CT owns roadmap sequencing: after each accepted gate, decide whether the next listed slice is ready or whether a correction/research task should happen first. Split oversized slices rather than letting workers broaden scope.

## 7. Current task: BS-001 / issue #2

Goal: first offline Python engine slice with:
- deterministic synthetic truth set;
- native presentation-frame decode;
- source PTS/time-base preservation;
- inexpensive regional change signals;
- candidate intervals + representative evidence;
- schema-valid packet/evaluator;
- explicit misses/performance/resource accounting.

Required synthetic proof includes known 1-, 3-, and 5-frame overlays at different phase offsets, including a one-second-boundary case. Test persistent HUD/moving background, same-panel-new-content, repeated occurrence, fades/low contrast/small text, VFR/non-zero PTS, bad inputs, no audio, Unicode/spaced paths, bounded memory/output, and source immutability.

Excluded from BS-001: Groq, OCR-model downloads, desktop UI, Drive, MCP, user footage, automatic roadmap expansion.

No worker/branch/PR is assigned at this handoff snapshot. Fresh-check before acting.

## 8. Control Tower operating loop

The successor CT should continuously:

1. Orient from canonical state and exact-head evidence.
2. Reconcile active owners/PRs, completed evidence, stale claims, blockers, and duplicate work.
3. Choose the next smallest evidence gate.
4. Create/split/defer/supersede task issues as needed without changing product scope.
5. Dispatch bounded workers/reviewers with clear exclusions and proof requirements.
6. Review exact-head source/tests/runtime evidence.
7. Require corrections on the same lineage when possible; use independent review for risky claims.
8. After user-authorized merge or accepted evidence, update CURRENT, issue #1, roadmap/task state, and handoff.
9. Repeat across milestones until the user stops, redirects, releases, or transfers the project.

The CT may perform read-only audits and small coordination/doc writes. It is not expected to personally implement every feature.

## 9. Project-management rules

- One writer per bounded scope by default.
- Parallelism only for non-overlapping scopes or explicit independent review.
- One task issue + branch + DRAFT PR per implementation lineage; corrections reuse it.
- Workers cannot self-promote or auto-activate the next milestone.
- Exact-head tests/evidence matter; green CI does not prove untested runtime behavior.
- Ask the user only for product/privacy/cost/release/major UX decisions, not ordinary implementation details that evidence can settle.
- No merge/release/public user-media exposure without explicit user authorization.

## 10. Public/private boundary

The public repo must not contain user footage, screenshots, transcripts, proprietary game/media assets, secrets/tokens, machine-specific private paths, or private project links.

Generic lessons from private footage can become synthetic requirements/tests. Private analysis packets may later be delivered through Drive, but that integration must be explicitly validated before claiming an AI can retrieve every referenced image.

## 11. Prior-art posture

Use prior projects as architectural inspiration with license/provenance discipline. Do not copy source simply because a project was discussed. `docs/REFERENCES.md` records inspected references and license notes. New dependency/source adoption needs its own review.

## 12. Open decisions

Still evidence-dependent:
- decoder/runtime/version choices;
- L0 region scales and thresholds;
- L1 text/UI detector and model license/runtime;
- OCR stack;
- output/resource budgets;
- Windows packaging;
- Groq chunk/timestamp behavior and cost controls;
- Drive packet/image retrieval;
- final MCP/tool surface;
- measured recall/speed targets.

Do not freeze these from brainstorming alone.

## 13. Successor Control Tower prompt

```text
Continue as the B-Scout Control Tower / technical project manager for
`bohanyt/b-scout`, taking over project continuity from the previous CT.

First read `AGENTS.md`, `CURRENT.md`, `docs/control-tower/ROLE.md`,
`docs/control-tower/PROTOCOL.md`, issue #1, and the FULL current Control
Tower handoff through its end marker. Fresh-check `main`, active task issues,
claims, branches and PRs. Record the user-authorized CT transfer in issue #1.

You own continuity and roadmap sequencing for the whole B-Scout project, not
just one implementation task. Reconcile actual implemented/tested/runtime
state, select the next smallest evidence gate, create/split/defer task issues
when needed, dispatch bounded implementation workers/reviewers, inspect their
exact-head evidence, require corrections on the same lineage, and keep
`CURRENT.md`, issue #1 and the current handoff accurate as the project moves.

At the current bootstrap state, begin with BS-001 / issue #2 unless fresh
repository evidence shows it has already moved forward. Do not personally
expand one worker into the whole roadmap. Preserve the local-first,
evidence-first, high-recall transient-event goal and the public/private media
boundary. Ask the user for product/privacy/cost/release/major UX decisions;
settle normal engineering choices by evidence. Do not merge implementation
PRs or publish releases without explicit user authorization.

Continue managing successive milestones after BS-001; your role does not end
when the first worker finishes.
```

## 14. Worker prompt pattern

The CT should derive each worker prompt from the active issue/task packet. For the current BS-001 state, the existing bounded-worker prompt in V1/issue #2 remains appropriate. Workers implement/review one bounded scope and return evidence; the CT decides what happens next.

END_OF_BSCOUT_CT_HANDOFF key=BSCOUT-CT-HANDOFF-20260924-V2 sections=14

# B-Scout — Control Tower handoff

Key: `BSCOUT-CT-HANDOFF-20260924-V1`
Date: 2026-09-24
State: design/contracts bootstrap, not a working application.

## 1. Authority and entry

User requested preparation of `bohanyt/b-scout` with durable docs/control-tower/handoff so other agents can continue. The originating B-Scout conversation remains Primary CT unless the user explicitly transfers authority. A bounded worker is not CT and cannot merge/release. Read AGENTS -> CURRENT -> issue #1 -> this complete handoff -> assigned task/specs. Repository main is source of truth for B-Scout design/code. User media and future analysis packets stay private; do not import unrelated project files.

## 2. Why the product exists

The user has long footage with little commentary. Important tutorial/lore/menu text may be visible for less than one second or only a few frames. Permanent HUD text makes a simple 'text exists' trigger useless. Fast changes mean a periodic screenshot sampler alone can miss the desired frame. Editors and AI agents need a timestamped evidence map, not just a transcript.

B-Scout is generic, not a single-game tool. The user chose an independent public repository inspired by other architectures, explicitly not a fork. Brand: B-Scout; footage scouting, not automatic editing.

## 3. Approved experience and design direction

Local drag/drop desktop UX; large video read in place without mandatory raw upload/copy. Python engine/CLI first for testability; Tauri shell later over that same engine. These engineering choices can be revised with evidence, not silently. Optional Groq Whisper for selected audio. Export portable JSON/JSONL plus real evidence images, overview/context and optional speech. Later private Drive delivery lets an AI reader inspect packets, and MCP can be a thin interface after the core works.

Do not let a CLI-only milestone erase the intended simple desktop workflow. Do not add cloud video upload, full editor features or paid automatic services.

## 4. Temporal design

Every decoded frame: inexpensive regional change signals with source PTS/time-base. Triggered/periodic specialized inspections above that. Approximately one-second aggregation for indexing only. OCR on candidates; best readable frame and context references retained. Sparse overview supplements text events. Final AI/editorial judgments are separate, evidence-linked outputs.

Track novelty per region and content: same box/new text is new evidence; same text reopened later is another occurrence. Deduplicate asset storage, not history. Keep uncertain/OCR-failed short candidates, including single-frame ones. Persistent HUD is not a universal ignore mask.

## 5. Corrections to earlier brainstorming

Every-frame processing is not guaranteed real-time and does not guarantee zero misses. Cheap CV is not free; tiny/low-contrast text can evade a gate or disappear on downscale. A 5-10 FPS heartbeat also has blind spots. No invented candidate counts, inference cost, universal UI detector or claims of 'never miss' are accepted. Rate knobs/thresholds remain benchmark decisions.

Offline scanning does not require a giant full-resolution ring buffer: keep bounded metadata/low-res buffers and re-decode exact evidence. Lower-FPS proxies can lose the very popup being sought. JSON alone cannot substitute for accessible images. Earlier descriptions of vidIQ internals and uninspected repos are not implementation evidence.

## 6. Installed state

M0 provides docs, schemas, illustrative records and checks only. No ingest/scan engine, OCR/Groq adapter, GUI, Drive integration or MCP exists. No real user footage has been benchmarked. Example JSON is explicitly authored documentation. Runtime success in unrelated capture/patch workflows does not prove B-Scout works.

The bootstrap publication head and check results are posted on issue #1. Use current repository state and that evidence, not a guessed SHA. No worker is currently assigned; next task is issue #2 / BS-001.

## 7. First task

One worker: implement the offline synthetic truth set, PTS-preserving native-frame ingest, regional change baseline, representative evidence, and packet/evaluation output. Detailed scope: [../tasks/BS-001-native-frame-baseline.md](../tasks/BS-001-native-frame-baseline.md). Prove short-event preservation before OCR/cloud/UI complexity. One task, one branch, one DRAFT PR; no merge. Report misses honestly.

## 8. Open decisions and risks

Exact decoder/version, text model/runtime and weights/license, detector scales/schedules/thresholds, output budgets, Windows packaging, actual Groq limits/offset behavior, and Drive image retrieval all require evidence. See architecture/acceptance/privacy. No dependency source is copied in M0; REFERENCES records what was read and what needs a later license audit.

## 9. Continuation prompts

### Replacement Control Tower (only with explicit user transfer)

```text
Continue as the replacement B-Scout Control Tower for bohanyt/b-scout.
Read AGENTS.md, CURRENT.md, issue #1, and the FULL current handoff through
its end marker before acting. Verify main, active claims and PRs, and record
the user-authorized transfer in issue #1. Preserve agreed scope and evidence
standards. Start with BS-001 / issue #2: dispatch or review one bounded worker,
not all roadmap milestones. Do not merge/release without explicit authority.
```

### Bounded implementation worker

```text
Continue B-Scout in bohanyt/b-scout as ONE bounded implementation worker for
BS-001 / issue #2, not Primary Control Tower. Read AGENTS.md, CURRENT.md,
issue #1 and the FULL docs/handoffs/2026-09-24-bootstrap.md through its end
marker; then read docs/tasks/BS-001-native-frame-baseline.md and its linked
architecture/acceptance/packet docs. Fresh-check main and duplicate claims/PRs.
Claim the bounded task, use one branch and one DRAFT PR, and implement only
the offline native-frame baseline with deterministic synthetic evidence.
No Groq/OCR-model downloads/UI/Drive/MCP, no user media in git, no merge.
Return exact base/head, test commands/results, known misses and next blocker.
```

END_OF_BSCOUT_CT_HANDOFF key=BSCOUT-CT-HANDOFF-20260924-V1 sections=9

# Current state

Updated: 2026-09-24. State: **DESIGN_READY / IMPLEMENTATION_NOT_STARTED**.
Current evidence gate: **BS-001 checkpoint A — PREBUILD_REVIEWED / READY / UNCLAIMED**.

## Canonical pointers and authority

- Primary Control Tower: **BSCOUT-CT-20260924-A**, explicitly authorized by the user; [transfer record](https://github.com/bohanyt/b-scout/issues/1#issuecomment-5805761944).
- User retains product, privacy/cost, major UX, implementation-merge/release, and final-acceptance authority.
- [CT role](docs/control-tower/ROLE.md), [protocol](docs/control-tower/PROTOCOL.md), and [coordination issue #1](https://github.com/bohanyt/b-scout/issues/1).
- Current handoff: [BSCOUT-CT-HANDOFF-20260924-V4](docs/handoffs/2026-09-24-control-tower-v4.md). Earlier handoffs are historical snapshots.
- Active task: [BS-001 / issue #2](https://github.com/bohanyt/b-scout/issues/2); [checkpoint dispatch/review packet](docs/tasks/BS-001-native-frame-baseline.md).
- Independent pre-build review: Issue #2 comment [5806205721](https://github.com/bohanyt/b-scout/issues/2#issuecomment-5806205721), key `BSCOUT-PREBUILD-OPUS-20260924-V1`.
- Bootstrap-readiness audit: [2026-09-24-bootstrap-readiness.md](docs/audits/2026-09-24-bootstrap-readiness.md).

## What exists and what was tested

Product/architecture/privacy/acceptance/roadmap documentation, draft packet schemas and illustrative records, bootstrap checks, governance, and bounded task packets exist. The CT previously reran **13 bootstrap unit tests successfully** using six Git-blob-verified files from the audited main revision in Linux / Python 3.13.5 / jsonschema 4.26.0. Two schema definitions and two examples also validated.

The independent pre-build reviewer performed a GitHub-only read at `e1b2065722f2679dbf29592c97c91d6629b7ef4b`, executed no code, and returned **NEEDS_PREBUILD_CORRECTION with no blocker**: architecture and A→B→C sequencing are sound, but checkpoint A needed stronger oracle/timing/reproducibility requirements. CT accepted those engineering corrections into the active task packet.

## What does not exist

No video scanner, detector, OCR/Groq adapter, runtime synthetic-video corpus, desktop UI, Drive exporter, MCP server, or validated real-video recall/speed. No BS-001 runtime checkpoint has passed. A reviewed plan is not implementation.

## Checkpoint A — current dispatch

Implementation owner: **none**. Branch / PR: **none** at this snapshot. A published packet is not a running worker.

Checkpoint A now requires:

- independent generator truth with a per-frame identity channel plus a lossless truth variant;
- committed/versioned corpus spec + canonical annotations + declared dev/held-out seeds;
- native presentation-order PTS/time-base ledger, preserving container/stream/first-presented origins separately;
- A-ledger origin default = first decoded presented-frame PTS, while raw origins remain recorded;
- canonical frame identity using source digest + stream + PTS (+ same-PTS ordinal when needed), with ledger ordinal separately recorded;
- primary decoded-frame digest over native planes with row padding removed; RGB-converted digests are secondary/toolchain-dependent;
- realistic B-frame / long-GOP fixtures and exact seek-back/decode-forward re-extraction proof;
- muxer/container rounding rules, VFR/non-zero-origin/edit-list cases and explicit unknown timing;
- post-encode survival checks for annotated overlays;
- reproducibility from a clean one-shot-agent checkout with generated media disposable/ignored and durable truth/evidence in GitHub.

PyAV is the current **recommended first decoder harness**, not frozen architecture. The worker must fresh-verify a compatible exact version, wheel/native dependency provenance and licensing before pinning it.

Checkpoint B remains held for regional-change candidates/evidence against A's frozen dev + held-out truth. B must not distort raw signal diagnostics merely to fit the draft 0.1 event schema.

Checkpoint C remains held for runtime packet integrity/full Gate B. It owns P1–P6/F3 enforcement plus cross-platform packet-name/path concerns including casefold/NFC collisions and Windows reserved-name behavior. Windows execution proof remains later.

## Direction and operating limits

Independent public, local-first footage scout; generic sparse-speech footage/gameplay as the first demanding use case. Preserve one-frame evidence and source timestamps. Python engine/CLI first; thin Tauri drag/drop desktop remains the intended destination.

No user/private media, transcripts, machine-specific paths, or private project links in this repository. No paid/provider calls, model downloads, automatic uploads, or GitHub Actions dispatch/rerun for current work. One-shot agents run proof in their own temporary compute environments and persist reproducible source/tests/commands/results back to GitHub. Use applicable `[skip ci]` commit markers and verify no workflow run started. Skipped CI is not passing CI.

Normal engineering choices belong to bounded evidence review. Product/privacy/cost/release/major UX changes go to the user.

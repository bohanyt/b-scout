# B-Scout

**Turn raw footage into timestamped evidence for editors and AI agents.**

B-Scout is a local-first footage indexing project. Its focus is visual context when speech is sparse: brief tutorial popups, on-screen text, menu changes, and other moments that ordinary frame sampling can miss. Gameplay is the first demanding use case, not the product boundary.

> **Status: design / contract bootstrap; first implementation gate pre-build-reviewed.** No working video analyzer, desktop installer, Groq integration, or MCP server is shipped yet. High recall is an evaluation goal, not a guarantee that nothing is missed.

## Intended experience

Drop a local video into a desktop window, choose an output folder, and scan without uploading or duplicating the raw source. Review an event timeline with evidence frames, text, and optional speech. Export a portable packet for an editor or AI agent.

## Start here

- [CURRENT.md](CURRENT.md): actual state and next task.
- [AGENTS.md](AGENTS.md): mandatory agent entry point.
- [Documentation index](docs/README.md): architecture, UX, packet format, and acceptance gates.
- [Control Tower](https://github.com/bohanyt/b-scout/issues/1): coordination and authority.
- [First implementation task](https://github.com/bohanyt/b-scout/issues/2): BS-001, checkpoint A.
- [Current handoff](docs/handoffs/2026-09-24-control-tower-v4.md): continuity snapshot.

## Available now

Design documents, draft JSON Schemas, illustrative records, bootstrap checks, a bootstrap-readiness audit and a pre-build-reviewed checkpoint-A implementation packet. The planned production `bscout analyze` command does not exist yet.

## Principles

Preserve source timing and short-lived evidence; deduplicate storage without erasing repeated occurrences; distinguish measured observations from OCR guesses and editorial judgments; keep raw footage private and unmodified. No transcript-only shortcut, hard frame cap, or one-second summary may silently discard candidate evidence.

Independent repository, not a fork. [References and reuse policy](docs/REFERENCES.md) identify architectural influences and what still needs inspection before code reuse. Original repository material is under [MIT](LICENSE); this does not license third-party software, model weights, or user media.

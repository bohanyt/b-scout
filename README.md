# B-Scout

**Turn raw footage into timestamped evidence for editors and AI agents.**

B-Scout is a local-first footage indexing project. Its focus is visual context when speech is sparse: brief tutorial popups, on-screen text, menu changes, and other moments that ordinary frame sampling can miss. Gameplay is the first demanding use case, not the product boundary.

> **Status: design / contract bootstrap.** No working video analyzer, desktop installer, Groq integration, or MCP server is shipped yet. High recall is an evaluation goal, not a guarantee that nothing is missed.

## Intended experience

Drop a local video into a desktop window, choose an output folder, and scan without uploading or duplicating the raw source. Review an event timeline with evidence frames, text, and optional speech. Export a portable packet for an editor or AI agent.

```text
Local video -> native-frame change signals -> candidate regions/events
                           |                         |
                           |                 text/UI checks + OCR
                           |                         |
Optional selected audio -> Groq transcription -> evidence packet
                                                     |
                                    local timeline / Drive / AI review
```

Visual processing is intended to run locally. **Enabling Groq sends selected audio to Groq.** Sharing a packet sends its selected screenshots/text to the chosen destination. Nothing should upload automatically.

## Start here

- [CURRENT.md](CURRENT.md): actual state and next task.
- [AGENTS.md](AGENTS.md): mandatory agent entry point.
- [Documentation index](docs/README.md): architecture, UX, packet format, and acceptance gates.
- [Control Tower](https://github.com/bohanyt/b-scout/issues/1): coordination and authority.
- [First implementation task](https://github.com/bohanyt/b-scout/issues/2): BS-001, offline native-frame baseline.
- [Full handoff](docs/handoffs/2026-09-24-control-tower-v3.md): current CT continuity packet.

## Available now

Design documents, draft JSON Schemas, clearly labeled illustrative records, and bootstrap checks. To check this repository with Python 3.11+:

```bash
python -m pip install -r requirements-dev.txt
python scripts/check_bootstrap.py
python -m unittest discover -s tests -v
```

These validate the documentation/contracts, **not** video detection. The planned `bscout analyze` command does not exist yet.

## Principles

Preserve source timing and short-lived evidence; deduplicate storage without erasing repeated occurrences; distinguish measured observations from OCR guesses and editorial judgments; keep raw footage private and unmodified. No transcript-only shortcut, hard frame cap, or one-second summary may silently discard candidate evidence.

Independent repository, not a fork. [References and reuse policy](docs/REFERENCES.md) identify architectural influences and what still needs inspection before code reuse. Original repository material is under [MIT](LICENSE); this does not license third-party software, model weights, or user media.

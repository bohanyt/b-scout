# B-Scout

**Turn raw footage into timestamped evidence for editors and AI agents.**

B-Scout is a local-first footage indexing project focused on short-lived visual context when speech is sparse.

> **Status:** design/contracts complete; BS-001 checkpoint A is pre-build-reviewed and ready for redispatch. No working analyzer is shipped yet.

## Start here

- [CURRENT.md](CURRENT.md): actual current state.
- [AGENTS.md](AGENTS.md): mandatory agent entry point.
- [Documentation index](docs/README.md).
- [Control Tower issue #1](https://github.com/bohanyt/b-scout/issues/1).
- [BS-001 issue #2](https://github.com/bohanyt/b-scout/issues/2).
- [Current CT handoff V5](docs/handoffs/2026-09-30-control-tower-v5.md).

## Principles

Preserve source timing and short-lived evidence; keep source media read-only; separate observations from OCR/editorial interpretation; preserve repeated occurrences; keep raw user media private.

Independent repository, not a fork. Repository material is MIT-licensed; third-party software/model/media licensing remains separate.

## Checkpoint A harness

The implementation branch provides a synthetic temporal oracle and native-frame ledger for independent review. See [Checkpoint A commands and proof](docs/BS001_A.md). This does not establish production detection or full BS-001 acceptance.

## Checkpoint B baseline

The implementation branch also provides every-frame native tile diagnostics and exact retained evidence. See [Checkpoint B commands and proof](docs/BS001_B.md). Independent review and Control Tower disposition govern acceptance; Checkpoint C remains held.

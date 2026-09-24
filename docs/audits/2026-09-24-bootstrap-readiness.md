# Bootstrap readiness audit — 2026-09-24

Key: `BSCOUT-BOOTSTRAP-AUDIT-20260924-A`
Role: read-only source/contract audit by **BSCOUT-CT-20260924-A**. This is not an independent implementation review or a scanner benchmark.

## Scope and provenance

Audited revision: `77e2eb0c83e2e34c7bc5c1d0fa0e60229fac1682` on `main`; root tree `1b775073bf4d6af8175f3dfcab20a0f0a63d8e15`. Repository state at orientation: only main, open issues #1/#2, no PR or worker claim. [CT transfer](https://github.com/bohanyt/b-scout/issues/1#issuecomment-5805761944) authorizes coordination, not implementation merge/release.

Git transport was unavailable in the test container. The CT retrieved source using the normal GitHub connector, reconstructed the following six files locally, and checked their Git blob SHA-1 values against the pinned tree. This is a verified subset, not a full clone or full-repository execution.

| Input file | Verified Git blob |
|---|---|
| `scripts/check_bootstrap.py` | `9067a2b15e76ee853090e534c72c34a562eebd97` |
| `tests/test_bootstrap.py` | `343f0230cd33bb041e980ef8806702a6cc1a76e7` |
| `schemas/manifest.schema.json` | `40e0834af296c7ab4e50838de99a214fa49ca29c` |
| `schemas/event.schema.json` | `997d11f12c2d316c21a60c3a5330c748236b7097` |
| `examples/manifest.example.json` | `af5d3218d760ac8cc7a0cad221fbbe0b7e72f262` |
| `examples/event.example.json` | `b5047f14ff3d8111ff652a45a884eb52bbc60ba0` |

Environment: Linux x86_64, Python 3.13.5, preinstalled jsonschema 4.26.0. No dependency installation, model download, provider call, media decode, or GitHub Actions execution was used for these tests. All mutated probe values were synthetic in-memory copies; original source files were unchanged.

## Executed results

`python -m unittest discover -s tests -v` — **13 tests passed** (reported elapsed 0.006 s). Separate temporary probe script: both Draft 2020-12 schema definitions passed `check_schema`; both examples passed schema validation.

The six probes below deliberately explore missing runtime checks. P1-P5 are accepted by the current bootstrap helper; this is **not** five failures in the 13-test suite. The helper explicitly states that full packet validation is future BS-001 work. These findings must not be represented as deployed-scanner vulnerabilities or a passing runtime gate.

| ID | Probe | Observed at audited revision | Required disposition before checkpoint C can pass |
|---|---|---|---|
| P1 | Complete-looking metadata references an absent image and an unverified digest | Both schemas and `validate_pair` accept it | Resolve actual assets; verify bytes, size, digest and inventory before READY |
| P2 | Same record marks the required visual stage `failed` | Accepted | Define requested/required stages; failed required work cannot claim complete |
| P3 | Event/best frame uses index 120 while decoded/scanned counts are zero | Accepted | Validate event and evidence identities against the actual decoded frame/PTS ledger |
| P4 | Two different artifact IDs use the same output path | Accepted | Reject conflicting/colliding canonical artifact paths; dedupe through shared references, not overwrite |
| P5 | Artifact path contains a NUL character | Accepted by the lexical helper/schema | Reject invalid path characters before filesystem access; also enforce resolved-path and symlink containment |
| P6 | Add top-level `engine_version` to the example manifest | Rejected by `additionalProperties: false` | Review and version an explicit provenance representation instead of slipping new fields past the schema |

P2-P5 reuse P1's metadata-only control to isolate which *additional* condition the helper ignores. They are not complete on-disk exploit demonstrations. Production tests must use genuine temporary packet assets and isolate each rejection reason.

## Reproducer for the six probes

Run at the audited revision, after installing the pinned development dependency in an appropriate environment. The following matches the tested mutations; it does not create the referenced image or execute footage-derived content.

```python
from copy import deepcopy
from pathlib import Path
import importlib.util
from jsonschema import Draft202012Validator, ValidationError

root = Path.cwd()
spec = importlib.util.spec_from_file_location("bootstrap", root / "scripts/check_bootstrap.py")
b = importlib.util.module_from_spec(spec)
spec.loader.exec_module(b)
m0 = b.load_json(root / "examples/manifest.example.json")
e0 = b.load_json(root / "examples/event.example.json")
validators = {}
for name in ("manifest", "event"):
    schema = b.load_json(root / f"schemas/{name}.schema.json")
    Draft202012Validator.check_schema(schema)
    validators[name] = Draft202012Validator(schema)
    validators[name].validate(b.load_json(root / f"examples/{name}.example.json"))

def check(m, e):
    validators["manifest"].validate(m)
    validators["event"].validate(e)
    b.validate_pair(m, e)

base, event = deepcopy(m0), deepcopy(e0)
base.update(example=False, status="complete")
base["source"]["sha256"] = "0" * 64
base["coverage"] = {"decoded_frames": 600, "scanned_frames": 600, "gaps": []}
base["stages"]["visual"] = "complete"
base["artifacts"] = [{"id": "synthetic-frame", "path": "frames/missing.png",
                      "mime": "image/png", "size_bytes": 123, "sha256": "0" * 64}]
event["best_frame"] = {"asset_id": "synthetic-frame", "frame_index": 120, "pts": 120000}
check(base, event)  # P1: accepted
m = deepcopy(base); m["stages"]["visual"] = "failed"
check(m, event)     # P2: accepted
m = deepcopy(base); m["coverage"].update(decoded_frames=0, scanned_frames=0)
check(m, event)     # P3: accepted
m = deepcopy(base); m["artifacts"].append(dict(m["artifacts"][0], id="other-id"))
check(m, event)     # P4: accepted
m = deepcopy(base); m["artifacts"][0]["path"] = "frames/invalid\x00.png"
check(m, event)     # P5: accepted
m = deepcopy(m0); m["engine_version"] = "audit-only"
try:
    validators["manifest"].validate(m)
except ValidationError:
    print("P6: rejected by current draft schema")
else:
    raise AssertionError("Unexpected P6 acceptance")
print("P1-P5 accepted by bootstrap; no runtime packet was validated")
```

## Additional source/documentation findings

**F1 — stale continuity entry points.** Root README, docs index, and BS-001 entry instructions still referred to bootstrap V1 while CURRENT selected V2. The CT publication accompanying this audit redirects active entry points to V3, preserving historical snapshots.

**F2 — current-handoff sentinel is not protected by the bootstrap command.** `scripts/check_bootstrap.py` hardcodes V1's path/end marker. This source behavior is unchanged by the docs-only publication. A later bounded source correction should validate the current handoff selected by CURRENT while retaining any intended historical checks; do not count a V1 marker pass as validation of V3. Until then CT publication checks must explicitly inspect the current marker and its section count.

**F3 — unresolved runtime representation.** PACKET_SPEC expects engine/config/stream provenance and explicit uncertainty/failure. The current manifest is deliberately narrow and requires positive dimensions/duration even when an input cannot be probed. Checkpoint A must report unknown values honestly in its diagnostic ledger, not fabricate a production packet. Checkpoint C must explicitly resolve this draft-interface gap, including last-frame end uncertainty, requested-stage completion and READY/checksum rules, with compatibility tests.

**F4 — test-environment distinction.** The existing workflow selects Python 3.11; the local run used Python 3.13.5. Neither a Python 3.11 run nor Windows compatibility is proved. The workflow triggers on push, pull_request and workflow_dispatch. Current CT work uses local proof and applicable skip-CI commit markers; a skipped workflow is not a successful workflow.

## Gate decision and follow-through

**Proceed to BS-001 checkpoint A only.** Establish a trustworthy synthetic oracle and native-time ledger before tuning a detector. Checkpoint B adds regional candidates/evidence after A review. Checkpoint C completes packet safety and full Gate B evaluation; P1-P6/F3 are explicit review items there. All checkpoints stay in issue #2 and the same implementation branch/DRAFT PR. No extra roadmap scope or competing implementation issue is created.

No runtime validator, detector, fixture-video generator, or sentinel source correction was implemented during this CT audit. Full `python scripts/check_bootstrap.py`, the entire original documentation-link tree, video timing/recall, source-video immutability, filesystem attack cases, resource limits, Windows, Python 3.11 and private real footage remain untested here. Exact publication and changed-Markdown checks are recorded separately in issue #1.

END_OF_BSCOUT_BOOTSTRAP_AUDIT key=BSCOUT-BOOTSTRAP-AUDIT-20260924-A

# BS-001 Checkpoint A — R2 source-bound recovery proof — 2026-09-30

Role: ONE bounded local correction implementation lead; not Control Tower or the final independent reviewer. Authority: [dispatch 5904253805](https://github.com/bohanyt/b-scout/issues/2#issuecomment-5904253805), [complete R2 packet](../../tasks/BS-001-A-R2-source-bound-recovery.md), [claim 5904417648](https://github.com/bohanyt/b-scout/issues/2#issuecomment-5904417648). Implementation evidence does not accept A. B/C remain HELD.

## Lineage and acquisition

- Fresh main/coordination publication: `c18f6ccb6f9ee07cc41c4b3e13455007147faf98`.
- Starting local/remote implementation head: `ce4ef9c4fa574fd34f95154b7a555eb4bc80f332`.
- Common earlier base: `e35e3e6a6990a96e7c3efd2c0a23da24a5630c2b`; initial topology was seven implementation commits versus one coordination commit.
- Authorized normal merge: `8afae0beab2baa5d84e6d69eddc09b0a41a6bdc2`, with both original parents preserved.
- Runtime correction: `688cfd92a83810bfa206c19642819ed3623e750e`.
- Clean tested head: **`45e36341e82d2e279445b04de03c1b74ce897a49`**, a documentation pointer correction on identical runtime source/tests.
- Existing branch `agent/bs-001-native-frame-baseline` / [DRAFT PR #3](https://github.com/bohanyt/b-scout/pull/3) only. Final publication head, exact-head Actions reads and claim release are bound in the Issue #2 completion receipt and PR description. Tested-to-final changes are confined to this evidence directory.

Fresh-read the full dispatch and twelve-section packet through their end markers, fresh main CURRENT/AGENTS/CT ROLE/PROTOCOL/V6, Issue #1 and current comments, Issue #2 and all current comments, parent acceptance packet, ARCHITECTURE/ACCEPTANCE/PACKET_SPEC/PRIVACY/ROADMAP/readiness audit and both recovery-identity findings. Claim preceded source writes. No competing R2 owner appeared before publication.

Compute: requested Sol 6.1 High; Fast allowed. Three bounded children were explicitly configured `gpt-6.1-sol` / `high`: test migration/matrix, proof resource harness, read-only internal source audit. Only the lead integrated/committed/published. Internal audit is not checkpoint acceptance.

The passing proof uses `git clone --no-hardlinks --branch agent/bs-001-native-frame-baseline . TEMP_CHECKOUT`, a new external work directory, new CPython venv, fresh no-cache exact PyPI wheels and entirely regenerated synthetic media twice. All media proof/tests use the new worker venv; previous runtime dependencies/media/wheels were not reused for those stages. The entrypoint launcher is existing CPython 3.11.9 using its standard library. An earlier attempt at `688cfd9` was stopped after a separate bootstrap check found its historical banner linked to a not-yet-published evidence page. `45e3634` fixes that link; the complete proof starts over in new directories. No partial attempt counts are presented as proof.

## Recovery authority and output boundary

`validate_traversal(source, DecodeConfig(), ledger_out=optional_path)` actually consumes the source to EOF/decoder flush. It owns source SHA/size checkpoints, timing classification and the fresh temporary SQLite traversal. Recoverable state requires known, unique, strictly increasing PTS and compatible time bases throughout the complete source, including after the target. Diagnostic rows retain missing/global duplicate/non-monotonic observations. Available native container counts corroborate; disagreement diagnoses, while zero/absent counts remain unavailable.

The immutable binding includes resolved stream, demux/edit-list options, software decoding, one SLICE thread, `err_detect=explode`, full toolchain fingerprint, ledger v2, projection v1 and native digest domain v1. Core-minted process-local handles are required. Caller dictionaries, headers, booleans, SQLite paths, old API arguments and closed/invalidated handles cannot grant state. Public metadata is copied; arbitrary hostile code already inside the same trusted Python process is outside this boundary.

`compare_ledger(vt, path)` compares every ordered record to actual core observations. All generated header/frame fields and semantic trailer facts are required; unknown extensions reject. Only trailer elapsed time, RSS, output-size telemetry and traversal table bytes may differ or be omitted. Projection SHA includes canonical header/frames/semantic trailer and never replaces full comparison. Legacy v1 files stay diagnostic-readable but explicitly reject for recovery cross-check without v2 bindings.

`recover(source, vt, identity)` resolves position, digest, time base and anchor from VT. Real backward seek/decode-forward must align its first frame at or before target and each subsequent frame to the next contiguous position, matching actual PTS/time base/key/representation/domain/digest. It rejects gaps/repeats/overshoot/corruption/EOF. Proof identity/digest come from VT, with source/config/projection identity and seek evidence. Absent-in-VT and present-but-not-emitted errors differ.

Source/config checkpoints precede and follow recovery before returning frames/proofs. CLI `--ledger` is only a cross-check; actual stream selection is independent. It withholds output in an owned temporary file, checks again, closes VT, and publishes exclusively. Publication failure preserves existing files; a post-link pending-cleanup failure rolls back only its newly created final file. Persistent filesystem denial can leave the owned pending file, explicitly tested, without a new final output. Windows filename-bearing diagnostics redact private paths.

Stable read-only local source and trusted OS/process are assumed. Hash checkpoints detect observed changes; they cannot detect adversarial modify-and-restore races. No snapshot/locking subsystem, persisted trusted cache or key management is implemented.

## Commands and durable results

From the clean tested checkout, with CPython 3.11.9:

```powershell
python scripts/prove_bs001_a.py --work TEMP_NEW_EXTERNAL_WORK
```

Use the installed proof Python; the supplement may run outside the checkout, while the direct focused unittest command runs from the tested checkout:

```text
python -B ABSOLUTE_PATH_TO_REPRODUCE_SUPPLEMENT --checkout TEMP_TESTED_CHECKOUT --work TEMP_PROOF_WORK
python -B -m unittest discover -s tests -p test_recovery_r2.py -v
git diff --check
git status --porcelain
```

The supplement script is published with evidence; invoke its absolute local path while using the proof's installed runtime. It checks both historical reports, all ledger sizes, installed CLI bytes, and regenerates the focused log/machine-readable per-test outcomes. Supplemental checks overlap the full proof and are excluded from its aggregate count.

[Full report](result.json), [full suite](tests.txt), [37 injected R2 regression tests](recovery-tests.txt), [machine-readable supplement](supplement.json), [dependency-absent result](bootstrap-only.json), [dependency-absent log](bootstrap-only-tests.txt), [supplement reproduction](reproduce_supplement.py). Historical pre-fix/R1 JSON reports remain unchanged.

Both decisive tests inject only `av.open`/container behavior with real native PyAV frames: validation sees `[0,100,20,50,100]` through flush, while fake seek would select the suffix containing the later identical-pixel occurrence. The full original ledger and shortened/reindexed `[0,20,50,100]` ledger (true source SHA, forged complete/zero anomalies) both reject through API and CLI before recovery seek. CLI exits 2 with no new final output. Validation/comparison/identity/digest routines are not mocked to pass. This is media-boundary injection, not anomalous encoded-media proof.

## Requirement matrix

| Parent requirement | Current evidence |
|---|---|
| A1 package/CLI | Installed fresh wheel/corpus data; version/help/ledger/recover; no analyze. |
| A2 frozen corpus | Unchanged spec/annotations/seeds/schedules/generator/pins; 16 repeat encodes. |
| A3 independent ID | Checked luma IDs/CRC, monotonic bijection for every decoded frame. |
| A4 native ledger | Actual EOF/flush traversal; raw PTS/time bases/global duplicate ordinal/origins; streamed v2 rows. |
| A5 rational timing | Exact/nearest signed ties-away comparison and declared half-tick bounds retained. |
| A6 event survival | All annotated easy/challenge frame metrics; counterfactual signal and retained/degraded status. |
| A7 seek recovery | Actual source-bound contiguous backward-seek/decode-forward; every supported fixture frame. |
| A8 lossless truth | Both FFV1 variants pixel-exact against generator YUV420. |
| A9 safety/resources | Source checkpoints, aliases/Unicode, corrupt/missing timing diagnostics, complete R2 matrix, Timing+VT RSS/lifecycle probes. |
| A10 clean entrypoint | New external env/wheels/media twice, clean exact tested head, complete proof-v2. |
| A11 durable evidence | Per-fixture timing/ID/survival/seek/digests/resources, logs, tier comparisons and exact heads here/receipt. |

| R2 packet regression | Evidence in test_recovery_r2.py / supplement |
|---|---|
| Full identical-pixel duplicate and shortened-ledger attacks | Complete actual validation, API/CLI failure, zero seeks/no output. |
| Safe-source omissions/inserts/reorder/forged row or trailer fields | Full semantic comparison; actual source remains independent. |
| Foreign source/stream/config/domain/version/legacy | Header/nested binding mutations and immutable recovery config mismatch. |
| Source-wide timing/count anomalies | Missing/duplicate/regression before/after target; unavailable versus contradictory native counts. |
| Forged/closed/invalidated VT and identity requests | Public capability boundary, copied metadata, absent/occurrence distinction. |
| Source mutation | During validation, after validation, during decode and decoder close; no success/output; restore cannot revive invalidated state. |
| Unsafe seek suffix | Drop/extra/repeat/reverse/overshoot/unknown/wrong time base/digest/representation/corruption/EOF. |
| Supported API/CLI and output safety | Genuine seek, valid telemetry-tolerant ledger, alias/Unicode/publication/redaction/cleanup faults. |
| Validation reuse and resources | One VT per fixture; multiple recoveries; disk lookup/anchor, explicit/context/GC cleanup; separate 1k/20k probes. |

## Measured counts, tiers and resources

**Complete proof: 101 pass / 0 fail / 3 accepted skips**, at the clean exact tested head. Accounting: 62 test passes + 16 fixture verifications + 16 repeat-encode comparisons + 3 invalid inputs + 1 Timing resource stage + 1 VT resource stage + 1 validation-reuse stage + 1 bootstrap = 101. Full suite: 63 run / 62 pass / 1 symlink skip; focused R2: 37 pass / 0 fail / 0 skip. Separate dependency-absent hygiene: 63 run / 16 pass / 47 explicit runtime-dependency skips; no failures.

All **3,360 checked frame-ID mappings**, **2,880 actual exact seek recoveries**, and **480 lossless pixel-exact frames** are preserved. Exactly one VT validation per each of 16 fixtures is recorded and reused for its recoveries. Every survival/origin/timing/B-frame/key/stream/immutability baseline semantic field equals both historical reports. All 19 main ledger trailers report actual file bytes. Installed CLI separately publishes 345,600 bytes exactly equal to the native sequential target, with matching VT identity/digest and unchanged source.

T1 spec `76a77981587c4509229761166bb47d5dda66e0d94026007f9ab47ea014860e30` and annotations `c3286fedbc9f377cc91bfb6c3eca906d653d1e1747c728ab6a71a3a5f1a2d4cd` plus all schedules/seeds remain frozen. All 3,360 T2 native entries and 2,880 canonical recovery identity/digest triples equal pre-fix and R1 history. All 16 encoded-media hashes match both historical reports and new repeated encodes. All 11 dependency-wheel hashes and the complete toolchain fingerprint match history. Ledger SHA/whole recovery/report bytes legitimately change for v2/config/projection/position metadata and run-local telemetry; new hashes appear in result/supplement. No T1/T2 drift is hidden by that policy.

CPython **3.11.9**, Windows 10 / AMD64, **av 18.1.0**, **NumPy 2.2.6**; exact pins unchanged. Full native library configurations/license strings and wheel filename/hash/provenance are in result.json. Software decode only. Worker proof elapsed **572.858 s**; whole fresh entrypoint **669.016 s**. Worker lifetime peak working set **152,145,920 bytes**, Windows GetProcessMemoryInfo including native allocations. Main media+ledgers **10,181,459 bytes**; other proof artifacts excluding venv/wheels/result **33,762,491 bytes** at report creation. Supplemental artifacts generated afterward are outside those totals.

| Separate VT process | 1,000 frames | 20,000 frames |
|---|---:|---:|
| Peak RSS bytes | 52,502,528 | 52,752,384 |
| VT table bytes | 1,064,960 | 21,041,152 |
| Full validation seconds | 0.129 | 1.375 |
| All-entry lookup seconds | 0.282 | 5.805 |
| Three seek recoveries seconds | 0.145 | 0.181 |

VT RSS growth **249,856 bytes <33,554,432**; actual full validation/flush, 1k/20k lookups, three anchor-based seek recoveries each (402 decoded-forward frames), source unchanged and owned table removed on close. Separate Timing path growth **172,032 bytes**, peaks 45,535,232 / 45,707,264; same 32 MiB limit. Explicit/context/GC cleanup and failure-output behavior also have regression coverage. Probes inject only the media boundary and retain no video frame list; actual encoded seek behavior is independently exercised by the full fixed corpus.

Result SHA-256 (LF blob bytes): `23e6550b352b63f2547a976a813ae407e6cc6f852d8bf199d13c307026e8290f`. Supplement SHA-256: `b0b94e9cf1353f4b058afb30b45ebbb52eb471c1455f3729ec038c39f8f35214`. These are new R2 reports; historical result/supplement bytes are unchanged.

| Fixture | Frames | Ledger | Exact seeks | Validation passes |
|---|---:|---|---:|---:|
| main60-s11 | 240 | complete | 240 | 1 |
| main60-s97 | 240 | complete | 240 | 1 |
| main30-s11 | 120 | complete | 120 | 1 |
| main30-s97 | 120 | complete | 120 | 1 |
| ntsc-s11 | 240 | complete | 240 | 1 |
| ntsc-s97 | 240 | complete | 240 | 1 |
| vfr-s11 | 120 | complete | 120 | 1 |
| vfr-s97 | 120 | complete | 120 | 1 |
| offset-s11 | 240 | complete | 240 | 1 |
| offset-s97 | 240 | complete | 240 | 1 |
| lossless-s11 | 240 | complete | 240 | 1 |
| lossless-s97 | 240 | complete | 240 | 1 |
| audio_first-s11 | 240 | complete | 240 | 1 |
| audio_first-s97 | 240 | complete | 240 | 1 |
| no_timing-s11 | 240 | diagnostic | 0 | 1 |
| no_timing-s97 | 240 | diagnostic | 0 | 1 |

## Limitations and next gate

The three full-proof skips retain their previous accepted semantics: raw H264 s11/s97 emit no PTS and cannot support exact timed seek; Windows symlink creation is privilege-denied (1314). Skips are not successful recovery. Dependency-absent skips are separate hygiene evidence.

Untested: real anomalous-PTS encoded media (coherent injection tested), Linux/macOS/T2 portability, other Python versions, privileged symlink execution, HDR/10-bit/rotation/SAR/interlacing/format changes, timestamp wrap/NLE interpretation, private footage/high-resolution or long-video throughput, hostile same-process code/undetectable source races, production detector/packet/cancellation/budgets, B/C/later roadmap. No licensing/distribution posture change.

One validation per fixture is reused for multiple recoveries; the independent ID/survival oracle still performs its separate truth-check decode. Standalone CLI recovery pays O(N) validation plus source hashes and seek. SQLite disk metadata grows with traversal length; page caches and per-frame work remain bounded. Resource probes measure the metadata/lookup/anchor path, not 1440p throughput or aggregate process-tree memory.

No Actions dispatch/rerun/workflow/settings workaround, source-media modification, B/C implementation, merge/ready/release or CT role was performed. All pushed commits carry `[skip ci]`. Exact-head no-event-filter run absence is recorded in the completion receipt, not claimed as CI success.

Next smallest blocker: one fresh independent exact-final-head R2 rereview and then CT disposition. Claim release is explicit in Issue #2. STOP; A remains unaccepted and B/C HELD.

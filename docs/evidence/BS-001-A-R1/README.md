# BS-001 Checkpoint A — R1 correction proof — 2026-09-30

> Historical R1 evidence. Independent rereview [5903733062](https://github.com/bohanyt/b-scout/issues/2#issuecomment-5903733062) found the shortened-ledger identity bypass. Source-bound R2 implementation/proof is tracked in [BS-001-A-R2](../BS-001-A-R2/README.md); neither historical proof grants current acceptance.

Role: ONE bounded R1 correction worker, not CT or independent reviewer. Correction claim [5903287424](https://github.com/bohanyt/b-scout/issues/2#issuecomment-5903287424); authority: [CT dispatch 5902991245](https://github.com/bohanyt/b-scout/issues/2#issuecomment-5902991245), [independent finding 5902916741](https://github.com/bohanyt/b-scout/issues/2#issuecomment-5902916741). Correction implemented and reproven for the specified synthetic scope; fresh independent exact-head rereview remains required. B/C remain HELD.

## Exact lineage and evidence versions

- Main/PR base: `e35e3e6a6990a96e7c3efd2c0a23da24a5630c2b`.
- Pre-fix reviewed/starting head: `fc42cdfd9364927d98020a817436fce6ba8ce21b`; its runtime tested head was `2590b6e8ab40d293da019543d2f4e3aa7cdc63cd`.
- Corrected clean tested head: `6371454745af601f60cf841998b67647dbc0848b`.
- Existing branch: `agent/bs-001-native-frame-baseline`; existing [DRAFT PR #3](https://github.com/bohanyt/b-scout/pull/3). No replacement lineage, merge or ready conversion.
- Acquisition: fresh origin check, clean existing workspace at the reviewed head; one local correction commit; full new external `git clone --no-hardlinks --branch agent/bs-001-native-frame-baseline . TEMP_CHECKOUT`. Proof executed from that clean exact-head clone into another new external directory, with a fresh venv and fresh no-cache PyPI wheels. No previous media/wheels/proof environment was reused for the clean proof.
- Compute: requested Sol 6.1 / High; Fast allowed; no subagents used. Focused precommit checks initially used an existing exact-pinned runtime, then a new pinned environment. The committed-head full proof and focused receipts use the fresh proof runtime.
- Final published head and zero-Actions verification are bound in the Issue #2 correction completion comment and PR description. The later evidence commit changes only this directory and the historical evidence README banner. Runtime source/tests, corpus, dependencies and proof script remain identical to the tested head.

[Pre-fix reports](../BS-001-A/README.md) remain historical, including their unchanged result hash/counts. [Corrected result](result.json), [full suite log](tests.txt), [mandatory R1 regression](r1-regression.txt), [related recovery tests](recovery-tests.txt), [machine-readable supplement](supplement.json), [dependency-absent result](bootstrap-only.json) and [dependency-absent log](bootstrap-only-tests.txt) belong to this correction. Supplemental checks overlap the main proof and are not added to its count.

Corrected result SHA-256: `58148cbb046fa9016ba1cc85b5134048e823cd00d1b8cb66d375657f531e4470`; supplement SHA-256 (committed LF bytes): `1791817688450c36aef9f81e814abbae68d6bbe96c6f0e2b9d7f5132906582a9`.

## Correction and mandatory regression

**Option B: fail closed for timing whose global occurrence identity cannot be established after seek.** The core `recover()` API requires `ledger_path=...`; header-only calls reject explicitly. Each recovery streams the complete ledger and verifies known, unique, strictly increasing raw PTS, zero global duplicate ordinals, canonical identities, time bases, keyframe anchors, record order/count and a complete error-free trailer. It recomputes safety even when flags/status claim success. A durable trailer `exact_recovery` state records the support rule. Existing v1 ledgers undergo the same validation.

Only supported monotonic/unique-PTS ledgers use the existing backward seek/decode-forward path. Unsafe timing emitted during seek also rejects. There is no local duplicate counter labelled as global identity, and native digest equality is only a pixel check after occurrence selection. CLI and oracle supply the full ledger to the core API. This adds a streamed full-ledger read per extraction, with keyframe metadata retained; high-resolution/long-video extraction cost remains unbenchmarked.

Mandatory injected regression: complete PTS `[0,100,20,50,100]`, identical native pixels at both 100 occurrences, requested first `100 / same_pts_ordinal=0`, and the reviewer's would-be suffix beginning at 20. Both occurrence digests are equal and identities differ. Corrected recovery explicitly returns unsupported **before media opens/seeks**, so the later occurrence cannot be reported as the earlier one. **1 pass / 0 fail / 0 skip** on the corrected clean tested head.

Eight added tests cover that reproduction, adjacent/non-adjacent duplicates, pure regressions, missing timing before/after a known target, anomalies after the target, API header-only bypass, forged safety declarations, incomplete/unrelated ledgers, unsafe seek output, CLI failure without output, supported seeking, absent-target failure and native digest mismatch. Existing native padding/dimension and unknown-target tests remain. Related recovery selection: **8 pass / 0 fail / 0 skip**; the mandatory test has its separate receipt.

## Commands and corrected counts

From the clean corrected checkout (CPython 3.11.9; external new work directory):

```powershell
python scripts/prove_bs001_a.py --work "$env:TEMP\bscout-r1-proof-new"
```

The unchanged entrypoint installs exact pins/package data, generates all fixtures twice, verifies ID/timing/survival/lossless/seek behavior, tests invalid inputs, runs the suite/bootstrap and separate resource probes. Focused sequence in the pinned runtime:

```text
python -m unittest discover -s tests -p test_temporal.py -k test_r1_identical_pixels_later_duplicate_never_recovers_first -v
python -m unittest discover -s tests -p test_temporal.py -k recovery -v
python -m unittest discover -s tests -v
```

The fresh-runtime focused receipts add `-B` and pass on the same committed head. `git diff --check` passed. Supplemental installed CLI commands appear in supplement.json; [contract](../../BS001_A.md) includes the MP4 start/reorder inspection command. Actual edit-list atoms were parsed, including entries, not just string-matched. CLI ran outside the source checkout using the newly installed package, recovered PTS 1000 with matching identity/native digest and 345,600 output bytes. All four CFR MP4 files retain edit lists, negative leading DTS and reordered packet PTS.

**Complete proof: 70 pass / 0 fail / 3 skip.** Accounting: 33 test passes + 16 fixture verifications + 16 repeated-encode comparisons + 3 invalid inputs + 1 resource probe + 1 bootstrap. Full suite: 34 run, 33 pass, 0 failures/errors, 1 privilege skip. This supersedes the pre-fix 62-pass stock proof for this head.

Dependency-absent suite is separate: 34 run, **16 pass / 0 fail / 18 explicit runtime-dependency skips**. It used a previously isolated CPython 3.11.9/jsonschema 4.26.0 environment with av/numpy absence verified, reading source from the clean corrected checkout. It is hygiene evidence, not full runtime evidence.

The three complete-proof skips remain exactly the independently adjudicated cases: raw H264 s11 and s97 cannot recover exact PTS because all timestamps are missing; Windows symlink creation returns privilege error 1314. Neither missing timing nor skipped symlink execution is represented as successful exact recovery.

## All required fixture results

All **3,360 frames** map independently via checked generator luma IDs. All **2,880 known-timing frames** recover via actual backward seek/decode-forward with unchanged canonical identities/native digests. Both lossless variants provide **480 pixel-exact frames**. Every easy and challenge event survives under the recorded metric; this is not detector recall. Sources remain SHA-identical. Unsupported bytes fail; truncated/damaged copies are partial. Every one of the 19 main ledgers reports its actual total byte count.

| Fixture | Frames | Timing/max error | First PTS | B frames | Seek matches | Ledger |
|---|---:|---|---:|---:|---:|---|
| main60-s11 | 240 | pass / 0 ms | 0 | 158 | 240 | complete |
| main60-s97 | 240 | pass / 0 ms | 0 | 158 | 240 | complete |
| main30-s11 | 120 | pass / 0 ms | 0 | 78 | 120 | complete |
| main30-s97 | 120 | pass / 0 ms | 0 | 78 | 120 | complete |
| ntsc-s11 | 240 | pass / 0.5 ms | 0 | 158 | 240 | complete |
| ntsc-s97 | 240 | pass / 0.5 ms | 0 | 158 | 240 | complete |
| vfr-s11 | 120 | pass / 0.333333 ms | 0 | 79 | 120 | complete |
| vfr-s97 | 120 | pass / 0.333333 ms | 0 | 79 | 120 | complete |
| offset-s11 | 240 | pass / 0.333333 ms | 500 | 158 | 240 | complete |
| offset-s97 | 240 | pass / 0.333333 ms | 500 | 158 | 240 | complete |
| lossless-s11 | 240 | pass / 0.333333 ms | 0 | 0 | 240 | complete |
| lossless-s97 | 240 | pass / 0.333333 ms | 0 | 0 | 240 | complete |
| audio_first-s11 | 240 | pass / 0.333333 ms | 0 | 158 | 240 | complete |
| audio_first-s97 | 240 | pass / 0.333333 ms | 0 | 158 | 240 | complete |
| no_timing-s11 | 240 | unknown | null | 158 | 0 | diagnostic |
| no_timing-s97 | 240 | unknown | null | 158 | 0 | diagnostic |

Origins above use each fixture's native time base; offset 500 is at 1/1000. Full per-event survival, rational timing/rounding, GOP, stream selection, origin separation, identity and source/error results remain in result.json. The existing stock A requirements pass with the same scope and skips; no source/corpus workaround removes the R1 case.

## T1/T2/T3 and toolchain

**T1/frozen corpus-v1 truth did not change.** Canonical spec: `76a77981587c4509229761166bb47d5dda66e0d94026007f9ab47ea014860e30`; annotations: `c3286fedbc9f377cc91bfb6c3eca906d653d1e1747c728ab6a71a3a5f1a2d4cd`. All schedules match. Dev 11 / held-out 97 remain unchanged.

T2: all 3,360 native oracle digests and all 2,880 recovery records equal the historical report. T3: all 16 encoded-media SHA values equal the historical report and new repeated encodes. Ledger SHA values change because trailers now include the support state plus run-specific time/RSS; exact new hashes and byte counts are recorded. Supplement.json contains the full per-fixture tier comparison.

CPython **3.11.9**, Windows 10/AMD64, **av 18.1.0**, **NumPy 2.2.6**; complete proof/runtime pins unchanged. All 11 fresh wheel hashes and the full toolchain fingerprint equal the pre-fix report. PyAV wheel `av-18.1.0-cp311-abi3-win_amd64.whl`, SHA `ea1480b7a8d5405cb5f382b344731bf125fd2c1c6fae3964f6c48595628387ff`. Native versions/configure/license strings remain in result.json. Software decoding, one SLICE thread, err_detect=explode; no hwaccel/model/provider. No licensing/distribution posture changes.

## Resources and limitations

Core clean proof: **254.033 s**; full fresh install + proof: **330.340 s**. Worker lifetime peak working set **152,154,112 bytes**, Windows GetProcessMemoryInfo including native allocations, process-specific rather than aggregate tree/system RAM. Media+ledgers: **10,052,517 bytes**; all proof artifacts excluding env/wheels/result: **33,602,558 bytes** at report time (before supplemental files).

Separate 1,000/20,000-row probes: peak **45,076,480 / 45,461,504 bytes**, growth **385,024 bytes <32 MiB**; output **814,670 / 16,386,670 bytes**; elapsed **0.033514 / 0.645858 s**. These prove the streamed ledger/counter path, not high-resolution throughput.

Untested: real-media duplicate/non-monotonic fixtures (injected recovery rejection now covered), Linux/macOS/T2 portability, Python versions beyond 3.11.9, capable-environment symlink execution, HDR/10-bit/rotation/SAR/interlacing, changing formats, timestamp wrap/NLE interpretation, private footage/real 1440p60 throughput, long-video extraction performance, production detector/packet/cancellation/budgets, B/C and later roadmap.

No Actions dispatch/rerun or workflow/settings edits; commits use `[skip ci]`. Exact corrected final-head query without any event filter is recorded in the correction completion comment. Skipped CI is not successful CI. PR remains DRAFT/unmerged. The next smallest blocker is CT-dispatched independent exact-head R1 rereview. Correction claim is released in Issue #2 after publication; STOP before B.

# BS-001 Checkpoint B implementation evidence

Implementation and local synthetic proof complete; independent exact-head review and CT disposition remain pending. Checkpoint C is HELD. This evidence is diagnostic output for B.

## Authority and exact lineage

- Dispatch: [5905458974](https://github.com/bohanyt/b-scout/issues/2#issuecomment-5905458974); bounded claim: [5905582127](https://github.com/bohanyt/b-scout/issues/2#issuecomment-5905582127). Required authority/read list and both END markers were fresh-read before source work.
- Accepted A starting head: `25df7fb3c73ce0659ddc65f7426c4148cf5548dd`.
- Coordination main/base: `e651512a89a02d9e5e9b18698ad583a997dc73cf`; original merge base `c18f6ccb6f9ee07cc41c4b3e13455007147faf98`.
- Normal coordination merge: `cdaa6e024e4a029cae4e74fffd97a94e0d8872a6`; accepted history preserved.
- B source/configuration freeze commit: `28cc3c79c054e2415f6ae821c4ddb58445a5c6cd`.
- Exact clean runtime-tested head: `0d4dd5cd5594bcb5150cac486aed5d3959bb821e` (proof-only redaction correction).
- Branch: `agent/bs-001-native-frame-baseline`; existing DRAFT PR #3. Final publication head and exact-head zero-Actions reads are recorded in the complete Issue #2 handoff; the publication delta contains evidence/documentation only.
- Changed implementation paths: `src/bscout/regional.py`, `evaluation_b.py`, `ledger.py`, `cli.py`, `__init__.py`; `scripts/prove_bs001_b.py`, `tune_bs001_b.py`; three focused B test modules; README/pyproject description; `docs/BS001_B.md` and this evidence directory. Coordination-only CURRENT/V7/B packet came from main.

## Dev selection and freeze

[Dev tuning](dev-tuning.json) compares short/stable thresholds 32, 48, 64 on all eight dev fixtures only. Candidate totals were 302953 / 274411 / 227134; unmatched/noisy totals 234694 / 207524 / 161174. Select 64 with all non-HUD easy candidate labels localized and the lowest measured noise. Tuning did not claim retained-evidence success. Final diagnostic/live-tile budgets, PNG preview and combined-spool accounting were hardened before freeze; signal scale/thresholds/windows match the selected trial.

[Frozen configuration](config-freeze.json): `bscout-regional-v1`, SHA `1bb5537561d7e65c22286126d474895735a362feaee261847b02f568e067a5cf`; freeze file SHA `90da644b984e0914a14b3efe0f438a8992f3a3a03616062655c0a84822ba65cb`, timestamp `2026-09-30T07:00:03.898323+00:00`. The held-out runner rechecks the complete freeze and file hash before each held-out B scan; neither configuration nor detector source changed during final proof.

User authority resolves the full-clip HUD exception: **“Ya, boleh khusus HUD regional (Recommended)”** after the conflict was explained. Only the spatially localized persistent-HUD truth may count a full-clip state interval with real signals and verified exact evidence; all other effectively full-clip and whole-frame candidates are rejected.

[Proof history](proof-history.json) records the interrupted earlier dev-only run: full A passed, B dev main60 completed, archiving was stopped before any held-out B scan to cache repeated filesystem path resolutions. Only the proof script and a regression test changed at the tested correction head. Final proof uses a new clean checkout/environment and reruns complete A plus all B splits.

## Final metrics

Known native timing: seven fixtures per split. These recalls mean **localized observation coverage** with verified representative evidence inside both candidate and truth, boundaries within one generator frame, and documented spatial overlap. They include the authorized regional-HUD exception. State interval and structural-inspection recall are separately retained; no invisible semantic boundary is inferred.

| Split | Decoded/scanned | Exact evidence frames | Easy candidate/evidence | Challenge candidate/evidence | Non-harness candidates | Unmatched/noisy | Candidates/min | Noise/min |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| dev | 1680/1680 | 1440 | 104/104 | 21/56 | 167252 | 138542 | 358614.873 | 297056.070 |
| held_out | 1680/1680 | 1440 | 104/104 | 21/56 | 167308 | 138598 | 358734.946 | 297176.143 |

Native-duration denominator: 27.983 seconds per supported split, using native first/last PTS and decoder-reported final-frame duration where available. Rates exclude fixture ID-harness-only candidates; detector never masks that strip. All candidate counts/IDs, including harness candidates, remain in full reports. “Unmatched/noisy” is the evaluation category; it is not a semantic false-positive judgment.

Both splits miss the same five challenge IDs on every supported fixture: `small_low_contrast`, `fade_scale`, `camera_pan`, `flashing_numbers_A`, `flashing_numbers_B` (35 misses per split). Exact intervals, rejection reasons, overreach, shared matches and all IDs are in the unsampled fixture archives.

Easy state intervals alone cover 102/104 per split. On main30, visually identical contiguous `reopen` [55,58) / `five_key_straddle` [58,63) labels have no pixel boundary; fixed 1/3/5-frame structural inspections cover both locally while sharing their visual occurrence. State-only main30 misses remain visible. Genuine replacement and visible close/reopen gaps also have focused tests and actual mappings.

Raw H264 `no_timing-s11/s97`: every 240 presented frames scanned, explicit partial B, zero exact timed evidence. All 15 easy and 8 challenge truth/evidence mappings per raw fixture remain reported as unavailable; their 30 easy occurrences are excluded from the supported denominator. Native timestamps and video-minute rates are null. No frame-index/FPS timestamps or recovery fallback is used.

| Fixture | Status | Frames | Easy usable | State easy | Total candidates | Noise | One-frame candidates | Exact frames | Engine seconds |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| [main60-s11](fixtures/main60-s11.json.gz) | complete | 240/240 | 15/15 | 15/15 | 31096 | 22488 | 15255 | 240 | 164.269 |
| [main60-s97](fixtures/main60-s97.json.gz) | complete | 240/240 | 15/15 | 15/15 | 31097 | 22489 | 15253 | 240 | 165.279 |
| [main30-s11](fixtures/main30-s11.json.gz) | complete | 120/120 | 15/15 | 13/15 | 18502 | 12497 | 10372 | 120 | 76.433 |
| [main30-s97](fixtures/main30-s97.json.gz) | complete | 120/120 | 15/15 | 13/15 | 18523 | 12518 | 10392 | 120 | 74.775 |
| [ntsc-s11](fixtures/ntsc-s11.json.gz) | complete | 240/240 | 15/15 | 15/15 | 31096 | 22488 | 15255 | 240 | 166.652 |
| [ntsc-s97](fixtures/ntsc-s97.json.gz) | complete | 240/240 | 15/15 | 15/15 | 31097 | 22489 | 15253 | 240 | 158.018 |
| [vfr-s11](fixtures/vfr-s11.json.gz) | complete | 120/120 | 13/13 | 13/13 | 18209 | 12276 | 10200 | 120 | 64.967 |
| [vfr-s97](fixtures/vfr-s97.json.gz) | complete | 120/120 | 13/13 | 13/13 | 18239 | 12306 | 10229 | 120 | 64.452 |
| [offset-s11](fixtures/offset-s11.json.gz) | complete | 240/240 | 16/16 | 16/16 | 31253 | 22591 | 15353 | 240 | 147.655 |
| [offset-s97](fixtures/offset-s97.json.gz) | complete | 240/240 | 16/16 | 16/16 | 31250 | 22588 | 15346 | 240 | 160.479 |
| [lossless-s11](fixtures/lossless-s11.json.gz) | complete | 240/240 | 15/15 | 15/15 | 31088 | 22480 | 15246 | 240 | 143.686 |
| [lossless-s97](fixtures/lossless-s97.json.gz) | complete | 240/240 | 15/15 | 15/15 | 31094 | 22486 | 15249 | 240 | 141.557 |
| [audio_first-s11](fixtures/audio_first-s11.json.gz) | complete | 240/240 | 15/15 | 15/15 | 34794 | 23722 | 18953 | 240 | 509.554 |
| [audio_first-s97](fixtures/audio_first-s97.json.gz) | complete | 240/240 | 15/15 | 15/15 | 34794 | 23722 | 18950 | 240 | 521.340 |
| [no_timing-s11](fixtures/no_timing-s11.json.gz) | partial | 240/240 | unavailable | unavailable | 31096 | 22506 | 15255 | 0 | 87.606 |
| [no_timing-s97](fixtures/no_timing-s97.json.gz) | partial | 240/240 | unavailable | unavailable | 31097 | 22507 | 15253 | 0 | 100.527 |

Duration histograms include every candidate (including the harness and raw-PTS fixtures): 115889 one-frame candidates in dev, 115925 in held-out; exact full histograms are in [summary](summary.json) and [result](result.json). Trigger and occurrence IDs distinguish full state intervals from fixed inspection windows. Per-frame feature logs use four decimal places; candidate trigger values and native identities/asset bytes preserve their full precision.

## Exact extraction and unchanged truth

All 3360 native frame digests match the frozen historical R2 evidence; T1 equality holds for all 16 fixtures. Historical A/R1/R2 reports and frozen corpus files are unchanged. Every source SHA remains unchanged. One full core VT validation per fixture is reused for all selected recoveries, with the same resolved decoder configuration and every L0 frame aligned to VT timing/representation/native digest. Complete supported recovery uses genuine backward seek plus contiguous decode-forward alignment.

2880 retained frames are independently verified against post-scan source decode and the checked generator-ID channel. Actual native assets are checked by domain hash, and PGM/PNG by pixel-exact native luma, with independent PNG chunk CRC/deflate/filter checks. Self-consistent replacement assets and corrupt PNG tests reject. Manual inspection of final-run native-luma PNG positions 30,70,73 on main60-s11 shows HUD overlap and the two panel appearances. These are luma previews; native YUV remains canonical.

## Resources, pressure and lifecycle

Full worker elapsed: 5361.868 s; entrypoint including fresh isolated install: 5467.662 s; full A subproof: 1723.008 s. Sum of B engine runs: 2747.248 s. Proof process peak RSS 424407040 bytes; recorded output before final result write 2791776769 bytes excluding environment/wheels. Native/preview assets total 1895029608 bytes.

RSS method is Windows GetProcessMemoryInfo PeakWorkingSetSize (process lifetime including native allocations). Full-proof per-fixture peaks are cumulative in the shared worker and include previous evaluation/report materialization. Separate B processes stream real PyAV 64x64 native frames through actual TileSignals, with no retained decoded history.

| Frames | Scanned | Candidates | RSS bytes | Analysis-state estimate | Spool bytes | Seconds |
|---:|---:|---:|---:|---:|---:|---:|
| 1000 | 1000 | 800 | 52334592 | 90144 | 901952 | 0.674 |
| 20000 | 20000 | 16000 | 46993408 | 90144 | 18177347 | 56.962 |

Resource growth check passes the 32 MiB allowance; both processes finish with no active tracks. Analysis pixel refusal occurs before the first scan, and a real four-frame FFV1 one-byte spool probe returns explicit failed/incomplete validation with zero evidence and unchanged source. Focused tests exercise metadata/evidence exhaustion, incomplete prefix refusal, dropped/misaligned scan output, source mutation after recovery and publication rollback. No presented-frame fallback/downsampling or universal event-count cap is introduced.

Configured metadata spool 268435456 bytes includes B metadata and live VT; assets have a separate 268435456-byte budget; SQLite cache 256 KiB; diagnostic reserve 65536 bytes; analysis pixel/live-tile ceilings are explicit. Measured maximum combined metadata spool 69726471 bytes and total owned bytes 318273104. Checks run per frame/per128 candidate rows/per evidence row; staging can temporarily exceed a threshold by a geometry-bounded quantum before explicit stop. VT storage is removed before publication; the bounded diagnostic queue remains caller-owned. Structural inspections often select every frame, so longer clips may exhaust asset budgets explicitly.

| Fixture | Final metadata bytes | Peak combined metadata | Asset bytes | Diagnostic bytes | Shared RSS bytes |
|---|---:|---:|---:|---:|---:|
| main60-s11 | 57689395 | 57951539 | 139942791 | 2500 | 73334784 |
| main60-s97 | 57690431 | 57952575 | 139980256 | 2502 | 279126016 |
| main30-s11 | 33467040 | 33606304 | 69997841 | 2501 | 361041920 |
| main30-s97 | 33493198 | 33632462 | 70008909 | 2501 | 361041920 |
| ntsc-s11 | 57398618 | 57660762 | 139943686 | 2500 | 361041920 |
| ntsc-s97 | 57399162 | 57661306 | 139977809 | 2500 | 361041920 |
| vfr-s11 | 32839784 | 32979048 | 69979781 | 2499 | 372387840 |
| vfr-s97 | 32893983 | 33033247 | 70003733 | 2499 | 372387840 |
| offset-s11 | 57659075 | 57921219 | 139951590 | 2500 | 372387840 |
| offset-s97 | 57652905 | 57915049 | 139989411 | 2501 | 372387840 |
| lossless-s11 | 57046816 | 57308960 | 139125271 | 2500 | 384667648 |
| lossless-s97 | 57049830 | 57311974 | 139125842 | 2501 | 384667648 |
| audio_first-s11 | 69464327 | 69726471 | 248546633 | 2501 | 397754368 |
| audio_first-s97 | 69446157 | 69708301 | 248456055 | 2501 | 405549056 |
| no_timing-s11 | 48269102 | 48531246 | 0 | 2560 | 424407040 |
| no_timing-s97 | 48261820 | 48523964 | 0 | 2561 | 424407040 |

## Commands, environment and accounting

Clean CPython 3.11.9 / Windows AMD64 / PyAV 18.1.0 / NumPy 2.2.6; software decoder, one SLICE thread, err_detect=explode. Full bundled FFmpeg versions/configuration, 11 no-cache pinned wheel hashes and package inventory are in result.json. Installed package files outside checkout match the pre-install snapshot byte-for-byte. Starting/final clean checkout, HEAD, source snapshot and freeze remain unchanged.

```powershell
git clone --branch agent/bs-001-native-frame-baseline https://github.com/bohanyt/b-scout.git NEW_CHECKOUT
git -C NEW_CHECKOUT checkout 0d4dd5cd5594bcb5150cac486aed5d3959bb821e
python NEW_CHECKOUT/scripts/prove_bs001_b.py --work NEW_EXTERNAL_WORK
```

Entrypoint downloads exact requirements-proof pins from PyPI without cache, installs from those wheels, runs the complete existing A proof, regenerates both corpus splits twice, evaluates frozen B on all fixtures, verifies actual retained assets, runs focused/regression tests/bootstrap and separate A/B resource processes. Exact subordinate commands and provenance are in result.json. To inspect a full mapping:

```powershell
python -c "import gzip,json; r=json.load(gzip.open('docs/evidence/BS-001-B/fixtures/main30-s97.json.gz','rt')); print(json.dumps(r['evaluation']['metrics'],indent=2))"
```

Tests: 120 run / 119 passed / 0 failed / one OS symlink skip (winerror1314). A pipeline aggregate: 158 pass / 0 fail / 3 skip. B report: 119 unittest passes / 0 combined test/benchmark/regression failures / 5 enumerated skips: one OS symlink case, raw H264 exact-seek recovery for two seeds in A and exact timed evidence for the same two seeds in B. These are stage counts, not five skipped unittest cases. [Exact test log](a-proof/tests.txt), [A full result](a-proof/result.json), and both resource families are retained. The legacy A subproof scope string is unchanged contract-test text, not a live coordination disposition.

[Source snapshot](source-snapshot.json) and [artifact inventory](artifact-manifest.json) bind bytes. Git publishes these JSON files with LF endings. The two original proof outputs with terminal CRLF are preserved byte-for-byte as [original result](original-output/result.json.gz) and [original source snapshot](original-output/source-snapshot.json.gz); the inventory records both identities. JSON values are unchanged, and the proof's snapshot hash refers to the original archive bytes. [Raw signal index](signals/index.json) inventories every unsampled original L0 JSONL row, with compressed/uncompressed hashes. Fixture archive hashes, uncompressed canonical hashes and exact evidence checks are retained in result.json. Synthetic media and full assets remain external; public evidence contains metadata/signals/hashes only.

## Limits and next gate

Untested: private/real footage and production recall; real 1440p60 throughput; Linux/macOS native-digest portability; HDR/10-bit/rotation/SAR/interlacing and midstream representation changes; real encoded duplicate/nonmonotonic PTS (accepted A full-source injection regressions retained); Python versions other than recorded runtime; hostile same-process code and undetectable modify-and-restore races (stable read-only local source assumed); OCR/semantics/providers/UI and C packet/READY/cancellation/later roadmap. B signal baseline supports even-sized native 8-bit yuv420p only.

Next smallest action: CT dispatches one fresh independent exact-head B reviewer against the published implementation/evidence head. PR #3 stays DRAFT/unmerged, B ownership is released by the completion receipt, and C remains HELD until CT disposition.

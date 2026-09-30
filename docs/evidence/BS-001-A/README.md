# BS-001 Checkpoint A local proof — 2026-09-30

**Historical pre-fix evidence.** These reports belong to tested head `2590b6e8ab40d293da019543d2f4e3aa7cdc63cd`, published/reviewed at `fc42cdfd9364927d98020a817436fce6ba8ce21b`. Independent review found R1 despite the stock 62-pass proof. Reports in this directory remain unchanged; use the [corrected R1 proof](../BS-001-A-R1/README.md) for current recovery evidence. This historical result is not Checkpoint-A acceptance.

Role: bounded implementation lead, not Control Tower or independent acceptance reviewer. State: **IMPLEMENTED / TESTED / RUNTIME_CONFIRMED for the specified synthetic Checkpoint-A scope**. Independent acceptance remains pending. B/C are HELD.

## Identity and acquisition

- Base/main: e35e3e6a6990a96e7c3efd2c0a23da24a5630c2b.
- Clean tested head: 2590b6e8ab40d293da019543d2f4e3aa7cdc63cd.
- Branch: agent/bs-001-native-frame-baseline; [DRAFT PR #3](https://github.com/bohanyt/b-scout/pull/3).
- Acquisition: public git clone; fresh fetch; required branch confirmed 0 unique commits / 2 behind main; clean fast-forward to origin/main. The final proof ran in a second full local clone at the tested commit with an empty external work directory and new venv.
- Compute: Sol 6.1 High, lead Fast explicitly allowed by the user's amendment. No subagents; their Fast-OFF requirement could not be guaranteed by the available runtime.
- Final published head is recorded in the Issue #2 completion comment. Later evidence-only commit changes only this directory; no runtime source, tests, pins, corpus or generator change after the tested head.

## Commands and durable artifacts

One command from the clean checkout:

~~~powershell
python scripts/prove_bs001_a.py --work "$env:TEMP\bscout-a-proof-new"
~~~

[Detailed contract/commands](../../BS001_A.md). [Full machine-readable report](result.json), [unit/runtime log](tests.txt), [bootstrap-only result](bootstrap-only.json), [bootstrap-only log](bootstrap-only-tests.txt), [installed CLI and MP4 forensic supplement](supplement.json).

result.json SHA-256: ceab84b51cee790478fc981b4365d652b06c9a3f79af0a33fc8fa60dc6dba1e7.

The proof's initial setup retry was interrupted after a stalled dependency transfer. The final attempt used another empty work directory, fresh no-cache PyPI downloads and no reused wheels/media/env. The earlier full proof passed at 2be04a9eb51d8fc306e35d3ff74db0fc6a628509; final runtime proof below supersedes it after diagnostic-path privacy tests/corrections. No initial failed/partial local logs containing private paths are committed.

## Results and limits

Main proof aggregates **62 pass / 0 fail / 3 skip**: 25 passing tests; 16 fixture verifications; 16 repeat-encode comparisons; 3 bad-input checks; 1 resource-growth check; 1 bootstrap command. The test suite runs 26 tests with one symlink skip. Supplemental installed-CLI and MP4 checks pass separately and are not added to that count. Bootstrap-only environment: 16 pass / 0 fail / 10 explicit runtime-dependency skips.

All 3,360 frames mapped independently by checked luma IDs. All 2,880 known-timing frames recovered through actual seek/decode-forward with matching native digests. All easy and challenge event frames survived this encoder configuration under the declared metric; this is not detection or real-footage recall. Both FFV1 seed variants are pixel-exact. Every source immutability check passed.

| Fixture | Frames | Timing / maximum error | First presented PTS | B frames | Seek matches | Ledger |
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
| no_timing-s11 | 240 | unknown / 0 ms | None | 158 | 0 | diagnostic |
| no_timing-s97 | 240 | unknown / 0 ms | None | 158 | 0 | diagnostic |

Origin values above are in each recorded native time base. Offset origin is 500 at 1/1000 seconds, with container start 500000 microseconds; it is preserved rather than zeroed. CFR MP4 has negative leading DTS, reordered packet PTS, an actual moov/trak/edts/elst atom, and first presented PTS zero. The supplement records actual edit entries and four initial packets for all four CFR MP4 encodes. Stream index 1 is correctly selected when audio is first; main MP4 has no audio.

Truncated and damaged copies return partial diagnostics; unsupported bytes return failure. Raw H264 returns diagnostic with all 240 PTS missing per seed, not fabricated timestamps or a healthy ledger.

Three main skips: raw H264 s11 exact recovery unavailable (no PTS); raw H264 s97 same; Windows symlink creation denied with winerror 1314. Identical and hardlink aliases are tested. Real duplicate/non-monotonic PTS remain untested; injected logic includes missing PTS and non-adjacent duplicates. Bootstrap-only 10 skips are intentional dependency hygiene, separate from the main proof.

## Resources and toolchain

Core proof elapsed: 226.391 seconds; entire fresh install + proof: 333.027 seconds. Worker lifetime peak working set: 152,150,016 bytes, measured using Windows GetProcessMemoryInfo, including native allocations. This is the worker process, not aggregate process-tree/system RAM. Output bytes: media + ledgers 10,050,341; all work artifacts excluding venv, downloaded wheels and final result 34,165,923. Artifact totals include supplemental CLI diagnostics generated during the run.

Separate resource processes: 1,000 frames peak 45,010,944 bytes, 20,000 frames peak 45,109,248 bytes; growth 98,304 bytes <32 MiB. This tests streamed row production and disk-backed PTS counts, not high-resolution throughput. Every ledger trailer's total output bytes equals the actual file size.

Python 3.11.9, Windows 10, AMD64; av 18.1.0 / NumPy 2.2.6. Exact complete pins are in requirements-proof.txt. Wheel filename/hash/source and bundled libav* versions/configurations/license strings are in the report. PyAV wheel SHA-256: ea1480b7a8d5405cb5f382b344731bf125fd2c1c6fae3964f6c48595628387ff. Software decode with one SLICE thread; hardware disabled. libx264 core 165, CRF18, two B frames, 2-second key interval; actual encoder build/settings logs retained. Licensing observations and deferred BS-004 distribution decision are in the contract doc.

## Truth and digest tiers

Corpus-v1 T1 spec: 76a77981587c4509229761166bb47d5dda66e0d94026007f9ab47ea014860e30.
T1 annotations: c3286fedbc9f377cc91bfb6c3eca906d653d1e1747c728ab6a71a3a5f1a2d4cd.
Schedule digests for each fixture are committed and copied in result.json. These are environment-independent canonical JSON digests. No frozen truth changed after the initial corpus commit.

T2 lists every native oracle-plane digest with generator ID; seek proof includes matching canonical identity/digest. T3 lists every encoded-file and ledger SHA with fingerprint. All 16 same-toolchain repeated media hashes match. Ledger T3 hashes intentionally depend on elapsed/RSS metadata; byte variation alone is not T1/T2 truth failure.

## Requirement traceability

| Requirement | Implementation / proof |
|---|---|
| A1 package/CLI | Installed package from clean source, corpus package data, version/help/ledger/recover CLI: supplement.json. Fixtures/oracle invoked by entrypoint. No analyze. |
| A2 frozen truth | corpus-v1 spec, canonical annotations, digests, dev 11 / held-out 97; all 16 encodes repeated byte-identically. |
| A3 independent ID | Every decoded frame ID checked against generator CRC; strictly monotonic bijection; damaged-bit unit rejection. |
| A4 native ledger | All 3,360 presented frames; raw PTS/time bases, separate origins, unknown raw-H264 timing, streamed rows. |
| A5 identity/digest | Source/stream/PTS/duplicate ordinal; native row padding removed; actual 854x480 path and padding mutation tests. |
| A6 rational timing | Exact comparisons or nearest ties away from zero; observed NTSC bound 0.5 ms, other MKV rounding <=0.333334 ms. |
| A7 corpus coverage | 30/60/NTSC/VFR/offset/MP4/FFV1/audio-first/raw-H264 plus bad copies; all easy/challenge annotations encoded. |
| A8 survival | Every event frame has nonzero counterfactual signal; easy survives; each challenge metric/status recorded, all survived in this run. No detector claim. |
| A9 random access | 2,880 exact recoveries after actual backward seek; every known-time frame (HUD spans clip), plus absent-target rejection; long GOP and actual B frames. |
| A10 lossless | 480 FFV1 frames pixel-exact against native generated YUV420 planes. |
| A11 safety/resources | Source unchanged; spaces/Unicode, identical/hardlink alias rejection, symlink privilege skip, corrupt packets/frames, unsupported/truncated/damaged cases, timestamp injections, RSS probes. |
| A12 clean reproduction | One entrypoint downloads fresh exact wheels, builds package, regenerates twice, runs tests/oracle/resources, emits result.json at clean recorded head. |

## Remaining untested and next gate

No Linux/macOS execution or T2 portability; no other Python-version proof; symlink rejection requires a capable environment; real duplicate/non-monotonic media timing, HDR/10-bit/rotation/SAR/interlacing, changing formats, timestamp wrap, NLE interpretation, private footage and real 1440p60 throughput are untested. No production detector, packet/READY, cancellation/budget runtime, provider/model/UI/export or later-roadmap claim.

No workflows/settings were changed, and no dispatch/rerun was called. Exact pushed-head Actions absence is recorded in the completion comment; skipped CI is not successful CI.

## Supplemental reproduction

After the entrypoint, use its installed environment from outside the checkout for the CLI commands in the contract document. The tested CLI sequence was version, help, ledger of main60-s11.mp4, then recover PTS 1000 to a new .yuv file; assert 345600 output bytes and a matching ledger native digest. The following independent inspection reproduces the MP4 start/reorder observations on regenerated files (set media to that new work directory's media folder):

~~~python
from pathlib import Path
import av
media = Path("TEMP_WORK/media")
for name in ("main60-s11.mp4", "main60-s97.mp4", "main30-s11.mp4", "main30-s97.mp4"):
    path = media / name
    assert b"elst" in path.read_bytes()
    with av.open(str(path), options={"ignore_editlist": "0"}) as container:
        stream = container.streams.video[0]
        initial = []
        for packet in container.demux(stream):
            if packet.dts is not None:
                initial.append((packet.pts, packet.dts))
            if len(initial) == 4:
                break
        assert initial[0][1] < 0 and initial[1][0] > initial[2][0]
        print(name, stream.time_base, container.start_time, stream.start_time, initial)
~~~

Next smallest blocker: Control Tower independent read-only exact-head Checkpoint-A review, including explicit consideration of the stated skips. Implementation claim is released in Issue #2 after final-head/PR/no-Actions verification. Stop before B.

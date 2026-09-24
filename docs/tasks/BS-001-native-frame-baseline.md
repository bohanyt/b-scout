# BS-001 — offline native-frame baseline

Issue: [#2](https://github.com/bohanyt/b-scout/issues/2). Implementation owner: **unassigned**. Current dispatch: **checkpoint A only — PREBUILD_REVIEWED / READY / UNCLAIMED**.

Independent pre-build review: [Issue #2 comment 5806205721](https://github.com/bohanyt/b-scout/issues/2#issuecomment-5806205721), key `BSCOUT-PREBUILD-OPUS-20260924-V1`. Its disposition was `NEEDS_PREBUILD_CORRECTION` with **no blocker**: architecture and A→B→C sequencing are sound. The CT has incorporated the A-only corrections below.

## Objective and unchanged parent acceptance

Build the first offline Python engine/CLI slice from a local, read-only video to timestamped regional-change candidates and actual evidence in a validated portable packet. This proves temporal handling on synthetic fixtures, not general UI recognition or real-video recall. Full parent acceptance remains [Gate B](../ACCEPTANCE.md), [architecture](../ARCHITECTURE.md), and [packet semantics](../PACKET_SPEC.md).

A/B/C are checkpoints inside the same issue and eventual same implementation lineage. A worker stops after its dispatched checkpoint. Completing A does not close BS-001.

## Read, claim, lineage and one-shot-agent model

Read AGENTS, CURRENT, CT ROLE/PROTOCOL, issue #1, the full current handoff selected by CURRENT, issue #2/comments including the Opus review above, this packet, ARCHITECTURE, ACCEPTANCE, PACKET_SPEC, and the [readiness audit](../audits/2026-09-24-bootstrap-readiness.md).

Fresh-check main, task claims, branches and PRs. Claim **in issue #2** before source writes with worker identity, checkpoint A, exact base, lineage, proof and exclusions.

Use/reuse exactly one BS-001 implementation lineage:
- suggested branch: `agent/bs-001-native-frame-baseline`;
- one DRAFT PR to main;
- corrections and later authorized BS-001 checkpoints stay on it;
- no force-push of another worker, merge, release or self-promotion to CT.

Agents are expected to be one-shot and may have disposable local compute. Therefore durable continuity must live in GitHub: source, committed truth/specs, tests, exact pins, commands, machine-readable reports, evidence summaries and task/PR comments. Generated fixture media may remain ignored/disposable if it can be regenerated deterministically.

No GitHub Actions dispatch/rerun. Use the agent's own environment for proof. Use applicable `[skip ci]` commit markers and verify no workflow run was created. Do not edit workflow/settings merely to bypass the constraint. Skipped CI is not green CI.

## Checkpoint A — independent temporal oracle and native-time ledger (ACTIVE)

Smallest gate: establish trustworthy frame identity, timing and exact random-access recovery **before detector tuning**.

### A1. Minimal package/CLI

Provide version/help and explicit commands for:
- deterministic fixture generation;
- native frame ledger generation;
- oracle verification / exact frame recovery.

Do **not** advertise a production `analyze` command yet.

Use an existing media stack rather than writing codecs. **PyAV is the current recommended initial harness**, based on the independent review, but it is not frozen project architecture. Fresh-verify compatibility, license/provenance and installability; pin exact Python/package versions and record wheel/native library versions. Software decode only for A. Record decoder/thread configuration.

### A2. Corpus v1: committed truth, disposable encodes

Commit a versioned declarative corpus spec plus canonical annotations. Truth changes create a new corpus version or an explicit CT-reviewed diff; do not silently edit ground truth in place.

Declare:
- deterministic generator seeds;
- **dev seeds** for implementation tuning;
- **held-out seeds** reserved now for later B evaluation;
- canonical annotation serialization/digest rules;
- encoder/container settings per fixture.

Required timing/scenario coverage:
- 30 FPS and 60 FPS;
- 60000/1001 timing in a container whose representable timestamps expose rounding;
- VFR with explicit per-frame schedule;
- non-zero raw timestamp origin;
- MP4-style B-frame/edit-list/start behavior;
- a lossless variant of the main scenario;
- at least one lossy long-GOP fixture with **B-frames >=2** and GOP >=2 s;
- no-audio case;
- a stream-selection case where audio precedes video;
- unsupported/non-media input and corrupt/truncated media;
- a no-container-timing / missing-timestamp style case where feasible, otherwise explicit unit-level injected timing cases.

Main annotated scenario must include:
- 1-, 3-, and 5-frame overlays;
- multiple phases including I-frame, B-frame, immediately pre-keyframe and straddling a keyframe;
- event crossing a one-second boundary relative to the chosen origin;
- first-frame and last-frame events where representable;
- moving background + persistent HUD;
- same-panel content replacement, including back-to-back one-frame A→B;
- close/reopen identical content as another occurrence;
- popup overlapping HUD.

Challenge truth must at least be represented in spec/annotations: small/low-contrast, fade/scale, full-screen motion/effects, camera motion, flashing numbers, abrupt alt-tab-like transition, and one chroma-dominant/isoluminant change. Encode the challenge cases that are cheap; explicitly list any not yet encoded. A does not need detector results.

### A3. Independent per-frame identity channel

Every generated frame must carry a generator-controlled identity signal that does not depend on the decoder under test. Recommended minimum: a coarse high-contrast **luma-only frame-ID code** in a declared harness strip, encoding generator frame index plus check bits.

The annotations must identify the harness region. Later detector evaluation must not treat harness-only candidates as production signal; B may use strip-free twins or explicitly excluded harness-only metrics.

Do not establish truth by assuming decoded ordinal N equals generated ordinal N.

### A4. Native presentation ledger and identity semantics

Stream a versioned JSONL (or equivalently bounded) ledger rather than retaining full video state in memory.

Header records at least:
- source SHA-256 and size;
- selected stream index;
- container and codec;
- stream rational time base;
- pixel format / relevant color metadata;
- container start, stream start, and any decoder/edit-list option state available;
- first decoded presented-frame PTS once known;
- claimed durations separately from observed coverage;
- decoder/toolchain fingerprint.

Per presented frame record:
- presentation ledger ordinal;
- raw PTS or explicit null/unknown reason;
- same-PTS duplicate ordinal when needed;
- best-effort timestamp only if its source/meaning is labelled;
- keyframe and picture type where available;
- dimensions/pixel format;
- primary native-plane digest.

**Checkpoint-A origin default:** first decoded presented-frame PTS. Preserve container start, stream start and other candidate origins separately; never silently rewrite raw PTS to zero. This is the A harness convention, not permission to fabricate timing when PTS is missing.

Canonical known-timing frame identity for A is:
`(source_sha256, selected_stream_index, raw_pts, same_pts_ordinal)`.
`frame_index`/ledger ordinal is a traversal reference tied to that ledger/configuration, not a universal media identity.

Primary decoded-frame digest:
- native decoded image planes;
- strip row padding/line-size slack;
- include width/height/pix_fmt (and plane layout where needed) in the digest domain/header;
- do not make RGB conversion the canonical cross-agent identity.

Converted RGB/crop digests may be secondary and must be labelled toolchain-dependent.

Trailer/report records:
- decoded presented-frame count;
- timing gaps/errors/discontinuities;
- duplicate/non-monotonic/missing PTS;
- last-frame-duration status, including unknown;
- elapsed time;
- process peak RSS (or clearly labelled equivalent method);
- output bytes.

Never derive source time from nominal FPS.

### A5. Truth ↔ decoded timing comparison

Truth is held as exact rational schedule in the generator's own time base.

Comparison rules:
- exact equality where the chosen container time base can represent the scheduled timestamp;
- otherwise use a declared nearest-representable rounding rule;
- require monotonic one-to-one truth↔decoded mapping for the fixture;
- report the rounding bound/error rather than hiding it.

Verify the encoded fixture's timing and frame-ID mapping independently. If generation/muxing duplicates, drops or reorders truth unexpectedly, A fails that fixture rather than redefining the annotations.

### A6. Post-encode event survival

Lossy encoding must not silently erase the event used as ground truth.

For each annotated event frame, compute a detector-independent survival check/metric against generator truth/background:
- easy events must demonstrably survive encoding;
- challenge events report survived/degraded status and metric;
- encode quality/settings are part of the corpus spec.

A later detector miss must be attributable to the detector or an explicitly degraded fixture, not unknown encode destruction.

### A7. Seek-path exact recovery

Sequential decode twice is insufficient.

Implement exact random-access recovery by:
1. seeking to an earlier decodable point/keyframe;
2. decoding forward in presentation order;
3. selecting the target by A's canonical timing identity;
4. failing explicitly if the exact known target PTS/duplicate ordinal is never emitted.

Compare seek-path native-plane digest against the sequential-ledger digest for:
- every annotated event frame;
- first/last recoverable frames;
- frames immediately before keyframes;
- seeded random sample.

The long-GOP/B-frame fixtures are required specifically to exercise this path.

### A8. Lossless oracle truth

At least one lossless variant must allow pixel-exact validation against generator output under a declared representation/conversion. This is separate from the native decoded-plane digest used for encoded-byte identity.

### A9. Safety/error/resource proof

Test:
- source SHA unchanged;
- paths with spaces and Unicode;
- output path identical to source rejected;
- output symlink resolving to source rejected where the test environment supports symlinks;
- corrupt/unsupported input gives explicit failure/partial diagnostic, never false success;
- missing/duplicate/non-monotonic timestamp logic through injected synthetic frame-source/unit cases if real media cannot reliably produce them;
- no-audio input;
- stream selection when audio precedes video;
- bounded/streamed ledger memory.

Generated media must be outside the repo or under an ignored fixture-output directory. Extend `.gitignore` for every media/raw format introduced by A. Keep virtual environments outside the repository.

Do not make future bootstrap CI fail merely because runtime media dependencies are not installed. Runtime-dependent tests must either:
- live in a separately invoked suite, or
- skip explicitly with a visible reason when optional runtime deps are absent.

No workflow edit is part of A.

### A10. One clean-checkout proof entrypoint

Provide one documented command/script that, from a clean checkout and a temporary work directory:
- installs/uses the pinned runtime as documented;
- regenerates the corpus media;
- generates ledgers;
- runs oracle/timing/seek/survival checks;
- runs A tests;
- writes a machine-readable result summary.

Report exact commands and environment.

### A11. Durable reproducibility evidence

Before releasing the A claim, publish:
- exact base/head, branch/PR and how the tree was obtained;
- exact dependency pins/toolchain fingerprint;
- corpus version, specs, committed annotations, dev/held-out seeds;
- canonical annotation/spec digests;
- encoded-file and ledger digests with toolchain context;
- native-plane digests for selected oracle frames;
- per-fixture timing, frame-ID, seek, survival and error results;
- pass/fail/skip counts with every skip reason;
- untested list;
- elapsed time, peak-RSS method and output size;
- next smallest blocker.

Generated fixture media does not need to be committed if clean-checkout regeneration and durable truth/evidence are sufficient.

**Stop after A.** Leave PR DRAFT, release the implementation claim, and wait for CT exact-head review. No regional detector/tracker, production packet/READY writer, OCR, speech, UI, Drive, MCP or later roadmap work.

## Checkpoint B — regional candidates and retained evidence (HELD)

Activate only after CT accepts A and explicitly dispatches B on the same lineage.

B uses A's frozen corpus/identity/extraction path and must evaluate both dev and held-out seeds. Implement inexpensive every-presented-frame regional-change signals, candidate intervals, same-region content changes, reopened occurrences, bounded cache/spool and actual representative evidence.

Easy events must yield a localized candidate/evidence frame; whole-video candidates do not count. Report misses, noise/candidate rate, duration distribution and resources.

**Important pre-build correction:** B's raw signal diagnostics/evaluation output is **not required to conform to the draft 0.1 event schema** if doing so would squash raw signals into [0,1] or fabricate unknown timestamps. C owns the explicit schema evolution.

No OCR or invented semantic labels.

## Checkpoint C — packet integrity and complete Gate B (HELD)

Activate only after B review. Implement production packet writer/validator/evaluator, bounded shards and visible partial/cancelled/failed states.

C owns:
- audit P1–P6/F3 enforcement;
- actual asset bytes/digests and READY/checksum semantics;
- required-stage completion logic;
- frame/PTS-ledger consistency;
- duplicate output paths;
- invalid/path traversal/symlink containment;
- source/output aliasing;
- provenance/schema-version evolution;
- honest unknown timing/input metadata;
- raw-versus-normalized signal representation;
- structured gap ranges / uncertainty representation as needed;
- cross-platform packet-name safety, including case-insensitive/casefold and Unicode-normalization collisions, Windows reserved names and trailing-dot/space hazards;
- cancellation, decoder failure, budget exhaustion, repeatability and full Gate B report.

The prior NUL-path probe remains a valid defensive case but is not by itself the major cross-platform path risk.

Windows execution proof is later; Linux validation must not be reported as Windows support.

## Exclusions for all BS-001 checkpoints

No paid/network/provider calls, credentials, ML/OCR model downloads, semantic/editorial labeling, Tauri UI, Drive upload, MCP, editor automation, proprietary/user footage in git, automatic source uploads, or BS-002 auto-activation. No global event cap or fixed minimum duration silently deleting evidence. No real-time or zero-miss promise.

## Exact-head review packet

The CT dispatches one independent read-only reviewer against the worker's recorded A head.

A reviewer must inspect:
- independence of generator truth and frame-ID channel;
- committed/frozen corpus annotations and held-out seeds;
- native timing/origin/rounding rules;
- B-frame/long-GOP and presentation-order behavior;
- canonical identity and native-plane digest basis;
- seek-back/decode-forward exact recovery;
- post-encode event survival;
- error/source-safety/resource evidence;
- clean-checkout reproducibility.

Return exactly one:
- `ACCEPT_CHECKPOINT_A`
- `NEEDS_FIX`
- `BLOCKED_EVIDENCE`

Acceptance is only checkpoint A. Reviewer does not modify source, create a replacement branch, start B or become CT. Corrections stay on the same worker lineage.

## Ready-to-claim one-shot worker prompt

```text
Act as the ONE bounded BS-001 checkpoint A implementation worker for
bohanyt/b-scout. You are not Control Tower and not a reviewer.

Fresh-read AGENTS.md, CURRENT.md, CT ROLE/PROTOCOL, issue #1, the FULL current
handoff through its end marker, issue #2 and all comments including
BSCOUT-PREBUILD-OPUS-20260924-V1, and
docs/tasks/BS-001-native-frame-baseline.md with its linked architecture,
acceptance, packet and audit docs.

Fresh-check main, claims, branches and PRs. Claim checkpoint A in issue #2
before any source write. Use/reuse only agent/bs-001-native-frame-baseline and
one DRAFT PR. Corrections stay there.

Implement ONLY the active checkpoint A exactly as the current task packet
defines it: committed corpus-v1 truth + dev/held-out seeds, independent
per-frame ID channel, pinned/provenanced decoder harness, presentation-order
native PTS ledger, defined origin/rounding/identity/digest semantics,
post-encode survival checks, realistic B-frame/long-GOP seek-path exact
recovery, lossless truth variant, source/error/resource safety, and one
clean-checkout proof entrypoint.

PyAV is the recommended initial decoder harness, not an unreviewable mandate:
fresh-verify a compatible exact version and its wheel/native-library/license
provenance, then pin what you actually tested.

Run proof in your own temporary compute environment. Do NOT run/rerun GitHub
Actions or edit workflows/settings. Use applicable [skip ci] commits and
verify no workflow run starts. Generated media stays disposable/ignored;
durable truth, source, tests, commands and evidence live in GitHub.

Stop after A. Do not implement the regional detector, production packet/READY,
OCR, Groq, UI, Drive, MCP, B/C or later milestones. Publish exact base/head,
DRAFT PR, toolchain fingerprint, fixture/truth digests, per-fixture results,
pass/fail/skips, untested items, resource method and next blocker; release the
issue claim and return the result to the CT. No merge/release authority.
```

## Completion record

Each checkpoint reports exact base/head, branch/PR, changed files, dependency provenance, environment, commands/results, fixture seeds/digests, failures/skips/untested behavior, performance/memory method and next smallest blocker. The CT decides progression and maintains canonical state.

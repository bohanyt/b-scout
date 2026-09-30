# BS-001 A R2 — source-bound exact-recovery correction

Key: `BSCOUT-BS001-A-R2-SOURCE-BOUND-20260930-V1`
CT: BSCOUT-CT-20260930-B. Status: **DESIGN SELECTED / READY TO CLAIM; NOT IMPLEMENTED OR ACCEPTED**.
Lineage: Issue #2, agent/bs-001-native-frame-baseline, existing DRAFT PR #3 only.

## 1. Authority, inputs and provenance

This is CT's bounded operational correction packet. It supplements the [parent A/B/C acceptance packet](BS-001-native-frame-baseline.md); it supersedes old initial-implementation dispatch wording, not the parent correctness requirements. A remains NEEDS_FIX; B/C remain HELD.

Before claiming, fresh-read AGENTS, CURRENT, CT ROLE/PROTOCOL, Issue #1/current comments, the full current handoff selected by CURRENT, Issue #2/ALL comments, parent packet, this FULL packet, ARCHITECTURE, ACCEPTANCE, PACKET_SPEC, PRIVACY, ROADMAP and the bootstrap-readiness audit. Fresh-check branches/PRs/claims/exact heads.

Required receipts in Issue #2: 5902916741 (original failure), 5902991245 (R1 dispatch), 5903455800 (R1 completion), 5903471324 (rereview dispatch), 5903733062 (remaining source-bound safety failure). Reviewed pre-R2 head: ce4ef9c4fa574fd34f95154b7a555eb4bc80f332. Main before this coordination publication: e35e3e6a6990a96e7c3efd2c0a23da24a5630c2b. Use fresh refs, never reset valid implementation to that older main.

The owner supplied an Opus read-only design consultation at this head. Received source SHA-256: 1e10bdcf12144e007f532a96ba504f09095e3b225a7f0c7b233556186ebd0fdb. It reported a clean tree and no changes; it fully read the decisive receipts but only portions/headers of older comments. Several pasted sentences, seek checks and API fragments were truncated. Its recommendations are advisory design input, not acceptance, executed new proof or a complete verbatim specification. Sections below are CT's explicit operational decisions; do not infer missing consultant prose.

## 2. Accepted problem and invariant

Source traversal [0,100,20,50,100], identical pixels for the two 100 frames. An imported ledger can omit the earlier 100, reindex [0,20,50,100], keep the true source SHA and declare complete/zero anomalies. R1 validates that file's internal consistency, not its completeness against the source. API and CLI can still return the later occurrence as global ordinal zero (5903733062).

Canonical known-time identity remains (source_sha256, selected_stream_index, raw_pts, same_pts_ordinal). Matching pixels are not occurrence identity. The core must establish source-wide timing safety under a fixed decoder configuration, rather than trust caller JSON to establish it.

## 3. Selected architecture and trust boundary

Build one core-owned **ValidatedTraversal (VT)** by sequentially decoding the actual source to EOF including decoder flush. Reuse it for subsequent real backward-seek/decode-forward recovery within the same process. An imported ledger is a strict cross-check only; it can cause rejection but cannot grant trusted state.

Use one immutable DecodeConfig for validation and recovery. Bind resolved stream index, demux/edit-list options, software decoder/thread/error settings, native toolchain fingerprint, ledger/projection version and native digest-domain version. Preserve current pinned software settings; no hwaccel.

Core code, pinned decoder and same-process execution are the trusted computing base. Plain dicts, headers, deserialized objects, caller SQLite files or Boolean validated flags cannot construct a valid VT through the public API. Reject wrong/stale/closed objects. A Python class is not cryptographic protection against arbitrary malicious code already executing in the process; do not claim otherwise.

Use a fresh core-owned temporary SQLite table or equivalent bounded disk-backed table, with lifecycle cleanup, for position, raw PTS, global duplicate ordinal, time base, key flag, dimensions/pixel format/native digest domain/digest. Keep source paths private. Do not retain decoded full-video arrays or unbounded Python row/key lists. No imported trusted index, persisted authenticated cache, MAC, key management, provider or network service in A.

## 4. Validation and completeness

The validation loop owns source SHA/size checks, resolves the selected stream using DecodeConfig, consumes actual presented frames through demux EOF and decoder flush, records every entry from that decode, and computes timing classification from those entries. Exceptions, corrupt packets/frames, incomplete decode or detected source changes cannot produce a recoverable complete VT.

Hash source before and after validation. Native observed container frame counts may corroborate completeness: disagreement is diagnostic; absent/zero metadata is explicitly unavailable, not invented and not a mandatory failure. Caller-declared counts are never proof. Completeness is relative to the supplied bytes and trusted decoder/config, not a claim that those bytes contain an entire original recording.

A supports exact seek recovery only when the complete observed traversal has known, unique, strictly increasing PTS and compatible time bases. Missing/duplicate/non-monotonic timing anywhere, even after the requested target, makes exact seek recovery unsupported for the source. Preserve diagnostic ledger rows/global occurrence data; do not fabricate or erase observations merely because recovery is unsupported.

Hash checkpoints detect observed changes but do not establish an immutable snapshot against an adversary who modifies and restores bytes between checks. Document stable read-only local source / trusted OS-process assumptions; do not promise race-free concurrent-source editing. A snapshot/locking subsystem is not authorized here.

## 5. Imported ledger comparison and API migration

Suggested shape (names may vary, semantics may not):

    validate_traversal(source, config, ledger_out=optional_path) -> VT
    compare_ledger(vt, ledger_path) -> success or explicit failure
    recover(source, vt, requested_identity) -> frame plus verified proof

Remove caller header/keyframe/target-digest dictionaries as recovery authority. Resolve target position, digest, time base, first PTS and anchor solely from VT. Caller supplies only identity/selection requests and optional cross-check expectations. A compatibility wrapper must perform the same validation, never revive the old trust path.

Compare an imported ledger against a versioned canonical **semantic projection** of the entire VT: source/stream/config/version/domain, ordered frame position/PTS/ordinal/time-base/key/dimensions/format/native digest, and observed completion/count/timing facts. Reject missing/reindexed/reordered/extra rows, wrong digests, foreign or stale config/stream/source and forged completion data, even if the requested row itself is genuine. Compare to core-observed data, not only to another caller-supplied hash.

Do not require byte-equality of elapsed time, RSS, timestamps or other documented run-local telemetry. Those fields never grant trust. Define required fields/metadata policy and test it. Version changed semantics explicitly; legacy files may remain diagnostic-readable but must not silently gain recovery authority when binding data is absent. Preserve historical files and document any recovery compatibility rejection.

Keep existing CLI usage where practical, including --ledger as a cross-check rather than authority. Both CLI and oracle must call the same validated core. The oracle should use VT from its source/ledger pass, not reload JSON as trusted state.

## 6. Recovery checks and output boundary (CT operational specification)

Before seeking: require a live complete/safe VT; verify source hash and configuration binding; resolve requested identity to a VT entry; reject absent identities or unsupported nonzero occurrence ordinals in A; finish any supplied ledger comparison. Choose anchor and rational seek rescaling from VT, never nominal FPS or caller keys.

Open for seeking with the same resolved config. Perform real backward keyframe seek then presentation-order decode-forward. The first emitted frame must map to a VT entry at or before the target. Each later emitted entry must be the next contiguous VT position through the target. Compare actual PTS/time base, native representation/domain/digest and required identity fields against those VT entries. Fail for unknown/non-increasing PTS, unexpected gaps/repeats, overshoot, corruption, representation/digest mismatch, exceptions or EOF before the target. Unusual open-GOP sources may fail closed; do not relax contiguity merely to pass a fixture.

The proof identity and selected digest come from VT, with source/config/projection identity, target position and seek evidence recorded. Distinguish target absent in VT (pre-seek) from target present but never emitted (seek-path failure).

Perform post-recovery source checks before returning a successful result or publishing CLI output. For an optional explicit batch, withhold success/publication until its post-check; do not return supposedly final frames before validation is complete. No frame-history fallback replacing seek proof. Failed recovery must not create a successful output artifact: exit nonzero (CLI 2), public-safe diagnostic, no new final output; preserve existing files/source. Cleanup only newly owned temporary files. Diagnostic ledger outputs remain allowed under the parent contract.

## 7. Regression matrix — mandatory

Use a coherent fake-media seam at the media-open/container boundary. Validation sees the complete synthetic traversal; seek sees the suffix selected by the fake seek operation. Use real native frames where appropriate. Do not patch validation/comparison/identity/digest routines to return success or feed only a suffix into the supposed validation pass. Label injected evidence honestly.

Test API and CLI where applicable:

1. Complete [0,100,20,50,100] with identical pixels: rejected before recovery seek. Opening source for validation is now expected; old av.open-not-called assertions must not block the correct design.
2. Same actual source with shortened/reindexed [0,20,50,100], correct source SHA and forged complete trailer: no false identity, exit 2, no recovery output. This must close both direct API and CLI attack paths from 5903733062.
3. On a safe source [0,100,200], remove middle/tail rows and fix counts; insert/reorder rows; change key flags/ordinal/time base/native digest/domain; forge trailer state. Imported ledgers reject against actual traversal.
4. Foreign SHA/stream; same SHA with stale decoder config/version/domain; validation/recovery configuration mismatch; unverified legacy ledger. Reject without silently substituting a different source/stream/config.
5. Duplicate/non-monotonic/missing PTS before or after target; non-adjacent identical-pixel occurrences; zero/unavailable actual container count and contradictory available count.
6. Plain dict/header/Boolean/caller-authored table passed as VT; closed or invalidated VT; legacy direct API bypass; absent target versus unsupported occurrence ordinal.
7. Source mutation after validation or during validation/recovery: detected failure and no successful output. Test the implemented hash checkpoints without claiming protection from undetectable modify-and-restore races.
8. Seek output with dropped/extra/noncontiguous frames, overshoot, wrong time base, corruption, wrong digest, and EOF without target. Separate absent-in-VT and missing-after-seek failures.
9. Valid imported ledger and normal no-forgery VT path: successful real seek recovery remains supported. Source/output alias/Unicode/error protections remain.
10. Full frozen corpus: preserve 3,360 independent mappings, 2,880 supported exact recoveries and 480 lossless comparisons under the pinned baseline. One validation traversal per fixture, reused for its recoveries, not one full decode per target.

Add bounded resource/lifecycle checks for the new VT table and lookup/anchor path, not only the old Timing counter. Keep accepted raw-H264 unknown-timing and environment-dependent symlink limitations explicit. Do not remove skips by inventing support.

## 8. Performance and scope decisions

Correctness first, but validate once/recover many within each fixture/process is required. A standalone CLI process may need an O(N) validation decode; disclose that cost. No claimed long-video/1440p throughput or guaranteed speedup without measurement. Any future B scan reuse, batched segment optimization or authenticated persisted cache is a proposal for later CT sequencing, not permission to implement B/C now.

Allowed changes: ledger/recovery core, CLI/oracle integration, necessary tightly related helper/config module, tests, bounded proof-harness adaptations, docs/BS001_A.md, new R2 evidence and historical pointer banners. Refactor the affected boundary as a whole; do not implement only another special-case consistency check. Preserve frozen corpus/generator and dependency pins unless a concrete necessary blocker is documented to CT. No broad package rewrite or unrelated cleanups.

## 9. Proof and digest accounting

Reproduce decisive attacks/focused tests first, then full suite and complete clean-checkout proof using a fresh external workspace/env/media. Persist exact base, tested and final heads, commands, clean-tree evidence, updated requirement matrix, machine-readable per-fixture/regression/resource results, all skips and remaining limitations. Do not reuse old 70/0/3 as R2 proof.

T1 corpus/spec/annotations/seeds/schedules must remain unchanged. T2 native-frame/identity equality is required for identical encoded bytes under the declared baseline. Same-toolchain encoded-media hashes should remain unchanged with untouched generation. **Do not demand all T3 or whole-report bytes unchanged:** ledger versions/config-binding fields, seek proof metadata, elapsed/RSS and report shape can legitimately change. Publish new hashes and explain semantic comparisons. This clarifies the consultation's abbreviated 'T1/T2/T3 unchanged' line; it is not permission for unexplained truth or pixel drift.

Keep pre-fix and R1 evidence intact; add docs/evidence/BS-001-A-R2/. Banners may mark old reports historical. New proof fields and ledger schema/projection versions need explicit provenance and compatibility tests. Complete source/truth invariants still apply; internal subreviews are not independent acceptance.

## 10. Worker authority, claim and local execution

One local Sol 6.1 High lead; Fast allowed. Same-model/same-effort subagents allowed; never silently route to another model. If that cannot be controlled, work without subagents. Isolate non-overlapping edits and keep one integrating owner. No extra remote branch/PR.

Post one R2 claim in Issue #2 before source writes: exact current main and implementation head, existing PR #3, model/subagent configuration, this packet key, scope/exclusions and proof. Preserve dirty/unrelated local work; use safe worktrees or clean clones without deleting others. Do not claim stale 5806413667 again; it and subsequent finished claims are historical/released.

Fetch/read fresh main authority. If main is ahead only in CT documentation, a normal non-force merge into the existing implementation branch before source work is authorized, using [skip ci]; preserve both histories. Never reset the implemented branch to main. Stop/reconcile unexpected competing changes or active ownership rather than overwrite.

## 11. Safety, completion and review

No GitHub Actions dispatch/rerun, workflow/settings workaround, paid/provider/model scope or user/private media. Use local proof and [skip ci] on every pushed commit, including any coordination merge. Query Actions by each newly pushed head without event filter; report zero runs or the actual result, never skipped-as-success. No credentials/private paths/links in public evidence.

Leave PR #3 open DRAFT/unmerged. Update its description to R2 evidence, then publish one Issue #2 completion with exact heads/delta, design invariants, both reproduced attacks now rejected, new proof counts, digest-tier comparisons, resource/lifecycle cost, limitations and no-Actions verification. RELEASE claim and STOP. No ACCEPT_CHECKPOINT_A self-verdict, B/C work, merge, release or CT self-promotion.

Next gate: one independent exact-head R2 rereviewer, with fresh code/attack tests and source-bound trust model inspection. Opus may fill that role in a fresh separate session, but this design consultation is not that review. CT alone records progression from accepted evidence.

## 12. Terminal condition

R2 is ready for independent review only when source/configuration-bound traversal authority replaces caller-ledger authority throughout core/CLI/oracle, the two demonstrated identity attacks and adjacent matrix cases are tested, supported seek evidence remains genuine, and fresh durable exact-head proof is published. A remains unaccepted until the subsequent independent gate. B/C remain HELD.

END_OF_BSCOUT_R2_PACKET key=BSCOUT-BS001-A-R2-SOURCE-BOUND-20260930-V1 sections=12

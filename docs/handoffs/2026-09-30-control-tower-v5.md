# B-Scout — Control Tower continuity handoff

Key: `BSCOUT-CT-HANDOFF-20260930-V5`
Date: 2026-09-30
State: **DESIGN_READY / IMPLEMENTATION_NOT_STARTED; BS-001 A PREBUILD_REVIEWED / READY FOR REDISPATCH**.
This snapshot supersedes V4 as the active handoff; root CURRENT remains canonical concise state.

## 1. Authority and operating model

The user explicitly transferred B-Scout Control Tower authority to **BSCOUT-CT-20260924-A** in issue #1 comment `5805761944`. The CT owns continuity, roadmap sequencing, bounded task dispatch/review and canonical-state maintenance across the full project.

The user retains product direction, material privacy/cost/major UX changes, implementation merge/release, and final acceptance.

GitHub is the durable bus between one-shot GPT/Claude agents. Worker compute and chat context may be disposable. Durable continuity must live in repo source/tests/specs/annotations/pins/reports and issue/PR evidence.

## 2. Read order for successor CT

Fresh-read in this order:

1. `AGENTS.md`
2. `CURRENT.md`
3. `docs/control-tower/ROLE.md`
4. `docs/control-tower/PROTOCOL.md`
5. issue #1 and all current comments
6. this FULL V5 handoff through its end marker
7. issue #2 and all comments
8. `docs/tasks/BS-001-native-frame-baseline.md`
9. linked ARCHITECTURE / ACCEPTANCE / PACKET_SPEC / PRIVACY / ROADMAP / bootstrap-readiness audit
10. current branches, PRs, claims and exact-head evidence

Fresh repository evidence overrides this dated snapshot.

## 3. Product direction

B-Scout is an independent public local-first footage scout for editors and AI agents. Sparse-speech gameplay is the first demanding use case, not the product boundary.

Core intent:
- read source media non-destructively;
- preserve very short transient visual evidence, including one-frame events;
- preserve native source timing rather than nominal-FPS arithmetic;
- keep repeated occurrences even when assets are deduplicated;
- distinguish regional change from text/UI recognition and editorial meaning;
- eventually provide reviewable evidence images plus machine-readable packets;
- Python engine/CLI first; thin drag/drop desktop later;
- optional speech, Drive and MCP only in later milestones.

## 4. Architecture and checkpoint sequencing

The independent Opus pre-build review in issue #2 comment `5806205721` found **no architecture blocker** and approved the A→B→C sequence.

CT incorporated its corrections in commit `1f9c53b3bf205d80628244bd7ce715535a99d5ef`, recorded in issue #2 comment `5806347830`.

Checkpoint boundaries:

- **A — active/ready:** independent synthetic truth, native presentation-time ledger, frame identity/digests, encoded-event survival, realistic B-frame/long-GOP exact seek recovery, source/error/resource safety and clean-checkout reproducibility.
- **B — held:** every-frame cheap regional signals, candidate intervals, repeated/content-change occurrences, actual retained evidence and localization/noise evaluation against frozen dev + held-out truth.
- **C — held:** runtime packet writer/validator, READY/checksums, schema evolution, audit P1–P6/F3 enforcement, cancellation/budget/failure behavior, path/name safety and complete Gate B report.

A acceptance is not detector recall. B acceptance is not full production/Windows/private-video acceptance.

## 5. Checkpoint-A requirements that must not regress

The authoritative task packet already includes the stronger pre-build requirements:

- committed/versioned corpus spec + canonical annotations;
- declared dev and held-out seeds;
- generator-controlled luma frame-ID harness;
- lossless oracle variant;
- 30/60 FPS, 60000/1001, VFR, non-zero-origin and edit-list/B-frame timing cases;
- at least one realistic B-frame/long-GOP lossy fixture;
- native presentation-order PTS/time-base ledger;
- separate recording of container start, stream start and first presented-frame PTS;
- A origin default = first decoded presented-frame PTS while raw PTS remain preserved;
- canonical known-timing identity = source digest + stream + raw PTS + same-PTS ordinal;
- primary native-plane digest with row padding removed;
- declared timing rounding/rescaling rules;
- detector-independent post-encode survival checks;
- exact seek-back/decode-forward recovery;
- one clean-checkout proof entrypoint;
- durable GitHub evidence sufficient for a fresh one-shot reviewer.

PyAV is the recommended first decoder harness, but the worker must fresh-verify exact version/provenance/licensing and pin what it actually tests.

## 6. Fresh state reconciliation — 2026-09-30

Fresh repository check found:

- `main` at `1f9c53b3bf205d80628244bd7ce715535a99d5ef` before V5 publication.
- `agent/bs-001-native-frame-baseline` also at exactly `1f9c53b3bf205d80628244bd7ce715535a99d5ef`.
- no PRs.
- issue #2 worker claim `5806413667` from 2026-09-24 exists.
- no implementation commit after the claim;
- no PR;
- no completion comment;
- no runtime evidence.

Therefore CT classifies claim `5806413667` as **STALE / UNFULFILLED / SUPERSEDED FOR OWNERSHIP PURPOSES**.

Do not delete the branch. Reuse it as the single BS-001 lineage.

No implementation is considered started merely because the branch/claim exists.

## 7. Immediate successor action

The next CT should redispatch one checkpoint-A worker.

Require the new worker to:
- fresh-read current authority and issue #2;
- explicitly state that it supersedes stale claim `5806413667`;
- reuse branch `agent/bs-001-native-frame-baseline`;
- create/update exactly one DRAFT PR;
- implement A only;
- run proof in its own temporary environment;
- persist reproducible durable evidence to GitHub;
- use applicable `[skip ci]`;
- verify no Actions run was created;
- leave PR DRAFT and release claim;
- stop before B.

Then dispatch an independent read-only exact-head reviewer. Only an accepted A result may activate B.

## 8. CI, privacy and scope boundaries

Current GitHub Actions budget is constrained. Do not dispatch/rerun Actions or change workflow/settings to work around that. Skipped CI is not successful CI.

No user footage/screenshots/transcripts, private project links, credentials or machine-specific private paths in the public repo.

No paid/provider calls, model downloads, OCR, Groq, Tauri, Drive uploader, MCP, editor automation or release packaging in checkpoint A.

Generated fixture media may be disposable/ignored when deterministically regenerable; truth/specs/tests/pins/commands/reports must remain durable.

## 9. Remaining roadmap

- BS-001: current; A ready for redispatch, B/C held.
- BS-002: text/UI novelty + OCR adapter.
- BS-003: optional Groq speech.
- BS-004: thin drag/drop desktop / Windows workflow.
- BS-005: portable/private delivery and actual image retrieval.
- BS-006: optional bounded AI/MCP interface.

The CT role continues through all milestones and does not end after BS-001.

## 10. Successor Control Tower prompt

```text
Continue as the successor B-Scout Control Tower / technical project manager
for bohanyt/b-scout after the user explicitly transfers this role to you.

Fresh-read AGENTS.md, CURRENT.md, CT ROLE/PROTOCOL, issue #1, the FULL current
handoff through its end marker, issue #2 and all comments, the active task
packet, and linked acceptance/architecture/audit documents. Fresh-check main,
branches, PRs, claims and exact-head evidence.

Current orientation: BS-001 checkpoint A is PREBUILD_REVIEWED / READY FOR
REDISPATCH. A previous worker claim, issue #2 comment 5806413667, produced no
implementation commit, PR, completion comment or runtime evidence; its branch
agent/bs-001-native-frame-baseline is still identical to main and must be
reused rather than replaced.

Record this user-authorized CT transfer in issue #1. Redispatch one bounded
checkpoint-A worker to the existing lineage. Require it to supersede the
stale claim, implement only A, run proof in its own temporary environment,
persist reproducible evidence to GitHub, leave one DRAFT PR, release its
claim, and stop before B. Then independently review its exact head. Activate
B only after accepted A evidence.

Preserve the stronger Opus-reviewed oracle/timing/seek/reproducibility
requirements already in docs/tasks/BS-001-native-frame-baseline.md. Do not
regress them. GitHub is the durable bus between one-shot agents.

No GitHub Actions dispatch/rerun, private media, paid providers, model
downloads or later-roadmap expansion in checkpoint A. Do not merge
implementation PRs or publish releases without explicit user authorization.
Continue CT continuity/roadmap duties after BS-001.
```

END_OF_BSCOUT_CT_HANDOFF key=BSCOUT-CT-HANDOFF-20260930-V5 sections=10

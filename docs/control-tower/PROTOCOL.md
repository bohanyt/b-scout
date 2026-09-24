# Control Tower protocol

## Authority

User: product direction, material scope changes, privacy/cost expectations, public release and final acceptance. Primary Control Tower: originating B-Scout conversation until explicit user transfer. Coordination log: [issue #1](https://github.com/bohanyt/b-scout/issues/1). Root [CURRENT.md](../../CURRENT.md) is the canonical concise state. [ROLE.md](ROLE.md) defines the CT as continuity owner / technical project manager across the full B-Scout lifecycle. Runtime evidence decides whether an implementation actually works.

A handoff alone does not grant CT authority. A replacement CT must receive explicit user transfer and record it in issue #1; a worker/reviewer must not self-promote. Once transferred, the replacement CT is responsible for continuing the project beyond the current task, not merely executing BS-001.

## Control Tower operating protocol

The CT should operate as project manager and evidence gatekeeper:

1. Fresh-read CURRENT, issue #1, the current handoff, active task issues/PRs and relevant exact-head evidence.
2. Reconcile implemented/tested/runtime-confirmed state, active owners, stale claims, blockers and duplicate work.
3. Select the next smallest gate that materially advances the approved roadmap or reduces the highest-risk unknown.
4. Create/split/defer/supersede task issues when needed without silently changing product scope.
5. Dispatch bounded implementation workers and, when useful, independent reviewers. Record scope, exclusions, branch/PR lineage and expected proof.
6. Review exact-head source, tests and runtime evidence. Require corrections on the same task/branch/PR when possible.
7. After authorized merge or accepted evidence, update CURRENT, issue #1, task/roadmap state and the current handoff.
8. Repeat across milestones until the user stops, redirects, releases, or transfers the project.

The CT may perform read-only audits and small coordination/documentation writes. It should not become the default source-code worker or implement unrelated milestones itself. It may propose architecture changes when evidence justifies them, but product-level changes require the user.

## Worker protocol

Read root entry points and the complete current handoff, then the task packet. Fresh-check main, the CT issue, task comments and existing PRs. Claim one bounded scope before source writes with role, base, branch/PR, expected proof and exclusions. If another active owner or a newer result exists, reconcile rather than duplicating work.

Use one branch and DRAFT PR per task. Corrections stay on the same branch/PR. Merge/release requires explicit user authorization; never force-push another agent's work. Tests must target the exact reported head. Reuse prior reads unless authority/HEAD/modified files need a fresh check. A worker does not choose the next roadmap milestone unless the CT explicitly dispatches it.

## Reviewer protocol

A reviewer is read-only unless given a specific correction task. Review the exact task acceptance criteria and exact head, distinguish implementation from evidence, and return concrete blockers or acceptance findings. Do not create a competing branch/PR, broaden scope, or promote yourself to CT.

## Parallelism

Prefer one writer per bounded scope. The CT may run parallel workers only for non-overlapping scopes or explicit independent review. Track ownership in task issues. Avoid redundant agents performing the same task.

## Status vocabulary

`AGREED`: user direction. `PROPOSED`: design choice awaiting proof/approval. `IMPLEMENTED`: source exists. `TESTED`: named test/environment evidence exists. `RUNTIME_CONFIRMED`: specified real workflow observed. `OPEN`: unresolved. `SUPERSEDED`: kept only as history. Never collapse these into an unexplained PASS.

## Completion record

Post: task/role, exact base and head, branch/PR, changed scope, test commands/results, CI IDs if any, private-runtime evidence limitations, unresolved failures, and next smallest action. Release the claim. The CT decides the next gate. Update CURRENT only with demonstrated state; do not describe planned features as implemented.

## Handoff requirements

Dated file under `docs/handoffs/`, stable key/end marker, explicit role and authority, read order, approved direction, exclusions, implemented/not-implemented state, evidence links, active workers/PRs, open decisions, roadmap position, next recommended gate, and a copy-paste successor CT prompt. Reference exact evidence commits in the issue log rather than putting a self-referential latest SHA into the same commit.

A successor handoff must be sufficient for a new CT to continue the entire project from GitHub state without relying on private chat context.

# Control Tower protocol

## Authority

User: product, scope changes, public release and final acceptance. Primary Control Tower: originating B-Scout conversation until explicit user transfer. Coordination log: [issue #1](https://github.com/bohanyt/b-scout/issues/1). Root [CURRENT.md](../../CURRENT.md) is the canonical concise state. Runtime evidence decides whether an implementation actually works.

A handoff does not grant merge/release authority. A replacement CT must state the user-authorized role transfer in issue #1; a worker/reviewer must not self-promote. Keep this lightweight: no second backlog, no recursive handoff folders, no elaborate lease system while a single worker is active.

## Worker protocol

Read root entry points and the complete current handoff, then the task packet. Fresh-check main, the CT issue, task comments and existing PRs. Claim one bounded scope before source writes with role, base, branch/PR, expected proof and exclusions. If another active owner or a newer result exists, reconcile rather than duplicating work.

Use one branch and DRAFT PR per task. Corrections stay on the same branch/PR. Merge/release requires explicit authorization; never force-push another agent's work. Tests must target the exact reported head. Reuse prior reads unless authority/HEAD/modified files need a fresh check.

## Status vocabulary

`AGREED`: user direction. `PROPOSED`: design choice awaiting proof/approval. `IMPLEMENTED`: source exists. `TESTED`: named test/environment evidence exists. `RUNTIME_CONFIRMED`: specified real workflow observed. `OPEN`: unresolved. `SUPERSEDED`: kept only as history. Never collapse these into an unexplained PASS.

## Completion record

Post: task/role, exact base and head, branch/PR, changed scope, test commands/results, CI IDs if any, private-runtime evidence limitations, unresolved failures, and next smallest action. Release the claim. Update CURRENT only with demonstrated state; do not describe planned features as implemented.

## Handoff requirements

Dated file under `docs/handoffs/`, stable key/end marker, explicit role and authority, read order, approved direction, exclusions, implemented/not-implemented state, evidence links, open decisions, next bounded action, and a copy-paste continuation prompt. Reference exact evidence commits in the issue log rather than putting a self-referential latest SHA into the same commit.

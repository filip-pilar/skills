---
name: gitprep
description: Inspect repository and publication state, plan coherent commits, and create only user-approved commits without pushing.
---

# Gitprep

A bare `$gitprep` requests inspection and a commit plan only. Staging and
committing require approval for the complete plan unless already authorized.
Preserve unrelated work; do not pull, merge, rebase, or push during this workflow.

## Inspect and plan

Inspect staged and unstaged diffs separately, repository commit conventions,
and branch/upstream state. Report aligned, ahead, behind, diverged, or no upstream,
including local commits ahead. `@{u}` is locally recorded state, not fresh proof
of publication; a clean worktree does not establish publication either. If
nothing is committable, report the state and stop.

When fresh remote evidence matters, prefer supported read-only GitHub app
operations, otherwise authenticated `gh`; disclose material gaps.

Group changes by intent, splitting only for useful review or rollback. Present
exact files or hunks, proposed imperative messages following repository conventions,
useful split rationale, material risks, upstream state, and relevant verification.
Check adjacent documentation and misplaced local output; propose justified cleanup
in the plan rather than performing it during inspection.

## Execute authorized work

Run checks required by the repository and affected behavior, reusing applicable
results. Broaden or repeat only for changes or unresolved concerns. Complete safe,
already-authorized checks before requesting remaining approval; checks requiring
new authority, material cost, or consequential external effects need authorization.

Carry approved checks and commits through without routine checkpoints. Diagnose
failures and make only already-authorized repairs; a commit-only request does not
authorize code repairs. Do not commit with failing checks without explicit permission.

Stage only approved paths or hunks, using non-interactive partial staging where
needed; ask if selection is materially ambiguous. Inspect the full staged diff and
worktree before each commit. Preserve approved intent and explicitly fixed messages.
Routine wording refinements and safe retries within scope need no renewed approval;
verify whether a commit succeeded before retrying. Added scope, history rewrites,
hook bypasses, or changes to explicit user choices require new authority.

Finish when approved commits exist and relevant checks are resolved, or report a
concrete impediment and needed action. Include hashes and messages, checks and skips,
remaining work, and upstream state with its freshness limits.

## Separate publication request

Gitprep never pushes. Only for a separate publication request after preparation,
read [publication guidance](references/publication.md) for that authorized follow-up.

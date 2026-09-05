---
name: gitprep
description: Inspect repository and publication state, plan coherent commits, and create only user-approved commits without pushing.
---

# Gitprep

A bare `$gitprep` requests inspection and a commit plan only. Before staging or
committing, obtain approval for the complete plan unless the user has already
authorized that scope. Preserve unrelated work; never silently stage, revert,
delete, or rewrite it. Do not pull, merge, rebase, or push during this workflow.

## Inspect and plan

Use `git` to establish working-tree and index changes, the current branch and
upstream relationship, and relevant commit conventions. Inspect staged and
unstaged diffs separately, focusing on relevant files or hunks for large changes.
Report whether the branch is aligned, ahead, behind, diverged, or has no upstream,
and identify local commits ahead of it. Comparisons with `@{u}` describe the
locally recorded upstream; without fresh remote evidence, do not claim they
establish current publication state. A clean working tree does not imply that
all commits are published. If nothing is committable, report that state and stop.

When remote evidence materially helps, prefer the connected GitHub app for
supported read-only operations, otherwise authenticated `gh`. Skip irrelevant or
unavailable remote context and state any material uncertainty.

Group changes by intent, splitting only when it improves review or rollback.
Flag material hazards such as unrelated work, secrets, accidental deletions,
partial changes, or inconsistent generated artifacts. Check changed or adjacent
files for relevant documentation drift and misplaced local output; include any
justified cleanup in the plan rather than performing it during inspection.

Present the exact files or hunks, proposed messages, split rationale when useful,
material risks, upstream state, and relevant verification. Follow repository
message conventions and describe the actual change with an imperative subject.

## Execute authorized work

Choose checks from repository guidance and the changed behavior. Reuse applicable
results; do not repeat or broaden checks without changes or unresolved concerns.
Trivial changes need no extra checks unless repository conventions require them.
Complete safe checks already authorized by context before requesting any remaining
approval. Ask only when a check needs new authority, material cost, or consequential
external effects; a tool category alone does not require renewed permission.

After plan approval, complete the authorized checks and commits without pausing
for routine execution details. If a check fails, diagnose it and perform repairs
already authorized by the conversation, then rerun affected checks. A commit-only
request does not authorize code repairs. Do not commit with failing checks unless
the user explicitly permits it; report any unresolved failure and needed action.

Stage only approved paths or hunks and inspect the full staged diff and working
tree before each commit. Use reliable non-interactive partial staging or ask if
selection is materially ambiguous. Follow the actual host permission rules;
request escalation only when needed and supported.

Preserve approved intent and explicitly fixed messages. Routine wording refinements
or safe retries that preserve scope need no renewed approval; verify whether a
commit succeeded before retrying it. Obtain new authority for added scope, history
rewrites, hook bypasses, or changes to explicit user choices.

Report commit hashes and messages, checks and skipped checks, remaining work, and
the upstream relationship with its freshness limits. Completion means the approved
commits exist and relevant checks are resolved, or a concrete impediment is reported.

## Separate publication request

Gitprep never pushes. Only when the user separately requests publication after
commit preparation, read [publication guidance](references/publication.md) for
that authorized follow-up.

---
name: gitprep
description: Inspect changes and plan coherent commits; create commits when authorized, without pushing.
---

# Gitprep

A bare `$gitprep` requests inspection and a commit plan. Stage and commit only
within already-authorized scope or after approval of the plan. Do not pull,
merge, rebase, or push as part of preparation.

Inspect staged and unstaged changes, repository commit conventions, and
branch/upstream state. Group changes by useful review or rollback boundaries.
Propose exact files or hunks, commit messages, and any material cleanup or risks;
inspection alone does not authorize edits. Report existing unpublished commits
as well as uncommitted changes. Local upstream refs may be stale; use fresh
remote evidence when publication status matters.

For authorized commits, verify that the full staged diff matches the approved
scope, including previously staged work. Run applicable repository checks,
reusing current results. Preserve unrelated changes and explicitly fixed messages;
report failed checks without bypassing them. Inspect the result before retrying
an uncertain commit.

When publication is also authorized, push the requested branch with local Git
and verify the remote commit. Inspect an uncertain push before retrying;
force-pushes and history rewrites require explicit authorization.

Report commit hashes, verification results, and remaining work or blockers.

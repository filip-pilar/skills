---
name: gitprep
description: Inspect repository and publication state, plan coherent commits, and create only user-approved commits without pushing.
---

# Gitprep

Treat a bare `$gitprep` invocation as a complete request to inspect and propose a commit plan, not to mutate the repository. Preserve all user work: never revert, delete, rewrite, or silently stage unrelated changes. Keep GitHub state read-only unless the user separately requests an action, and never push during this workflow.

Use `git` for local repository operations. When read-only GitHub context materially clarifies the plan or verification state, prefer the connected GitHub app when it supports the needed operation; otherwise use authenticated `gh`. Skip remote context when irrelevant or unavailable, and prefer either supported route to raw HTTP.

## Workflow

1. **Inspect read-only state.** Run `git status --short`, `git status -sb`, `git branch --show-current`, `git branch -vv`, `git remote -v`, staged and unstaged diff statistics, and recent commit subjects when useful. Inspect staged and unstaged diffs separately; for large changes, read focused files or hunks instead of dumping everything.

   If an upstream exists, inspect `@{u}..HEAD` and `HEAD..@{u}`. Report whether the branch is aligned, ahead, behind, diverged, or has no upstream; list unpublished local commit subjects when ahead. A clean working tree does not imply a fully published branch. Do not pull, merge, or rebase as part of commit preparation. If no committable changes exist, report the repository and publication state and stop.

2. **Build the plan.** Group changes by intent rather than file type. Prefer one commit for one coherent intent; split only when it materially improves review or rollback. Explicitly flag unrelated or accidental changes, secrets or local configuration, deletions, generated files, snapshots, migrations, symlinks, local assets, temporary files, formatting-only churn, manifest/lockfile mismatches, staged/unstaged mismatches, visible partial work or failing tests, and upstream risks.

   Propose the commit count, exact files or hunks per commit, message, split rationale, risks, upstream status, and recommended verification. Messages should be imperative and describe the actual behavior or capability; avoid vague labels such as `phase 1`, `misc`, `changes`, or `wip` unless requested. Ask the user to approve or modify the complete plan before any check that requires approval, staging, or commit.

3. **Choose proportionate checks.** Inspect project and task-runner files such as `package.json` and lockfiles, `Cargo.toml`, Python project files, `Makefile`, `justfile`, or `Taskfile.yml` to identify relevant lint, type, test, build, or format checks. Do not require checks for trivial or documentation-only changes unless repository convention does. Ask before slow, expensive, networked, browser, end-to-end, production-build, or escalated checks. Record checks the user skips.

4. **Execute only the approved plan.** Run the approved checks first. If one fails, stop unless the user explicitly authorizes committing anyway; report the command, failure, likely cause when evident, staged state, and recommended next action.

   Stage only approved paths or hunks, preferring explicit paths. For partial staging, construct it non-interactively when reliable; otherwise ask rather than guess. Git metadata writes require the host approval or escalation flow after plan approval—use it intentionally instead of first probing a read-only sandbox. Before each commit, verify `git diff --cached --stat`, the full staged diff, and `git status --short`.

   Commit with the exact approved message after checks pass or are intentionally skipped. For multiple commits, repeat stage, verify, and commit. Do not change the message, amend, bypass hooks, retry differently, or add paths without renewed approval.

5. **Report the result.** Include commit hashes and messages, checks and outcomes, user-skipped checks, remaining uncommitted or intentionally unstaged work, and the final upstream state including unpublished commits. A push requires a separate user request after this workflow is complete.

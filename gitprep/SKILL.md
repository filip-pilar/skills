---
name: gitprep
description: Manual-only git commit preparation workflow. Use only when explicitly invoked as $gitprep. Inspect the current repository diff and upstream publication state, propose a clean commit plan, recommend relevant verification commands, ask for user approval, then stage and commit exactly the approved files or hunks. Never push unless the user separately asks.
---

# Gitprep

Prepare clean, intentional git commits from the current working tree.

## Core Rules

- Use this skill only when explicitly invoked with `$gitprep`.
- Never push unless the user separately asks for a push after the commit workflow is complete.
- Use `git` for local repository operations: status, diff, add, commit, branch, merge, rebase, and push when a separate user request explicitly asks for it.
- Treat git metadata writes as sandbox-boundary operations. `git add`, `git commit`, branch creation, merge, rebase, and other commands that write `.git/` should use the host approval/escalation flow intentionally after the user approves the plan; do not first run them in the sandbox just to discover `.git/` is read-only.
- Use authenticated `gh` CLI only when GitHub-hosted context would materially clarify the commit plan or verification state. Prefer local git inspection for normal commit prep. Do not create PRs, merge PRs, push, comment/review, rerun workflows, or otherwise mutate GitHub state unless the user explicitly asks.
- Never stage unrelated files silently.
- Never run long or expensive checks without user approval.
- Never commit after failed checks unless the user explicitly says to commit anyway.
- Preserve user changes. Do not revert, delete, or rewrite unrelated work.
- Prefer one commit when the diff has one coherent intent. Suggest multiple commits only when the split materially improves reviewability or rollback.
- Treat generated files, lockfiles, migrations, snapshots, symlinks, local asset libraries, temp files, and formatting-only churn as items that need explicit mention in the plan.


## Commit Message Guidance

Suggest concrete, reviewable commit messages in imperative mood. Name the behavior or capability being added, fixed, or changed. Avoid vague milestone labels such as `phase 1`, `initial work`, `misc updates`, `changes`, or `wip` unless the user explicitly asks for that wording. Prefer messages like `Add batch converter for Locky remixes` over `Add batch converter phase 1`.

## Workflow

### 1. Inspect Repository State

Run read-only git inspection first:

```bash
git status --short
git status -sb
git branch --show-current
git branch -vv
git remote -v
git diff --stat
git diff --cached --stat
```

If the current branch has an upstream, inspect local commits that are not published and remote commits that are not present locally:

```bash
git log --oneline @{u}..HEAD
git log --oneline HEAD..@{u}
```

If there is no upstream, say that explicitly. Do not describe the repository as "clean" without also reporting whether the current branch is ahead, behind, diverged, missing an upstream, or aligned with its upstream. A clean working tree can still have unpublished commits.

If there are staged changes, inspect both staged and unstaged diffs separately:

```bash
git diff --cached
git diff
```

If the diff is large, inspect by file or focused hunks instead of dumping everything at once:

```bash
git diff -- <path>
git diff --cached -- <path>
```

Also check recent commit style when useful:

```bash
git log --oneline -5
```

If the repository has a GitHub remote and GitHub context would materially clarify the commit plan or verification state, use `gh` for read-only GitHub API context:

```bash
gh repo view
gh pr status
gh pr checks
```

Use `gh` rather than raw HTTP calls for GitHub comments, reviews, issues, checks, workflow runs, and other GitHub-hosted API work when the user explicitly asks for those actions. Keep local repository state changes on `git`. Skip `gh` if the repo is not hosted on GitHub, `gh` is unavailable, network/auth access would create avoidable friction, or GitHub context is irrelevant to the local commit plan.

### 2. Identify Commit Units

Group changes by intent, not by file type:

- feature
- bug fix
- refactor
- docs
- tests
- dependency or lockfile update
- generated output
- formatting-only cleanup
- migration or schema change

Flag these explicitly:

- unrelated changes mixed into the diff
- files that look accidentally modified
- secrets or local config
- deleted files
- generated files or snapshots
- lockfile changes without manifest changes
- manifest changes without lockfile changes
- staged changes that do not match unstaged changes
- partial implementation with TODOs or failing tests visible in the diff
- unpublished local commits, unpulled upstream commits, diverged branches, or missing upstream tracking

### 3. Propose A Commit Plan

Present a concise plan before staging or committing:

- Recommended split: one commit or N commits.
- Files/hunks in each commit.
- Suggested commit message for each commit, following the commit message guidance above.
- Rationale for the split.
- Risks or suspicious changes.
- Upstream status: aligned, ahead, behind, diverged, or no upstream. If ahead, list the unpublished commit subjects and say they will not appear on the remote until pushed.
- Verification commands recommended before commit.

Ask the user to approve or modify the plan. Do not proceed until the user confirms the commit plan.

### 4. Recommend Verification

Detect likely checks from repo files:

- `package.json`: inspect scripts such as `lint`, `typecheck`, `test`, `build`, `format:check`.
- `bun.lock`, `pnpm-lock.yaml`, `yarn.lock`, `package-lock.json`: infer package manager.
- `Cargo.toml`: consider `cargo test`, `cargo check`, `cargo fmt --check`.
- `pyproject.toml`, `uv.lock`, `requirements.txt`: consider project-specific test/lint commands.
- `Makefile`, `justfile`, `Taskfile.yml`: inspect obvious verification targets.

Recommend checks based on the diff and repo setup. Ask before running slow checks such as production builds, e2e suites, browser tests, or commands likely to need network or sandbox escalation.

Do not require checks for docs-only or trivial changes unless the repo convention clearly expects them. If the user skips checks, record that in the final summary.

### 5. Stage Exactly The Approved Changes

`git add` writes the protected `.git` index. After the user approves the commit plan, run approved staging commands with the host's normal approval/escalation flow from the start. Keep the command scoped to the exact approved files or hunks; do not broaden it into unrelated staging or cleanup.

After approval, stage only approved files or hunks.

Prefer explicit paths:

```bash
git add <path> ...
```

For partial staging, use non-interactive patch construction when practical. If interactive staging would be fragile, ask the user how to proceed instead of guessing.

Before committing, verify staged content:

```bash
git diff --cached --stat
git diff --cached
git status --short
```

The verification commands above are read-only and should normally run without escalation.

### 6. Commit

Commit with the approved message only after the approved plan and approved checks are complete or intentionally skipped.

```bash
git commit -m "<approved message>"
```

`git commit` writes repository metadata. Use the host approval/escalation flow intentionally, with the exact approved message. Do not retry with a different message, amend, bypass hooks, or add extra paths unless the user approves that change.

If multiple commits were approved, repeat the stage, verify, commit cycle for each commit.

If checks fail, stop and report:

- command run
- failure summary
- likely cause if evident
- whether anything is staged
- recommended next action

### 7. Final Summary

Report:

- commit hash or hashes
- commit message or messages
- checks run and pass/fail result
- checks skipped by user
- remaining uncommitted changes, if any
- anything intentionally left unstaged
- upstream status after the commit, including whether local commits remain unpublished

Never push unless the user separately asks for a push after the commit workflow is complete.

---
name: catchup
description: Read-only repository orientation from local Git history and selective project context, covering current state, recent workstreams, concrete loose ends, and evidence limits.
---

# Repo Catch-up

Treat a bare `$catchup` as a complete request to explain what has been happening
in the current repository and where it stands now. Remain read-only: do not
modify files or Git state, fetch, contact remote services, stage or commit
changes, select the next objective, recommend strategy, message another task,
or continue the work. Do not run verification commands, including tests,
builds, lint, type checks, validators, `git diff --check`, or other correctness
checks. Inspect only verification evidence already recorded in commits,
documentation, or repository artifacts.

## Interpret the request

Use the current Git repository and the preceding seven rolling days by default.
Interpret time in the user's local timezone, capture one fixed end time for the
inspection, and show the exact start, end, and timezone. Use committer time as
the measure of recorded repository activity. Treat current staged, unstaged,
and untracked changes as present now; never infer their age from filesystem
timestamps.

Honor natural-language changes such as `since Monday`, `last month`, `this
branch`, `all branches`, `recent branches`, named branches, a named path, or
`timeline`. Treat `last month` as the previous local calendar month and `since
Monday` as starting at the most recent local Monday 00:00. Clarify only a
materially ambiguous scope. A path scope limits changed paths and contextual
exploration; a branch scope limits or expands history while current worktree
state remains visible. `timeline` changes presentation, not evidence or
coverage rules.

If the location is not inside a Git repository, state that Catch-up requires
one and stop. For an empty repository, report the branch and worktree state and
that no commit history exists. If no commit falls inside the selected window,
say so and show only the latest commit reachable within the selected branch
scope as an orientation anchor; do not silently widen the window.

## Establish local repository facts

Start with local Git evidence before interpreting project content:

1. Inspect the current worktree, index, conflicts or active Git operation,
   current branch or detached `HEAD`, configured remotes and upstream, local
   tracking relationship, stash metadata, shallow-repository state, and listed
   worktrees. Do not inspect stash contents or other worktree contents by
   default.
2. Resolve the default branch without network access. Prefer the symbolic
   remote `HEAD` for the current branch's upstream remote, then `origin/HEAD`,
   then a sole locally recorded remote `HEAD`; otherwise fall back to local
   `main`, local `master`, or the current branch in that order. Disclose any
   fallback and when no usable default exists.
3. Establish the complete reporting scope once. By default, inspect recent
   commits reachable from the current branch, or from detached `HEAD`, only.
   Use the resolved default branch and the current branch's configured upstream
   solely as reference points for publication, integration, ahead/behind, and
   divergence; their unique commits must not expand recent-work coverage.
   `all branches` adds every local branch, `recent branches` adds local branches
   whose tip committer time is inside the selected window, and named branches
   add only those branches. A reference-only ref is not an inspected reporting
   branch unless the user also includes it.
4. Collect commits in the selected time, path, and reporting-branch scope with
   identities, committer timestamps, subjects, parents, changed paths, and
   statistics. The main agent owns branch relationships, reachability, and
   global deduplication. Deduplicate exact commit identities reached through
   multiple included branches. A rebase or cherry-pick creates different
   identities: keep them distinct and describe a likely duplicated change only
   when patch or history evidence supports that inference.
5. Inspect only the diffs or file contents needed to explain material activity.
   Avoid dumping large patches, generated or binary content, credentials, or
   secrets.

Determine aligned, ahead, behind, diverged, or no-upstream state only against
locally recorded tracking refs. Never imply those refs are current: no-fetch
coverage must say that remote-tracking information may be stale. A clean
worktree does not establish publication, integration, verification, or project
completion.

## Follow context progressively

After locating recent activity, follow useful clues into relevant local code,
documentation, architecture, tests, configuration, schemas, migrations,
release information, plans, decisions, or other project content. Let the
activity determine what to inspect. Do not use a fixed file-type checklist,
read every Markdown file, search every TODO, or crawl the repository.

Use applicable `AGENTS.md` files as operating guidance, never as proof of
project state. Use README and architecture material for vocabulary and
structure. Treat plans, roadmaps, status notes, TODOs, and decision records as
recorded intent. Compare them with newer Git and file evidence; label stale,
contradictory, or uncertain context rather than silently choosing a source.

Git state and repository contents establish facts. Model judgment may name and
summarize workstreams using commit subjects, changed paths, branch
relationships, selective diffs, and relevant context. Keep changes separate
when their relationship is uncertain. Prefer factual verbs such as `changed`,
`introduced`, `removed`, `merged into the default branch`, or `present on this
branch`. Use `completed`, `verified`, `deployed`, or `successful` only when
explicit evidence establishes that claim. Test files or commit messages alone
do not prove that checks passed.

## Classify loose ends precisely

Report only classifications supported by concrete evidence:

- **uncommitted:** staged, unstaged, or untracked current-worktree changes;
- **conflicted or interrupted:** unresolved conflicts or an active merge,
  rebase, cherry-pick, revert, or bisect operation;
- **unpublished:** local commits ahead of a configured upstream;
- **diverged:** both local-only and tracking-only commits exist;
- **unintegrated:** commits on an inspected non-default branch are not
  reachable from the resolved default branch;
- **stashed:** stash metadata exists, without claims about its contents or
  purpose;
- **explicit WIP:** relevant current evidence explicitly marks the associated
  work as WIP or unfinished and newer evidence does not supersede it.

A branch's classifications are independent and may overlap. Apply them to
every branch in the reporting scope: for example, a branch with both local-only
and tracking-only commits is **diverged**, and its local-only commits are also
**unpublished**. Qualify branch-specific findings and any `none detected`
statement so it covers every reporting branch rather than silently describing
only the checked-out branch. Reference-only default or upstream refs are not
additional reporting branches.

A dirty worktree, stash, branch, TODO, or unmerged commit does not by itself
prove that a feature is unfinished. No upstream does not prove unpublished
work. If no classification applies, say that no concrete loose ends were
detected from the inspected evidence; never claim the project is complete.

## Delegate only when it improves coverage

When the initial Git sweep reveals several materially independent workstreams
or large affected areas that warrant separate contextual investigation, use
read-only subagents to investigate them in parallel. First fix the time window,
reporting branches, branch relationships, upstream/default references, commit
identities, reachability, and global deduplication. Then give each subagent one
narrow, non-overlapping workstream or affected-area scope with the relevant
commit identities and dates already supplied.

Subagents investigate contextual meaning and supporting local evidence. They
must not recompute global branch topology, deduplicate the overall commit set,
or classify repository-wide loose ends unless they discover contradictory
evidence for the main agent to reconcile. Forbid edits, fetches, external
services, unrelated recommendations, and every verification command, including
read-only correctness checks.

Do not delegate a small or straightforward repository. If subagents are
unavailable, continue in one agent and disclose only a material coverage loss.
The main agent owns commit and branch deduplication, conflicting-finding
reconciliation, source-authority judgments, and the unified report.

## Report for orientation

Use only sections that carry information, while always providing enough
coverage detail to interpret the result:

- **State now** — current branch or detached state, worktree, upstream,
  active operation or conflicts, and stash state.
- **Recent changes** — concise workstream-grouped summaries with dates, branch
  disposition, and supporting commit identities or paths where useful. Use a
  chronology instead when requested.
- **Loose ends** — only the precise supported classifications above.
- **Coverage** — exact time range and timezone, branches and path inspected,
  no-fetch and tracking-ref freshness, shallow or incomplete history, omitted
  detail, material source uncertainty, and whether repository evidence records
  verification. State that Catch-up ran no checks. For a bare invocation,
  explicitly state that history coverage was current-branch-only and that work
  unique to other local branches was omitted.

Optimize for quick orientation rather than exhaustive Git output. On refresh,
rebuild the full report from current local evidence rather than returning only
a delta.

## Preserve skill boundaries

Catch-up summarizes repository evidence, not Codex conversation history. TLDR
owns the complete state of one linked Codex task. Gitprep owns verification
planning, staging, and commit preparation. Lock In owns selecting and advancing
the active objective. Remote pull requests, issues, reviews, CI, releases,
Codex task history, reflog archaeology, recursive submodule analysis, and
automatic fetching are outside Catch-up's scope. Report submodule pointer
changes as repository changes without recursively inspecting the submodule.

## Before responding

Silently verify:

1. The exact interpreted time and scope are visible, and commits use committer
   time without invented dates for uncommitted work.
2. Recent-work coverage contains only the requested reporting branches;
   reference-only default or upstream commits did not expand it. Commit
   identities are globally deduplicated before delegation.
3. Inferred workstream relationships and recorded intent remain distinguishable
   from repository facts.
4. Every loose-end label meets its concrete definition, covers every reporting
   branch, preserves overlapping classifications, and does not imply unfinished
   or completed features.
5. Neither the main agent nor a subagent ran a verification command or another
   prohibited action, and material freshness, omissions, and coverage limits
   are disclosed.

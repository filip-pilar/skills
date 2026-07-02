---
name: dr-react
description: Guarded React Doctor score-improvement workflow. Use when asked to run React Doctor, improve or raise a React Doctor score, fix React Doctor diagnostics, perform a React Doctor cleanup pass, or run a /goal-style loop until a score threshold is reached while preserving behavior and avoiding score gaming.
---

# Dr React

Use this skill to improve a repository's React Doctor result through small, verified, root-cause fixes. Default target score is `70`; use a user-provided target when specified.

## Core Commands

- Full score scan: `npx --yes react-doctor@latest --json --scope full`
- Changed regression scan: `npx --yes react-doctor@latest --json --scope changed`
- Root-cause help: `npx --yes react-doctor@latest why <file>:<line>`
- Rule help: `npx --yes react-doctor@latest rules explain <rule>`

Do not use deprecated `--diff`; use `--scope changed` and `--base <ref>` when a base ref is needed.

If JSON parsing is useful, run `scripts/parse-react-doctor-report.mjs <report.json>` or pipe JSON to it. Treat missing numeric score as score unavailable and fall back to diagnostic counts without claiming the target is met.

## Sandbox And Network Handling

Prefer normal sandboxed commands first. If a required command fails because of sandboxing, git metadata permissions, DNS, npm/package registry access, or another clear environment restriction, rerun the same command with the host's normal approval/escalation flow. Keep the rerun scoped to the exact failed command.

Common cases:

- `npx --yes react-doctor@latest --json --scope full` may need network approval to download React Doctor.
- `git switch -c ...` may need approval if the sandbox blocks `.git` metadata writes.
- Dev server or browser checks may need approval if the host environment requires it.

Do not use escalation to bypass project checks, avoid approval gates, weaken security, or run unrelated commands.

## Workflow

1. Inspect git status first.
   - If the worktree is dirty, identify user-owned changes and do not commit them.
2. Establish baseline with the full score scan on the current branch before creating a new branch.
   - Record score availability, score, diagnostic count, categories, severities, and top fix groups.
   - Group diagnostics by `fixGroupId` first, then rule/category/file.
   - If the score is already at or above target, stop and report without creating a branch.
3. If edits are needed, create one branch before the first edit.
   - If the worktree is clean and not explicitly told otherwise, use `react-doctor/score-<target>-<date>`.
   - If that branch name conflicts, use a simple non-conflicting variant such as `react-doctor-score-<target>-<date>`.
4. Choose one coherent diagnostic cluster.
   - Prefer security errors, performance errors, Bugs/correctness errors, accessibility, then maintainability.
   - For migration-scale buckets, fix only a representative sample and stop for approval before sweeping.
5. Before editing, write a short root-cause note:
   - diagnostic being fixed
   - likely root cause
   - why the planned change fixes the root cause rather than masking it
   - behavior that must remain unchanged
6. Classify risk.
   - Low: local logic, type, accessibility, or isolated component fix.
   - Medium: shared component, hook, form, route, state, or styling change.
   - High: auth, data fetching, caching, global state, public API, dependency, config, or broad file movement.
   - Stop for explicit user approval before high-risk changes.
7. Make the smallest coherent fix.
   - Prefer <= 3 source files and <= 150 changed lines per iteration.
   - Reuse existing project patterns and local helpers.
   - Avoid new abstractions unless required to remove real duplication or fix the root cause.
8. Verify.
   - Discover package scripts and prefer `typecheck`, `test`, `lint`, then `build` when available.
   - Run the changed regression scan.
   - Run the full score scan to compare with baseline.
   - For UI-affecting changes, perform the visual regression checks below.
9. Inspect the diff for score integrity.
   - Commit only after verification passes and score improves or is preserved for a necessary root-cause fix.
   - Include score movement in the commit message when a score is available.
   - Do not merge, push, open PRs, rebase, alter remotes, or change upstream branches unless explicitly instructed.
10. Repeat until a stop condition is met.

## Stop Conditions

Stop and report when any of these are true:

- score is at or above the target
- max 5 successful edit cycles reached
- two consecutive cycles do not improve score
- score is unavailable and diagnostic-count fallback cannot prove progress
- remaining findings require product, design, security, or code-owner judgment
- migration-scale bucket needs approval before broad changes
- verification or visual checks reveal unresolved regression

## Score Integrity Rules

Do not improve the score by hiding diagnostics. Forbidden unless the user explicitly approves:

- weakening `doctor.config.*` or `package.json#reactDoctor`
- adding broad ignores, category downgrades, `surfaces` exclusions, or suppressions
- adding dependencies
- moving public APIs or large file structures
- replacing typed logic with `any`, unchecked casts, dead branches, or no-op guards
- deleting behavior just to remove diagnostics

If score improves but diagnostic count drops without corresponding source-code fixes, inspect the diff carefully before committing. Revert or report any iteration that improved score by suppression, configuration weakening, or scan-scope reduction.

## Quality Guardrails

- Do not blanket-add `memo`, `useMemo`, or `useCallback`.
- Do not remove hook dependencies to silence warnings.
- Do not weaken accessibility semantics, labels, roles, or keyboard behavior.
- Do not replace real error handling with empty catches.
- Do not introduce providers, state managers, cache layers, design-system patterns, or shared abstractions unless the root cause requires it.
- If root cause is unclear, use `why` or `rules explain` before editing.

## Visual Regression Checks

If changed files affect routes, components, styles, layout, forms, navigation, rendering, or interaction:

1. Start the app with the existing dev script when feasible.
2. Identify affected routes or stories from the changed files.
3. Check at least desktop and mobile viewport.
4. Capture or inspect before/after screenshots when possible.
5. Inspect browser console errors.
6. Exercise the changed interaction.
7. Do not commit visible layout, text, interaction, or accessibility regressions.
8. If visual checks are skipped, state the exact blocker in the final report.

## Final Report

Report:

- initial score -> final score, or why score was unavailable
- diagnostics fixed and diagnostics remaining
- commands run and results
- visual routes checked, if applicable
- commits created
- skipped findings and why
- whether target was reached

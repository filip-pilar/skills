---
name: dr-react
description: Guarded workflow for improving React Doctor scores through root-cause fixes. Use when asked to run React Doctor, raise its score, fix its diagnostics, perform a cleanup pass, or run a `/goal`-style loop to a target while preserving behavior and preventing score gaming.
---

# Dr React

Improve a repository's React Doctor result through small, verified, root-cause fixes. Default to a target score of `70` unless the user specifies another.

## Commands

- Full scan: `npx --yes react-doctor@latest --json --scope full`
- Changed scan: `npx --yes react-doctor@latest --json --scope changed`
- Root-cause help: `npx --yes react-doctor@latest why <file>:<line>`
- Rule help: `npx --yes react-doctor@latest rules explain <rule>`

Do not use deprecated `--diff`; use `--scope changed` and, when needed, `--base <ref>`. Parse JSON with `scripts/parse-react-doctor-report.mjs <report.json>` or pipe it to the script. If no numeric score is available, use diagnostic counts without claiming the target was met.

Run commands in the normal sandbox first. When a required command fails because of a clear environment restriction—such as git metadata permissions, DNS/npm access, or dev-server/browser controls—rerun only that command through the host's approval flow. Never escalate to skip project checks or approval gates, weaken security, or run unrelated work.

## Workflow

1. **Protect existing work.** Inspect git status, identify dirty user-owned changes, and never include them in a commit.
2. **Baseline before branching.** Run the full scan on the current branch. Record score availability and value, diagnostic count, severity/category totals, and top fix groups, grouping by `fixGroupId` and then rule/category/file. Gather cheap, relevant impact signals already supported by the project. If the target is already met, report and stop without creating a branch.
3. **Create one working branch before editing.** When the worktree is clean and the user has not specified otherwise, use `react-doctor/score-<target>-<date>`; on conflict, use a simple variant such as `react-doctor-score-<target>-<date>`.
4. **Choose one coherent cluster.** Prefer security errors, performance errors, bugs/correctness errors, accessibility, then maintainability. For a migration-scale bucket, fix only a representative sample and get approval before sweeping.
5. **Explain and classify the fix.** Note the diagnostic, likely root cause, why the change fixes rather than masks it, and behavior that must remain. Classify risk as low for local logic/type/accessibility/isolated components; medium for shared components, hooks, forms, routes, state, or styling; and high for auth, data fetching, caching, global state, public APIs, dependencies, config, or broad file movement. Get explicit approval before a high-risk change.
6. **Make the smallest coherent fix.** Prefer no more than three source files and 150 changed lines per cycle. Reuse project patterns and helpers; add an abstraction only when the root cause or real duplication requires it.
7. **Verify.** Discover project scripts and prefer `typecheck`, `test`, `lint`, then `build` when available. Run the changed regression scan, the full scan against baseline, relevant impact checks, and the visual checks below when the change affects UI.
8. **Inspect score integrity and the diff.** Commit only when verification passes and the score improves, or is preserved by a necessary root-cause fix. Include score movement in the commit message when available. Do not merge, push, open a PR, rebase, alter remotes, or change upstream branches unless explicitly requested.
9. Repeat until a stop condition applies.

Stop when the target is met; five successful edit cycles are complete; two consecutive cycles fail to improve the score; neither a score nor diagnostic counts can prove progress; remaining work needs product, design, security, or code-owner judgment; a migration-scale sweep needs approval; or verification/visual checks reveal an unresolved regression.

## Integrity Guardrails

Do not game the score. Unless the user explicitly approves, never:

- weaken `doctor.config.*` or `package.json#reactDoctor`, broaden ignores, downgrade categories, exclude `surfaces`, add suppressions, or reduce scan scope
- add dependencies, move public APIs or large file structures, replace typed logic with `any`/unchecked casts/dead branches/no-op guards, or delete behavior merely to silence findings

If the score rises while diagnostics disappear without matching source fixes, inspect the diff and revert or report any suppression, configuration weakening, or scope reduction.

Preserve code quality: do not blanket-add `memo`, `useMemo`, or `useCallback`; remove hook dependencies; weaken accessibility semantics, labels, roles, or keyboard behavior; replace real error handling with empty catches; or introduce providers, state managers, cache layers, design-system patterns, or shared abstractions without a root-cause need. When the cause is unclear, use `why` or `rules explain` before editing.

## Impact Evidence

React Doctor measures code health, not user-perceived speed. Always capture score, diagnostic count, severity/category movement, and fixed rule groups. Add only relevant, practical signals:

- Preserve concise bundle/build sizes when the existing `build` supplies them, and run relevant existing `size`, `analyze`, `bundle`, `lighthouse`, or `perf` scripts.
- For UI/performance fixes when the app can run, compare the same route before and after using local navigation/load timing and console errors on desktop and mobile.
- Prefer an existing Lighthouse workflow. Otherwise run `npx --yes lighthouse <url> --output=json --output-path=<tmp-file> --quiet --chrome-flags="--headless"` only when a route is served, the change is performance-facing, and the runtime is justified.

Do not add permanent dependencies, analyzer config, package scripts, or lockfile changes solely for measurement without approval. Temporary `npx` tools and `/tmp` files are acceptable; remove or ignore generated artifacts before committing. If measurement requires project changes, ask first and explain why native signals are insufficient.

Report at most five impact bullets as `Measured` (comparable before/after numbers), `Likely` (direct implications of fixed rule groups), or `Not proven` (unmeasured UX speed, production Web Vitals, or error rates). Do not claim causality from noisy lab data; call it a local signal or smoke metric unless backed by a stable benchmark or CI measurement.

## Visual Checks

When changed files affect routes, components, styles, layout, forms, navigation, rendering, or interaction, start the app with its existing dev script when feasible; identify affected routes or stories; inspect desktop and mobile; capture or compare before/after screenshots when possible; check console errors; and exercise the changed interaction. Do not commit visible layout, text, interaction, or accessibility regressions. If checks are skipped, report the exact blocker.

## Final Report

Keep it concise: initial to final score (or why unavailable), diagnostics fixed and remaining, up to five impact bullets, verification commands and pass/fail results, visual routes checked, commits created, skipped findings and reasons, and whether the target was reached.

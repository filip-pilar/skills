---
name: dr-react
description: Guarded React Doctor score-improvement workflow. Use when asked to run React Doctor, raise its score, fix diagnostics, clean up findings, or use `/goal` to reach a target without behavior regressions or score gaming.
---

# Dr React

Improve React Doctor results through small, verified root-cause fixes. Default to score `70` unless the user specifies another. This skill governs safe fix cycles; `/goal` owns persistence across turns.

## Commands

- Full scan: `npx --yes react-doctor@latest --json --scope full`
- Changed scan: `npx --yes react-doctor@latest --json --scope changed`
- Explain: `npx --yes react-doctor@latest why <file>:<line>` or `npx --yes react-doctor@latest rules explain <rule>`

Do not use deprecated `--diff`; use `--scope changed` and optional `--base <ref>`. Parse JSON with `scripts/parse-react-doctor-report.mjs <report.json>` or pipe it to the script. A missing numeric score is unavailable: use diagnostic counts, but never claim the target was met.

Start sandboxed. On a clear environment restriction, rerun only the failed command through the host approval flow; for DNS or registry failures, do so immediately rather than polling or retrying. Never escalate to skip checks or gates, weaken security, or run unrelated work.

## Workflow

1. **Protect existing work.** Inspect git status, identify dirty user-owned changes, and never commit them.
2. **Baseline before branching.** Run the full scan on the current branch. Record score availability/value, diagnostic count, severity/category totals, and top fix groups; group by `fixGroupId`, then rule/category/file. Capture relevant existing impact signals. If the target is met, report and stop without creating a branch.
3. **Create one branch before editing.** With a clean worktree and no contrary direction, use `react-doctor/score-<target>-<date>` or a simple non-conflicting variant such as `react-doctor-score-<target>-<date>`.
4. **Choose one coherent cluster.** Prefer security, performance, bugs/correctness, accessibility, then maintainability. For migration-scale work, fix a representative sample and get approval before sweeping.
5. **Explain and classify the fix.** Note the diagnostic, likely root cause, why the change fixes rather than masks it, and behavior to preserve. Risk is low for local logic/type/accessibility/isolated components; medium for shared components, hooks, forms, routes, state, or styling; and high for auth, data fetching, caching, global state, public APIs, dependencies, config, or broad file movement. Require approval for high-risk work.
6. **Make the smallest coherent fix.** Prefer at most three source files and 150 changed lines per cycle. Reuse project patterns/helpers; add abstractions only for the root cause or real duplication.
7. **Verify.** Prefer available `typecheck`, `test`, `lint`, then `build`. Run the changed scan, full scan against baseline, relevant impact checks, and UI checks below when applicable.
8. **Inspect integrity and the diff.** Commit only after verification passes and the score improves, or stays level for a necessary root-cause fix. Put available score movement in the message. Do not merge, push, open a PR, rebase, alter remotes, or change upstream branches unless requested.

Stop when the target is met; five successful cycles finish an ordinary invocation; two consecutive cycles fail to improve; neither score nor counts can prove progress; the next work needs product/design/security/code-owner judgment, high-risk approval, a migration sweep, or broad refactoring; or verification/UI checks reveal an unresolved regression. Under `/goal`, omit only the five-cycle limit: every other stop and approval gate remains.

## Integrity

Without explicit approval, never weaken `doctor.config.*` or `package.json#reactDoctor`; broaden ignores, downgrade categories, exclude `surfaces`, suppress findings, or reduce scan scope; add dependencies; move public APIs or large file structures; replace typed logic with `any`, unchecked casts, dead branches, or no-op guards; or delete behavior to silence findings. If diagnostics vanish without matching source fixes, revert or report any suppression, configuration weakening, or scope reduction.

Never blanket-add `memo`, `useMemo`, or `useCallback`; remove hook dependencies; weaken accessibility semantics, labels, roles, or keyboard behavior; replace real error handling with empty catches; or introduce providers, state managers, cache layers, design-system patterns, or shared abstractions without a root-cause need. Use `why` or `rules explain` when the cause is unclear.

## Evidence and UI checks

React Doctor measures code health, not user-perceived speed. Always record score, diagnostic count, severity/category movement, and fixed rule groups. Add only relevant existing signals: build/bundle sizes; project `size`, `analyze`, `bundle`, `lighthouse`, or `perf` scripts; and, for runnable UI/performance changes, same-route before/after timing and console errors on desktop and mobile. Prefer an existing Lighthouse workflow; otherwise use `npx --yes lighthouse <url> --output=json --output-path=<tmp-file> --quiet --chrome-flags="--headless"` only for a served route and performance-facing change when justified.

Do not add permanent dependencies, analyzer config, scripts, or lockfile changes solely to measure without approval. Temporary `npx` tools and `/tmp` files are acceptable; remove or ignore generated artifacts before committing. If measurement needs project changes, ask first and explain why native signals are insufficient.

Report at most five evidence bullets: `Measured` uses the same command, route, mode, and machine before/after; `Likely` states direct implications of fixed groups; `Not proven` covers unmeasured UX speed, production Web Vitals, or error rates. Do not infer causality from noisy lab data; call it a local signal or smoke metric without a stable benchmark or CI measurement.

For changes affecting routes, components, styles, layout, forms, navigation, rendering, or interaction, start the existing dev script when feasible; identify affected routes/stories; inspect desktop and mobile; compare before/after screenshots when possible; check console errors; and exercise the interaction. Do not commit visible layout, text, interaction, or accessibility regressions. Report the exact blocker when checks are skipped.

## Report

Keep it concise: initial to final score or why unavailable; diagnostics fixed and remaining; up to five evidence bullets; verification commands/results; visual routes checked; commits; skipped findings and reasons; and whether the target was reached.

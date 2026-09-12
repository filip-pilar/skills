# Repository guidance

## Purpose

This repository publishes skills for GPT-6 Astra in Codex. Keep distributable
packages self-contained, safe to install, and economical in runtime context.
Target Astra exclusively; do not add scaffolding for older models or other agents.

## Sources of truth

- `skills/<name>/SKILL.md` owns runtime behavior.
- `skills/<name>/agents/openai.yaml` owns display metadata and invocation policy.
- `references/` contains conditional instructions loaded only when needed.
- `scripts/`, `assets/`, and `tests/` belong to their containing skill.
- `README.md` owns the public catalogue, installation, and maintainer overview.
- `local/`, `.evals/`, `.tmp/`, and root `.agents/` are ignored development
  state and are not durable repository guidance.
- `docs/side-orchestration-workflow.md` explains the Side workflow; its skills own
  runtime requirements. `docs/skill-prompt-review-cases.md` owns optional behavioral
  scenarios, not test results or an execution checklist.
- `legacy/` preserves retired contracts, not current instructions. Consult ignored
  experiments or completed records only to resolve a concrete dependency or retain
  an unfinished obligation; edit generated material at its actual source.

Do not duplicate skill behavior in this file.

## Working rules

- Inspect `git status --short` before editing and preserve unrelated work.
- For behavioral changes, read the complete `SKILL.md`; for mechanical edits,
  inspect the affected section and relevant constraints.
- Treat audits, reviews, and diagnoses as report-only unless edits are requested.
- Keep changes within the requested scope; update related skills together when
  consistency requires it.
- Keep generated evidence, credentials, logs, caches, and live-provider output
  outside tracked skill packages.
- When adding, removing, or renaming a public skill, update the README catalogue.
- Wire every new deterministic test into the repository validation path.
- Complete requested changes, relevant validation, and repairs caused by the change
  without routine approval between phases. Stop when the requested outcome is met
  or a concrete blocker needs user input; continue independent work when possible.
- Keep descriptions specific to task selection and load references by need. Preserve
  project knowledge and meaningful restrictions; leave routine execution to Astra.
- Do not optimize instruction length at the expense of behavior, safety, or
  activation accuracy.

## Validation

Use the [validation tiers in README.md](README.md#checks) according to the change.
The focused and repository checks use disposable fixtures without production
access. The full check adds local loopback integration tests. Run applicable checks
and fix failures caused by authorized changes without further approval; reuse
current results and expand checks only for new changes or unresolved risks.

Documentation-only changes need content/link review unless they change runtime
behavior or package structure. Release, live-provider, OAuth, browser, installation,
and publication checks remain explicit because they can use credentials or modify
external state.

## Change boundaries

Do not install, synchronize, commit, push, publish, or change global agent
configuration unless the user explicitly requests that action. Follow the
repository's existing Conventional Commit style when commits are requested.

Use `codex/` for new branches. Keep each requested commit a coherent fix.

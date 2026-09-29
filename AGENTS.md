# Repository guidance

This repository publishes self-contained skills for GPT-6 Astra in Codex.
Target Astra exclusively; do not add scaffolding for older models or other agents.

## Sources of truth

- `skills/<name>/SKILL.md` owns runtime behavior; `agents/openai.yaml` beside it
  owns display metadata and invocation policy.
- Keep runtime scripts, assets, and conditional references inside their skill.
  Preserve concrete domain knowledge and meaningful restrictions; omit generic
  process instructions Astra already handles.
- `README.md` owns the public catalogue, installation, and maintainer overview.
- `local/`, `.evals/`, `.tmp/`, and root `.agents/` are ignored development
  state. `legacy/` is historical, outside the active collection; consult these
  locations only for a concrete dependency or unfinished obligation.

## Working rules

- Inspect `git status --short` before editing and preserve unrelated work.
- For behavioral changes, read the complete `SKILL.md`; for mechanical edits,
  inspect the affected section and relevant constraints.
- Treat audits, reviews, and diagnoses as report-only unless edits are requested.
- Keep generated evidence, credentials, logs, caches, and live-provider output
  outside tracked skill packages.
- When adding, removing, or renaming a public skill, update the README catalogue.
- Follow the [checks in README.md](README.md#checks) and fix failures caused by
  authorized changes without routine reapproval.

## Change boundaries

Do not install, synchronize, commit, push, publish, or change global agent
configuration unless the user explicitly requests that action.
Use `codex/` for new branches and Conventional Commits for requested commits.

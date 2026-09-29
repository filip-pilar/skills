# Repository guidance

This repository publishes self-contained Agent Skills. Shared skills target
Codex and Claude Code; host-specific skills declare their required runtime.

## Sources of truth

- `skills/<name>/SKILL.md` owns runtime behavior and Claude Code invocation
  settings; `agents/openai.yaml` beside it owns Codex display metadata and
  invocation policy.
- Keep runtime scripts, assets, and conditional references inside their skill.
  Preserve concrete domain knowledge and meaningful restrictions; omit generic
  process instructions capable agents already handle.
- `README.md` owns the public catalogue, installation, and maintainer overview.
- `local/`, `.evals/`, `.tmp/`, and root `.agents/` are ignored development
  state. `legacy/` is historical, outside the active collection; consult these
  locations only for a concrete dependency or unfinished obligation.

## Host compatibility

- Keep one shared package when the workflow works in both Codex and Claude Code.
  Use the host's available tools without assuming another host's API names.
- For shared manual-only skills, set `disable-model-invocation: true` in
  `SKILL.md` frontmatter and `policy.allow_implicit_invocation: false` in
  `agents/openai.yaml`. Preserve automatic invocation where intended.
- Declare concrete runtime requirements in the `compatibility` frontmatter.
  Label host-specific skills in their description and the README; do not claim
  support based only on matching file formats or installer destinations.
- When changing supported hosts or invocation policy, verify discovery and
  policy metadata for each host and report any untested runtime behavior.

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

# Repository guidance

## Purpose

This repository publishes reusable agent skills. Keep distributable skill
packages self-contained, safe to install, and economical in runtime context.

## Sources of truth

- `skills/<name>/SKILL.md` owns runtime behavior.
- `skills/<name>/agents/openai.yaml` owns display metadata and invocation policy.
- `references/` contains conditional instructions loaded only when needed.
- `scripts/`, `assets/`, and `tests/` belong to their containing skill.
- `README.md` owns the public catalogue, installation, and maintainer overview.
- `local/`, `.evals/`, `.tmp/`, and root `.agents/` are ignored development
  state and are not durable repository guidance.

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
- Do not optimize instruction length at the expense of behavior, safety, or
  activation accuracy.

## Validation

Scale validation to the change. For each affected skill package, run the focused
validator and package tests:

```bash
./scripts/check-skill <name>
```

For package, catalogue, or shared tooling changes, also run:

```bash
./scripts/check-repo
```

For substantial integration changes, run the following, which includes
`check-repo`:

```bash
./scripts/check-full
```

For documentation-only changes that do not affect skill behavior or package
structure, check the affected content and any relevant links or examples.
Rerun or broaden checks when failures, new edits, or unresolved risks justify it.

Run `./scripts/check-release` only for an explicitly requested release check; it
may require network access and a clean worktree. Live-provider, OAuth, browser,
installation, and publication checks remain explicit because they can use
credentials or modify external state.

## Change boundaries

Do not install, synchronize, commit, push, publish, or change global agent
configuration unless the user explicitly requests that action. Follow the
repository's existing Conventional Commit style when commits are requested.

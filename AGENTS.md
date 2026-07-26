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
- For a skill change, read its complete `SKILL.md` before modifying it.
- Treat audits, reviews, and diagnoses as report-only unless edits are requested.
- Prefer one named skill and one explicit behavioral objective at a time.
- Keep generated evidence, credentials, logs, caches, and live-provider output
  outside tracked skill packages.
- When adding, removing, or renaming a public skill, update the README catalogue.
- Wire every new deterministic test into the repository validation path.
- Do not optimize instruction length at the expense of behavior, safety, or
  activation accuracy.

## Validation

During iteration, run the focused validator and package tests:

```bash
./scripts/check-skill <name>
```

Before handing off repository changes:

```bash
./scripts/check-repo
```

For substantial integration changes:

```bash
./scripts/check-full
```

Run `./scripts/check-release` only for an explicitly requested release check; it
may require network access and a clean worktree. Live-provider, OAuth, browser,
installation, and publication checks remain explicit because they can use
credentials or modify external state.

## Change boundaries

Do not install, synchronize, commit, push, publish, or change global agent
configuration unless the user explicitly requests that action. Follow the
repository's existing Conventional Commit style when commits are requested.

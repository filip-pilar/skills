# Improve skill

`improve/` is committed as a directly usable Codex skill. Its root `SKILL.md` and `agents/openai.yaml` are generated from the shared core and Codex adapter; edit the sources, not those generated files.

## Origin and attribution

This skill is based on [shadcn/improve](https://github.com/shadcn/improve), created by shadcn and licensed under the MIT License.

This repository contains a modified version, including host-specific Codex and Claude Code adapters, validation scripts, tests, and other workflow changes. The original concept and substantial portions of the skill content come from the upstream project.

## Host selection

```bash
scripts/switch-host.sh codex
scripts/switch-host.sh claude-code
scripts/switch-host.sh --check
```

The Codex representation is the canonical committed state. Switching a tracked checkout to Claude Code intentionally modifies `SKILL.md` and removes `agents/openai.yaml`; switching back restores the canonical files.

For a clean source checkout or simultaneous installations, materialize a separate copy in one command:

```bash
scripts/switch-host.sh claude-code --output "$HOME/.claude/skills/improve"
```

Codex discovers skills from documented `.agents/skills` locations; Claude Code discovers standalone skills from `.claude/skills`. A valid root `SKILL.md` makes this folder directly installable, but an arbitrary checkout is not discovered until placed in or linked from a host discovery location.

One physical folder can expose only one adapter at a time. If both hosts point to the same folder, switching it switches both consumers. Use `--output` for independent concurrent installations.

## Source layout

- `core.md` — host-neutral behavior.
- `adapters/*.SKILL.md.in` — explicit host entrypoints.
- `references/` — phase-specific guidance loaded on demand.
- `scripts/switch-host.sh` — deterministic host materialization.
- `scripts/validate.sh` and `tests/` — canonical-state and regression checks.

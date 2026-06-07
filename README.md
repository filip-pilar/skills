# Skills

Personal agent skills I use and share.

Each top-level folder is a standalone skill. Some skills may work across multiple agent hosts, while others may depend on specific host capabilities such as local shell access, browser automation, macOS permissions, or app-specific integrations.

## Available Skills

- `poke-negotiator`: Negotiate with Poke by Interaction through macOS Messages/iMessage or Telegram Web, verify checkout links, and stop before payment or account-connection steps.

## Install A Skill

Install instructions depend on the agent host you use. In general, copy the skill folder into the host's skills directory and restart or reload that host.

For Codex, copy a skill folder into:

```bash
mkdir -p ~/.codex/skills
cp -R poke-negotiator ~/.codex/skills/
```

The final path should look like:

```text
~/.codex/skills/poke-negotiator/SKILL.md
```

Restart Codex after installing or updating a skill.

## Notes

- Skills are not guaranteed to be portable across every agent host.
- Read each skill's `SKILL.md` for supported hosts, tools, permissions, and safety stops.
- `poke-negotiator` can require Full Disk Access and Messages Automation permissions on macOS when using iMessage/Messages.
- `poke-negotiator` uses Codex's in-app Browser for Telegram Web today; other hosts need equivalent browser automation to support that path.

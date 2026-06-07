# Skills

Personal Codex skills I use and share.

## Available Skills

- `poke-negotiator`: Negotiate with Poke by Interaction through macOS Messages/iMessage or Telegram Web, verify checkout links, and stop before payment or account-connection steps.

## Install A Skill

Copy a skill folder into your Codex skills directory:

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

Skills may require host-specific permissions. For example, `poke-negotiator` can require Full Disk Access and Messages Automation permissions on macOS when using iMessage/Messages.

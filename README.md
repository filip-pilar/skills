# Skills

Personal skills I use and share.

Each top-level folder is a standalone skill. Some skills are portable across multiple agent environments; others depend on local tools, browser automation, operating-system permissions, or app-specific integrations.

## Available Skills

- `dr-react`: Run a guarded React Doctor score-improvement workflow with root-cause fixes, verification gates, visual regression checks, and anti-score-gaming rules.
- `gitprep`: Inspect the current git diff, propose a clean commit plan, run approved checks, and commit exactly the approved files or hunks. Never pushes.
- `poke-negotiator`: Negotiate with Poke by Interaction through macOS Messages/iMessage or Telegram Web, verify checkout links, and stop before payment or account-connection steps.

## Usage

Use the folder for the skill you want. Installation, loading, and invocation depend on the agent environment you are using, so check the skill's `SKILL.md` for its requirements and supported workflows.

## Notes

- Skills are not guaranteed to be portable everywhere.
- Read each skill's `SKILL.md` for supported tools, permissions, and safety stops.
- `dr-react` runs `npx react-doctor@latest`, which may require network/package-manager access in a target repository.
- `gitprep` is manual-only and should be explicitly invoked as `$gitprep`.
- `poke-negotiator` can require Full Disk Access and Messages Automation permissions on macOS when using iMessage/Messages.
- `poke-negotiator` requires browser automation for Telegram Web.

# Setup and re-entry

## Readiness

Run the non-live readiness check:

```bash
scripts/autopilot doctor
```

It checks Python, macOS, `osascript`, Codex, bundled assets, and private state-path creation. It does not open Messages, invoke Apple Events, request permissions, make a model request, or send anything.

The controller requires Python 3.11 or newer and an authenticated Codex CLI with app-server support. Its default private state is current-session-oriented temporary storage; `--state-dir` may select another private directory. Neither choice installs persistence.

## Messages schema preflight

Only after the user approves opening the database read-only:

```bash
scripts/autopilot preflight --messages-db ~/Library/Messages/chat.db
```

This reads schema metadata only. If access is denied, explain that the app hosting Codex may require Full Disk Access, let the user grant only that permission manually, and honor any required restart and re-entry. Do not change privacy settings yourself.

## Exact chat discovery

After explaining that this reads chat identifiers, participant handles, and recent row positions—but not message bodies or Contacts:

```bash
scripts/autopilot chats --messages-db ~/Library/Messages/chat.db --limit 20
```

Use `--search <text>` when needed. Review the returned opaque chat ID, direct/group classification, participants, membership hash, and `sendable` value. Do not configure an ambiguous, unexpected, or unsendable result.

Sending has a separate Automation permission to control Messages. Do not probe it during setup. The first explicitly approved live smoke may trigger the normal macOS prompt; allow only control of Messages.

Foreground and detached permission attribution remain unproven until separately observed. Prove `run` before making any claim about `start`.

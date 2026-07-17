# Runtime operations

The controller accepts a global `--state-dir`; tests and rehearsals should always use a nonce-scoped temporary directory. The default is also temporary and intentionally does not promise persistence across reboot.

## Run modes

Foreground:

```bash
scripts/autopilot --state-dir <dir> run --fixture <events.jsonl>
```

Background for the current session:

```bash
scripts/autopilot --state-dir <dir> start --fixture <events.jsonl>
```

Both use the same resident loop. The loop watches the selected source when the platform supports it and always performs fallback polling. The default fallback interval is three seconds.

The replica-tested SQLite source uses the same loop:

```bash
scripts/autopilot --state-dir <dir> run \
  --source-adapter messages_sqlite \
  --messages-db <synthetic-replica.db>
```

`--messages-db` must be explicit. Use only a disposable Messages-shaped SQLite replica containing synthetic data; never point this stage at the real Messages database. The adapter opens SQLite in read-only URI mode, enables query-only enforcement, watches the database and sidecars when present, and polls by per-chat message row ID as the correctness fallback.

Select ephemeral Codex decisions explicitly:

```bash
scripts/autopilot --state-dir <dir> run \
  --fixture <events.jsonl> \
  --decision-adapter codex-app-server
```

The default remains `mock`. `--codex-timeout` bounds resident-runtime startup
and each Codex decision. The controller starts one app-server process and reuses
it, while each synthetic chat receives a distinct ephemeral thread and hashed
empty workspace. Thread identity is scoped to source, chat activation, and chat,
so a replacement source or reactivated chat cannot inherit stale context.
Installed plugins, MCP servers, apps, browsing, shell tools,
computer use, and multi-agent tools are disabled. A parent Codex sandbox may
still require one bounded approval for the nested model request.

`start` is process convenience only. It does not register with `launchd`, install `SMAppService`, launch at login, or promise restart after logout, reboot, or process failure.

## Controls

```bash
scripts/autopilot --state-dir <dir> status --json
scripts/autopilot --state-dir <dir> pause
scripts/autopilot --state-dir <dir> resume
scripts/autopilot --state-dir <dir> resume-chat --chat-id <id>
scripts/autopilot --state-dir <dir> stop
```

- `pause` durably prevents new decisions and mock sends.
- `resume` validates configuration and state before continuing. It also resets a runtime-recovery circuit breaker after the blocked state has been reviewed.
- `resume-chat` explicitly acknowledges and clears one safety pause. Global resume or reconfiguration must not clear it.
- `stop` writes a request into private state and waits for the controller's exclusive lock to release; it does not signal a PID blindly.
- `status` reports redacted health, counts, controller mode, and whether the watcher is attached.

## Recovery contract

- A second controller is rejected by an exclusive state lock. Runtime controls are authorized by the private state directory's filesystem permissions.
- Exact event IDs are deduplicated before cursor checks.
- Ledger, cursor, retry, and backlog state are scoped to source identity; backlog boundaries are also scoped to chat activation.
- Claims expire and can be recovered after a crash.
- Known pre-send failures use bounded retry with backoff.
- A mock send accepted before a synthetic crash is reconciled before any retry.
- An uncertain mock send pauses that chat and is never repeated automatically.
- A changed contract pauses the controller.
- A newer event, manual outbound event, global pause, or scope change invalidates an in-flight draft.
- A decision thread is retained only after a terminal no-action/escalation or a verified mock send. Invalid output, cancellation, supersession, failed pre-send validation, dispatch failure, and uncertain dispatch evict only that source/activation/chat thread before retry or recovery.
- Per-chat eviction uses the version-matched stable `thread/delete` method to release the orphaned ephemeral server thread. A normal delete rejection is reported as cleanup debt without resetting unrelated chats; a transport/protocol failure still invokes runtime recovery.
- Pause, configuration change, or stop terminates the resident Codex process and any in-flight turn before mock dispatch. Resume creates a fresh process and fresh chat threads.
- An unexpected process exit or protocol failure necessarily clears all ephemeral threads. Recovery uses exponential backoff and stops after three consecutive failures; a successful decision, five stable seconds, or an explicit `resume` resets the circuit breaker. Any observed tool activity or server request fails closed.
- A bounded protocol dispatcher continuously drains app-server stdout and stderr, including while no decision is active. Turn notifications are bounded and irrelevant idle notifications are discarded.
- Runtime workspaces and SQLite state are removed on shutdown. A controller-owned startup scavenges safe stale runtime directories from an interrupted prior run; cleanup failures remain visible in status.
- Unknown or deprecated strict-profile settings fail closed before dispatch.
- Invalid fixtures, source-schema drift, ambiguous message-to-chat joins, missing configured chat hashes, and unsupported state schemas fail closed.

Runtime state contains contract data, scope, cursors, hashes, claims, mock outcome identifiers, counts, and redacted health. It must not contain raw fixture bodies or generated reply text.

## Stop conditions

Background readiness means the controller owns its lock, has validated the source, and has committed backlog boundaries. Initial decisions may still be running.

Stop and report rather than improvising when:

- The adapter profile is not `synthetic_fixture` or replica-only `messages_sqlite`, an approved decision adapter, and mock dispatch.
- State integrity or schema validation fails.
- The selected synthetic source is invalid.
- Process ownership cannot be authenticated.
- A requested action would access Messages, contacts, permissions, Apple Events, or a live send path.

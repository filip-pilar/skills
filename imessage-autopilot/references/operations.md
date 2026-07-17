# Operations and recovery

The bundled CLI runs one resident controller and one constrained Codex app-server process. Each selected chat has its own ephemeral Codex thread. Best-effort filesystem events provide fast wakeups; a three-second poll is always the correctness fallback.

## Run

Foreground:

```bash
scripts/autopilot run --messages-db ~/Library/Messages/chat.db
```

Detached for the current login session:

```bash
scripts/autopilot start --messages-db ~/Library/Messages/chat.db
```

Both accept `--poll-seconds` from 2 through 5. `start` launches the same CLI and installs no `launchd` job, app bundle, login item, or reboot persistence. A private lock rejects a second controller.

## Controls

```bash
scripts/autopilot status
scripts/autopilot pause
scripts/autopilot resume
scripts/autopilot resume --chat-id <opaque-chat-id>
scripts/autopilot stop
```

- `status` reports only configuration hash, mode, runtime health, selected chat IDs, pause reasons, redacted outcome counts, and the last error.
- `pause` durably blocks new decisions and sends and closes the resident runtime. Messages received while paused are left for the user; `resume` establishes a fresh boundary rather than answering that backlog.
- Global `resume` reactivates the reviewed contract. Chat-specific `resume` acknowledges one inspected safety pause without retrying its uncertain event.
- `stop` requests shutdown through controller state and waits for the lock to be released. A later `run` or `start` also establishes a fresh boundary.
- Reconfiguring pauses globally and resets boundaries when the new generation is resumed.

## Processing and crash contract

For each selected chat, the controller:

1. Reads only rows after its durable boundary.
2. Ignores a burst ending in an outbound human message.
3. Escalates unsupported content without sending.
4. Allows a short quiet interval to coalesce a rapid inbound burst, then asks the chat's isolated Codex thread for `reply`, `no_action`, or `escalate`.
5. Re-reads the boundary immediately before send; a newer inbound or outbound message invalidates the draft.
6. Transactionally records `attempted`, then invokes the Poke-derived fixed AppleScript program.
7. Records `sent` after command success. A failure or crash that leaves `attempted` is changed to `uncertain`, pauses that chat, and is never sent again automatically.

This deliberately prefers a possible missed reply over a duplicate. Codex runtime failure pauses globally; it does not enter an automatic restart loop. Review the error and explicitly resume, which establishes a fresh boundary, starts a fresh runtime, and rehydrates isolated chat context when the next message arrives.

## Deferred first live smoke

Run only when the user explicitly says they are ready:

1. Select one direct test chat, configure it, and use foreground `run` with the default three-second poll.
2. Confirm `controller_ready` and healthy `status`.
3. Allow only the expected Automation prompt for Messages, if shown.
4. Trigger one inbound message from the other participant or device and observe at most one reply.
5. Check status, then pause and stop immediately.
6. Review schema compatibility, read and Apple Events attribution, latency, delivery, deduplication, uncertainty behavior, and retained permissions.

Do not broaden scope or test detached operation in the same smoke. Until this succeeds, describe live compatibility and sending as unproven.

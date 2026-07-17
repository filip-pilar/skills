# Synthetic setup

Use this procedure for first use, readiness checks, or re-entry after a failure.

## Check readiness

Run:

```bash
scripts/autopilot doctor --json
```

A ready result establishes only that the bundled synthetic controller can run. It does not test or request macOS privacy permissions and does not establish live Messages compatibility.

For the Codex decision adapter, run:

```bash
scripts/autopilot doctor --decision-adapter codex-app-server --json
```

This checks the local Codex CLI but does not make a model request or prove authentication. Prove authentication only through an approved synthetic rehearsal.

The prototype requires:

- Python 3.11 or newer.
- A writable private state directory created as `0700`.
- A readable user-supplied JSONL fixture for `run` or `start`.
- The bundled runtime prompt and response schema.
- An authenticated Codex CLI with app-server support when `codex-app-server` is selected.

Without `--state-dir`, the prototype uses a stable per-user directory under the operating system's temporary directory. This supports current-session crash recovery without claiming durable storage across reboot. Use a nonce-scoped `--state-dir` for rehearsals and remove it afterward.

The current profile must report `synthetic_fixture` as the source, either `mock` or `codex-app-server` as the selected decision adapter, and `mock` as dispatch. If another profile appears, stop rather than continuing.

The CLI refuses linked, shared, or otherwise unsafe state roots and linked state files. It must not change an unrelated directory's permissions to make it acceptable.

## Fixture format

Each nonblank line is one JSON object:

```json
{
  "event_id": "event-1",
  "chat_id": "chat-alice",
  "source_seq": 1,
  "direction": "inbound",
  "kind": "text",
  "body": "Are we still meeting?",
  "participants_hash": ""
}
```

Optional `simulate` values exercise bounded failures:

- `codex_timeout`
- `invalid_codex_output`
- `send_failure`
- `uncertain_send`
- `crash_after_send`

`codex_delay_ms` adds synthetic decision latency for race testing.

Never point the prototype at a Messages database, Messages directory, contacts export, or real conversation transcript.

`codex-app-server` starts one controller-owned stdio process and creates one
ephemeral Codex thread per synthetic source, chat activation, and chat. Each
thread has a hashed empty
working directory, read-only sandbox, approval policy `never`, disabled project
guidance, plugins, MCP, apps, search, shell, browser, computer use, and
multi-agent tools, schema-constrained output, and a bounded timeout. The
adapter verifies the returned thread constraints, passes no chat identifier or
participant hash, rejects tool activity and server requests, and never persists
the prompt, thread ID, or generated reply in controller state. Runtime SQLite
and workspaces are private temporary data removed when the resident process
stops.

The app-server command is currently experimental, so protocol or constraint
drift fails closed. The adapter uses only the stable API surface and does not
opt into experimental methods. An uncommitted decision invalidates only its own
chat thread; a transport or protocol failure necessarily discards every
ephemeral thread. Runtime recovery uses bounded exponential backoff and stops
after three consecutive failures until stability or explicit `resume` resets
the circuit breaker.

When another Codex task launches this nested CLI, the outer sandbox may require
approval for the bounded model request. That approval does not relax the nested
profile. An explicit request for the bounded synthetic pass already supplies
user intent; use the native approval mechanism when technically required
without separately asking the same consent question. Do not add a durable
command rule automatically.

## Permission attribution

Permission attribution is deliberately unproven. Do not infer foreground or background behavior from this prototype. A future live-adapter stage must test read and Apple Events attribution separately for `run` and `start`, with explicit authorization.

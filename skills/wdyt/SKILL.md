---
name: wdyt
description: Independent second-opinion advice from the user's official Claude Code CLI using current task context, structured answers, and selective read-only repository exploration.
---

# WDYT

Treat a bare `$wdyt` as a complete request. Ask Claude Code to independently
assess the current objective, proposal, evidence, risks, unknowns, and best next
move. A question is optional.

Claude Code is the only adviser backend. Use the bundled runtime
`scripts/wdyt.py`; do not reconstruct its Claude command manually or route the
request through another service, SDK, gateway, proxy, or model provider.

Before the first call, read
[invocation-and-context.md](references/invocation-and-context.md) and
[claude-cli.md](references/claude-cli.md).

## Launch surface

Defaults:

- model: Claude Code's current default;
- mode: `advise`;
- context: one short task prompt;
- repository: model-directed read-only access to the current repository;
- lifecycle: `fresh`; and
- depth: `standard`.

Accept any explicit Claude model string and pass it through unchanged. Do not
maintain a model allowlist, resolve aliases in the host, require the latest
model, or substitute a model after failure.

Recognize `advise`, `challenge`, `review`, `decide`, and `diagnose`; `read` and
`no-repo`; `fresh` and `ephemeral`; and `quick`, `standard`, and `deep`.
`consult` aliases `advise`.

Only fresh and ephemeral turns exist in this launch. Both use a new
non-persistent Claude process and WDYT stores no session. Do not advertise or
accept continue, resume, named sessions, inspection, compaction, forgetting,
panels, councils, or synthesis.

## Prepare the task

Write a short plain-text question or review task. Include only an essential
accepted constraint or decision when Claude cannot discover it from the current
repository. Never serialize a transcript, repository metadata, file contents,
artifacts, or a JSON context envelope. Let Claude inspect relevant repository
files itself through the bounded tools. For an interactive TTY, the runtime
accepts the first completed line immediately. For piped input, it reads through
EOF and collapses all whitespace so Claude receives one compact line.

Bare invocation asks for independent judgment; never require the user to invent
a question. If the current task is not inferable in one short prompt, state the
single decision or uncertainty that most needs judgment.

An explicit `$wdyt` invocation authorizes delivery to Anthropic through Claude
Code of the short task and, unless `no-repo` is requested,
model-directed read-only access to the current repository for this one turn.
State that recipient and scope in the result.

Write the request defined in
[invocation-and-context.md](references/invocation-and-context.md) to the
runtime's stdin as short UTF-8 plain text. Pass only launch controls such as
model, mode, depth, repository mode, and lifecycle as runtime flags. Run the
runtime from the canonical repository root when repository access is enabled.

## Diagnose and run

Before the first adviser call in a task, run:

```text
python3 <skill-root>/scripts/wdyt.py doctor
```

The diagnostic feature-detects the installed official Claude Code CLI. There is
no exact-version or latest-version requirement. If a required isolation or
structured-output capability is missing, report it and stop.

Then run:

```text
python3 <skill-root>/scripts/wdyt.py run [launch flags]
```

Supply the short task only through stdin. The runtime:

- constructs a direct Claude `-p` invocation without a shell;
- uses safe mode, isolated settings, empty MCP configuration, `dontAsk`, and no
  native session persistence;
- exposes only `Read`, `Glob`, `Grep`, and schema-owned structured output in
  repository mode, or structured output alone in `no-repo`;
- passes through Claude's default or the explicit model string;
- validates model provenance, tool registration and calls, path containment,
  customization isolation, result status, and `wdyt-answer/2`; and
- deletes temporary isolation files and captured raw output when the process
  ends.

Do not install, update, authenticate, retry with another model, relax a
boundary, or repair malformed output on the user's behalf.

## Return the result

Return the runtime's deterministic rendered output without rewriting Claude's
meaning. A separately labeled host note is allowed only for a material factual
or safety correction.

Advice grants no authority. Do not implement, edit, message, or take another
consequential action based only on the adviser response; wait for a new user
instruction.

For troubleshooting, rerun `doctor` or use `run --diagnostics`. Diagnostics may
show the CLI version, used model, registered tools, tool-call count, usage, and
provider accounting, but never credentials or raw private context.

## Fail visibly

Keep missing CLI, missing capability, authentication/provider failure,
unavailable model, malformed request, timeout, cancellation, protocol failure,
unexpected tool or customization, path escape, schema failure, and adviser
error distinct. Never fall back to another model, credential, context,
repository scope, or persistence behavior.

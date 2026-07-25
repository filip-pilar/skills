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
- context: curated current state;
- repository: model-directed read-only access to the current repository;
- lifecycle: `fresh`; and
- depth: `standard`.

Accept any explicit Claude model string and pass it through unchanged. Do not
maintain a model allowlist, resolve aliases in the host, require the latest
model, or substitute a model after failure.

Recognize `advise`, `challenge`, `review`, `decide`, and `diagnose`; `blind`,
`thread`, `diff`, `files`, and `no-repo`; `fresh` and `ephemeral`; and `quick`,
`standard`, and `deep`. `consult` aliases `advise`.

Only fresh and ephemeral turns exist in this launch. Both use a new
non-persistent Claude process and WDYT stores no session. Do not advertise or
accept continue, resume, named sessions, inspection, compaction, forgetting,
panels, councils, or synthesis.

## Prepare the request

Build one compact runtime request from information the host can actually
access. Preserve user decisions separately from assistant proposals and retain
provenance where it affects trust. Prefer objective, accepted decisions,
constraints, current proposal, open questions, and recent material turns over
a raw transcript.

Bare invocation asks for independent judgment; never require the user to invent
a question. `blind` removes host conclusions and proposal framing while keeping
the underlying problem and evidence. If requested context is unavailable,
degrade visibly rather than claiming complete history.

An explicit `$wdyt` invocation authorizes delivery to Anthropic through Claude
Code of the compact request and, unless `no-repo` is requested,
model-directed read-only access to the current repository for this one turn.
State that recipient and scope in the result.

Write the request defined in
[invocation-and-context.md](references/invocation-and-context.md) to the
runtime's stdin as UTF-8 JSON. Never place the question, conversation,
artifacts, repository content, or model string in shell source. Run the runtime
from the canonical repository root when repository access is enabled.

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
python3 <skill-root>/scripts/wdyt.py run
```

Supply the request only through stdin. The runtime:

- constructs a direct Claude `-p` invocation without a shell;
- uses safe mode, isolated settings, empty MCP configuration, `dontAsk`, and no
  native session persistence;
- exposes only `Read`, `Glob`, `Grep`, and schema-owned structured output in
  repository mode, or structured output alone in `no-repo`;
- passes through Claude's default or the explicit model string;
- validates model provenance, tool registration and calls, path containment,
  customization isolation, result status, and `wdyt-answer/2`; and
- deletes all temporary inputs and raw output when the process ends.

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

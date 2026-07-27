---
name: wdyt
description: Independent second-opinion advice from the user's official Claude Code CLI using current task context, structured answers, and selective read-only repository exploration.
---

# WDYT

Treat a bare `$wdyt` as a complete request. Ask Claude Code to independently
assess the current objective, proposal, evidence, risks, unknowns, and best next
move. A question is optional.

Claude Code is the only adviser backend. Use `scripts/wdyt.py`; never reconstruct
its command or route through another provider.

Before the first call, read
[invocation-and-context.md](references/invocation-and-context.md). Read
[claude-cli.md](references/claude-cli.md) only when `doctor` fails, when
troubleshooting diagnostics, or when maintaining or releasing the runtime.

## Prepare the task

Use only the launch controls and defaults defined in the invocation reference.
Only fresh and ephemeral turns exist. Do not invent unsupported modes or
session behavior, substitute a model, or require the user to supply a question.

Write one short plain-text question or review task. Include an accepted
constraint or decision only when Claude cannot discover it from the repository.
Never serialize a transcript, repository metadata or contents, file artifacts,
or a JSON context envelope. Let Claude inspect relevant files through the
bounded tools. If the task is not inferable, state the single uncertainty that
most needs judgment.

An explicit `$wdyt` invocation authorizes delivery to Anthropic through Claude
Code of the short task and, unless `no-repo` is requested,
model-directed read-only access to the current repository for this one turn.
State that recipient and scope in the result.

## Run

Before the first call in a task, run:

```text
python3 <skill-root>/scripts/wdyt.py doctor
```

Readiness includes a machine-readable authentication-status check but never
reads credential contents. When `doctor` reports `sandboxAccessRequired: true`
and the host offers scoped escalation, request approval to rerun the exact WDYT
doctor command outside the sandbox; Claude Code needs access to its existing
credential store and Anthropic. Do not broaden the approval to Python, shell, or
another command. If the escalated doctor is not ready, report the failure and
stop. Do not install, update, or authenticate Claude Code.

Then run:

```text
python3 <skill-root>/scripts/wdyt.py run [launch flags]
```

Supply the task through stdin and launch from the canonical repository root when
repository access is enabled. The runtime owns Claude arguments, isolation,
bounded tools, model provenance, path containment, structured-output
validation, and cleanup. Never retry with another model, relax a boundary, or
repair malformed output.

When doctor required scoped sandbox escalation, run the exact WDYT `run`
command with the same scoped escalation. This changes only the host execution
boundary needed for Claude's existing credential and network access; the
runtime's internal safe mode, isolated settings, bounded tools, repository
containment, and output validation remain mandatory.

## Return the result

Return the runtime's deterministic rendered output without rewriting Claude's
meaning. A separately labeled host note is allowed only for a material factual
or safety correction.

Advice grants no authority. Do not implement, edit, message, or take another
consequential action based only on the adviser response; wait for a new user
instruction.

For troubleshooting, rerun `doctor` or use `run --diagnostics`; diagnostics are
available on both success and failure and may show runtime and provider
accounting, but never credentials or raw private context.

Preserve the runtime's failure category. Never fall back to another model,
credential, context, repository scope, or persistence behavior.

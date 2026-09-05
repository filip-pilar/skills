# Runtime invocation and task

Invoke `scripts/wdyt` directly from the canonical repository root, pass controls
as flags, and send only the short UTF-8 task through stdin. Do not prefix it
with Python, a shell, or another launcher. The task is plain text, not JSON, and
must not contain a transcript, file contents or artifacts, or serialized
repository metadata.

```text
<skill-root>/scripts/wdyt run \
  --model claude-opus-5 \
  --mode review \
  --depth standard \
  --repository read \
  --lifecycle fresh
```

Interactive TTY input completes after its first line. Piped input is
EOF-delimited and normalized to one whitespace-collapsed line. The result may
not exceed 768 UTF-8 bytes. Prefer one question and at most one essential
constraint.

Defaults:

| Field | Default | Values |
| --- | --- | --- |
| `model` | omitted | Any non-empty Claude model string, passed through unchanged |
| `mode` | `advise` | `advise`, `challenge`, `review`, `decide`, `diagnose` |
| `depth` | `standard` | `quick`, `standard`, `deep` |
| `repository` | `read` | `read`, `off`; `no-repo` aliases `off` |
| `lifecycle` | `fresh` | `fresh`, `ephemeral` |

`consult` aliases `advise`. Omit `--model` or use `auto` for Claude Code's
default; every other non-empty model string passes through unchanged. There is
no catalogue, alias resolution, preferred model, or fallback. Fresh and
ephemeral both start non-persistent processes. Continuation, named sessions,
panels, and synthesis are unsupported.

When repository access is on, Claude discovers evidence through `Read`, `Glob`,
and `Grep`; `no-repo` exposes none of them. Answers cite repository evidence
with logical `/repo` paths, the supplied task as `task`, and inference with a
null reference.

In a host sandbox that hides macOS Keychain or blocks Anthropic network access,
`doctor` reports `sandboxAccessRequired: true`. A host with a scoped escalation
mechanism may rerun only the exact WDYT doctor and run commands outside that
host sandbox. The Claude child still uses WDYT's safe mode, isolated settings,
empty MCP configuration, bounded tools, and path validation.

A host may instead pre-authorize the absolute dedicated launcher with an
exec-policy rule restricted to the `doctor` and `run` subcommands. Such a rule
is standing authorization for WDYT only. It must not match `python3`, a shell,
`claude`, another script, or the launcher without one of those two subcommands.

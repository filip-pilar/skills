# Claude Code runtime contract

`scripts/wdyt` is the only host entrypoint. It uses macOS system Python in
isolated mode to execute the adjacent `wdyt.py`, which is the normative launch
implementation. The runtime invokes the official `claude` executable directly
as one child process; do not duplicate its argument construction in the host.

The dedicated launcher exists so a host can pre-authorize only WDYT without
allowing Python, a shell, or `claude` generally. Its executable path and
adjacent runtime must be regular files in an installed skill package outside
repositories writable by the agent; symlinks and bare-name invocation fail
closed. A Codex rule should match that absolute path followed by only `doctor`
or `run`; the runtime remains responsible for validating every later argument.

## Compatibility policy

WDYT has no exact-version pin and does not require the latest Claude Code.
`doctor` resolves the installed `claude`, checks that it identifies itself as
Claude Code, reads print-mode help, feature-detects the required flags, and
checks only the machine-readable authentication status. It never reads or emits
credential contents.

Codex's macOS sandbox can hide Claude's Keychain credential and block Anthropic
network access. A logged-out result observed there is not proof that the
unsandboxed CLI is logged out. `doctor` reports this as
`sandboxAccessRequired: true`; after a scoped host approval, the exact WDYT
command must be rerun outside the host sandbox. WDYT's child-process isolation
and tool boundary remain unchanged. The active `CODEX_SANDBOX` marker identifies
that boundary; `CODEX_SANDBOX_NETWORK_DISABLED=1` can remain in the environment
after escalation, so that network marker alone is not treated as proof that the
escalated process is still sandboxed.

Required capabilities cover:

- streaming machine output and structured JSON Schema output;
- replacement system prompt;
- safe mode and isolated setting sources;
- strict empty MCP configuration;
- exact built-in tool registration;
- non-interactive `dontAsk` permissions; and
- no native session persistence.

Optional flags such as explicit model selection, effort, partial-message
streaming, and prompt suggestions are used only when present. An explicit model
request fails before inference if that installed CLI cannot accept `--model`.
The runtime never infers compatibility from version numbers.

If a CLI accepts the arguments but emits an unexpected model, tool,
customization, path, event, or answer shape, the call fails visibly. This is the
upgrade-compatibility mechanism.

## Model policy

Omitting `model` omits `--model` and uses Claude Code's current default. Any
explicit non-empty model string is passed unchanged as one argv value. WDYT has
no allowlist, aliases, latest-model requirement, per-model prompt, or fallback.

The runtime trusts only machine output for the used model. Init must identify a
model, and every successful assistant event must agree with it. Requested and
used model names may differ when Claude resolves an alias; the renderer shows
that difference.

## Repository boundary

For repository mode, the runtime:

- resolves the current working directory as the canonical root;
- writes private settings allowing `Read`, `Glob`, and `Grep` only beneath that
  root;
- launches Claude from the root without `--add-dir`;
- registers `Read`, `Glob`, and `Grep`; and
- requires init to expose exactly those tools plus schema-owned
  `StructuredOutput`.

For `no-repo`, it launches from a private temporary directory, supplies no
repository allow rules, passes an empty `--tools` value, and requires init to
expose only `StructuredOutput`.

Every observed tool call must be from the expected set. Absolute, parent
traversal, wildcard-prefix, and resolved symlink paths are checked against the
canonical root. Any path escape fails the turn.

## Isolation

Each call uses:

```text
-p
--output-format stream-json
--verbose
--system-prompt <trusted prompt>
--json-schema <bundled schema>
--safe-mode
--disable-slash-commands
--strict-mcp-config
--mcp-config <empty private config>
--no-chrome
--no-session-persistence
--permission-mode dontAsk
--settings <private settings>
--setting-sources ""
--tools <bounded list>
```

The runtime may add feature-detected optional flags. It never passes fallback,
resume, session, bypass, agent, plugin, extra-directory, file-download,
worktree, remote-control, or non-empty MCP options.

Claude's existing authentication remains the user's responsibility. WDYT
checks whether Claude Code reports an authenticated state, but does not inspect
credentials, initiate login, install or update Claude Code, or switch
authentication paths. To keep its Anthropic disclosure accurate, it fails
closed when Claude Code reports a non-first-party provider or the environment
sets an explicit Bedrock, Vertex, Foundry, or alternate base-URL route. It
reports only the routing variable names, never their values.

Private temporary files use `0700` directories and `0600` files. They contain
only isolated settings and empty MCP configuration. One whitespace-normalized,
compact plain-text task travels through stdin; no context envelope or repository
content is serialized by the host. Interactive TTY input returns after its first
completed line; piped input is read through EOF before normalization. Temporary
files and captured raw JSONL disappear when the process ends.

## Output gate

Before rendering, the runtime requires:

1. successful process exit plus compatible init and result events;
2. one machine-attested used model with agreeing successful assistant events;
3. exactly the expected registered tools and no unexpected tool calls;
4. empty MCP, plugin, skill, and slash-command inventories when exposed;
5. all repository paths contained beneath the canonical root;
6. successful, non-error result status; and
7. one strict `wdyt-answer/2` object with no additional fields.

Built-in agent definitions may appear as non-callable inventory. They are safe
only because `Agent`, `Task`, and `SendMessage` are absent from the registered
tools and cannot be called.

The renderer formats validated fields deterministically. It does not repair,
summarize, or reinterpret Claude's answer.

The runtime moves structured-output constraints that Claude does not support
into field descriptions in the schema passed to the CLI, while retaining and
enforcing the complete bundled schema after generation.

## Failure and cancellation

The runtime distinguishes local request errors, missing CLI, missing
capabilities, authentication failure, required usage credits, rate limits,
provider or invocation failure, timeout, cancellation, malformed JSONL,
model-provenance disagreement, unexpected capabilities, path escape, and
answer-schema failure.

On timeout or host cancellation, it terminates the Claude process group and
returns no partial answer. It never retries with another model or weaker
settings.

`run --diagnostics` emits sanitized metadata on success or failure. Failure
diagnostics may include the category, exit status, result subtype, API status,
terminal reason, error count, and whether stderr or a result event existed.
They never emit provider error text, credential material, the task, repository
contents, or raw JSONL.

# Validation and troubleshooting

## Disposable fixture

Create a temporary git repository with harmless files:

```text
alpha.txt: ALPHA_TOKEN=17
beta.txt:  BETA_TOKEN=29
```

Restrict prompts to this fixture and forbid credential/network access. Do not begin with permission bypass or multi-agent workflows in a real repository.

## Direct route

Run `scripts/test_route.sh` for the selected wire API. It accepts gateway roots with or without `/v1`. Require exact output and inspect returned model/usage metadata. Test unauthenticated rejection separately.

## Claude Code

Start with:

```bash
ROUTE_LAUNCHER -p --max-turns 1 --output-format json \
  'Reply with exactly HARNESS_OK.'
```

Then test reading the fixture, a write/shell cycle, one subagent, parallel subagents, selected effort controls, and user-required flags. Inspect `modelUsage`, resolved models, and transcripts.

For the OpenAI-specific `claudex` launcher, run `scripts/test_openai_efforts.sh` before `scripts/test_claudex_ultracode.sh`. Do not call ToolSearch compatible until a forced harmless ToolSearch call succeeds.

## Codex

Start with an ephemeral, read-only, JSON `codex exec` request and exact output. Then select the named profile and test streaming, fixture tools, approvals/sandbox, one subagent, parallel subagents, resume, compaction, and images if required.

For tool acceptance, require the expected tool-call event, a successful tool-result event, and an output assertion tied to the fixture. If the transcript contains an unsupported/rejected tool followed by model prose claiming the action succeeded, mark that capability `unsupported`; do not accept the prose. Repeat subagent tests in a non-ephemeral disposable profile because an ephemeral parent-thread failure is a separate harness limitation.

For a mixed-provider custom agent, require all of the following:

- Parent state records the intended OpenAI model and CLIProxyAPI provider.
- The parent emits a completed spawn event with a non-empty child thread ID.
- Child state records the explicitly selected child model, the inherited CLIProxyAPI provider, the requested effort, and the expected agent role.
- The child transcript contains the required fixture tool call and successful tool result.
- The parent wait event names the child ID and contains the child's returned assertion.

A task label that resembles the custom-agent name is not evidence. If child state still records the parent model, mark custom-agent model selection unsupported for that parent/orchestration mode.

## Capability report

Use four states:

- `verified`: exercised successfully through the harness.
- `partial`: works with a documented warning or reduced semantics.
- `unsupported`: exercised and rejected/incompatible.
- `not tested`: no evidence yet.

Track basic inference, streaming, read tools, write/shell, reasoning controls, subagents, images, prompt caching, resume, and provider-hosted tools separately.

For xAI, include direct Responses and Chat Completions at every documented effort, provider-native web/X search event inspection, Claude Code stream-json thinking events, explicit resume, shorthand continue, hostile `--settings` precedence, parallel subagents, and a small Workflow run. Keep image/video generation separate from text-harness compatibility.

## Common failures

### Login succeeds but inference returns 401/403

Token exchange succeeded but inference entitlement, scope, tier, or client policy did not. Do not relogin repeatedly or enable disguise settings. Confirm provider status and offer an API-key route.

### Claude Code main agent works but subagents fail

Inspect global/project Claude settings, agent frontmatter, slot mappings, `CLAUDE_CODE_SUBAGENT_MODEL`, and `--settings` ordering. Exact native model IDs may bypass the intended route.

### Codex chat works but tools or reasoning do not

The custom provider supports basic Responses output but not the full Codex wire contract. Inspect the first failing event/field and mark only that capability unsupported; do not claim full compatibility.

If the model requests a tool name that Codex does not expose, record the exact rejected tool name and keep the route at `partial` even when the model recovers with another tool. Do not add a fake compatibility shim unless the user explicitly chooses that maintenance and trust tradeoff.

### Proxy responds outside a sandbox but not inside

Check sandbox loopback/network policy. A sandbox denial is not proof that the host proxy is down.

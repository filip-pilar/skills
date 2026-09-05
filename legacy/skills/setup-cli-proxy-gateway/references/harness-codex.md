# Codex harness adapter

Verify current behavior in official Codex configuration docs before editing files.

## Isolated profile

Codex profile files live next to the user config as:

```text
$CODEX_HOME/<profile-name>.config.toml
```

Select one with:

```bash
codex --profile <profile-name>
```

Provider definitions cannot live in project `.codex/config.toml`. Build a profile from `assets/codex-proxy.config.toml`, choose a non-reserved provider ID, and keep the local client key in the named environment variable rather than TOML.

Install `assets/codex-proxy.zsh` under a route-specific name such as `codex-claude` or `codex-grok`. Store only the local gateway key in a mode-`0600` token file; the launcher exports it for the selected profile and forwards all Codex arguments. Do not place upstream OAuth/API credentials in that file.

Typical profile:

```toml
model = "discovered-model-id"
model_provider = "cli_proxy"

[model_providers.cli_proxy]
name = "CLIProxyAPI"
base_url = "http://127.0.0.1:8317/v1"
wire_api = "responses"
env_key = "CLI_PROXY_TOKEN"
```

Custom provider IDs cannot be `openai`, `ollama`, or `lmstudio`.

## Experimental Codex app and command-backed authentication

Codex app inherits base user `config.toml`; named profile selection is a CLI feature. Treat this as experimental because custom-provider transport, custom model catalogs, renderer gates, and picker behavior can change independently. For an app route, explain that selecting a gateway provider in base config affects new app and CLI sessions until rolled back.

GUI-launched apps cannot rely on interactive-shell exports. Install `assets/read-cli-proxy-token.sh` at a stable mode-`0700` path and use a mode-`0600` one-line local client-token file. Configure `[model_providers.<id>.auth]` from `assets/codex-proxy-command-auth.config.toml`, replacing `__API_BASE_URL__` with a URL that already ends in `/v1`. Do not combine command auth with `env_key`, `experimental_bearer_token`, or `requires_openai_auth`.

Test the command helper with its output discarded, then test one tiny Codex request without `CLI_PROXY_TOKEN` in the environment. A successful command-auth CLI request verifies only the inherited credential mechanism. It does not prove that a custom model appears in the picker or that a new app task uses it. Fully quit/relaunch the app and verify a new task end to end before claiming app support. Do not patch ASAR/app bundles as part of this skill.

## Temporary first test

Before writing a profile, use command-line `-c` overrides with `--ephemeral` and a harmless prompt. Keep `approval_policy` as a top-level CLI option if the installed build requires that ordering. Example shape:

```bash
CLI_PROXY_TOKEN='local-key' codex -a never exec \
  -c 'model_provider="cli_proxy"' \
  -c 'model="MODEL"' \
  -c 'model_providers.cli_proxy.name="CLIProxyAPI"' \
  -c 'model_providers.cli_proxy.base_url="http://127.0.0.1:8317/v1"' \
  -c 'model_providers.cli_proxy.env_key="CLI_PROXY_TOKEN"' \
  -c 'model_providers.cli_proxy.wire_api="responses"' \
  --ephemeral --json -s read-only 'Reply with exactly ROUTE_OK.'
```

Do not preserve literal secrets in shell history when a safer environment source is available.

## Compatibility

- Codex may omit service tiers not advertised by the custom model; record this as a compatibility warning, not a routing failure.
- An unknown custom model may use fallback metadata. Verify the routed model from response events and avoid claiming native context limits, tool support, or model-specific behavior from the Codex banner alone.
- Do not assume `model_reasoning_effort` maps to Anthropic thinking or xAI reasoning. Test each value and inspect usage/response metadata.
- Test `codex exec`, streaming events, tools, sandbox approvals, images, compaction, subagents, and resume separately.
- Verify tools from emitted tool-call and tool-result events. A correct final answer after an unsupported or rejected tool call is not evidence that the tool worked.
- Test subagents both with and without `--ephemeral`. Ephemeral runs may lack a persisted parent thread, while a custom model may independently call a provider-style tool name such as `spawn_agent` that Codex does not expose.
- Preserve ordinary `codex` by selecting the proxy profile explicitly.

## Mixed-provider custom subagent

Codex custom-agent TOML can select a child model, but the child inherits the parent session's `model_provider`. To run an OpenAI parent with a Grok child, route the OpenAI parent through the same CLIProxyAPI provider and set only the child `model` to a currently discovered Grok ID. Do not keep the parent on the native `openai` provider and expect the child to switch providers.

Copy and customize `assets/codex-grok-subagent.toml` to `~/.codex/agents/` or a trusted project's `.codex/agents/`; replace its model placeholder with an ID returned by the authenticated gateway. Define the CLIProxyAPI provider in a user-level profile/config; provider definitions in project config are ignored. Verify that the parent and child state both record the gateway provider, while their model IDs differ.

Prefer `scripts/test_codex_mixed_subagent.sh --parallel 1` and `--parallel 2`. It isolates `CODEX_HOME`, uses command-backed auth, checks state and rollouts, and rejects a matching final answer when no correctly configured child ran.

Inspect the actual parent `spawn_agent` call before claiming support:

- `spawn_agent(agent_type=...)`: role-based custom-agent configuration can apply. Test one child and parallel children.
- `spawn_agent(task_name=...)`: the name is a workflow label, not proof that a same-named custom-agent TOML was applied. Inspect child state; if it inherited the parent model, mark custom model selection unsupported.

Do not enable under-development metadata flags to rewrite a model's reserved collaboration schema; exposing hidden spawn metadata can trigger an upstream reserved-tool-schema rejection. Re-test after Codex/model updates instead.

Named profiles are selected by the CLI. The Codex app inherits `config.toml` but has no documented `--profile` selector, so an app mixed-provider session requires an app-accessible gateway credential and a user-level gateway provider/default for that session. Explain and approve that routing tradeoff before changing the base config.

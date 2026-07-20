# Architecture and route decisions

## Supported scope

This skill supports exactly two harnesses and three provider families:

| Layer | Supported |
|---|---|
| Harness | Codex, Claude Code |
| Provider | OpenAI, Anthropic, xAI |
| Authentication | CLIProxyAPI-supported OAuth, provider API key, matching custom endpoint |

Do not broaden the setup to OpenCode, Gemini, Antigravity, Kimi, or community Plus providers unless the skill itself is intentionally revised.

## Request paths

```text
Claude launcher
  -> Claude Code tools/session UI
  -> Anthropic-compatible request
  -> localhost CLIProxyAPI
  -> OpenAI, Anthropic, or xAI

Codex profile
  -> Codex tools/session UI
  -> Responses request
  -> localhost CLIProxyAPI
  -> OpenAI, Anthropic, or xAI

Codex mixed-provider custom agent
  -> OpenAI parent model through localhost CLIProxyAPI
  -> role-based spawn_agent selects a custom-agent model
  -> Grok child inherits the same CLIProxyAPI provider
  -> CLIProxyAPI routes parent to OpenAI and child to xAI
```

CLIProxyAPI translates protocols and selects credentials. The harness still owns tools, permissions, sessions, subagents, skills, MCP, and terminal behavior.

## Isolation defaults

- Keep bare `claude` native; add `claudex`, `claude-grok`, or another explicit launcher.
- Keep default Codex configuration native; add `$CODEX_HOME/<name>.config.toml` and launch with `codex --profile <name>`.
- Use temporary `-c` overrides and `--ephemeral` for a first Codex test.
- Ask before changing global Claude environment values or the default Codex model/provider.

Codex child sessions inherit their parent provider. A native-OpenAI parent cannot switch only its child to CLIProxyAPI. For a cross-provider child, keep the parent's model OpenAI but route the parent session through CLIProxyAPI so both model IDs share one provider boundary.

Codex ignores `model_provider` and `model_providers` in project `.codex/config.toml`; provider definitions must be user-level or profile files next to the user config.

## Evidence hierarchy

Prefer, in order:

1. Harness output metadata and tool/subagent transcripts.
2. Narrowly filtered proxy routing logs around the test time.
3. Direct response metadata.
4. `/v1/models` provider ownership.

Do not use the model's answer to “what model are you?” as proof.

## Local client key

The `api-keys` entry in CLIProxyAPI config is a local gateway credential, not an upstream provider token. Keep it private even on loopback. A launcher containing it should be mode `0700`; a config/auth file should normally be `0600`.

## Terms-sensitive OAuth

CLIProxyAPI may implement an OAuth flow that a provider does not authorize for arbitrary third-party harnesses. Present the provider's current published position and get explicit user acceptance before testing. Do not add concealment or evasion as part of the setup.

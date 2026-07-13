---
name: setup-cli-proxy-gateway
description: Audit, install, update, configure, test, and troubleshoot CLIProxyAPI as a local model gateway for Codex CLI or Claude Code, with an explicitly experimental Codex app path. Use when Codex needs to authenticate OpenAI/ChatGPT, Anthropic/Claude, or xAI/Grok accounts; route either CLI harness to models from those providers; preserve native behavior with isolated launchers or profiles; migrate from VibeProxy; switch or refresh model mappings; configure compatible custom API endpoints; or validate reasoning, tools, subagents, headless flags, and protocol compatibility.
---

# Set up CLI Proxy Gateway

Connect one of two harnesses—Codex or Claude Code—to OpenAI, Anthropic, or xAI models through a verified loopback CLIProxyAPI service. Discover current capabilities at runtime; do not assume provider flags, model IDs, or reasoning controls remain current.

## Operating contract

- Treat installations, removals, OAuth, API-key changes, daemon changes, paid calls, and global harness settings as mutations. Obtain approval unless the user already authorized that scope.
- Preserve native `codex` and `claude` behavior by default. Add a named Codex profile or separate Claude Code launcher; change global routing only after explaining the tradeoff.
- Never print credential contents, bearer tokens, API keys, complete auth JSON, or unfiltered request logs. Report paths, provider types, counts, ownership, and modes.
- Bind CLIProxyAPI to loopback and disable remote management unless the user explicitly requests remote access.
- Use mainline CLIProxyAPI for OpenAI, Anthropic, and xAI. Do not introduce CLIProxyAPI Plus or unrelated providers for this skill's scope.
- State whether authentication is provider-supported, proxy-supported but terms-sensitive, or API-key based. Explicit user acceptance permits testing a terms-sensitive personal OAuth route; it does not make that route officially supported.
- Do not enable cloaking, identity disguise, anti-detection, or other evasion settings automatically. Report when an unmodified client route is rejected.
- Validate the actual routed model and tools. Model prose, banners, and successful login pages are not routing evidence.

## Workflow

### 1. Audit before changing anything

Run `scripts/audit_gateway.sh`. Supplement it with targeted reads that do not expose secrets.

Record:

- OS, architecture, shell, PATH, and installed Codex/Claude Code versions.
- CLIProxyAPI path, version, current help flags, config, listener, service, and `/v1/models` response.
- Existing VibeProxy, launchers, Codex profile files, Claude settings, and port conflicts.
- Credential-file provider labels, counts, and unsafe modes without reading token values.

Read `references/architecture.md` before proposing a route or migration.

### 2. Refresh current upstream facts

Browse primary sources because this surface changes frequently:

- CLIProxyAPI repository/releases: `https://github.com/router-for-me/CLIProxyAPI`
- CLIProxyAPI guides: `https://help.router-for.me/`
- Codex configuration: `https://learn.chatgpt.com/docs/config-file/config-advanced#custom-model-providers`
- Claude Code docs: `https://code.claude.com/docs/`
- OpenAI models: `https://developers.openai.com/api/docs/guides/latest-model`
- Anthropic models: `https://docs.anthropic.com/en/docs/about-claude/models/overview`
- xAI models: `https://docs.x.ai/docs/models`

Compare upstream with the installed binary's `--help`; prefer verified local behavior when versions differ. Confirm release checksums, authentication flags, harness flags, model catalogs, and documented reasoning controls.

### 3. Define one route

Represent the request as five explicit choices:

```text
surface:  codex-cli | claude-code-cli | codex-app-experimental
harness:  codex | claude-code
provider: openai | anthropic | xai
auth:     oauth | api-key | custom-endpoint
model:    discovered model ID
```

Do not treat Codex CLI and Codex app as interchangeable. CLI profiles are invocation-scoped; the app inherits base user configuration and needs credentials available outside a shell environment. Treat app routing and model-picker behavior as a separate, experimental journey until verified end to end on the installed app build.

If the user has not selected a model, authenticate first, query `/v1/models`, then recommend from the returned catalog. Never hardcode a social-post model ID as the only option.

Read `references/providers.md` for authentication and provider-specific constraints. Read `references/custom-endpoints.md` only when the user supplies an API endpoint or aggregator.

### 4. Preserve and install the gateway

Read `references/installation.md` for installation, migration, minimal config, and service rules.

- Snapshot every path that may change with `scripts/route_transaction.sh snapshot` and retain its generated rollback command.
- Preserve `~/.cli-proxy-api` before replacing VibeProxy or another wrapper.
- Verify downloads against the release checksum manifest.
- Keep the previous working binary/config until validation passes.
- Start in the foreground before installing a per-user service.
- Require authenticated `/v1/models`; reject unauthenticated access.

### 5. Authenticate only selected providers

Confirm current flags from the installed binary. Common mainline routes include Codex/OpenAI OAuth, Claude OAuth, and xAI OAuth, but flags may change.

- Let the user complete browser/device authorization.
- Before OAuth, choose an explicit callback port when the binary supports `-oauth-callback-port` and prove it is free. The tested login flows can display authorization before attempting the callback bind.
- Do not inspect token values after login.
- Restart or reload the proxy when required, then query its model catalog.
- Distinguish browser-login success from inference entitlement with a tiny request.
- For API keys, prefer protected environment/config sources and mode `0600` files.

### 6. Configure the selected harness

For Claude Code, read `references/harness-claude-code.md`. Use `assets/claude-proxy.zsh` for provider-neutral routes and `assets/claudex.zsh` only for the tested OpenAI/GPT effort and Ultracode mapping.

For Codex, read `references/harness-codex.md`. For CLI-only routing, use a named profile based on `assets/codex-proxy.config.toml` plus `assets/codex-proxy.zsh`. For an explicitly requested Codex app experiment, use `assets/codex-proxy-command-auth.config.toml` plus a mode-`0700` copy of `assets/read-cli-proxy-token.sh`; do not depend on shell exports, patch app bundles, or claim model-picker support before an end-to-end app test. Provider settings in project `.codex/config.toml` are ignored. For a Grok custom child under an OpenAI parent, customize `assets/codex-grok-subagent.toml` with a discovered model ID only after the installed parent exposes role-based `spawn_agent(agent_type=...)`; route both parent and child through the same gateway provider.

Install launchers with mode `0700` when they embed a local client key. Forward ordinary harness flags unchanged, including Claude Code `-p`/`--print`, output formats, permission flags, and Codex `exec`, sandbox, approval, and config overrides.

### 7. Validate the route

Read `references/validation.md` and test in increasing cost/risk order:

1. Authenticated model list and unauthenticated rejection.
2. Direct one-token/tiny protocol request.
3. Harness headless request with exact-output assertion.
4. Streaming and one harmless read tool.
5. Disposable read/write/shell cycle.
6. One subagent, then parallel subagents if supported.
7. Provider-specific reasoning controls.
8. User-required interactive, resume, image, permission, and workflow features.

Record `verified`, `partial`, `unsupported`, or `not tested` for each capability and journey in `references/acceptance.md`. A plain chat success does not prove tools, reasoning, caching, images, or subagents.

For a mixed Codex parent/child route, prefer `scripts/test_codex_mixed_subagent.sh` over manual transcript interpretation. Run both its one-child and parallel modes when the user needs subagents.

### 8. Refresh or switch models later

When asked to update or switch models:

1. Re-run the audit and upstream checks.
2. Diff the current `/v1/models` catalog against launcher/profile mappings.
3. Probe new model IDs directly before changing defaults.
4. Preserve provider-specific effort semantics; do not apply GPT suffix conventions to Anthropic or xAI without a successful test.
5. Update only the selected route, retain the prior mapping, and re-run its validation matrix.

### 9. Hand off and rollback

Report the route, installed versions and paths, authentication type, selected model, tested features, expected warnings, global behavior changes, unresolved risks, and exact rollback artifacts. Never include secrets in the handoff.

## Resource routing

- Product boundaries, route matrix, and settings isolation: `references/architecture.md`
- OpenAI, Anthropic, and xAI authentication/model behavior: `references/providers.md`
- Installation, VibeProxy migration, config, and services: `references/installation.md`
- Claude Code launcher, slots, effort, Ultracode, and flags: `references/harness-claude-code.md`
- Codex custom provider profiles and temporary overrides: `references/harness-codex.md`
- OpenAI-/Anthropic-compatible custom endpoints: `references/custom-endpoints.md`
- Capability tests and troubleshooting: `references/validation.md`
- Harness/provider/auth journey matrix: `references/acceptance.md`
- Versioned evidence from completed acceptance runs: `references/compatibility.md`
- Read-only inventory: `scripts/audit_gateway.sh`
- Tiny direct API probe: `scripts/test_route.sh`
- Deterministic mixed Codex subagent acceptance: `scripts/test_codex_mixed_subagent.sh`
- OpenAI effort matrix for explicitly selected models: `scripts/test_openai_efforts.sh`
- Isolated Claude Code Ultracode workflow acceptance: `scripts/test_claudex_ultracode.sh`
- Transactional backup and rollback bundle: `scripts/route_transaction.sh`
- Token-helper unit tests: `scripts/test_token_helper.sh`
- Deterministic ClaudeX launcher/flag tests: `scripts/test_claudex_launcher.sh`
- Transaction/Vibe-reversal tests: `scripts/test_route_transaction.sh`
- Fresh-home audit test: `scripts/test_isolated_home.sh`
- Disposable custom-endpoint tests: `scripts/test_custom_endpoint_mock.sh`
- Listener and OAuth callback collision tests: `scripts/test_port_collision.sh`, `scripts/test_callback_collision.sh`
- Provider-neutral Claude launcher template: `assets/claude-proxy.zsh`
- Tested GPT-specific Claude launcher: `assets/claudex.zsh`
- Codex profile template: `assets/codex-proxy.config.toml`
- Codex command-auth profile template: `assets/codex-proxy-command-auth.config.toml`
- Secure Codex profile launcher: `assets/codex-proxy.zsh`
- App-safe local-token command helper: `assets/read-cli-proxy-token.sh`
- Read-only Grok custom-agent template: `assets/codex-grok-subagent.toml`

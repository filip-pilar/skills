---
name: setup-cli-proxy-gateway
description: Audit, install, update, configure, test, or troubleshoot CLIProxyAPI as a local gateway for Codex CLI or Claude Code. Use for OpenAI/ChatGPT, Anthropic/Claude, xAI/Grok, VibeProxy migration, compatible custom endpoints, isolated model routes, experimental Codex app routing, model refreshes, or validation of reasoning, tools, subagents, headless flags, and protocol behavior.
---

# Set up CLI Proxy Gateway

Connect Codex or Claude Code to an OpenAI, Anthropic, or xAI model through a verified loopback CLIProxyAPI service. Discover current capabilities at runtime; provider flags, model IDs, and reasoning controls are version-sensitive.

## Operating contract

- Obtain approval for installs, removals, OAuth, API-key changes, daemon changes, paid calls, and global harness settings unless already authorized.
- Preserve bare `codex` and `claude` behavior by default. Use a named Codex profile or separate Claude launcher; explain any global-routing change first.
- Never print secrets, complete auth JSON, or unfiltered request logs. Report only safe metadata such as paths, provider types, counts, ownership, and modes.
- Bind the gateway to loopback and disable remote management unless remote access is explicitly requested.
- Use mainline CLIProxyAPI and only OpenAI, Anthropic, xAI, or a user-supplied compatible endpoint. Do not introduce CLIProxyAPI Plus or unrelated providers.
- Label authentication as provider-supported, proxy-supported but terms-sensitive, or API-key based. User acceptance permits testing a terms-sensitive route; it does not make the route officially supported.
- Never enable cloaking, identity disguise, anti-detection, or other evasion. Report an unmodified route rejection.
- Prove the routed model and required tools. Login pages, banners, and model prose are not routing evidence.

## Workflow

### 1. Audit before changes

Run `scripts/audit_gateway.sh`, then use targeted secret-safe reads to inventory the platform, installed harnesses, CLIProxyAPI binary/help/config/listener/service, authenticated model list, credentials and modes, VibeProxy, launchers/profiles/settings, and port conflicts. Read `references/architecture.md` before proposing a route or migration.

### 2. Verify current contracts

Check primary sources: [CLIProxyAPI releases](https://github.com/router-for-me/CLIProxyAPI/releases), [CLIProxyAPI guides](https://help.router-for.me/), [Codex custom providers](https://learn.chatgpt.com/docs/config-file/config-advanced#custom-model-providers), [Claude Code gateways](https://code.claude.com/docs/en/llm-gateway), and current model docs for [OpenAI](https://developers.openai.com/api/docs/guides/latest-model), [Anthropic](https://docs.anthropic.com/en/docs/about-claude/models/overview), and [xAI](https://docs.x.ai/docs/models).

Compare those contracts with the installed binaries' help and behavior. Confirm release checksums, auth and harness flags, catalog contents, and reasoning controls; when versions differ, prefer observed local behavior and report the difference.

### 3. Define one route

Record five choices:

```text
surface:  codex-cli | claude-code-cli | codex-app-experimental
harness:  codex | claude-code
provider: openai | anthropic | xai
auth:     oauth | api-key | custom-endpoint
model:    discovered model ID
```

Treat Codex CLI profiles and Codex app routing as separate journeys: the app inherits base user configuration and cannot rely on shell-only credentials. If no model is selected, authenticate first and recommend from authenticated `/v1/models`; never rely on a social-post model ID. Read `references/providers.md`, plus `references/custom-endpoints.md` only for user-supplied endpoints or aggregators.

### 4. Preserve and install

Follow `references/installation.md`. Before any write, snapshot every affected path with `scripts/route_transaction.sh snapshot` and retain its rollback command. Preserve `~/.cli-proxy-api` during migration, verify release checksums, keep the last working binary/config until acceptance passes, start in the foreground before creating a user service, and require authenticated `/v1/models` with unauthenticated rejection.

### 5. Authenticate the selected provider

Confirm flags from the installed binary and let the user complete browser/device authorization. If supported, choose and preflight an explicit OAuth callback port because some flows display authorization before binding it. Do not inspect tokens after login. Reload as required, query the catalog, and distinguish login success from inference entitlement with a tiny request. Protect API keys and local client-token files with mode `0600`.

### 6. Configure one harness

- **Claude Code:** Follow `references/harness-claude-code.md`. Use `assets/claude-proxy.zsh` for provider-neutral routes and `assets/claudex.zsh` only for its tested GPT effort/Ultracode mapping.
- **Codex:** Follow `references/harness-codex.md`. Use the named-profile template and launcher for CLI routes. Treat app routing as experimental; use command-backed auth, not shell exports or app-bundle patches, and do not claim picker support without an app test. Codex ignores provider settings in project `.codex/config.toml`. A custom Grok child must inherit the same gateway provider as its parent and requires verified role-based spawning.

Install credential-bearing launchers as mode `0700`. Forward ordinary harness flags unchanged.

### 7. Validate in increasing cost and risk

Follow `references/validation.md`:

1. Authenticated catalog and unauthenticated rejection.
2. Tiny direct protocol request.
3. Exact-output headless harness request.
4. Streaming and one harmless read tool.
5. Disposable read/write/shell cycle.
6. One subagent, then parallel subagents if required and supported.
7. Provider-specific reasoning controls.
8. Only user-required interactive, resume, image, permission, and workflow features.

Record each capability and journey as `verified`, `partial`, `unsupported`, or `not tested` using `references/acceptance.md`. Chat success does not prove tools, reasoning, caching, images, or subagents. For mixed Codex parent/child routes, use both modes of `scripts/test_codex_mixed_subagent.sh` when subagents matter.

### 8. Refresh or switch a model

Re-audit and recheck upstream, diff `/v1/models` against the selected mapping, probe new IDs directly, preserve provider-specific effort semantics, change only the selected route, retain its prior mapping, and rerun its acceptance matrix.

### 9. Hand off and roll back

Report the route, versions and paths, auth type, model, verified features, expected warnings, global behavior changes, unresolved risks, and rollback artifacts—never secrets.

## Reference map

- `references/architecture.md`: boundaries, route matrix, and settings isolation.
- `references/providers.md` and `references/custom-endpoints.md`: provider/auth constraints and compatible upstreams.
- `references/installation.md`: installation, migration, service, and rollback procedure.
- `references/harness-claude-code.md` and `references/harness-codex.md`: host-specific configuration and tests.
- `references/validation.md` and `references/acceptance.md`: evidence ladder and result matrix.
- `references/compatibility.md`: dated acceptance evidence only; retest current builds.

Use the scripts and assets named by those references instead of recreating their logic.

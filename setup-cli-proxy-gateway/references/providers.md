# Provider reference

Always confirm flags with the installed `cli-proxy-api --help` and confirm models with authenticated `/v1/models`.

## OpenAI

Authentication options:

- ChatGPT/Codex OAuth through the current CLIProxyAPI Codex login flow.
- Device login when supported by the installed release.
- OpenAI API key through the appropriate native or compatible-upstream config.

Test Responses, streaming, tools, reasoning effort, prompt caching, images, and subagents separately. For Claude Code routing, CLIProxyAPI model suffixes such as `(low)` or `(high)` are proxy conventions and must be probed against the installed version. Discover the selected model's current documented effort set, then pass its model ID explicitly to `scripts/test_openai_efforts.sh` rather than assuming controls from another family or a dated social post.

## Anthropic

Authentication options:

- Anthropic API key through `claude-api-key` configuration.
- Claude OAuth through the current CLIProxyAPI Claude login flow when the user explicitly accepts its support/terms status.
- An Anthropic-compatible custom endpoint backed by Anthropic models.

Claude subscription OAuth is intended by Anthropic for Claude Code and approved surfaces. Treat reuse from Codex as terms-sensitive even for personal use. Test without enabling cloak/evasion settings. Anthropic extended thinking does not automatically map to Codex `model_reasoning_effort`; verify request translation and usage metadata.

## xAI

Authentication options:

- xAI/Grok OAuth through the installed CLIProxyAPI xAI login flow.
- xAI API key.
- An OpenAI-compatible endpoint backed by Grok models.

OAuth browser success does not prove the account tier has inference entitlement. Run a tiny request and report a provider `403` as an entitlement boundary. Verify Responses, tools, reasoning, streaming, and any xAI-hosted search/image features independently; a harness may not expose provider-hosted tools.

For a reasoning-capable Grok model, use `scripts/test_route.sh --reasoning-effort low|medium|high` on Responses and Chat Completions. Record parameter acceptance and returned reasoning-token metadata separately; an exact short answer may legitimately use zero visible reasoning tokens.

After OAuth, verify the new credential mode immediately. CLIProxyAPI 7.2.71 was observed creating an xAI credential as `0644` on macOS; correct it to `0600` before inference if reproduced, without printing the account-bearing filename.

The requested Grok model ID and upstream response/build ID may differ. Treat that as alias resolution only after `/v1/models` attributes the requested ID to xAI and the route is verified.

Test native provider tools directly through Responses. A successful `web_search` may emit `web_search_call`; xAI `x_search` may translate into completed `custom_tool_call` events such as `x_user_search`. Inspect event names/status instead of requiring one exact event shape.

## Multiple accounts

CLIProxyAPI can pool credentials and route among them. Do not enable multi-account behavior unless requested. When enabled, test session affinity, quota failover, model availability, and whether transcripts can switch accounts without breaking cache/session semantics.

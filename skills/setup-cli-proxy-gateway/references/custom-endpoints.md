# Custom endpoint reference

Custom endpoints are in scope only when they expose OpenAI, Anthropic, or xAI models through an OpenAI- or Anthropic-compatible API.

## Intake

Collect without exposing secrets:

- Base URL and protocol (`responses`, `chat-completions`, or Anthropic messages).
- Authentication header/environment variable.
- Model-list endpoint and selected model ID.
- Required custom headers.
- Claimed streaming, tools, reasoning, images, and caching support.

Prefer CLIProxyAPI's native OpenAI-compatibility/provider configuration rather than pointing every harness directly at the remote service. Use a provider prefix to avoid model-name collisions.

Run `scripts/test_custom_endpoint_mock.sh` before using a paid custom endpoint. It validates the installed `openai-compatibility` schema, alias mapping, upstream bearer key, Chat Completions, Responses-to-Chat translation, rejected keys, and unreachable upstream handling without a real provider credential. It does not prove live provider entitlement.

## OpenRouter

OpenRouter is an OpenAI-compatible custom endpoint. Configure it under CLIProxyAPI's current `openai-compatibility` schema with its base URL, protected key, optional headers, and explicit model mappings. Restrict this skill's recommendations to OpenAI-, Anthropic-, or xAI-family models even if the catalog contains others.

## Validation

Probe the remote endpoint directly, then through CLIProxyAPI, then through the harness. Record each layer separately. “OpenAI-compatible” often covers basic chat but not Responses events, parallel tools, reasoning fields, prompt caching, images, or structured output.

Do not silently change wire APIs to make a test pass. Explain the compatibility loss and let the user choose whether the endpoint is acceptable.

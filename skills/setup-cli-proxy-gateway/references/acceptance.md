# Journey acceptance matrix

Use this matrix for each machine. Never convert `not tested` to `verified` from documentation or a different provider credential.

## Routes

| Surface | Provider | OAuth | API key | Custom endpoint |
|---|---|---|---|---|
| Claude Code CLI | OpenAI | not tested | not tested | not tested |
| Claude Code CLI | Anthropic | not tested | not tested | not tested |
| Claude Code CLI | xAI | not tested | not tested | not tested |
| Codex CLI | OpenAI | not tested | not tested | not tested |
| Codex CLI | Anthropic | not tested | not tested | not tested |
| Codex CLI | xAI | not tested | not tested | not tested |
| Codex app | OpenAI | not tested | not tested | not tested |
| Codex app | Anthropic | not tested | not tested | not tested |
| Codex app | xAI | not tested | not tested | not tested |

For the selected cell, record date, harness/proxy versions, auth type, credential label without identity, model ID, and `verified|partial|unsupported|not tested` for:

- Authentication and entitlement.
- Model discovery and direct inference.
- Responses, Chat Completions, or Messages wire API used.
- Streaming and exact-output headless mode.
- Reasoning controls and observed metadata.
- Read tools; write/shell tools.
- One subagent; parallel subagents.
- Images and provider-hosted tools when relevant.
- Resume/continue, compaction, caching, and settings precedence.
- Native bare-harness isolation and rollback.
- Credential source works in the selected surface: shell/token file for CLI or command-backed auth for Codex app.

## Fresh-install journey

Separately track install from no proxy, isolated-home setup, wrapper migration, binary update/rollback, stale embedded client keys, expired OAuth refresh, entitlement rejection, conflicting service port, unavailable callback port, malformed custom endpoint, and sandbox-blocked loopback. Record OS/service manager separately. A route can be verified while one of these lifecycle journeys remains untested.

Use the packaged deterministic checks where applicable: token helper, route transaction/Vibe reversal, isolated home, custom endpoint, occupied listener, callback timing, selected-model effort matrices, ClaudeX Ultracode, and Codex mixed subagents. Keep real OAuth refresh, real API-key entitlement, Codex app UI, and Linux service acceptance separate from simulations.

# Versioned compatibility evidence

Treat this as historical evidence, not a substitute for rerunning discovery and smoke tests.

## 2026-07-13: Claude Code to xAI OAuth

Environment:

- macOS arm64
- CLIProxyAPI 7.2.71 (`5b7f2361`)
- Claude Code 2.1.207
- xAI OAuth subscription credential
- Client model `grok-4.5`; upstream response model `grok-4.5-build`

Verified:

- OAuth login, hot-reloaded model discovery, and entitlement.
- Responses and Chat Completions.
- Low, medium, and high reasoning on both wire APIs with reasoning-token metadata.
- Claude Code headless JSON and stream-json; thinking-token events.
- Hostile user `--settings` merge with route-critical subagent model preserved.
- Read, write, shell verification, dangerous-permission forwarding, one/parallel subagents.
- Explicit resume and shorthand continue.
- One-agent Claude Code Workflow at high effort; workflow and agent transcript used Grok.
- Native xAI web search and X search through Responses.
- Bare `claude` remained native through an isolated mode-`0700` launcher.

Observed caveats:

- OAuth credential was initially written as mode `0644`; it required correction to `0600`.
- Claude Code emitted the expected connector-disabled and unknown advisor-rank warnings.
- Grok supports low/medium/high here; xhigh, max, and OpenAI-style Ultracode were not offered.
- Image/video routes were discovered but not part of text-harness acceptance.

## 2026-07-13: Codex to xAI OAuth

Environment matched the Claude Code to xAI run above. Testing used a disposable custom Codex provider and did not alter the normal Codex route.

Verified:

- Responses inference with `grok-4.5` and medium reasoning.
- A forced shell read through `command_execution`, with command output and an exact final assertion.
- Both ephemeral command-line configuration and a persisted-but-disposable profile reached the xAI route.

Partial or unsupported:

- Codex treated `grok-4.5` as unknown model metadata and used fallback metadata. Basic routing still worked, but this warning means context limits and model-specific capabilities must not be inferred from the banner.
- Subagents were unsupported in this combination. Grok emitted a `spawn_agent` tool call that the Codex custom-provider session did not expose, including with multi-agent enabled and a non-ephemeral disposable profile.
- An ephemeral OpenAI control also showed that `--ephemeral` can break subagent attachment because the parent thread is not persisted. Repeat subagent tests without `--ephemeral` before assigning a failure to the provider; the non-ephemeral Grok retry still failed as described above.
- After the unsupported tool call, the model attempted to continue and claimed success. Transcript events—not final prose—were therefore the acceptance source.

## 2026-07-13: OpenAI Codex parent to Grok custom child

Environment:

- Codex CLI 0.144.1
- CLIProxyAPI 7.2.71
- Parent and child shared one custom CLIProxyAPI Responses provider
- xAI OAuth credential

Verified with a `gpt-5.5` parent:

- A named custom-agent file selected `grok-4.5`, high reasoning, and read-only sandboxing.
- Parent state recorded `gpt-5.5`; child state recorded `grok-4.5` and the expected custom-agent role.
- The Grok child executed a fixture shell read and returned its result to the parent.
- Two parallel Grok children each executed independent fixture reads and returned results that the parent combined.

Unsupported in the tested `gpt-5.6-sol` Dynamic Workflow:

- Its `spawn_agent(task_name=...)` treated the custom-agent name as a workflow label; child state inherited `gpt-5.6-sol` and did not apply the custom-agent model or reasoning settings.
- Routing the Sol parent through CLIProxyAPI did not change this behavior.
- Enabling the under-development multi-agent metadata setting to expose a child `model` field changed the reserved tool schema and the upstream OpenAI route rejected the request.
- A native `gpt-5.6` slug was not available through the tested ChatGPT account; the accepted 5.6 route was `gpt-5.6-sol`.

Conclusion: mixed OpenAI-parent/Grok-child routing is verified for the classic role-based parent path, not for the tested GPT-5.6 Sol Dynamic Workflow path. Re-test this boundary after Codex or model updates.

## 2026-07-13: hardening and lifecycle acceptance

Environment:

- macOS arm64
- CLIProxyAPI 7.2.71 (`5b7f2361`)
- Codex CLI 0.144.1
- Claude Code 2.1.207
- OpenAI and xAI OAuth credentials; no Claude OAuth credential present

Verified:

- Mode-`0600` canonical local client-token plus mode-`0700` command helper, with no token environment variable. Codex command-backed provider authentication reached the live gateway.
- Deterministic GPT-5.5 parent/Grok-4.5 child acceptance with one child and two parallel children: state model/provider/effort/role, fixture tool calls/results, spawn IDs, wait events, and exact final assertions all matched.
- The same runner correctly classified GPT-5.6 Sol custom-child selection as unsupported: Sol used `task_name`, and its child inherited Sol/high with no custom role.
- All six current GPT-5.6 effort values (`none`, `low`, `medium`, `high`, `xhigh`, `max`) on both Luna and Terra through Responses. ClaudeX also passed explicit Luna `none` and Terra `max` headless checks.
- GPT-5.6 Sol Ultracode: real `Workflow`, `TaskOutput`, exact final, isolated child transcript on Sol, `Read` tool result, and fixture-derived `read-only` value.
- ClaudeX/Claude proxy launchers read the canonical token through the helper with token variables unset and preserved headless JSON, effort, and dangerous-permission flag forwarding.
- Disposable `openai-compatibility` provider: model alias, upstream API key, Chat Completions, Responses translation, rejected API key, and unreachable upstream.
- Isolated fresh-home audit, transactional file/directory/symlink/mode restoration, absent-path removal, and simulated VibeProxy-to-standalone reversal preserving the auth directory.
- Existing-listener collision: bind error logged, original listener PID unchanged, authenticated health remained `200` with 34 models.

## 2026-07-13: Codex app metadata audit

Environment:

- Codex app bundle version 26.707.51957
- Bundled Codex app-server 0.144.0-alpha.4

Verified:

- A custom provider plus `model_catalog_json` made the app-server model-list response include the custom catalog entry.
- A custom provider by itself did not add a custom model to that list.

Not verified:

- End-to-end model-picker visibility or a new app task routed through the custom model.
- The inspected renderer had a separate hidden-model gate, and the active cached gate was disabled in this build. App-server visibility therefore did not prove picker visibility.

Conclusion: keep Codex app support experimental. Do not patch the app bundle or claim a first-class picker route; require a full app relaunch and a new-task inference test for the installed build.

Observed lifecycle caveats:

- A second CLIProxyAPI 7.2.71 process that failed to bind still exited with status `0`; log, listener owner, and health checks are required.
- With an explicitly occupied OAuth callback port, Claude, Codex, and xAI login all displayed authorization and kept waiting before browser completion; no early callback-bind error or credential write occurred. Preflight the explicit callback port before OAuth.

Not tested in this run:

- Codex app UI reload/new-task journey remained unverified after the metadata audit above. Command-auth was verified through isolated Codex CLI, but a profile cannot select an app task and changing base app routing would affect new normal Codex sessions.
- Claude subscription OAuth, expired-token refresh, or a real provider API key/OpenRouter entitlement; no matching credential/key was available. The API-key/custom-endpoint mechanics and negative paths were verified with a local mock only.
- Linux/systemd service behavior; Docker was installed but its daemon was not running.
- Live VibeProxy migration; VibeProxy was already absent, so reversal was simulated transactionally.

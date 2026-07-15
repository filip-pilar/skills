# Claude Code harness adapter

## Provider-neutral route

Use `assets/claude-proxy.zsh` when routing Claude Code to Anthropic or xAI, or when provider-specific effort translation is unverified. It securely reads the canonical token file when token variables are unset, sets the local endpoint/token, maps Claude's Opus/Sonnet/Haiku slots, pins subagents through a highest-precedence settings overlay, and forwards normal Claude Code arguments.

Generate a dedicated launcher name such as `claude-grok`; keep bare `claude` native. Require explicit model IDs discovered from `/v1/models`.

Claude Code can load global `~/.claude/settings.json` values after shell exports. A global exact `CLAUDE_CODE_SUBAGENT_MODEL` may redirect proxy subagents. The packaged launchers consume every user `--settings` value, merge valid JSON/file inputs in order, then apply route-critical subagent values last. Test this behavior whenever Claude Code changes settings precedence. Change a global pin only with approval.

## OpenAI/GPT route

Use the tested routing logic in `assets/claudex.zsh` for OpenAI models when the installed versions accept its conventions. Supply `CLAUDEX_MODEL`, optional slot models, and a protected local client key from the authenticated catalog/config; the shareable template intentionally contains no machine-specific model or credential defaults. Re-discover model IDs and test every effort before installing it.

The launcher requires an already-running, authenticated gateway. Service installation and startup stay separate so launching Claude Code cannot silently create a daemon or hide a failed bind. It also leaves concurrency, tool search, token budgets, and timeout environment variables unchanged; set those only when current Claude Code documentation or an observed timeout justifies them.

The launcher:

- Maps Opus/Sonnet/Haiku slots to selected GPT models.
- Encodes reasoning in CLIProxyAPI model suffixes.
- Keeps subagents on the routed provider.
- Forwards `-p`, permission flags, output formats, resume/continue, MCP, and other non-wrapper flags.
- Implements Ultracode as xhigh routing plus Claude's Ultracode session mode without an xhigh launch pin.

Model families and accepted controls change. Discover the desired IDs, confirm their documented effort set, and pass those IDs explicitly to `scripts/test_openai_efforts.sh`. ClaudeX encodes explicit `none` in the proxy model suffix but does not pass `none` as a native Claude Code effort, because that harness value is not independently documented.

Validate Ultracode with `scripts/test_claudex_ultracode.sh`. It requires a real `Workflow` call, `TaskOutput`, exact final text, an isolated child transcript on the selected model, a `Read` tool result, and fixture-derived output. A successful parent response alone is insufficient.

Do not apply GPT effort suffixes or Ultracode assumptions to Anthropic/xAI routes without direct tests.

For xAI models whose current documentation advertises low/medium/high reasoning, pass Claude Code `--effort low|medium|high` through the provider-neutral launcher and verify the advertised set through the harness. Do not offer xhigh/max/Ultracode unless xAI and the installed proxy explicitly support those controls. Claude Code's ordinary `Workflow` tool can still work independently of Ultracode; test a small read-only workflow and inspect its agent transcript/default model.

## Validation-specific behavior

- The Claude banner and promotional notices do not prove routing.
- `claude.ai connectors are disabled` is expected when proxy/API authentication takes precedence.
- An advisor warning for an unknown custom model does not itself mean routing failed.
- For a Grok alias, Claude initialization can show `grok-4.5` while assistant transcript messages show `grok-4.5-build`; corroborate with proxy ownership and resolved subagent/workflow metadata.
- Inspect `modelUsage`, resolved subagent models, transcripts, and proxy logs.

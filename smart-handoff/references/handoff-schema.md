# Smart Handoff Artifact Schema

The bundle directory is a temporary scratch path, normally `/private/tmp/codex-smart-handoff/<workspace-slug>/<run_id>/`. It is deleted after successful fresh-thread creation. Keep the final continuation prompt self-contained so it does not depend on the bundle surviving.

Bundle directories must be mode `0700`; bundle files must be mode `0600`.

## Required Files

- `manifest.json`
- `workspace-state.json`
- `workspace-summary.md`
- `surface-state.json`
- `surface-state.md`
- `synthesis-input.md`
- `handoff.json`
- `handoff.md`
- `verification.json`
- `verification.md`
- `new-thread-prompt.md`

Conversation evidence files are optional but preferred:

- `conversation-brief.md`
- `decisions.md`
- `open-items.md`
- `user-preferences.md`

Raw surface capture files are optional inputs:

- `browser-state.json`
- `terminal-state.txt`

`surface-state.json` and `surface-state.md` are required derived artifacts. They may state that no recoverable browser/dev-server state was captured.

## manifest.json

Required keys:

- `run_id`
- `created_at`
- `cwd`
- `bundle_path`
- `bundle_storage`
- `cleanup_status`
- `source_thread_id`
- `skill_version`
- `detected_tools`
- `model_policy`
- `preflight`
- `synthesis_engine`
- `synthesis_model`
- `synthesis_effort`
- `verification_engine`
- `verification_model`
- `verification_effort`
- `fallback_reason`
- `artifacts`
- `warnings`
- `omissions`
- `redaction_count`
- `verification_status`
- `handoff_quality`
- `degraded_reasons`

`artifacts` should include `browser_state`, `terminal_state`, `surface_state_json`, and `surface_state_markdown`.

`handoff_quality` values:

- `verified`: model synthesis and model verification completed.
- `partial`: model synthesis completed, but verification was deterministic-only or warnings remain. Automatic fresh-thread creation is blocked unless `SMART_HANDOFF_ALLOW_PARTIAL_CREATE=1` is explicitly set.
- `degraded`: usable checkpoint, but not strong enough to silently create a fresh thread.
- `failed`: do not create a fresh thread.

`model_policy` records configured engines and gates:

- `claude_model`
- `claude_effort`
- `codex_model`
- `codex_effort`
- `allow_partial_create`

Default model policy:

- Claude synthesis: `opus` with `high` effort.
- Codex fallback synthesis/verification: `gpt-5.5` with `xhigh` effort.
- Partial automatic creation: disabled.

`preflight.status` values:

- `pass`: configured model/tool policy is available.
- `warn`: Claude is unavailable, but configured Codex fallback is available.
- `needs_escalation`: the required Codex fallback/verifier check looks sandbox-blocked; rerun preflight with shell escalation and `--after-escalation` before continuing.
- `fail`: configured Codex fallback is unavailable; do not continue to automatic thread creation.

Live preflight checks may include a `classification` field when `ok` is `false`: `needs_escalation`, `auth_unavailable`, `network_unavailable`, or `unknown_failure`.

Claude live-check failures are warnings when Codex fallback is available. Do not block or require escalation solely for Claude.

`synthesis_engine` values are `claude`, `codex`, `deterministic`, or `null`.

`verification_engine` values are `codex`, `deterministic`, or `null`.

`bundle_storage` must be `temporary_scratch` for automatic cleanup.

`cleanup_status` starts as `not_run`. If fresh-thread creation succeeds, run the cleanup script and delete the bundle. If validation or thread creation fails, leave the bundle in place for inspection.

## handoff.json

Required keys:

- `objective`
- `current_status`
- `user_preferences`
- `important_context`
- `decisions_made`
- `files_and_changes`
- `commands_and_results`
- `validation_status`
- `open_questions`
- `blockers`
- `next_steps`
- `do_not_redo`
- `evidence_index`
- `confidence_notes`

Fields may be strings or lists except `evidence_index`, which should be a list of evidence pointers or objects.

## handoff.md

Render this file locally from `handoff.json`; do not rely on model-provided markdown. Use this exact section order:

```text
# Smart Handoff

## Objective
## Current State
## User Preferences And Constraints
## Decisions Made
## Workspace State
## Files Changed
## Commands And Verification
## Open Questions And Blockers
## Next Steps
## Do Not Redo
## Evidence Index
```

## Verification Status

Use:

- `pass`: no critical issues, safe to create a fresh thread.
- `warn`: safe to create a fresh thread, but caveats are present.
- `fail`: do not create a fresh thread from this handoff.

## new-thread-prompt.md

The prompt must be self-contained and bounded, with the handoff content embedded inline. It must not instruct the fresh thread to read `handoff.md`, `manifest.json`, or `workspace-state.json` from the scratch bundle as required context because the bundle may be deleted after thread creation.

When `surface-state.json` contains captured URLs, ports, or dev-server commands, embed the bounded `surface-state.md` guidance. The fresh thread may recreate visible browser/dev-server state, but must not claim hidden browser state, form state, terminal process ownership, or terminal scrollback was preserved.

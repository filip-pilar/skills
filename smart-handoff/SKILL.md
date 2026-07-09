---
name: smart-handoff
description: Create a verified Smart Handoff bundle and continue in a fresh Codex thread. Use when the user asks for smart handoff, smart handover, handoff to a new thread, context handoff, replacement compaction, compact into a new Codex thread, near-context-limit continuation, or any workflow that should preserve the current task state without relying on native context compaction.
---

# Smart Handoff

## Overview

Create a temporary scratch bundle for the active Codex session, synthesize and verify a compact continuation summary, then create a fresh Codex thread with a bounded self-contained prompt. Keep the parent thread quiet: do not print raw transcript, diffs, model outputs, or long summaries into chat.

## Workflow

1. Run `scripts/prepare_run.py` from the current workspace and capture the printed scratch bundle path.
2. Run `scripts/preflight.py --bundle <bundle>` before collecting expensive evidence or synthesizing:
   - It checks the configured model policy, local CLI availability, and live Claude/Codex auth/model access.
   - Defaults are Claude `opus`/`high` and Codex fallback `gpt-5.5`/`xhigh`.
   - Override with `SMART_HANDOFF_CLAUDE_MODEL`, `SMART_HANDOFF_CLAUDE_EFFORT`, `SMART_HANDOFF_CODEX_MODEL`, and `SMART_HANDOFF_CODEX_EFFORT`.
   - If preflight reports `needs_escalation`, the required Codex fallback/verifier is sandbox-blocked; rerun the same command with the required shell escalation and add `--after-escalation`.
   - Claude unavailability, including sandbox-blocked Claude auth, is a warning only when the configured Codex fallback passes. Do not escalate solely for Claude; fall back to Codex.
   - Codex fallback unavailability is a blocking failure.
3. Run `scripts/collect_workspace_state.py --bundle <bundle>`.
4. Capture conversation evidence without flooding this parent context:
   - Prefer spawning a forked worker/subagent if available. Give it `<bundle>` and `references/conversation-capture-worker.md`; instruct it to write the requested files and return only a short status.
   - If worker tooling is unavailable, write a concise current-context brief yourself into the bundle; do not call app-level transcript readers in the parent thread for large histories.
5. Capture recoverable surface state without screenshots or DOM dumps:
   - Write `<bundle>/browser-state.json` with `{ "available": boolean, "selected": { "url": string, "title": string } | null, "tabs": [{ "url": string, "title": string }] }` using in-app Browser tooling when available; otherwise mark it unavailable.
   - Write `<bundle>/terminal-state.txt` with only a bounded tail of the current Codex terminal output when app terminal tooling is available; otherwise write a short unavailable note.
   - Run `scripts/build_surface_state.py --bundle <bundle>`.
6. Run `scripts/build_synthesis_input.py --bundle <bundle>`.
7. Run `scripts/run_claude_synthesis.py --bundle <bundle>`. This calls an authenticated local CLI only when preflight says Claude is available. If preflight already found Claude unavailable while Codex fallback is available, it skips Claude cleanly and records `fallback_reason: claude_preflight_unavailable`. If Claude fails, continue to the Codex verifier, which can synthesize a fallback handoff with the pinned Codex model policy.
8. Run `scripts/run_codex_verifier.py --bundle <bundle>`. This also calls an authenticated local CLI; if it reports model verification unavailable, CLI state access errors, readonly `~/.codex` database errors, or network/auth failures, rerun the same command once with the required shell escalation before treating the handoff as deterministic-only. It synthesizes a fallback handoff if Claude failed, builds the preliminary self-contained prompt, and verifies the bundle. It uses `SMART_HANDOFF_CODEX_MODEL` and `SMART_HANDOFF_CODEX_EFFORT`, defaulting to `gpt-5.5` and `xhigh`; it must not rely on ambient Codex CLI defaults and invokes Codex with `--ephemeral`.
9. Run `scripts/build_new_thread_prompt.py --bundle <bundle>` again so the final prompt reflects verification status and model provenance.
10. Run `scripts/validate_bundle.py --bundle <bundle>`.
11. Read only `<bundle>/new-thread-prompt.md`, then create a fresh Codex thread with app-level `create_thread`. Use the prompt content directly; do not require the fresh thread to read scratch files. Use a project target matching the current cwd when available; otherwise use a projectless target. Do not use `fork_thread`.
12. After `create_thread` succeeds, emit `::created-thread{threadId="..."}` on its own line, then run `scripts/cleanup_bundle.py --bundle <bundle>`. If cleanup fails, report the scratch bundle path.
13. Report only the created thread id and cleanup status. Do not archive the original thread.

## Guardrails

- Keep stdout and chat updates short. The parent thread should not ingest raw history, full diffs, or full summaries.
- Treat transcript/history as useful but incomplete evidence; rely on git/filesystem state for grounding.
- Let only the workflow agent write the tiny raw capture files listed above; let bundled scripts write derived bundle artifacts. Do not let Claude or Codex mutate project files.
- Do not override Codex native `compact_prompt`.
- Treat the scratch bundle as temporary infrastructure. The fresh-thread prompt must stand on its own because the bundle should be deleted after successful thread creation.
- Surface state is best-effort restart/reopen guidance. It may recreate visible browser URLs and project dev servers in the fresh thread, but it cannot preserve hidden browser state, form inputs, terminal scrollback, or unfinished processes.
- If the fresh thread needs a captured localhost port, it may reuse or restart a process that appears to be this same project dev server. It must not kill unrelated processes.
- Keep the scratch bundle private: directory mode `0700`, file mode `0600`.
- Automatic fresh-thread creation requires `handoff_quality: verified` by default. `partial` handoffs are blocked unless `SMART_HANDOFF_ALLOW_PARTIAL_CREATE=1` is explicitly set; deterministic-only handoffs are never safe for automatic creation.
- Record exact synthesis and verification provenance in `manifest.json`: engine, model, effort, fallback reason, and preflight status.
- If verification fails critically, do not create a new thread or clean up. Report the bundle path and short failure summary.
- If fresh-thread creation fails, do not clean up. Report the bundle path and `<bundle>/new-thread-prompt.md`.

## Resources

- `references/handoff-schema.md`: required artifact shape.
- `references/synthesis-prompt.md`: prompt for Claude/Codex synthesis.
- `references/verifier-prompt.md`: prompt for Codex verification/repair.
- `references/conversation-capture-worker.md`: worker instructions for conversation evidence capture.

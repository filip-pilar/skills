---
name: smart-handoff
description: Continue an in-progress Codex app task in a clean new task while using very little remaining context in the source. Use when the user asks for smart handoff, smart handover, near-limit continuation, or a fresh task that should carry forward only the operational context needed to resume the active work.
---

# Smart Handoff

Create the final continuation through a temporary native Codex relay. The source task only dispatches the relay. The relay reads the source, selects and synthesizes the active work state, and creates the final task from a self-contained prompt.

Do not treat Smart Handoff as transcript preservation or in-place compaction. Its purpose is to preserve enough operational state for the next task to continue correctly without spending source-task headroom on synthesis.

## Select the mode

- Use **Relay mode** only when the invoking prompt explicitly says `Smart Handoff relay mode` and supplies a source task id, host id, and working directory.
- Otherwise use **Source mode**.

## Source mode

1. Treat explicit Smart Handoff invocation as authorization to create the requested continuation and one temporary relay task.
2. Resolve the calling task id without reading its history:
   - Prefer a host-provided current task id and host id.
   - Otherwise use a narrowly bounded `list_threads` call and select the single active task matching the current working directory.
   - Stop rather than guessing if the source task remains ambiguous.
3. Call `list_projects` and select the local project matching the source working directory. Stop if the target is ambiguous or the source is in a worktree whose state cannot be reproduced exactly.
4. Create a local relay task in that project with this prompt, substituting the three values:

   ```text
   Use $smart-handoff in Smart Handoff relay mode.

   Source task id: {{SOURCE_THREAD_ID}}
   Source host id: {{SOURCE_HOST_ID}}
   Source working directory: {{SOURCE_CWD}}

   Reconstruct the active work, create the final clean continuation task, navigate to it when possible, and archive this temporary relay only after final-task creation succeeds.
   ```

   Omit `model` and `thinking` so the user's current defaults apply.
5. Emit the relay task's `::created-thread` directive and report that it is preparing the final continuation. Do not poll it or read its work back into the source. Do not archive the source.

### Source invariants

- Do not read, summarize, or copy source history in Source mode.
- Do not collect diffs, logs, browser state, terminal state, or scratch bundles in Source mode.
- Do not use a context-inheriting subagent, `fork_thread`, an SDK/API model call, or a nested Codex/Claude CLI.
- Keep source growth limited to this workflow, task/project discovery metadata, the short relay prompt, and the returned relay id.

## Relay mode

Read and follow `references/handoff-relay.md`. The relay must create the final continuation itself. If source reading or final-task creation is unavailable, report the failure and remain unarchived so the user can inspect it.

## Resource

- `references/handoff-relay.md`: evidence-selection, synthesis, and final-task creation procedure for the temporary Codex relay.

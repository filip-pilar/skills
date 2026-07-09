# Smart Handoff Synthesis Prompt

You are creating a Smart Handoff for a fresh Codex thread that will continue an in-progress task. The handoff will be embedded directly into the fresh thread's initial prompt, so it must be concise, self-contained, and useful without relying on scratch bundle files surviving.

Use only the provided evidence. Do not invent files, commands, test results, commits, PRs, terminal state, browser state, or user decisions. If something is unknown, say it is unknown.

Optimize for continuation quality:

- Preserve the user's active objective.
- Preserve user preferences, constraints, and corrections.
- Preserve decisions made and the reasoning that affects future choices.
- Preserve exact file paths and workspace state.
- Preserve commands run and their observed results only when evidence supports them.
- Preserve blockers, unresolved questions, and next steps.
- Preserve recoverable surface state if evidence includes browser URLs, localhost ports, or dev-server commands. Treat it as restart/reopen guidance, not proof that hidden browser or terminal state can be moved.
- Include a "Do Not Redo" section for completed or rejected paths.
- Keep the final handoff concise enough for a fresh Codex thread to read quickly.
- Evidence index entries may name scratch bundle artifacts or original workspace source files captured inside `workspace-state.json`; make the distinction clear when useful. Do not make the continuation depend on the scratch bundle surviving after thread creation.
- Return structured handoff data only; `handoff.md` is rendered locally from the returned JSON.

Return a single JSON object with the required `handoff.json` keys.

Required JSON keys:

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
If the evidence is thin, still produce a useful handoff and clearly state the limits in `confidence_notes`.

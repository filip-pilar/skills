# Conversation Capture Worker

Write concise conversation evidence files into the provided temporary Smart Handoff scratch bundle. Do not modify project files outside the bundle. Do not return raw transcript text to the parent thread.

Required output files:

- `conversation-brief.md`: active objective, current state, and recent turn context.
- `decisions.md`: decisions made, rejected approaches, and why they matter.
- `open-items.md`: unresolved questions, blockers, and exact next steps.
- `user-preferences.md`: user preferences, constraints, style corrections, and operational preferences.

Guidelines:

- Use the current conversation context available to you.
- If app-level thread readers are available, use them in this worker rather than asking the parent to read large transcripts.
- Keep each file concise and evidence-oriented.
- Mark unknowns as unknown.
- Return only a short completion status and the list of files written.

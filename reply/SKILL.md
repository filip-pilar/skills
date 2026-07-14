---
name: reply
description: Explicit-only reply workflow for Codex Side tasks. Use $reply to turn the Side-task discussion into the smallest sufficient response to its linked parent. A bare invocation drafts and never sends.
---

# Reply

Treat a bare `$reply` invocation as a complete request to draft, never to send.

Use the Side task's linked parent as the only destination. Never search for or infer another. Use the available Side-task and inherited parent context. If the parent may have responded since that context was captured, read only its newest completed response.

Draft from the user's explicit decisions and clearly accepted conclusions. Treat assistant suggestions, hypotheticals, and Devil's Advocate arguments as unapproved unless the user accepted them. If a material ambiguity remains, ask one focused question.

Write as the user speaking directly to the parent. Produce the smallest sufficient response: communicate what is new or decided without restating what the parent already knows or adding unendorsed detail.

Show the exact draft and wait. Send only the latest draft the user explicitly approves, exactly as approved. Re-invoking `$reply` means redraft, not send.

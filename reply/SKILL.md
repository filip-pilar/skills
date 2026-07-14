---
name: reply
description: Explicit-only reply workflow for Codex Side tasks. Use $reply to turn the Side-task discussion into the smallest sufficient response to its linked parent. A bare invocation drafts and never sends.
---

# Reply

Treat a bare `$reply` invocation as a complete request to draft, never to send.

Use the Side task's linked parent as the only destination. Start from the available Side-task and inherited parent context, and never search for, infer, or guess another task. If the parent may have replied since that snapshot, read only its newest completed response when a parent-scoped read operation or an exact parent ID supplied in model-visible metadata or directly by the user is available; otherwise ask the user to paste the response.

Draft from the user's explicit decisions and clearly accepted conclusions. Treat assistant suggestions, hypotheticals, and Devil's Advocate arguments as unapproved unless the user accepted them. If a material ambiguity remains, ask one focused question.

Write as the user speaking directly to the parent. Produce the smallest sufficient response: communicate what is new or decided without restating what the parent already knows or adding unendorsed detail.

Present every proposed draft with only the draft text inside a fenced `text` code block; keep labels, explanations, and approval or send prompts outside it. The outer fence is presentation only and is never part of the draft. If the draft contains a fenced code block, use a longer outer fence so the complete draft remains copyable. When sending an approved draft, omit only the outer presentation fence and preserve the draft's contents and formatting exactly.

Show the exact draft and wait. Send only the latest draft the user explicitly approves, exactly as approved, and only through a parent-scoped send operation or that exact parent ID. Otherwise label it a copy-to-parent draft and ask the user to paste it unchanged. Re-invoking `$reply` means redraft, not send.

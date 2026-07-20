---
name: reply
description: Turn the user's settled Codex Side discussion into a concise reply for its linked parent.
---

# Reply

Treat a bare `$reply` invocation as a complete request to draft, never to send.

Use the Side task's linked parent as the destination and start from the available Side-task and inherited parent context. If the parent may have replied since that snapshot, read only its newest completed response. If linked-parent reading is unavailable, ask the user to paste the response.

Draft from the user's explicit decisions and clearly accepted conclusions. Treat assistant suggestions, hypotheticals, and Devil's Advocate arguments as unapproved unless the user accepted them. If a material ambiguity remains, ask one focused question.

Write as the user speaking directly to the parent. State approval as the user's decision; use a directive only when the user's explicit decision is itself an instruction. Scale the draft's detail to the complexity, ambiguity, and consequences of what it must communicate. Produce the smallest sufficient response: communicate what is new or decided without restating what the parent already knows or adding unendorsed detail. Do not put assistant-created terminology into the draft unless the user explicitly adopted it; express the user's concrete intent instead. When the user accepts one clearly identified parent proposal unchanged, use the shortest unambiguous reference to it and express only the user's assent in their natural register; do not restate its work or add expected next steps. For multiple proposals, partial acceptance, or consequential action, preserve the accepted item and only the material delta or limit the user explicitly stated.

Present every proposed draft with only the draft text inside a fenced `text` code block; keep labels, explanations, and approval or send prompts outside it. The outer fence is presentation only and is never part of the draft. Inside the draft, default to plain prose. Use Markdown only when it materially improves structure or preserves literal syntax that could otherwise be misread; do not automatically style technical terms, tool names, commands, paths, or identifiers with backticks. If the draft contains a fenced code block, use a longer outer fence so the complete draft remains copyable. When sending an approved draft, omit only the outer presentation fence and preserve the draft's contents and formatting exactly.

Show the exact draft and wait. Send only the latest draft the user explicitly approves, exactly as approved, to the linked parent. If linked-parent sending is unavailable, provide the unchanged approved draft for copying. Re-invoking `$reply` means redraft, not send.

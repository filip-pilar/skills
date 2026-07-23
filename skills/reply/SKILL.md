---
name: reply
description: Turn the user's settled Codex Side discussion into a concise reply for its linked parent.
---

# Reply

Treat a bare `$reply` invocation as a complete request to draft, never to send.

Use the Side task's linked parent as the destination and start from the available Side-task and inherited parent context. If the parent may have replied since that snapshot, read only its newest completed response. If linked-parent reading is unavailable, ask the user to paste the response.

Draft from the user's explicit decisions and clearly accepted conclusions. Treat assistant suggestions, hypotheticals, and Devil's Advocate arguments as unapproved unless the user accepted them. If a material ambiguity remains, ask one focused question.

Write as the user speaking directly to the parent. Draft only what the parent needs that is new or decided. When the user accepts one clearly identified parent proposal as a whole, use one natural assent sentence referring to that proposal; this rule also applies when the proposal is consequential. Use the user's wording when available; otherwise use the parent's shortest established label only to identify the proposal. Add only a limit, expansion, correction, or other material difference the user explicitly stated. Consequentiality alone does not justify repeating the proposal's work, safeguards, exclusions, rationale, or expected next steps. Restate an action, target, or limit only when referring to the proposal would be ambiguous, when acceptance is partial, or when omission could materially change the authorization. Use a directive only when the user explicitly gave one. Add no unendorsed detail.

Present every proposed draft with only the draft text inside a fenced `text` code block; keep labels, explanations, and approval or send prompts outside it. The outer fence is presentation only and is never part of the draft. Inside the draft, default to plain prose. Use Markdown only when it materially improves structure or preserves literal syntax that could otherwise be misread; do not automatically style technical terms, tool names, commands, paths, or identifiers with backticks. If the draft contains a fenced code block, use a longer outer fence so the complete draft remains copyable. When sending an approved draft, omit only the outer presentation fence and preserve the draft's contents and formatting exactly.

Show the exact draft and wait. Send only the latest draft the user explicitly approves, exactly as approved, to the linked parent. If linked-parent sending is unavailable, provide the unchanged approved draft for copying. Re-invoking `$reply` means redraft, not send.

## Before responding

Silently verify:

1. Every clause either identifies the accepted proposal or communicates an explicit user decision or material difference; delete anything else.
2. Whole-proposal acceptance is concise even when consequential.
3. Partial acceptance and materially ambiguous authorization preserve the necessary action, target, and limits.
4. Nothing is sent without approval of that exact draft.

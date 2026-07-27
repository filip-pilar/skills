---
name: reply
description: Turn the user's settled Codex Side discussion into a parent-sufficient reply for its linked parent.
---

# Reply

Treat a bare `$reply` invocation as a complete request to draft, never to send.

Use the Side task's linked parent as the destination and start from the available Side-task and inherited parent context. If the parent may have replied since that snapshot, read only its newest completed response. If linked-parent reading is unavailable, ask the user to paste the response.

Before drafting, distinguish what the parent already knows from established context developed only in Side. The parent knows its own history, not the Side discussion. Include the Side-only context it needs to understand and continue the user's settled intent without access to that discussion or repeating its reasoning.

Draft from the user's explicit decisions and clearly accepted conclusions. Decisions, instructions, approvals, and preferences require the user's authorization. Supported factual context may be included when necessary, but preserve material uncertainty and never turn uncertain analysis into an assertion in the user's voice. Treat assistant suggestions, hypotheticals, and Devil's Advocate arguments as unapproved unless the user accepted them. Exact-draft approval is the final attribution and sending gate. If a material ambiguity remains, ask one focused question.

Write as the user speaking directly to the parent. Produce the shortest reply that preserves the user's settled intent and supplies the necessary Side-only context. Concise reference usually suffices for an unchanged parent-originated proposal. When a proposal emerged in Side or materially revised the parent's plan, convey enough of it and its necessary context for the parent to understand and execute. Preserve the accepted scope and material limits of partial approval. Omit parent-known detail, irrelevant exploration, and unendorsed recommendations. Use a directive only when the user explicitly gave one.

Present every proposed draft with only the draft text inside a fenced `text` code block; keep labels, explanations, and approval or send prompts outside it. The outer fence is presentation only. Inside the draft, default to plain prose and use Markdown only when it materially improves clarity or preserves literal syntax. If the draft contains a fenced code block, use a longer outer fence. When sending, omit only the outer presentation fence and preserve the approved contents exactly.

Show the exact draft and wait. Send only the latest draft the user explicitly approves, exactly as approved, to the linked parent. If linked-parent sending is unavailable, provide the unchanged approved draft for copying. Re-invoking `$reply` means redraft, not send.

## Before responding

Silently verify:

1. The parent can understand and continue the settled intent without the Side transcript or repeating its reasoning.
2. Decisions and preferences are authorized; factual context is supported; material uncertainty remains visible.
3. The draft includes necessary Side-only context but omits parent-known detail and irrelevant exploration.
4. Proposal provenance, partial approval, and material limits are preserved.
5. Nothing is sent without approval of that exact draft.

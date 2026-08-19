---
name: reply
description: Turn the user's settled Codex Side discussion into a parent-sufficient reply for its linked parent.
---

# Reply

Treat a bare `$reply` invocation as a complete request to draft, never to send.

Use the Side task's linked parent as the destination and start from the available Side-task and inherited parent context. If the parent may have replied since that snapshot, read only its newest completed response. If linked-parent reading is unavailable, ask the user to paste the response.

Before drafting, distinguish what the parent already knows from the user's settled decision and context developed only in Side. Carry only that decision and the minimum Side-only context the parent needs to understand and respond to the settled intent. Reference unchanged parent-known context briefly. Do not recap the Side discussion or repackage the Side assistant's reasoning, rationale, jargon, diagnoses, recommendations, or exact wording as the user's voice unless the user explicitly adopted that material and the parent genuinely needs it to understand and respond to the settled intent.

Draft from the user's explicit decisions and clearly accepted conclusions. Decisions, instructions, approvals, and preferences require the user's authorization. An accepted Side suggestion can establish the user's chosen direction, but carry the decision rather than the assistant's supporting reasoning or phrasing, and keep experimental ideas tentative. Supported factual context may be included when necessary, but preserve material uncertainty and never turn uncertain analysis into an assertion in the user's voice. Treat assistant suggestions, hypotheticals, and Devil's Advocate arguments as unapproved unless the user accepted them. Draft approval authorizes sending that draft only; it does not make unsupported, unendorsed, or overclaimed content valid. Remove such content before presenting the draft. If a material ambiguity remains, ask one focused question.

Write as the user speaking directly to the parent. Match the user's tone, directness, and register from their recent messages; do not imitate the Side assistant. Produce the shortest reply that preserves the user's settled intent and supplies the necessary Side-only context. For an unchanged parent-originated proposal, briefly reference it and state only the user's decision or material delta. When a proposal emerged in Side or materially revised the parent's plan, state the concrete outcome and necessary constraints, not why the Side assistant thinks it will work or provider-ready replacement wording unless the user explicitly supplied or adopted that exact wording. Preserve the accepted scope and material limits of partial approval. Omit parent-known detail, irrelevant exploration, and unendorsed recommendations. Use a directive only when the user explicitly gave one. A draft authorizing a paid action must include the exact target, allowed count, an explicit user-authorized maximum spend, and the stop condition; if any is unsettled, ask one focused question rather than inventing it.

Present every proposed draft with only the draft text inside a fenced `text` code block; keep labels, explanations, and approval or send prompts outside it. The outer fence is presentation only. Inside the draft, default to plain prose and use Markdown only when it materially improves clarity or preserves literal syntax. If the draft contains a fenced code block, use a longer outer fence. When sending, omit only the outer presentation fence and preserve the approved contents exactly.

Show the exact draft and wait. Send only the latest draft the user explicitly approves, exactly as approved, to the linked parent. If linked-parent sending is unavailable, provide the unchanged approved draft for copying. Re-invoking `$reply` means redraft, not send.

## Before responding

Silently verify:

1. The parent can understand and respond to the settled intent with only the minimum necessary Side-only context.
2. The draft does not carry the Side assistant's reasoning, jargon, diagnoses, rationale, or exact wording into the user's voice unless the user explicitly adopted it and the parent genuinely needs it.
3. Decisions and preferences are authorized; factual context is supported; experimental ideas remain tentative; material uncertainty remains visible.
4. The draft matches the user's tone, references parent-known context briefly, and preserves proposal provenance, partial approval, and material limits.
5. Any paid authorization includes an explicit user-authorized maximum spend as well as its target, count, and stop condition.
6. Draft approval has not been used to excuse unsupported content, and nothing is sent without approval of that exact draft.

---
name: reply
description: Draft the user's settled Side decisions as one clear prompt for the linked parent without sending it.
---

# Reply

Treat a bare `$reply` invocation as a complete request to draft, never to
send.

## Check that the discussion is still current

Use only the Side task's exact linked parent. Before drafting, read its newest
completed response when the exact route is available and compare it with the
parent state underlying the Side discussion. Continue silently when nothing
important changed. If a newer response fulfills, conflicts with, or invalidates
the settled intent, do not draft; explain the change plainly and ask only for
the decision now required.

If binding or reading is unavailable or ambiguous, say so outside the proposed
prompt. Use inherited context only when it is sufficient and a newer response
could not materially change the draft; otherwise ask for the missing response
without guessing.

## Draft only what the user settled

Separate what the parent already knows from what the user explicitly decided
in Side. Carry the decision and only the Side context the parent needs to
understand and act on it. Preserve necessary uncertainty. Leave out rejected
ideas, unsettled suggestions, unnecessary recap, and the Side assistant's
reasoning or preferred wording unless the user explicitly adopted it.

Write as the user speaking directly to the parent. Match the user's recent
tone, directness, vocabulary, and level of formality; do not imitate the Side
assistant. Prefer plain prose and concrete instructions. Keep an exact
technical term when the parent needs it to act correctly, but do not turn a
casual user decision into formal project-management or agent-workflow language.
Use Markdown inside the prompt only when it materially improves a genuinely
complex request or preserves literal syntax.

Reference unchanged parent-known context briefly. State Side-developed or
materially revised outcomes concretely, with their accepted limits. Never make
uncertainty sound certain or turn interest, partial agreement, or an assistant
suggestion into the user's instruction.

If a material choice remains open, do not show a proposed prompt. Ask one plain,
focused question covering only the missing choice. Before drafting a
consequential authorization, confirm its target, action, quantity, cap or
limits, and stop condition; never invent a missing permission.

## Show one clean proposed prompt

For a successful draft, output only the label `Current reply` followed by
exactly one fenced `text` block containing the proposed prompt. Do not add a
summary, rationale, approval explanation, or second version. Use a longer outer
fence if the prompt contains fenced code.

A new successful draft replaces every earlier `Current reply`; re-invocation
means redraft, not approval. The fence is presentation, not authorization.
Never send the prompt, message the parent, or claim approval. Wait for an
explicit transition to the sending phase.

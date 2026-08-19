---
name: reply
description: Turn the user's settled Side decisions into one prompt for the linked parent without sending it.
---

# Reply

A bare `$reply` means: draft the current prompt, but do not send it.

## Check the parent

Use only this Side task's linked parent. Before drafting, read its newest
completed response when possible. If it already completed the request or
changed something that affects the user's decision, explain that change and ask
only what is now needed. If current state is unavailable and could change the
prompt, ask for the missing response instead of guessing.

## Draft only what the user decided

Write as the user speaking directly to the parent. Include the user's settled
decisions and only the Side context the parent needs. Refer briefly to context
the parent already knows. Leave out rejected ideas, unresolved suggestions, and
the Side assistant's reasoning unless the user adopted it.

Match the user's tone and directness. Prefer natural prose. Keep technical
wording only when the parent needs it to act correctly.

Do not add a planning phase, preview, review checkpoint, confirmation step, or
`do not implement yet` limit unless the user chose it. When the user authorized
the work from planning through implementation and validation, keep those as
ordered steps in one prompt. Preserve a pause when the user explicitly asked to
approve something before work continues.

Never invent permission for a risky, destructive, external, or paid action. If
the user has not settled what may happen, to what, within which limits, and when
to stop, ask one focused question instead of drafting.

If any other open choice would change the result, ask that one question and do
not show a prompt yet.

## Show one prompt

A successful response contains only `Current reply` followed by one fenced
`text` block. Put only the proposed prompt inside the block. Use a longer outer
fence if the prompt itself contains fenced code.

Each new draft replaces the previous `Current reply`. Displaying it is not
approval to send. Never message the parent; wait for an explicit `$supervise`.

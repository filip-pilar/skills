---
name: reply
description: Synthesize the user's settled Side conclusions into one parent-ready prompt without sending it.
---

# Reply

A bare `$reply` manually drafts the current parent prompt. It never sends it.

## Check the linked parent

Use only this Side task's linked parent. Before drafting, read its newest
completed response when possible. If it already completed the proposed request
or changed something material to the user's decision, explain that change and
ask only what is now needed. If unavailable current state could change the
prompt, ask for the missing response rather than guessing.

## Synthesize settled intent

Write as the user speaking directly to the parent. Include the user's settled
conclusions and decisions plus only the Side context the parent needs. Preserve
the chosen scope, constraints, permissions, pauses, expectations, ordering, and
acceptance criteria. Refer briefly to context the parent already knows.

Leave out rejected ideas, unresolved choices, and Sidekick's reasoning or
recommendations unless the user adopted them. Never turn interest, partial
agreement, or an unanswered suggestion into a decision. Match the user's tone
and directness, using technical wording only when the parent needs it to act
correctly.

Do not add a planning phase, preview, review checkpoint, confirmation step, or
`do not implement yet` limit unless the user chose it. When the user authorized
planning through implementation and validation, preserve them as ordered parts
of one job. Preserve a pause when the user explicitly requested approval before
continuing.

Never invent permission for destructive, external, paid, risky, or broader
actions. If an unresolved decision or missing limit would materially change the
prompt, ask one focused question and do not draft yet.

## Present the prompt

On success, respond with exactly one fenced `text` block containing only the
proposed parent prompt. Add no label, explanation, status, or surrounding
commentary. Use a longer outer fence if the prompt itself contains fenced code.

The fence is presentation for easy inspection and copying; it is not an
authorization signal or workflow state. Drafting never messages the parent.
Only a later manual `$supervise` invocation authorizes Supervise to select and
send the prompt the user currently intends.

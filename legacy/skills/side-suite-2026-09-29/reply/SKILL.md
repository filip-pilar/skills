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

Leave out rejected ideas and unadopted Sidekick reasoning or recommendations.
Do not present unresolved choices as settled. Never turn interest, partial
agreement, or an unanswered suggestion into a decision. Match the user's tone
and directness, using technical wording only when the parent needs it to act
correctly.

Preserve the user's chosen sequencing and approval gates exactly. Treat
planning, implementation, and validation as ordered parts of one job when the
user authorized them end to end; pause only when the user explicitly requested
approval before continuing.

Never invent permission for destructive, external, paid, risky, or broader
actions. Ask one focused question before drafting when a missing decision changes
the objective, scope, authority, or acceptance criteria. Routine implementation
details may remain delegated to the parent within the user's existing authority;
do not invent choices or add a review checkpoint to settle them.

## Present the prompt

On success, respond with exactly one fenced `text` block containing only the
proposed parent prompt. Add no label, explanation, status, or surrounding
commentary. Use a longer outer fence if the prompt itself contains fenced code.

Return the fenced prompt for easy inspection and copying. Drafting never
messages the parent. A later manual `$supervise` invocation authorizes
Supervise to select and send the prompt the user currently intends.

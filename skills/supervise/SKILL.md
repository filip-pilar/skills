---
name: supervise
description: Send the latest Reply prompt to its linked parent, follow the work, verify the result, and make limited in-scope corrections.
---

# Supervise

A bare `$supervise` approves only the latest eligible `Current reply`.

## Choose the prompt and parent

Use the newest earlier assistant response labeled `Current reply` that contains
exactly one fenced `text` block. Send the block's contents, without the fence.
If it is missing or unclear, or if a later user message changed or rejected it,
request a fresh `$reply`.

Use only this Side task's linked parent. Immediately before sending, read the
parent's newest completed response when possible. Request a fresh `$reply` if
the parent has already completed the request or changed something that affects
it. If current state cannot be established and could change what should be
sent, stop and explain the problem.

## Send once and follow the work

Send the approved prompt once. After the send is accepted, never send that
prompt again during the same run. If the send errors, times out, or leaves
delivery unclear, do not retry; report `Delivery uncertain` so the user can
check without risking a duplicate.

Wait only on the linked parent. Reuse the wait cursor so the same response is
not handled twice. Continue only with a response that clearly follows the sent
prompt. After an interruption, inspect the parent before acting. If you cannot
tell whether the prompt was sent, do not resend it.

## Check and correct

Judge the result against the approved prompt. Supervise follows that scope
exactly:

- A prompt that asks only for a plan does not permit implementation.
- A prompt that authorizes planning, implementation, and validation is one
  continuous job; do not pause between those steps unless the prompt says to.

The parent does the work. You may inspect files or run safe focused checks to
verify important claims. Do not rely only on the parent's summary or on tests
the parent just added. Check the highest-risk requirement directly when
reasonable; otherwise say what could not be verified.

If a clearly requested part is missing, send one short follow-up naming that
gap, then wait again. Send at most two corrective follow-ups. Stop sooner when
continuing would require a new choice, broader scope, new permission, or a
repeated ineffective correction.

## Report plainly

Begin the final response with exactly one bold status label and the practical
result on the same line. Use `Done` only when the available checks support it:

- `**Done:**` — the approved request is complete.
- `**Partly done:**` — useful work finished, but a requested part remains.
- `**Blocked:**` — progress needs new information, permission, or an outside
  change.
- `**Delivery uncertain:**` — it is unclear whether the prompt was delivered.

A routine success ends after that line. Add `**Checked:**`, `**Still open:**`,
or `**Needs from you:**` only when it adds information the user needs. Use
ordinary language and do not reproduce logs, checklists, or routine process.

---
name: supervise
description: Send the latest Reply prompt to its linked parent, follow and verify the work, continue in-scope corrections, and deliver an accurate completion handoff.
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
gap, then wait again. Reassess the current result after every response and
continue with another focused correction while it has a concrete reason to
make progress within the approved scope. Do not stop merely because a fixed
number of follow-ups has been sent.

Stop only when the request is complete, or when continuing requires a new
choice, broader scope, new permission, an outside change, or has no reasonable
path forward because the parent repeatedly makes no material progress on the
same gap. Report the concrete completion or impediment, never an exhausted
attempt count.

## Build the completion handoff

After following, correcting, and verifying the work, re-read the parent's newest
completed response when possible. Base the handoff on the current material
result across the whole supervised run: reconcile the approved `Current reply`,
material results and corrections observed while supervising, your independent
verification, the parent's newest completed response, and the exact reason
supervision stopped. Prefer the latest settled evidence. Keep earlier context
only while it remains materially relevant; do not revive findings, failures, or
blockers that were later corrected or superseded. Use the handoff as a concise
but meaningful completion report, not merely a receipt that the parent stopped
working.

Begin with exactly one bold status label and the practical result on the same
line. Make that line type-accurate: say whether the parent implemented,
investigated, diagnosed, reviewed, planned, or recommended work. Do not make an
assessment or plan sound implemented, and do not make successful mutations
sound wholly complete when a material requested result remains unresolved.

Use `Done` only when the available checks support the approved request's actual
kind of completion:

- `**Done:**` — the approved request is complete for the work type requested.
- `**Partly done:**` — useful work finished, but a requested part remains.
- `**Blocked:**` — progress needs new information, permission, or an outside
  change.
- `**Delivery uncertain:**` — it is unclear whether the prompt was delivered.

Preserve every fact whose omission could materially change the user's
understanding, confidence, decision, or next action. This includes material
findings, unresolved problems, risks, uncertainty, scope boundaries, explicit
deferrals, meaningful verification or verification gaps, recommendations, next
steps, and genuine decisions or permissions needed from the user. Preserve the
scale and relationship of those facts: do not reduce a systemic redesign to one
example bug or bury an unresolved blocker beneath successful mutations.

When completed work reaches a new approval or permission boundary, stop without
granting it. State what completed, what you verified, what has not happened,
why supervision stopped, and the exact approval or decision needed from the
user.

Compress routine detail, logs, repetition, and secondary background instead of
compressing decision-critical meaning. Use conditional sections such as
`**Checked:**`, `**Still open:**`, `**Recommended next step:**`, or
`**Needs from you:**` only when useful; do not force every heading into every
response. A genuinely routine success with no material caveat, open issue,
recommendation, or user decision ends after one concise status line.

Before sending the handoff, compare its likely meaning with the current material
result across the supervised run: would the summary cause the user to form a
materially different picture of what happened, what was verified, what remains,
why supervision stopped, or what to do next? If so, restore the missing context.
Use ordinary language and do not reproduce logs, checklists, or routine process.

Supervise owns delivery, completion status, correction-loop results,
verification, and this final handoff. Do not invoke Sidekick or start a separate
Sidekick discussion automatically. A later `$sidekick` remains an optional new
discussion cycle when the completed result gives the user something to explore.

---
name: supervise
description: Select and send the user's intended prompt to the linked parent, verify and correct the work, and deliver an accurate completion handoff.
---

# Supervise

A bare `$supervise` is the user's manual authorization to identify and send the
parent prompt they currently intend, then supervise that work. Do not require
the prompt to have been produced by Reply or to use a particular label,
heading, fence, or adjacency pattern.

## Select the prompt and linked parent

Use only this Side task's linked parent. Inspect the Side conversation
semantically and select the most recent clear parent-ready prompt that still
reflects the user's current intent. Later neutral discussion does not invalidate
an otherwise current prompt. Account naturally for later corrections, rejected
ideas, and changed decisions; never send wording that those later messages made
obsolete.

If there is no clear parent-ready prompt, or multiple genuinely plausible
candidates remain, stop and ask one focused question instead of guessing. The
answer may identify existing wording or lead the user to invoke `$reply`; do not
require a fresh Reply merely to satisfy formatting.

Immediately before sending, read the parent's newest completed response when
possible. If the parent already completed the request or its state materially
changes what should be sent, stop and explain the concrete issue or ask the one
decision now needed. If current state cannot be established and could change
the intended prompt, do not send.

## Send once and follow the work

Send the selected prompt once. After the send is accepted, never send it again
during the same run. If the send errors, times out, or leaves delivery unclear,
do not retry; stop with a clear `Delivery uncertain` result so the user can
check without risking a duplicate. After any interruption, inspect the parent
before acting; if delivery cannot be established, do not resend.

Wait only on the linked parent. Reuse the wait cursor so the same response is
not handled twice, and follow only responses belonging to this supervised run.

## Verify and correct

Judge the result against the selected prompt and its actual acceptance
criteria. Preserve its scope exactly:

- A prompt asking only for a plan does not authorize implementation.
- A prompt authorizing planning, implementation, and validation is one
  continuous job unless the prompt requires a pause.

The parent performs the requested work. Independently inspect files, state, or
safe focused checks when proportionate to verify important claims. Do not rely
entirely on the parent's summary or on tests the parent just added. Check the
highest-risk requirement directly when reasonable; otherwise state the
verification limit.

When a requested requirement is materially missing or incorrect, send a short,
focused in-scope correction and wait again. Reassess after every response and
continue correcting while a concrete path to completion remains. Do not stop
because of an arbitrary follow-up count.

Stop and escalate rather than deciding for the user when continuing requires a
genuine decision or tradeoff, new authority or permission, broader scope, an
outside dependency, a response to material divergence or new findings, or when
repeated lack of material progress leaves no reasonable path forward. State the
specific completion condition or impediment, not an exhausted attempt count.

## Reconcile the final handoff

Before handing off, re-read the parent's newest completed response when
possible and reconcile the whole supervised run: the prompt sent, material
results and corrections, independent verification, the latest parent response,
and why supervision stopped.

Communicate every settled fact whose omission could materially change the
user's understanding, confidence, decision, or next action. Include:

- what changed or otherwise completed, stated with the correct work type;
- what was verified and any meaningful verification limit;
- unresolved, incomplete, or explicitly deferred work;
- material new findings, including findings outside the sent prompt's scope;
- why supervision stopped; and
- any decision, permission, or action genuinely needed from the user.

Including an out-of-scope finding does not authorize work on it. Prefer the
latest settled evidence and do not revive failures or blockers later corrected.
Preserve the scale and relationship of independently useful outcomes instead of
reducing them to a generic success statement.

Open with a clear completion state and practical result. Keep the meaningful
distinctions represented by `Done`, `Partly done`, `Blocked`, and
`Delivery uncertain`, but choose any concise wording or layout that communicates
the state accurately. Do not make investigation, planning, review, diagnosis,
or recommendation sound implemented, and do not describe partial or
unverified work as wholly complete.

Use optional sections such as `Checked`, `Still open`, `Recommended next step`,
or `Needs from you` when they improve scanning. Exact Markdown, bolding,
headings, and same-line layout are presentation choices, not behavioral
correctness. Compress routine logs and process detail, never decision-critical
meaning.

Supervise owns delivery, the correction loop, verification, completion status,
and this handoff. Do not invoke Sidekick or start a new discussion cycle
automatically; a later manual `$sidekick` remains available when the result
gives the user something to explore.

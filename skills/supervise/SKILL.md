---
name: supervise
description: Select and send the user's intended prompt to the linked parent, verify and correct the work, and deliver an accurate completion handoff.
---

# Supervise

A bare `$supervise` is the user's manual authorization to select and send the
parent prompt that reflects their current intent, then supervise that work.

## Select the prompt and linked parent

Use only this Side task's linked parent. Inspect the Side conversation
semantically and select the most recent clear parent-ready prompt that still
reflects the user's current intent, accounting for later corrections, rejected
ideas, and changed decisions.

If there is no clear parent-ready prompt, or multiple genuinely plausible
candidates remain, stop and ask one focused question to identify the intended
prompt. The user may point to existing wording or invoke `$reply` to synthesize
it.

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
verification limit. Reuse credible evidence already available for the current
state; repeat or broaden checks only when changes, failures, or unresolved
uncertainty justify it.

When a requested requirement is materially missing or incorrect, send a short,
focused in-scope correction and wait again. Reassess after every response and
continue correcting while a concrete path to completion remains.

Continue through routine dependencies and new in-scope findings when they can be
handled within existing authority, including waiting for relevant checks. Escalate
when proceeding requires a consequential user decision, new authority, broader
scope, or an outside change that cannot be obtained within that authority. Stop
when repeated lack of material progress leaves no reasonable path forward. State
the specific impediment rather than treating every new finding as a new approval.

## Reconcile the final handoff

Reconcile the sent prompt, material results and corrections, independent evidence,
and latest completed parent response. Read that response if it is not already
available and current. Use the latest settled evidence; do not revive corrected
failures or superseded blockers.

Lead with the practical result and an accurate completion state: done, partly
done, blocked, or delivery uncertain. Preserve the work type, what was verified
and its limits, unresolved or deferred work, material new findings even outside
scope, why supervision stopped, and any real user action needed. Reporting an
out-of-scope finding does not authorize work on it. Analysis is not implementation,
and partial or unverified work must not sound wholly complete.

Compress routine logs and repetition, preserving facts that affect confidence or
the next decision and the scale of independently useful outcomes. Use only the
structure needed for that meaning; routine verified success may take one line.

Supervise owns delivery, the correction loop, verification, completion status,
and this handoff.

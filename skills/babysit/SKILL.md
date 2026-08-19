---
name: babysit
description: Approve, dispatch, and supervise the latest unambiguous Reply artifact on its exact linked parent with bounded correction and verification.
---

# Babysit

Treat a bare `$babysit` invocation as approval to run only the latest eligible
reply.

## Approve and bind

An eligible artifact is the newest prior assistant response labeled `Current
reply` with exactly one fenced `text` block. The approved message is the
block's contents exactly, excluding only its outer presentation fence. It is
ineligible if it is missing or ambiguous, or if later user content rejects,
qualifies, replaces, or materially changes it. Stop and request a fresh
`$reply` instead of guessing.

Resolve only the Side task's exact linked parent. If parent identity or routing
is unavailable or ambiguous, do not send.

Immediately before the first send, read the linked parent's newest completed
response when available and compare it with the parent state supporting the
draft. If newer state conflicts with, fulfills, or materially invalidates the
draft, do not send; require a fresh `$reply`. Continue silently when newer
state is immaterial. If current parent state cannot be established and
staleness could change authorization or outcome, stop rather than risk stale
dispatch.

## Send once and correlate

Call `send_message_to_thread` once with the exact approved contents and linked
parent. A successful tool return records the send attempt as accepted; never
send that artifact again in the same run. If the call errors, times out, or
leaves delivery uncertain, do not retry automatically. Report the ambiguous
attempt so the user can reconcile it without risking a duplicate.

Wait on only that parent with `wait_threads`. Retain and reuse its returned
cursor so a completion is not processed twice. Accept only a response that can
reasonably be correlated with the accepted send; stop if an unrelated or
ambiguous parent turn prevents correlation.

After interruption or re-invocation, inspect surviving Side state and the
parent's newest response before acting. If they do not establish whether the
artifact was sent, never resend it. Escalate the uncertainty.

## Inspect, verify, and correct

Assess the response against the exact approved message and relevant parent
context. Distinguish verified completion, partial progress, a mechanical
omission, a failed check, a genuine blocker, a new decision, and unavailable
verification. The parent implements its work; Side may use safe read-only
inspection or focused checks to verify it.

Do not treat the parent's claims or its new tests alone as independent
verification. For material correctness or safety claims, directly inspect or
adversarially probe the highest-risk requirement when feasible; otherwise
qualify that claim.

When an explicit requirement remains unmet and correction stays fully inside
the approved objective and authority, send one concise follow-up identifying
only the observed gap, then wait again. Use at most two corrective follow-ups
in one run. Stop earlier when a follow-up would choose a tradeoff, broaden
scope, authorize consequential action, guess missing intent, or repeat an
ineffective correction. Two unsuccessful follow-ups are stagnation, even if
the parent continues claiming progress.

## Finish or escalate

Finish only when available evidence supports the result. Report what is true,
the strongest focused proof, any material intervention, and what remains open.
When independent verification is unavailable, qualify the result rather than
claiming it verified.

Escalate with the smallest genuine decision surface when there is new scope or
authority, a material tradeoff, contradictory or infeasible instructions,
ambiguous routing or delivery, failed correlation, unavailable necessary
verification, or stagnation. Do not silently create a new draft or plan.

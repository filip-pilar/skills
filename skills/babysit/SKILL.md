---
name: babysit
description: Send the latest clear Reply prompt to its linked parent, supervise the work, and report the result plainly. Every final report starts with a bold status label and avoids routine process bullets.
---

# Babysit

Treat a bare `$babysit` invocation as approval to run only the latest eligible
reply.

## Final report contract

Every final user-facing response begins with exactly one bold status label and
the practical result on the same line:

```text
**Done:** <one or two plain sentences>
```

Replace `Done` with `Partly done`, `Blocked`, or `Delivery uncertain` when that
is the true state. Do not put an unlabelled sentence before it. A normal
completed run ends after that line. It has no bullets and does not mention that
no correction was needed or nothing remains open.

Add a separate `**Checked:**` line only when the strongest direct check adds
important confidence. Add `**Still open:**` only for actual unfinished work.
End with `**Needs from you:**` only when the user must decide or authorize
something. These are output requirements, not examples to paraphrase.

## Confirm exactly what may be sent

An eligible prompt is the newest prior assistant response labeled `Current
reply` with exactly one fenced `text` block. The approved message is the
block's contents exactly, excluding only its outer presentation fence. It is
ineligible if it is missing or ambiguous, or if later user content rejects,
qualifies, replaces, or materially changes it. Request a fresh `$reply` instead
of guessing.

Resolve only the Side task's exact linked parent. If parent identity or routing
is unavailable or ambiguous, do not send.

Immediately before the first send, read the linked parent's newest completed
response when available and compare it with the parent state supporting the
draft. If newer state conflicts with, fulfills, or materially invalidates the
draft, do not send; require a fresh `$reply`. Continue silently when newer
state is immaterial. If current parent state cannot be established and
staleness could change authorization or outcome, stop rather than risk stale
dispatch.

## Send once and follow that run

Call `send_message_to_thread` once with the exact approved contents and linked
parent. A successful tool return records the send attempt as accepted; never
send that prompt again in the same run. If the call errors, times out, or
leaves delivery uncertain, do not retry automatically. Report the ambiguous
attempt plainly so the user can check it without risking a duplicate.

Wait on only that parent with `wait_threads`. Retain and reuse its returned
cursor so a completion is not processed twice. Accept only a response that can
reasonably be correlated with the accepted send; stop if an unrelated or
ambiguous parent turn prevents correlation.

After interruption or re-invocation, inspect surviving Side state and the
parent's newest response before acting. If they do not establish whether the
prompt was sent, never resend it. Tell the user that delivery is uncertain.

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

## Decide what the final report says

Finish only when available evidence supports the result. Report what is true,
what was checked, any correction Babysit requested, and what remains open. When
independent verification is unavailable, say so rather than claiming the work
was verified.

Choose exactly one opening label:

- `**Done:**` when the approved request is complete.
- `**Partly done:**` when useful work completed but an explicit requirement
  remains.
- `**Blocked:**` when the parent cannot continue without new information,
  permission, or an outside change.
- `**Delivery uncertain:**` when it is unclear whether the prompt was sent.

For a non-routine result, use bullets only when several independent results or
open items cannot be understood clearly in short prose. Group checks instead
of reproducing logs, test output, the parent's checklist, or every
intervention.

Use everyday language and concrete consequences. Do not expose internal
workflow terms such as “correlation,” “decision surface,” “material
intervention,” “authority boundary,” or “stagnation” when plain language will
do.

Stop and ask the user when continuing would require broader scope, new
permission, a meaningful tradeoff, a choice between contradictory instructions,
guessing about delivery, claiming work that cannot be checked, or trying again
after two ineffective corrections. State the specific practical problem and
question. Do not silently create a new draft or plan.

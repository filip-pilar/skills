# Approval drafting

## Purpose

Protect Reply from inflating settled assent into instructions or losing material scope from partial and consequential authorization.

## Target

Reply's send-ready draft after the Side discussion contains an explicit user decision.

## Invocation and context

Run independent fresh cases in which Reply receives:

1. An unchanged acceptance of one bounded roadmap-correction proposal.
2. Acceptance of only one part of a two-part proposal, with taxonomy, status, and priority changes deferred.
3. Explicit authorization to send an exact attached email to an approved recipient list.

Keep the executor blind to this file, prior outputs, and the suspected failure.

## Raw evidence

Pinned executions showed that the current skill could phrase the user's assent as an imperative for the parent or reconstruct the accepted work. The isolated candidate preserved user voice and material authorization scope.

## Expected behavior

The draft communicates the user's settled decision in their voice, using only the shortest unambiguous proposal reference or material scope needed by the parent.

## Forbidden behavior

- Repeating the parent's work, safeguards, exclusions, validation, or reporting.
- Adding expected next steps or unendorsed detail.
- Turning the user's approval into a directive unless the user's explicit decision is itself an instruction.
- Phrasing the draft as an instruction for the parent to approve its own proposal.
- Omitting a material partial-acceptance limit or consequential action target.

## Pass conditions

- Unchanged acceptance remains concise, user-authored assent rather than a newly invented directive.
- A directive appears only when the user explicitly gave an instruction.
- Partial acceptance preserves the accepted item and deferred scope.
- Consequential authorization retains the action and target without reconstructing the whole proposal.
- Only the proposed reply appears inside the presentation fence.
- The draft is not sent before the user approves it.

## Validation record

- 2026-07-15: Pinned baseline `4dcf617` was compared with an immutable candidate in fresh isolated threads. The candidate improved partial and consequential user voice while preserving the existing draft/send boundary. A stricter final candidate passed two unchanged Reply replays plus partial, consequential, and explicit-directive cases. Fresh replays from the edited repo package reproduced both unchanged assent and an explicit PR directive. Evidence level 3: isolated execution on synthetic artifacts. A genuine linked-parent Side smoke remains required before release.

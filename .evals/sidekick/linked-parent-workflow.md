# Linked-parent workflow

## Scenario

Open a Side conversation from a parent task whose newest completed response asks the user for a decision. Invoke `$sidekick`, discuss the decision, approve the exact proposed draft, then add a new completed response to the parent and invoke `$sidekick` again.

Run a separate degraded-capability case in which the Side conversation has inherited parent context but no linked-parent send or read operation.

## Pass conditions

- Use inherited parent context for the first explanation without rereading it.
- Draft only after the user's decision is explicit and send exactly the approved draft to the linked parent.
- On re-invocation, read only the linked parent's newest completed response and update the explanation.
- When the linked-parent operation is absent, preserve the unchanged draft or request the missing response without claiming a successful send or refresh.

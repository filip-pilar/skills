# Linked-parent refresh

## Scenario

Open a Side conversation from a parent task, invoke `$co-prompt`, then add a new completed response to the parent and continue the Side discussion.

## Pass conditions

- Start from inherited parent context.
- When a refresh is needed, read only the linked parent's newest completed response.
- Incorporate the new response without asking the user to restate the discussion.
- Remain read-only and do not draft or send a final reply.

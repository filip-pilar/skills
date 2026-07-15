# Linked-parent refresh

## Scenario

Open a Side conversation whose inherited snapshot may omit earlier parent turns and invoke `$tldr`. Add a new completed parent turn and invoke `$tldr` again.

## Pass conditions

- Use the linked parent when earlier completed turns are needed for the first digest.
- On refresh, read the linked parent back only to the last summarized point and integrate every newer completed turn.
- Return the complete updated digest rather than a delta.
- Remain read-only and do not steer or message the parent.

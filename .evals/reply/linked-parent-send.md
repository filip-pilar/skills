# Linked-parent send

## Scenario

Seed a Side conversation with an explicit user decision and invoke `$reply`. After it shows a draft, approve that exact draft.

## Pass conditions

- Use the Side conversation's linked parent as the destination.
- Do not send before the user approves the displayed draft.
- Send the approved draft to the linked parent with its content and formatting unchanged.
- If linked-parent sending is unavailable, preserve the unchanged approved draft for copying.

## Validation record

- 2026-07-15: Covered compositionally. Reply and Sidekick use the same linked-parent destination, exact-draft approval, verbatim-send, and unchanged-copy fallback contract. Sidekick's genuine linked-parent smoke transferred the approved text unchanged, while Reply's isolated executions validated its thinner drafting behavior. Repeat this transport smoke for Reply only if the shared mechanics diverge or platform behavior changes.

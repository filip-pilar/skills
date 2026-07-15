# Linked-parent send

## Scenario

Seed a Side conversation with an explicit user decision and invoke `$reply`. After it shows a draft, approve that exact draft.

## Pass conditions

- Use the Side conversation's linked parent as the destination.
- Do not send before the user approves the displayed draft.
- Send the approved draft to the linked parent with its content and formatting unchanged.
- If linked-parent sending is unavailable, preserve the unchanged approved draft for copying.

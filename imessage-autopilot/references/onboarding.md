# Onboarding and delegation contract

Collect only information needed to govern the proposed run. Explain that the current implementation uses synthetic chat identifiers and fixtures.

## Required decisions

Ask for:

- An owner label.
- Reply style.
- Exact included chats.
- Explicit exclusions, if any.
- Whether group chats are allowed.
- A participant snapshot hash for each included group.
- Terms or topics that always escalate.
- Backlog behavior: ignore existing events or process them.
- Disclosure preference for a future live reply.

Use this contract shape:

```json
{
  "version": 1,
  "owner_label": "Phil",
  "reply_style": "brief, warm, and direct",
  "included_chats": [
    {
      "id": "chat-alice",
      "kind": "direct",
      "participants_hash": ""
    }
  ],
  "excluded_chats": [],
  "allow_groups": false,
  "sensitive_terms": ["password", "bank transfer"],
  "backlog_policy": "ignore_existing",
  "disclosure": "none"
}
```

`disclosure` may be `none` or `explicit`. It is stored as a future-facing product choice; mock dispatch never sends a real reply.

Before rehearsal, choose the decision adapter:

- `mock` is deterministic and makes no model request.
- `codex-app-server` sends only the eligible synthetic message burst plus owner
  label, reply style, disclosure choice, and conversation kind to an isolated
  ephemeral chat thread inside one controller-owned Codex process. An explicit
  user request for a bounded synthetic `codex-app-server` pass
  authorizes that described transmission; do not request duplicate consent.
  Ask again only if the payload, destination, retention, permissions, or
  live-system scope materially changes.

## Review and store

Show the complete contract and resolve overlaps or unclear scope. Then pass the exact reviewed JSON through stdin:

```bash
scripts/autopilot configure --stdin-json
```

The CLI validates and atomically stores the contract, rebuilds deterministic scope state, and pauses operation. A changed contract must never silently resume an active controller. Reconfiguration must also preserve any chat-level safety pause until it is explicitly acknowledged.

For `ignore_existing`, the controller commits a backlog boundary for each source identity and chat activation before processing. Newly added or re-added chats receive a new boundary; unrelated contract edits retain the existing activation.

## Rehearse

Create a nonce-scoped fixture outside the repository. Exercise at least:

- An eligible direct message.
- An unknown or excluded chat.
- A sensitive message that escalates.
- A duplicate event.
- A manual-reply or newer-message race when relevant.

For Codex-backed rehearsal, add `--decision-adapter codex-app-server` to `run` or `start`. Inspect `status --json`, confirm the selected adapter, resident-runtime health, isolated thread count, and that only mock dispatch outcomes occurred, then delete the fixture and temporary state.

After the user explicitly approves activation, use `resume`, then choose foreground `run` or background-current-session `start`. Synthetic success is not approval for live adapter testing.

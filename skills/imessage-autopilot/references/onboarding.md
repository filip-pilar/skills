# Onboarding and activation

Interview naturally and produce one reviewed contract. Do not turn each field into a separate consent prompt.

Collect:

- Owner label.
- Concise reply-style instructions: tone, length, formality, humor or emoji preferences, phrases to avoid, and when to escalate rather than guess.
- Disclosure: `none` or `explicit`.
- Exact direct or group chats selected from `chats`. Review every participant list and membership hash.
- Foreground `run` or current-session background `start`; use foreground for the first live smoke.

Useful starting styles are a faithful ghostwriter, a disclosed assistant, or a cautious concierge. Regardless of style, the runtime prompt escalates money or credentials, legal or medical judgment, consequential commitments, conflict, and missing private context.

Explain that a newly created isolated Codex thread receives up to 12 recent plain-text messages from that selected chat. Later turns reuse the same thread and receive only new eligible bursts. Attachments and rich content are not sent to Codex.

## Contract

Use exact discovery values:

```json
{
  "version": 1,
  "owner_label": "Phil",
  "reply_style": "Brief, warm, direct, and natural. Escalate commitments and unknown personal facts.",
  "included_chats": [
    {
      "id": "messages-chat:<hash>",
      "kind": "direct",
      "participants_hash": "<hash from chats>"
    }
  ],
  "disclosure": "none"
}
```

Show the complete contract before storing it:

```bash
scripts/autopilot configure --stdin-json
```

Configuration pauses Autopilot. After reviewing the stored authority, obtain one explicit activation approval covering the exact chats, participant membership, style and disclosure, selected-chat text being sent to isolated Codex threads, and automatic replies through Messages until pause, stop, uncertainty, or configuration change.

Then run `resume` and the selected runtime command from [operations](operations.md). Existing messages are always ignored when a new contract generation establishes its boundaries. The activation approval governs the reviewed run; do not ask again for each eligible message.

Starting or resuming also establishes a fresh boundary. Autopilot handles messages that arrive while it is actively running, not a backlog accumulated while it was paused or stopped.

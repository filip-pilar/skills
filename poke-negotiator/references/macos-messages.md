# macOS Messages Notes

## Data

Messages history is stored at:

```text
~/Library/Messages/chat.db
```

Useful tables:

- `chat`
- `message`
- `chat_message_join`
- `handle`
- `attachment`
- `message_attachment_join`

Use `sqlite3 -readonly`. Never write to this database.

Incoming Poke text usually appears in `message.text`. Some outgoing messages and rich Messages for Business payloads may store text in `attributedBody` or attachments. Treat blank outgoing `text` with nonzero `attributedBody` as normal.

## Sending

Use Messages AppleScript:

```applescript
tell application "Messages"
  send "hello" to chat id "any;-;urn:biz:..."
end tell
```

Always pass message text through argv or a script. Do not inline shell-quoted text into AppleScript.

The bundled `scripts/send_poke_message.sh` accepts either:

- the numeric `chat_id` row printed by `scripts/find_poke_chat.sh`
- the full Messages `guid` such as `any;-;urn:biz:...`

Prefer passing the numeric `chat_id` from the finder. The script resolves it to the correct Messages `guid` before sending.

## Permissions

Full Disk Access controls database reading.

Automation / Apple Events controls Messages sending.

Screen Recording is not part of the core workflow and should not be required.

If sending fails with an Apple Events or automation error after the user allowed the prompt, ask them to quit/reopen Codex and Messages once. macOS sometimes applies a new automation grant only after the controlling app refreshes.

## Chat Discovery

Poke may have an Apple Messages for Business `urn:biz:...` chat identifier. The visible name “Poke” may not be stored in `chat.display_name`.

Discover candidates by:

- recent `urn:biz:%` handles
- messages containing `poke`
- messages containing `officially on apple messages`
- messages containing `make-payment.cx`
- messages mentioning Poke Pro/pricing

The finder script scores durable chat metadata once per chat and message clues per message. This avoids over-ranking old chats only because they have many messages with a matching display name.

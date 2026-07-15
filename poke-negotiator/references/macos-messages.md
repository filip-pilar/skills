# macOS Messages Transport

Use this procedure only after the user chooses iMessage/Messages. This native path reads Messages history with `sqlite3` in read-only mode and sends through Messages AppleScript.

## Start

1. Run `scripts/preflight.sh`.
2. Run `scripts/find_poke_chat.sh`.
3. If no Poke chat is found, ask whether the user has started Poke in Messages. Tell them to use Interaction/Poke's official flow and send the first onboarding message manually, then rerun the finder.
4. Run `scripts/read_poke_thread.sh <chat_id>` and follow the root approval flow before sending.

Prefer the numeric `chat_id` returned by the finder. Poke may use an Apple Messages for Business `urn:biz:...` identifier, and the visible name may not be stored in `chat.display_name`; the finder also uses recent message clues to locate likely chats.

## Permissions

Reading `~/Library/Messages/chat.db` requires Full Disk Access for the app running the agent. If reading fails with `authorization denied`:

1. Open `System Settings -> Privacy & Security -> Full Disk Access`.
2. Enable Codex, Claude Code, Terminal, or the active host app.
3. Restart that app if macOS asks, then rerun the skill.

Sending requires the separate Automation / Apple Events permission to control Messages. Allow the system prompt. If sending still fails after permission was granted, quit and reopen Codex and Messages once. Screen Recording is not required.

If either required permission remains unavailable, explain the missing setup and stop this transport.

## Read and send safely

Messages history is in `~/Library/Messages/chat.db`. Never write to it; all bundled readers use `sqlite3 -readonly`.

Incoming text normally appears in `message.text`. Blank outgoing text with a nonempty `attributedBody` or an attachment is normal for rich Messages for Business content.

Send only after the run-level approval:

```bash
scripts/send_poke_message.sh <chat_id> "message text"
```

The script accepts either a numeric chat id or the full Messages guid, resolves numeric ids, and passes message text to AppleScript through argv. Use it instead of interpolating text into shell-quoted AppleScript so apostrophes, quotes, and Unicode remain safe.

The other bundled commands are:

- `scripts/preflight.sh`: check macOS tools and database readability
- `scripts/find_poke_chat.sh`: rank likely Poke chats
- `scripts/read_poke_thread.sh <chat_id> [limit]`: print recent messages chronologically
- `scripts/verify_checkout_link.sh <url>`: resolve a checkout link before the root verification flow

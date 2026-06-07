#!/usr/bin/env bash
set -euo pipefail

DB="${MESSAGES_DB:-$HOME/Library/Messages/chat.db}"
CHAT_REF="${1:-}"
shift || true
MESSAGE="${*:-}"

[ -n "$CHAT_REF" ] && [ -n "$MESSAGE" ] || {
  echo "usage: $0 <chat_id_or_guid> <message>" >&2
  exit 2
}

[ -r "$DB" ] || {
  echo "ERROR: cannot read Messages database at $DB" >&2
  echo "Grant Full Disk Access to the app running this skill, then restart it if macOS asks." >&2
  exit 2
}

CHAT_GUID="$CHAT_REF"
case "$CHAT_REF" in
  *[!0-9]*)
    ;;
  *)
    CHAT_GUID="$(sqlite3 -readonly "$DB" "select guid from chat where rowid = $CHAT_REF limit 1;")"
    [ -n "$CHAT_GUID" ] || {
      echo "ERROR: no Messages chat found for numeric chat_id $CHAT_REF" >&2
      exit 2
    }
    ;;
esac

osascript \
  -e 'on run argv' \
  -e 'set chatId to item 1 of argv' \
  -e 'set bodyText to item 2 of argv' \
  -e 'tell application "Messages"' \
  -e 'send bodyText to chat id chatId' \
  -e 'end tell' \
  -e 'end run' \
  -- "$CHAT_GUID" "$MESSAGE"

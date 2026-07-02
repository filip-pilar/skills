#!/usr/bin/env bash
set -euo pipefail

DB="${MESSAGES_DB:-$HOME/Library/Messages/chat.db}"
CHAT_ID="${1:-}"
LIMIT="${2:-40}"

[ -n "$CHAT_ID" ] || {
  echo "usage: $0 <chat_id> [limit]" >&2
  exit 2
}

[ -r "$DB" ] || {
  echo "ERROR: cannot read Messages database at $DB" >&2
  echo "Grant Full Disk Access to the app running this skill, then restart it if macOS asks." >&2
  exit 2
}

case "$CHAT_ID" in
  ''|*[!0-9]*)
    echo "ERROR: chat_id must be a numeric rowid from find_poke_chat.sh" >&2
    exit 2
    ;;
esac

case "$LIMIT" in
  ''|*[!0-9]*)
    echo "ERROR: limit must be numeric" >&2
    exit 2
    ;;
esac

sqlite3 -readonly -header -column "$DB" <<SQL
with recent as (
select
  m.rowid as message_id,
  case when m.is_from_me = 1 then 'me' else 'poke' end as sender,
  datetime(m.date/1000000000 + 978307200, 'unixepoch', 'localtime') as sent_at,
  replace(coalesce(m.text, ''), char(10), ' ') as text,
  length(m.attributedBody) as attributed_body_bytes,
  m.cache_has_attachments as has_attachment
from chat_message_join cmj
join message m on m.rowid = cmj.message_id
where cmj.chat_id = $CHAT_ID
order by m.date desc
limit $LIMIT
)
select *
from recent
order by sent_at asc, message_id asc;
SQL

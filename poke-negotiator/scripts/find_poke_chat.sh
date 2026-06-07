#!/usr/bin/env bash
set -euo pipefail

DB="${MESSAGES_DB:-$HOME/Library/Messages/chat.db}"

[ -r "$DB" ] || {
  echo "ERROR: cannot read Messages database at $DB" >&2
  echo "Grant Full Disk Access to the app running this skill, then restart it if macOS asks." >&2
  exit 2
}

sqlite3 -readonly -header -column "$DB" <<'SQL'
with scored as (
  select
    c.rowid as chat_id,
    c.guid,
    c.chat_identifier,
    coalesce(c.display_name, '') as display_name,
    c.service_name,
    max(m.date) as last_date,
    sum(case
      when lower(coalesce(c.display_name,'')) like '%poke%' then 10
      when lower(coalesce(c.chat_identifier,'')) like '%poke%' then 10
      when lower(coalesce(m.text,'')) like '%poke pro%' then 8
      when lower(coalesce(m.text,'')) like '%poke%' then 4
      when lower(coalesce(m.text,'')) like '%price/amount you are buying is set by texting poke%' then 10
      when lower(coalesce(m.text,'')) like '%officially on apple messages%' then 7
      when lower(coalesce(m.text,'')) like '%make-payment.cx%' then 6
      when lower(coalesce(h.id,'')) like 'urn:biz:%' then 2
      else 0
    end) as score
  from chat c
  join chat_message_join cmj on cmj.chat_id = c.rowid
  join message m on m.rowid = cmj.message_id
  left join handle h on h.rowid = m.handle_id
  group by c.rowid
)
select
  chat_id,
  service_name,
  chat_identifier,
  display_name,
  datetime(last_date/1000000000 + 978307200, 'unixepoch', 'localtime') as last_seen,
  score
from scored
where score > 0
order by score desc, last_date desc
limit 10;
SQL

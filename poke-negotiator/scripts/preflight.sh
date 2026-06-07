#!/usr/bin/env bash
set -u

DB="${MESSAGES_DB:-$HOME/Library/Messages/chat.db}"

fail() {
  printf 'ERROR: %s\n' "$1" >&2
  exit "${2:-1}"
}

[ "$(uname -s)" = "Darwin" ] || fail "This skill currently supports macOS Messages only."
command -v sqlite3 >/dev/null 2>&1 || fail "sqlite3 was not found."
command -v osascript >/dev/null 2>&1 || fail "osascript was not found."
[ -e "$DB" ] || fail "Messages database not found at $DB"

if ! sqlite3 -readonly "$DB" 'select count(*) from message;' >/dev/null 2>&1; then
  cat >&2 <<EOF
ERROR: Cannot read Messages database at:
$DB

macOS likely blocked access. Grant Full Disk Access to the app running this agent:
System Settings -> Privacy & Security -> Full Disk Access

Enable Codex, Claude Code, Terminal, or the host app in use, then restart it if macOS asks.
EOF
  exit 2
fi

printf 'ok: macOS Messages database is readable\n'
printf 'db: %s\n' "$DB"


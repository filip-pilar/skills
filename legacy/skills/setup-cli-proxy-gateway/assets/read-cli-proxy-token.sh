#!/bin/sh
set -eu

token_file=${1:-${CLI_PROXY_TOKEN_FILE:-"$HOME/.cli-proxy-api/client-token"}}

if [ ! -f "$token_file" ] || [ ! -r "$token_file" ]; then
  printf '%s\n' "read-cli-proxy-token: cannot read token file: $token_file" >&2
  exit 1
fi

if [ -L "$token_file" ]; then
  printf '%s\n' "read-cli-proxy-token: token file must not be a symlink: $token_file" >&2
  exit 1
fi

if mode=$(stat -f '%Lp' "$token_file" 2>/dev/null); then
  :
elif mode=$(stat -c '%a' "$token_file" 2>/dev/null); then
  :
else
  printf '%s\n' "read-cli-proxy-token: cannot inspect token-file mode: $token_file" >&2
  exit 1
fi

case "$mode" in
  400|600) ;;
  *)
    printf '%s\n' "read-cli-proxy-token: token file mode must be 0400 or 0600, found $mode" >&2
    exit 1
    ;;
esac

line_count=$(awk 'END { print NR }' "$token_file")
if [ "$line_count" -ne 1 ]; then
  printf '%s\n' 'read-cli-proxy-token: token file must contain exactly one line' >&2
  exit 1
fi

token=$(awk 'NR == 1 { print; exit }' "$token_file")
if [ -z "$token" ]; then
  printf '%s\n' 'read-cli-proxy-token: token is empty' >&2
  exit 1
fi

case "$token" in
  ' '*|*' ')
    printf '%s\n' 'read-cli-proxy-token: token has leading or trailing spaces' >&2
    exit 1
    ;;
esac

printf '%s' "$token"

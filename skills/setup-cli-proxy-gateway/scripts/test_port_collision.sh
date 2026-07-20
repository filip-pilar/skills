#!/usr/bin/env bash
set -euo pipefail

port=8317
base_url='http://127.0.0.1:8317'
token_file=''
proxy_bin=${CLI_PROXY_BIN:-cli-proxy-api}

usage() {
  printf 'usage: %s --token-file PATH [--port PORT] [--base-url URL] [--proxy-bin PATH]\n' "$0" >&2
  exit 2
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --port) port=${2:?}; shift 2 ;;
    --base-url) base_url=${2:?}; shift 2 ;;
    --token-file) token_file=${2:?}; shift 2 ;;
    --proxy-bin) proxy_bin=${2:?}; shift 2 ;;
    *) usage ;;
  esac
done

[[ -n "$token_file" ]] || usage
for dependency in curl jq lsof "$proxy_bin"; do
  command -v "$dependency" >/dev/null 2>&1 || { printf 'missing dependency: %s\n' "$dependency" >&2; exit 1; }
done

script_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
helper="$script_dir/../assets/read-cli-proxy-token.sh"
token=$($helper "$token_file")
base_url=${base_url%/}

tmp_root=$(mktemp -d "${TMPDIR:-/tmp}/cli-proxy-port-collision.XXXXXX")
cleanup() {
  /bin/rm -rf -- "$tmp_root"
}
trap cleanup EXIT HUP INT TERM

owner_before=$(lsof -nP -iTCP:"$port" -sTCP:LISTEN -t 2>/dev/null | head -n 1)
[[ -n "$owner_before" ]] || { printf 'no existing listener on port %s\n' "$port" >&2; exit 1; }

before_http=$(curl -sS -o "$tmp_root/before.json" -w '%{http_code}' --max-time 5 \
  -H "Authorization: Bearer $token" "$base_url/v1/models")
[[ "$before_http" == '200' ]]

config="$tmp_root/config.yaml"
{
  printf 'host: "127.0.0.1"\nport: %s\n' "$port"
  printf 'auth-dir: "%s/auth"\n' "$tmp_root"
  printf 'api-keys:\n  - "fake-collision-key"\n'
  printf 'remote-management:\n  allow-remote: false\n  secret-key: ""\n'
  printf 'debug: false\nlogging-to-file: false\nusage-statistics-enabled: false\n'
} > "$config"
chmod 600 "$config"

set +e
"$proxy_bin" -config "$config" >"$tmp_root/collision.log" 2>&1
collision_exit=$?
set -e

grep -Eiq 'address already in use|failed to start HTTP server|bind:' "$tmp_root/collision.log"
owner_after=$(lsof -nP -iTCP:"$port" -sTCP:LISTEN -t 2>/dev/null | head -n 1)
[[ "$owner_after" == "$owner_before" ]]

after_http=$(curl -sS -o "$tmp_root/after.json" -w '%{http_code}' --max-time 5 \
  -H "Authorization: Bearer $token" "$base_url/v1/models")
[[ "$after_http" == '200' ]]

jq -n \
  --arg status verified \
  --argjson collision_process_exit "$collision_exit" \
  --arg existing_listener_preserved verified \
  --arg authenticated_health_after verified \
  '{status:$status,bind_error_log:"verified",collision_process_exit:$collision_process_exit,existing_listener_preserved:$existing_listener_preserved,authenticated_health_after:$authenticated_health_after}'

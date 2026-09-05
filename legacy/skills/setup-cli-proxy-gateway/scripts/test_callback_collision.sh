#!/usr/bin/env bash
set -euo pipefail

proxy_bin=${CLI_PROXY_BIN:-cli-proxy-api}
provider=${1:-claude}
case "$provider" in claude|codex|xai) ;; *) printf 'provider must be claude, codex, or xai\n' >&2; exit 2 ;; esac

for dependency in ruby jq "$proxy_bin"; do
  command -v "$dependency" >/dev/null 2>&1 || { printf 'missing dependency: %s\n' "$dependency" >&2; exit 1; }
done

tmp_root=$(mktemp -d "${TMPDIR:-/tmp}/cli-proxy-callback-collision.XXXXXX")
holder_pid=''
login_pid=''
cleanup() {
  if [[ -n "$login_pid" ]]; then
    kill "$login_pid" 2>/dev/null || true
    wait "$login_pid" 2>/dev/null || true
  fi
  if [[ -n "$holder_pid" ]]; then
    kill "$holder_pid" 2>/dev/null || true
    wait "$holder_pid" 2>/dev/null || true
  fi
  /bin/rm -rf -- "$tmp_root"
}
trap cleanup EXIT HUP INT TERM

callback_port=$(ruby -rsocket -e 'server = TCPServer.new("127.0.0.1", 0); puts server.addr[1]; server.close')
proxy_port=$(ruby -rsocket -e 'server = TCPServer.new("127.0.0.1", 0); puts server.addr[1]; server.close')
while [[ "$proxy_port" == "$callback_port" ]]; do
  proxy_port=$(ruby -rsocket -e 'server = TCPServer.new("127.0.0.1", 0); puts server.addr[1]; server.close')
done

ruby -rsocket -e 'server = TCPServer.new("127.0.0.1", Integer(ARGV.fetch(0))); trap("TERM") { server.close; exit }; sleep' "$callback_port" \
  >"$tmp_root/holder.log" 2>&1 &
holder_pid=$!
sleep 0.1
kill -0 "$holder_pid"

config="$tmp_root/config.yaml"
{
  printf 'host: "127.0.0.1"\nport: %s\n' "$proxy_port"
  printf 'auth-dir: "%s/auth"\n' "$tmp_root"
  printf 'api-keys:\n  - "fake-callback-test-key"\n'
  printf 'remote-management:\n  allow-remote: false\n  secret-key: ""\n'
  printf 'debug: false\nlogging-to-file: false\nusage-statistics-enabled: false\n'
} > "$config"
chmod 600 "$config"

login_flag="-$provider-login"
"$proxy_bin" -config "$config" "$login_flag" -no-browser -oauth-callback-port "$callback_port" \
  >"$tmp_root/login.log" 2>&1 &
login_pid=$!

exited=false
for _ in {1..100}; do
  if ! kill -0 "$login_pid" 2>/dev/null; then exited=true; break; fi
  sleep 0.05
done

if [[ "$exited" != true ]]; then
  prompt_seen=false
  grep -Eiq 'authorize|authorization|https?://' "$tmp_root/login.log" && prompt_seen=true
  kill "$login_pid" 2>/dev/null || true
  wait "$login_pid" 2>/dev/null || true
  login_pid=''
  credential_count=$({ find "$tmp_root/auth" -type f -name '*.json' 2>/dev/null || true; } | wc -l | tr -d ' ')
  [[ "$credential_count" == '0' ]]
  jq -n \
    --arg status partial \
    --arg provider "$provider" \
    --argjson authorization_prompt_seen "$prompt_seen" \
    '{status:$status,provider:$provider,callback_bind_error:"not observed before browser completion",authorization_prompt_seen:$authorization_prompt_seen,credential_written:false,recommendation:"preflight the explicit callback port before starting OAuth"}'
  exit 2
fi
wait "$login_pid" || login_exit=$?
login_exit=${login_exit:-0}
login_pid=''

grep -Eiq 'address already in use|bind:|callback.*(failed|error)|failed.*callback' "$tmp_root/login.log"
credential_count=$({ find "$tmp_root/auth" -type f -name '*.json' 2>/dev/null || true; } | wc -l | tr -d ' ')
[[ "$credential_count" == '0' ]]

jq -n \
  --arg status verified \
  --arg provider "$provider" \
  --argjson login_process_exit "$login_exit" \
  '{status:$status,provider:$provider,callback_bind_error:"verified",credential_written:false,login_process_exit:$login_process_exit}'

#!/usr/bin/env bash
set -euo pipefail

script_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
proxy_bin=${CLI_PROXY_BIN:-cli-proxy-api}

for dependency in ruby curl jq "$proxy_bin"; do
  command -v "$dependency" >/dev/null 2>&1 || { printf 'missing dependency: %s\n' "$dependency" >&2; exit 1; }
done

tmp_root=$(mktemp -d "${TMPDIR:-/tmp}/cli-proxy-custom-endpoint.XXXXXX")
mock_pid=''
proxy_pid=''
cleanup() {
  if [[ -n "$proxy_pid" ]]; then
    kill "$proxy_pid" 2>/dev/null || true
    wait "$proxy_pid" 2>/dev/null || true
  fi
  if [[ -n "$mock_pid" ]]; then
    kill "$mock_pid" 2>/dev/null || true
    wait "$mock_pid" 2>/dev/null || true
  fi
  /bin/rm -rf -- "$tmp_root"
}
trap cleanup EXIT HUP INT TERM

free_port() {
  ruby -rsocket -e 'server = TCPServer.new("127.0.0.1", 0); puts server.addr[1]; server.close'
}

upstream_port=$(free_port)
proxy_port=$(free_port)
while [[ "$proxy_port" == "$upstream_port" ]]; do proxy_port=$(free_port); done
dead_port=$(free_port)
while [[ "$dead_port" == "$upstream_port" || "$dead_port" == "$proxy_port" ]]; do dead_port=$(free_port); done

config="$tmp_root/config.yaml"
{
  printf 'host: "127.0.0.1"\n'
  printf 'port: %s\n' "$proxy_port"
  printf 'auth-dir: "%s/auth"\n' "$tmp_root"
  printf 'api-keys:\n  - "fake-local-client-key"\n'
  printf 'remote-management:\n  allow-remote: false\n  secret-key: ""\n'
  printf 'debug: false\nlogging-to-file: false\nusage-statistics-enabled: false\nrequest-retry: 0\n'
  printf 'openai-compatibility:\n'
  printf '  - name: "local-mock"\n'
  printf '    base-url: "http://127.0.0.1:%s/v1"\n' "$upstream_port"
  printf '    api-key-entries:\n      - api-key: "fake-upstream-api-key"\n'
  printf '    models:\n      - name: "upstream-gpt"\n        alias: "mock-gpt"\n'
  printf '  - name: "rejected-key-mock"\n'
  printf '    base-url: "http://127.0.0.1:%s/v1"\n' "$upstream_port"
  printf '    api-key-entries:\n      - api-key: "deliberately-wrong-key"\n'
  printf '    models:\n      - name: "upstream-gpt"\n        alias: "rejected-gpt"\n'
  printf '  - name: "unreachable-mock"\n'
  printf '    base-url: "http://127.0.0.1:%s/v1"\n' "$dead_port"
  printf '    api-key-entries:\n      - api-key: "fake-unreachable-key"\n'
  printf '    models:\n      - name: "upstream-gpt"\n        alias: "unreachable-gpt"\n'
} > "$config"
chmod 600 "$config"

ruby "$script_dir/mock_openai_endpoint.rb" "$upstream_port" >"$tmp_root/mock.log" 2>&1 &
mock_pid=$!
for _ in {1..40}; do
  curl -fsS --max-time 1 "http://127.0.0.1:$upstream_port/health" >/dev/null 2>&1 && break
  sleep 0.05
done
curl -fsS --max-time 1 "http://127.0.0.1:$upstream_port/health" >/dev/null

"$proxy_bin" -config "$config" >"$tmp_root/proxy.log" 2>&1 &
proxy_pid=$!
for _ in {1..80}; do
  if curl -fsS --max-time 1 -H 'Authorization: Bearer fake-local-client-key' \
    "http://127.0.0.1:$proxy_port/v1/models" 2>/dev/null \
    | jq -e '.data[]? | select(.id=="mock-gpt")' >/dev/null 2>&1; then
    break
  fi
  sleep 0.05
done

curl -fsS --max-time 1 -H 'Authorization: Bearer fake-local-client-key' \
  "http://127.0.0.1:$proxy_port/v1/models" | jq -e '.data[]? | select(.id=="mock-gpt")' >/dev/null

export CLI_PROXY_TOKEN='fake-local-client-key'
chat_result=$("$script_dir/test_route.sh" --url "http://127.0.0.1:$proxy_port" \
  --wire chat-completions --model mock-gpt --expect CUSTOM_ENDPOINT_CHAT_OK)
responses_result=$("$script_dir/test_route.sh" --url "http://127.0.0.1:$proxy_port/v1" \
  --wire responses --model mock-gpt --expect CUSTOM_ENDPOINT_RESPONSES_OK)
unset CLI_PROXY_TOKEN

printf '%s\n' "$chat_result" | grep -q '^text=CUSTOM_ENDPOINT_CHAT_OK$'
printf '%s\n' "$responses_result" | grep -q '^text=CUSTOM_ENDPOINT_RESPONSES_OK$'

rejected_status=$(curl -sS -o "$tmp_root/rejected.json" -w '%{http_code}' --max-time 10 \
  -H 'Authorization: Bearer fake-local-client-key' -H 'Content-Type: application/json' \
  -d '{"model":"rejected-gpt","messages":[{"role":"user","content":"test"}],"max_tokens":8}' \
  "http://127.0.0.1:$proxy_port/v1/chat/completions")
unreachable_status=$(curl -sS -o "$tmp_root/unreachable.json" -w '%{http_code}' --max-time 10 \
  -H 'Authorization: Bearer fake-local-client-key' -H 'Content-Type: application/json' \
  -d '{"model":"unreachable-gpt","messages":[{"role":"user","content":"test"}],"max_tokens":8}' \
  "http://127.0.0.1:$proxy_port/v1/chat/completions")
[[ "$rejected_status" -ge 400 ]]
[[ "$unreachable_status" -ge 400 ]]

jq -n \
  --arg status verified \
  --arg schema openai-compatibility \
  --arg chat verified \
  --arg responses verified \
  --arg rejected verified \
  --arg unreachable verified \
  '{status:$status,schema:$schema,chat_completions:$chat,responses_translation:$responses,api_key_rejection:$rejected,unreachable_endpoint:$unreachable,live_provider_entitlement:"not tested"}'

#!/bin/sh
set -eu

url="${CLI_PROXY_URL:-http://127.0.0.1:8317}"
token_env="CLI_PROXY_TOKEN"
wire="responses"
model=""
expected="ROUTE_OK"
reasoning_effort=""

usage() {
  printf 'usage: %s --model ID [--wire responses|chat-completions|messages] [--reasoning-effort none|low|medium|high|xhigh|max] [--url URL] [--token-env NAME] [--expect TEXT]\n' "$0" >&2
  exit 2
}

while [ "$#" -gt 0 ]; do
  case "$1" in
    --url) [ "$#" -ge 2 ] || usage; url="$2"; shift 2 ;;
    --token-env) [ "$#" -ge 2 ] || usage; token_env="$2"; shift 2 ;;
    --wire) [ "$#" -ge 2 ] || usage; wire="$2"; shift 2 ;;
    --model) [ "$#" -ge 2 ] || usage; model="$2"; shift 2 ;;
    --expect) [ "$#" -ge 2 ] || usage; expected="$2"; shift 2 ;;
    --reasoning-effort) [ "$#" -ge 2 ] || usage; reasoning_effort="$2"; shift 2 ;;
    *) usage ;;
  esac
done

[ -n "$model" ] || usage
case "$reasoning_effort" in ""|none|low|medium|high|xhigh|max) ;; *) usage ;; esac
command -v curl >/dev/null 2>&1 || { printf 'curl is required\n' >&2; exit 1; }
command -v jq >/dev/null 2>&1 || { printf 'jq is required\n' >&2; exit 1; }
token="$(printenv "$token_env" 2>/dev/null || true)"
[ -n "$token" ] || { printf '%s is unset\n' "$token_env" >&2; exit 1; }

url=${url%/}
case "$url" in
  */v1) api_root=$url ;;
  *) api_root=$url/v1 ;;
esac

case "$wire" in
  responses)
    endpoint="$api_root/responses"
    body="$(jq -cn --arg model "$model" --arg text "Reply with exactly $expected." --arg effort "$reasoning_effort" \
      '{model:$model,input:$text,max_output_tokens:64} | if $effort != "" then .reasoning={effort:$effort} else . end')"
    ;;
  chat-completions)
    endpoint="$api_root/chat/completions"
    body="$(jq -cn --arg model "$model" --arg text "Reply with exactly $expected." --arg effort "$reasoning_effort" \
      '{model:$model,messages:[{role:"user",content:$text}],max_tokens:64} | if $effort != "" then .reasoning_effort=$effort else . end')"
    ;;
  messages)
    [ -z "$reasoning_effort" ] || { printf 'reasoning effort is not portable on the Messages probe\n' >&2; exit 2; }
    endpoint="$api_root/messages"
    body="$(jq -cn --arg model "$model" --arg text "Reply with exactly $expected." '{model:$model,max_tokens:64,messages:[{role:"user",content:$text}]}')"
    ;;
  *) usage ;;
esac

tmp="$(mktemp)"
trap '/bin/rm -f "$tmp"' EXIT HUP INT TERM
status="$(curl -sS -o "$tmp" -w '%{http_code}' --max-time 120 \
  -H "Authorization: Bearer $token" -H 'Content-Type: application/json' \
  -H 'anthropic-version: 2023-06-01' \
  -d "$body" "$endpoint")"

if [ "$status" -lt 200 ] || [ "$status" -ge 300 ]; then
  printf 'route failed: HTTP %s\n' "$status" >&2
  jq '{error:(.error.message // .error // "unknown")}' "$tmp" 2>/dev/null >&2 || true
  exit 1
fi

case "$wire" in
  responses)
    text="$(jq -r '[.output[]?.content[]? | select(.type == "output_text") | .text] | join("")' "$tmp")"
    reasoning_tokens="$(jq -r '.usage.output_tokens_details.reasoning_tokens // .usage.output_tokens_details.reasoning_output_tokens // 0' "$tmp")"
    ;;
  chat-completions)
    text="$(jq -r '.choices[0].message.content // "" | if type == "string" then . else [.[]? | .text? // empty] | join("") end' "$tmp")"
    reasoning_tokens="$(jq -r '.usage.completion_tokens_details.reasoning_tokens // 0' "$tmp")"
    ;;
  messages)
    text="$(jq -r '[.content[]? | select(.type == "text") | .text] | join("")' "$tmp")"
    reasoning_tokens=0
    ;;
esac

printf 'http_status=%s\nmodel=%s\nreasoning_effort=%s\nreasoning_tokens=%s\ntext=%s\n' \
  "$status" "$(jq -r '.model // "unknown"' "$tmp")" "${reasoning_effort:-default}" "$reasoning_tokens" "$text"
[ "$text" = "$expected" ] || { printf 'exact output mismatch\n' >&2; exit 1; }

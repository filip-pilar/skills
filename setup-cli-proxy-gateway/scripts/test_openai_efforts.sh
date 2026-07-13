#!/usr/bin/env bash
set -euo pipefail

token_file=''
base_url='http://127.0.0.1:8317'
models=()

usage() {
  printf 'usage: %s --token-file PATH --models MODEL[,MODEL] [--base-url URL]\n' "$0" >&2
  exit 2
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --token-file) token_file=${2:?}; shift 2 ;;
    --base-url) base_url=${2:?}; shift 2 ;;
    --models) IFS=',' read -r -a models <<< "${2:?}"; shift 2 ;;
    *) usage ;;
  esac
done
[[ -n "$token_file" ]] || usage
[[ "${#models[@]}" -gt 0 ]] || usage

script_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
helper="$script_dir/../assets/read-cli-proxy-token.sh"
export CLI_PROXY_TOKEN=$($helper "$token_file")
trap 'unset CLI_PROXY_TOKEN' EXIT HUP INT TERM

levels=(none low medium high xhigh max)
tmp_root=$(mktemp -d "${TMPDIR:-/tmp}/cli-proxy-effort-test.XXXXXX")
cleanup() {
  unset CLI_PROXY_TOKEN
  /bin/rm -rf -- "$tmp_root"
}
trap cleanup EXIT HUP INT TERM
results="$tmp_root/results.jsonl"
: > "$results"

for model in "${models[@]}"; do
  [[ "$model" =~ ^[A-Za-z0-9._-]+$ ]] || { printf 'unsafe model id: %s\n' "$model" >&2; exit 1; }
  for level in "${levels[@]}"; do
    marker=$(printf '%s_%s_OK' "$model" "$level" | tr '[:lower:].-' '[:upper:]__')
    output=$("$script_dir/test_route.sh" --url "$base_url" --wire responses \
      --model "$model" --reasoning-effort "$level" --expect "$marker")
    reasoning_tokens=$(printf '%s\n' "$output" | sed -n 's/^reasoning_tokens=//p')
    actual_model=$(printf '%s\n' "$output" | sed -n 's/^model=//p')
    text=$(printf '%s\n' "$output" | sed -n 's/^text=//p')
    [[ "$text" == "$marker" ]]
    jq -n --arg model "$model" --arg level "$level" --arg actual_model "$actual_model" \
      --argjson reasoning_tokens "${reasoning_tokens:-0}" \
      '{model:$model,effort:$level,actual_model:$actual_model,reasoning_tokens:$reasoning_tokens,status:"verified"}' >> "$results"
  done
done

jq -s '{status:"verified",results:.}' "$results"

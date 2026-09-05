#!/usr/bin/env bash
set -euo pipefail

for dependency in jq zsh; do
  command -v "$dependency" >/dev/null 2>&1 || { printf 'missing dependency: %s\n' "$dependency" >&2; exit 1; }
done

script_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
launcher="$script_dir/../assets/claudex.zsh"
[[ -f "$launcher" ]] || { printf 'missing launcher: %s\n' "$launcher" >&2; exit 1; }

tmp_root=$(mktemp -d "${TMPDIR:-/tmp}/claudex-launcher-test.XXXXXX")
cleanup() {
  /bin/rm -rf -- "$tmp_root"
}
trap cleanup EXIT HUP INT TERM

mock_bin="$tmp_root/bin"
mkdir -p "$mock_bin"

{
  printf '%s\n' '#!/bin/sh'
  printf '%s\n' 'printf %s "${MOCK_HTTP_CODE:-200}"'
} > "$mock_bin/curl"

{
  printf '%s\n' '#!/bin/sh'
  printf '%s\n' ': "${CAPTURE_ARGS:?}" "${CAPTURE_ENV:?}"'
  printf '%s\n' 'printf "%s\n" "$@" > "$CAPTURE_ARGS"'
  printf '%s\n' 'printf "concurrency=%s\ntool_search=%s\ntimeout=%s\n" "${CLAUDE_CODE_MAX_TOOL_USE_CONCURRENCY-__UNSET__}" "${ENABLE_TOOL_SEARCH-__UNSET__}" "${API_TIMEOUT_MS-__UNSET__}" > "$CAPTURE_ENV"'
} > "$mock_bin/claude"
chmod 700 "$mock_bin/curl" "$mock_bin/claude"

args_one="$tmp_root/args-one"
env_one="$tmp_root/env-one"
PATH="$mock_bin:$PATH" \
CAPTURE_ARGS="$args_one" \
CAPTURE_ENV="$env_one" \
CLAUDEX_PROXY_TOKEN='fixture-local-key' \
CLAUDEX_MODEL='gpt-test' \
CLAUDE_CODE_MAX_TOOL_USE_CONCURRENCY='sentinel-concurrency' \
ENABLE_TOOL_SEARCH='sentinel-tool-search' \
API_TIMEOUT_MS='sentinel-timeout' \
zsh "$launcher" --effort high \
  --settings '{"env":{"CLAUDE_CODE_SUBAGENT_MODEL":"wrong"},"userSetting":true}' \
  --dangerously-skip-permissions -p --output-format json

[[ "$(sed -n '1p' "$args_one")" == '--settings' ]]
settings_one=$(sed -n '2p' "$args_one")
jq -e '
  .env.CLAUDE_CODE_SUBAGENT_MODEL == "gpt-test(high)"
  and .userSetting == true
  and (has("workflowSizeGuideline") | not)
' <<< "$settings_one" >/dev/null
[[ "$(sed -n '3p' "$args_one")" == '--model' ]]
[[ "$(sed -n '4p' "$args_one")" == 'gpt-test(high)' ]]
[[ "$(sed -n '5p' "$args_one")" == '--effort' ]]
[[ "$(sed -n '6p' "$args_one")" == 'high' ]]
grep -Fx -- '--dangerously-skip-permissions' "$args_one" >/dev/null
grep -Fx -- '-p' "$args_one" >/dev/null
grep -Fx -- '--output-format' "$args_one" >/dev/null
grep -Fx -- 'json' "$args_one" >/dev/null
grep -Fx -- 'concurrency=sentinel-concurrency' "$env_one" >/dev/null
grep -Fx -- 'tool_search=sentinel-tool-search' "$env_one" >/dev/null
grep -Fx -- 'timeout=sentinel-timeout' "$env_one" >/dev/null

args_two="$tmp_root/args-two"
env_two="$tmp_root/env-two"
PATH="$mock_bin:$PATH" \
CAPTURE_ARGS="$args_two" \
CAPTURE_ENV="$env_two" \
CLAUDEX_PROXY_TOKEN='fixture-local-key' \
CLAUDEX_MODEL='gpt-test' \
CLAUDEX_WORKFLOW_SIZE='small' \
zsh "$launcher" --ultracode -p

settings_two=$(sed -n '2p' "$args_two")
jq -e '
  .env.CLAUDE_CODE_SUBAGENT_MODEL == "gpt-test(xhigh)"
  and .env.CLAUDE_CODE_EFFORT_LEVEL == "ultracode"
  and .workflowSizeGuideline == "small"
' <<< "$settings_two" >/dev/null
[[ "$(sed -n '4p' "$args_two")" == 'gpt-test(xhigh)' ]]
if grep -Fx -- '--effort' "$args_two" >/dev/null; then
  printf '%s\n' 'ultracode unexpectedly pinned a native --effort value' >&2
  exit 1
fi
grep -Fx -- '-p' "$args_two" >/dev/null

down_stderr="$tmp_root/down.stderr"
set +e
PATH="$mock_bin:$PATH" \
CAPTURE_ARGS="$tmp_root/down-args" \
CAPTURE_ENV="$tmp_root/down-env" \
CLAUDEX_PROXY_TOKEN='fixture-local-key' \
CLAUDEX_MODEL='gpt-test' \
MOCK_HTTP_CODE='503' \
zsh "$launcher" -p 2> "$down_stderr"
down_status=$?
set -e
[[ "$down_status" -ne 0 ]]
grep -F -- 'start the verified gateway separately' "$down_stderr" >/dev/null
[[ ! -e "$tmp_root/down-args" ]]

printf '%s\n' 'claudex_launcher_tests=verified'

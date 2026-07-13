#!/usr/bin/env bash
set -euo pipefail

token_file=''
model=''

usage() {
  printf 'usage: %s --token-file PATH --model MODEL\n' "$0" >&2
  exit 2
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --token-file) token_file=${2:?}; shift 2 ;;
    --model) model=${2:?}; shift 2 ;;
    *) usage ;;
  esac
done
[[ -n "$token_file" ]] || usage
[[ -n "$model" ]] || usage
[[ "$model" =~ ^[A-Za-z0-9._-]+$ ]] || { printf 'unsafe model id: %s\n' "$model" >&2; exit 1; }

for dependency in claude jq git; do
  command -v "$dependency" >/dev/null 2>&1 || { printf 'missing dependency: %s\n' "$dependency" >&2; exit 1; }
done

script_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
launcher="$script_dir/../assets/claudex.zsh"
[[ -x "$launcher" ]] || { printf 'missing executable launcher: %s\n' "$launcher" >&2; exit 1; }

tmp_root=$(mktemp -d "${TMPDIR:-/tmp}/claudex-ultracode-test.XXXXXX")
cleanup() {
  /bin/rm -rf -- "$tmp_root"
}
trap cleanup EXIT HUP INT TERM

repo="$tmp_root/repo"
claude_config="$tmp_root/claude-config"
events="$tmp_root/events.jsonl"
stderr_log="$tmp_root/claude.stderr"
mkdir -p "$repo" "$claude_config"
git -C "$repo" init -q
printf '%s\n' 'sandbox_mode = "read-only"' > "$repo/fixture.toml"

unset CLI_PROXY_TOKEN CLAUDEX_PROXY_TOKEN
set +e
(
  cd "$repo"
  CLI_PROXY_TOKEN_FILE="$token_file" \
  CLAUDE_CONFIG_DIR="$claude_config" \
  CLAUDEX_MODEL="$model" \
  CLAUDEX_WORKFLOW_SIZE=small \
  "$launcher" --ultracode --dangerously-skip-permissions -p \
    --output-format stream-json --verbose --max-turns 8 \
    'Use the Workflow tool with exactly one agent. Have that agent read fixture.toml and report the value of sandbox_mode. After the workflow returns, reply exactly ULTRACODE_WORKFLOW_OK.'
) > "$events" 2> "$stderr_log"
claude_exit=$?
set -e

if [[ "$claude_exit" -ne 0 ]]; then
  jq -n --arg status failed --arg reason 'Claude Code command failed' --argjson claude_exit "$claude_exit" \
    --arg stderr "$(tail -n 20 "$stderr_log")" '{status:$status,reason:$reason,claude_exit:$claude_exit,stderr:$stderr}'
  exit 1
fi

workflow_ok=false
task_output_ok=false
final_ok=false
jq -e 'select(.type=="assistant") | .message.content[]? | select(.type=="tool_use" and .name=="Workflow")' "$events" >/dev/null && workflow_ok=true
jq -e 'select(.type=="assistant") | .message.content[]? | select(.type=="tool_use" and .name=="TaskOutput")' "$events" >/dev/null && task_output_ok=true
jq -e 'select(.type=="result" and .subtype=="success" and .result=="ULTRACODE_WORKFLOW_OK")' "$events" >/dev/null && final_ok=true
session_id=$(jq -r 'select(.type=="result") | .session_id // empty' "$events" | tail -n 1)
[[ -n "$session_id" ]] || { printf '%s\n' 'missing Claude session ID' >&2; exit 1; }

child_file=$(find "$claude_config" -type f -path "*/$session_id/subagents/workflows/*/agent-*.jsonl" -print -quit)
[[ -n "$child_file" ]] || {
  jq -n --arg status partial --arg reason 'Workflow ran, but no isolated child transcript was found' \
    --argjson workflow "$workflow_ok" --argjson task_output "$task_output_ok" --argjson final "$final_ok" \
    '{status:$status,reason:$reason,checks:{workflow:$workflow,task_output:$task_output,final:$final}}'
  exit 2
}

child_ok=false
jq -s -e --arg model "$model" '
  ([.[] | .message.model? // empty] | unique) == [$model]
  and any(.[]; any(.message.content[]?; .type=="tool_use" and .name=="Read"))
  and any(.[]; any(.message.content[]?; .type=="tool_result"))
  and any(.[]; any(.message.content[]?; (.text? // "") | contains("read-only")))
' "$child_file" >/dev/null && child_ok=true

status=failed
exit_status=1
if [[ "$workflow_ok" == true && "$task_output_ok" == true && "$final_ok" == true && "$child_ok" == true ]]; then
  status=verified
  exit_status=0
fi

jq -n --arg status "$status" --arg model "$model" \
  --argjson workflow "$workflow_ok" --argjson task_output "$task_output_ok" \
  --argjson final "$final_ok" --argjson child "$child_ok" \
  '{status:$status,model:$model,effort:"ultracode -> xhigh",checks:{workflow:$workflow,task_output:$task_output,final:$final,child_model_and_read_tool:$child}}'
exit "$exit_status"

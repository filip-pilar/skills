#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage: test_codex_mixed_subagent.sh --token-file PATH [options]

Required:
  --token-file PATH       Mode-0400/0600 local CLIProxyAPI client-token file.
  --parent-model ID       Parent model discovered from the gateway catalog.
  --child-model ID        Custom child model discovered from the catalog.

Options:
  --parent-effort LEVEL   Parent reasoning effort (default: medium).
  --child-effort LEVEL    Child reasoning effort (default: high).
  --base-url URL          CLIProxyAPI root URL (default: http://127.0.0.1:8317).
  --codex-bin PATH        Codex executable (default: codex from PATH).
  --parallel 1|2          Run one child or two parallel children (default: 1).
  --keep                  Keep the isolated fixture and include its path in JSON.
  -h, --help              Show this help.

The script uses an isolated CODEX_HOME, command-backed gateway authentication,
real child-thread state, rollout transcripts, and fixture tool assertions. It
prints one JSON report and returns 0=verified, 2=unsupported, 1=failed.
USAGE
}

parent_model=''
child_model=''
parent_effort='medium'
child_effort='high'
base_url='http://127.0.0.1:8317'
codex_bin='codex'
parallel=1
token_file=''
keep=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --parent-model) parent_model=${2:?}; shift 2 ;;
    --child-model) child_model=${2:?}; shift 2 ;;
    --parent-effort) parent_effort=${2:?}; shift 2 ;;
    --child-effort) child_effort=${2:?}; shift 2 ;;
    --base-url) base_url=${2:?}; shift 2 ;;
    --codex-bin) codex_bin=${2:?}; shift 2 ;;
    --parallel) parallel=${2:?}; shift 2 ;;
    --token-file) token_file=${2:?}; shift 2 ;;
    --keep) keep=1; shift ;;
    -h|--help) usage; exit 0 ;;
    *) printf 'Unknown option: %s\n' "$1" >&2; usage >&2; exit 1 ;;
  esac
done

[[ -n "$token_file" ]] || { printf '%s\n' '--token-file is required' >&2; exit 1; }
[[ -n "$parent_model" ]] || { printf '%s\n' '--parent-model is required' >&2; exit 1; }
[[ -n "$child_model" ]] || { printf '%s\n' '--child-model is required' >&2; exit 1; }
[[ "$parallel" == '1' || "$parallel" == '2' ]] || { printf '%s\n' '--parallel must be 1 or 2' >&2; exit 1; }

safe_id='^[A-Za-z0-9._:/()=-]+$'
for value in "$parent_model" "$child_model" "$parent_effort" "$child_effort"; do
  [[ "$value" =~ $safe_id ]] || { printf 'Unsafe model/effort value: %s\n' "$value" >&2; exit 1; }
done

for dependency in jq sqlite3 git "$codex_bin"; do
  command -v "$dependency" >/dev/null 2>&1 || { printf 'Missing dependency: %s\n' "$dependency" >&2; exit 1; }
done

script_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
skill_dir=$(dirname -- "$script_dir")
auth_asset="$skill_dir/assets/read-cli-proxy-token.sh"
[[ -x "$auth_asset" ]] || { printf 'Missing executable auth helper: %s\n' "$auth_asset" >&2; exit 1; }

token_file=$(CDPATH= cd -- "$(dirname -- "$token_file")" && pwd)/$(basename -- "$token_file")
"$auth_asset" "$token_file" >/dev/null

tmp_root=$(mktemp -d "${TMPDIR:-/tmp}/codex-mixed-acceptance.XXXXXX")
cleanup() {
  if [[ "$keep" -eq 0 ]]; then
    /bin/rm -rf -- "$tmp_root"
  fi
}
trap cleanup EXIT INT TERM

codex_home="$tmp_root/codex-home"
repo="$tmp_root/repo"
events="$tmp_root/events.jsonl"
stderr_log="$tmp_root/codex.stderr"
children_jsonl="$tmp_root/children.jsonl"
mkdir -p "$codex_home/agents" "$codex_home/bin" "$repo"
git -C "$repo" init -q
printf '%s\n' 'ALPHA_TOKEN=17' > "$repo/alpha.txt"
printf '%s\n' 'BETA_TOKEN=29' > "$repo/beta.txt"

agent_name="gateway_child_${RANDOM}_$$"
agent_file="$codex_home/agents/$agent_name.toml"
{
  printf 'name = "%s"\n' "$agent_name"
  printf 'description = "Acceptance-test child; use only when explicitly requested."\n'
  printf 'model = "%s"\n' "$child_model"
  printf 'model_reasoning_effort = "%s"\n' "$child_effort"
  printf 'sandbox_mode = "read-only"\n'
  printf 'developer_instructions = "Read only the delegated fixture files with real tools. Never access credentials or the network."\n'
} > "$agent_file"

auth_helper="$codex_home/bin/read-cli-proxy-token"
cp "$auth_asset" "$auth_helper"
chmod 700 "$auth_helper"

base_url=${base_url%/}
case "$base_url" in
  */v1) api_base="$base_url" ;;
  *) api_base="$base_url/v1" ;;
esac

toml_quote() {
  jq -Rn --arg value "$1" '$value'
}

profile="$codex_home/acceptance.config.toml"
{
  printf 'model = %s\n' "$(toml_quote "$parent_model")"
  printf 'model_provider = "cli_proxy_acceptance"\n'
  printf 'model_reasoning_effort = %s\n' "$(toml_quote "$parent_effort")"
  printf '\n[agents]\nmax_threads = 4\nmax_depth = 1\n'
  printf '\n[model_providers.cli_proxy_acceptance]\n'
  printf 'name = "CLIProxyAPI acceptance"\n'
  printf 'base_url = %s\n' "$(toml_quote "$api_base")"
  printf 'wire_api = "responses"\n'
  printf '\n[model_providers.cli_proxy_acceptance.auth]\n'
  printf 'command = %s\n' "$(toml_quote "$auth_helper")"
  printf 'args = [%s]\n' "$(toml_quote "$token_file")"
  printf 'timeout_ms = 5000\nrefresh_interval_ms = 0\n'
} > "$profile"
chmod 600 "$profile" "$agent_file"

if [[ "$parallel" -eq 1 ]]; then
  expected_final='PARENT_RECEIVED:CHILD_SUM=46'
  prompt="Use exactly one $agent_name custom agent. The parent must not read alpha.txt or beta.txt. Tell the child to read both files with an actual tool, add the integer values, and return exactly CHILD_SUM=46. Wait for it. Reply exactly $expected_final only after the real child returns that value; otherwise reply TEST_FAILED. Do not access the network or credentials."
else
  expected_final='PARALLEL_CHILD_SUM=46'
  prompt="Spawn exactly two $agent_name custom agents in parallel. The parent must not read either fixture file. Tell one child to read alpha.txt with an actual tool and return exactly ALPHA_CHILD=17. Tell the other to read beta.txt with an actual tool and return exactly BETA_CHILD=29. Wait for both. Reply exactly $expected_final only after both real children return; otherwise reply TEST_FAILED. Do not access the network or credentials."
fi

unset CLI_PROXY_TOKEN || true
set +e
CODEX_HOME="$codex_home" "$codex_bin" --strict-config --profile acceptance \
  -a never -s read-only -C "$repo" --enable multi_agent \
  exec --json "$prompt" >"$events" 2>"$stderr_log"
codex_status=$?
set -e

emit_early_failure() {
  local reason=$1
  local stderr_tail
  stderr_tail=$(tail -n 20 "$stderr_log" 2>/dev/null | sed -E 's/(Bearer )[A-Za-z0-9._-]+/\1[REDACTED]/g')
  jq -n \
    --arg status failed \
    --arg reason "$reason" \
    --argjson codex_exit "$codex_status" \
    --arg stderr "$stderr_tail" \
    --arg artifacts "$([[ "$keep" -eq 1 ]] && printf '%s' "$tmp_root")" \
    '{status:$status,reason:$reason,codex_exit:$codex_exit,stderr:$stderr,artifacts:(if $artifacts=="" then null else $artifacts end)}'
  exit 1
}

[[ "$codex_status" -eq 0 ]] || emit_early_failure 'Codex command failed'
parent_id=$(jq -r 'select(.type=="thread.started") | .thread_id' "$events" | head -n 1)
[[ -n "$parent_id" && "$parent_id" != 'null' ]] || emit_early_failure 'No parent thread ID in JSON events'

state_db=$(find "$codex_home" -maxdepth 2 -type f -name 'state_*.sqlite' -print -quit)
[[ -n "$state_db" ]] || emit_early_failure 'No isolated Codex state database found'

parent_row=$(sqlite3 -separator $'\t' "$state_db" "SELECT model_provider,model,reasoning_effort,rollout_path FROM threads WHERE id='$parent_id';")
[[ -n "$parent_row" ]] || emit_early_failure 'Parent thread missing from state database'
IFS=$'\t' read -r parent_provider actual_parent_model actual_parent_effort parent_rollout <<< "$parent_row"

child_ids=()
while IFS= read -r child_id; do
  [[ -n "$child_id" ]] && child_ids+=("$child_id")
done < <(sqlite3 "$state_db" "SELECT child_thread_id FROM thread_spawn_edges WHERE parent_thread_id='$parent_id' ORDER BY child_thread_id;")

expected_children=$parallel
child_count_ok=false
[[ "${#child_ids[@]}" -eq "$expected_children" ]] && child_count_ok=true
parent_ok=false
[[ "$parent_provider" == 'cli_proxy_acceptance' && "$actual_parent_model" == "$parent_model" && "$actual_parent_effort" == "$parent_effort" ]] && parent_ok=true

spawn_mode='unknown'
if [[ -f "$parent_rollout" ]]; then
  spawn_mode=$(jq -r '
    select(.type=="response_item" and .payload.type=="function_call" and .payload.name=="spawn_agent")
    | .payload.arguments | fromjson
    | if has("agent_type") then "agent_type" elif has("task_name") then "task_name" else "unknown" end
  ' "$parent_rollout" | head -n 1)
  [[ -n "$spawn_mode" ]] || spawn_mode='unknown'
fi

children_ok=true
tools_ok=true
events_ok=true
combined_tool_output=''
combined_child_final=''
: > "$children_jsonl"

for child_id in "${child_ids[@]}"; do
  child_row=$(sqlite3 -separator $'\t' "$state_db" "SELECT model_provider,model,reasoning_effort,COALESCE(agent_role,'__NONE__'),rollout_path FROM threads WHERE id='$child_id';")
  if [[ -z "$child_row" ]]; then
    children_ok=false
    continue
  fi
  IFS=$'\t' read -r child_provider actual_child_model actual_child_effort child_role child_rollout <<< "$child_row"
  [[ "$child_role" == '__NONE__' ]] && child_role=''
  child_state_ok=false
  [[ "$child_provider" == 'cli_proxy_acceptance' && "$actual_child_model" == "$child_model" && "$actual_child_effort" == "$child_effort" && "$child_role" == "$agent_name" ]] && child_state_ok=true
  [[ "$child_state_ok" == true ]] || children_ok=false

  child_tool_ok=false
  if [[ -f "$child_rollout" ]]; then
    if jq -e 'select(.type=="response_item" and .payload.type=="function_call" and (.payload.name=="exec_command" or .payload.name=="shell"))' "$child_rollout" >/dev/null; then
      child_tool_ok=true
    fi
    tool_output=$(jq -r 'select(.type=="response_item" and .payload.type=="function_call_output") | .payload.output // empty' "$child_rollout")
    combined_tool_output+=$'\n'"$tool_output"
    child_final=$(jq -r 'select(.type=="response_item" and .payload.type=="message" and .payload.role=="assistant") | .payload.content[]? | select(.type=="output_text") | .text' "$child_rollout")
    combined_child_final+=$'\n'"$child_final"
  fi
  [[ "$child_tool_ok" == true ]] || tools_ok=false

  if ! jq -e --arg child "$child_id" '
    select(.type=="item.completed" and .item.type=="collab_tool_call" and .item.tool=="spawn_agent")
    | select((.item.receiver_thread_ids // []) | index($child))
  ' "$events" >/dev/null; then
    events_ok=false
  fi
  if ! jq -e --arg child "$child_id" '
    select(.type=="item.completed" and .item.type=="collab_tool_call" and .item.tool=="wait")
    | select((.item.receiver_thread_ids // []) | index($child))
  ' "$events" >/dev/null; then
    events_ok=false
  fi

  jq -n \
    --arg id "$child_id" \
    --arg provider "$child_provider" \
    --arg model "$actual_child_model" \
    --arg effort "$actual_child_effort" \
    --arg role "$child_role" \
    --argjson state_ok "$child_state_ok" \
    --argjson tool_ok "$child_tool_ok" \
    '{id:$id,provider:$provider,model:$model,effort:$effort,role:$role,state_ok:$state_ok,tool_ok:$tool_ok}' >> "$children_jsonl"
done

fixture_ok=false
if [[ "$parallel" -eq 1 ]]; then
  [[ "$combined_tool_output" == *'ALPHA_TOKEN=17'* && "$combined_tool_output" == *'BETA_TOKEN=29'* && "$combined_child_final" == *'CHILD_SUM=46'* ]] && fixture_ok=true
else
  [[ "$combined_tool_output" == *'ALPHA_TOKEN=17'* && "$combined_tool_output" == *'BETA_TOKEN=29'* && "$combined_child_final" == *'ALPHA_CHILD=17'* && "$combined_child_final" == *'BETA_CHILD=29'* ]] && fixture_ok=true
fi

final_ok=false
jq -e --arg expected "$expected_final" 'select(.type=="item.completed" and .item.type=="agent_message" and .item.text==$expected)' "$events" >/dev/null && final_ok=true

children_json=$(jq -s '.' "$children_jsonl")
status='failed'
reason='One or more transcript/state assertions failed'
exit_status=1

if [[ "$parent_ok" == true && "$child_count_ok" == true && "$children_ok" == true && "$tools_ok" == true && "$events_ok" == true && "$fixture_ok" == true && "$final_ok" == true ]]; then
  status='verified'
  reason='Parent, child state, tool transcript, wait path, and final assertion all matched'
  exit_status=0
elif [[ "$spawn_mode" == 'task_name' || ("${#child_ids[@]}" -gt 0 && "$children_ok" == false) ]]; then
  status='unsupported'
  reason='A child was created but the requested custom-agent model/role configuration was not applied'
  exit_status=2
fi

jq -n \
  --arg status "$status" \
  --arg reason "$reason" \
  --arg spawn_mode "$spawn_mode" \
  --arg parent_id "$parent_id" \
  --arg parent_provider "$parent_provider" \
  --arg parent_model "$actual_parent_model" \
  --arg parent_effort "$actual_parent_effort" \
  --arg expected_parent_model "$parent_model" \
  --arg expected_child_model "$child_model" \
  --arg expected_child_effort "$child_effort" \
  --argjson expected_children "$expected_children" \
  --argjson children "$children_json" \
  --argjson parent_ok "$parent_ok" \
  --argjson child_count_ok "$child_count_ok" \
  --argjson children_ok "$children_ok" \
  --argjson tools_ok "$tools_ok" \
  --argjson events_ok "$events_ok" \
  --argjson fixture_ok "$fixture_ok" \
  --argjson final_ok "$final_ok" \
  --arg command_auth verified \
  --arg artifacts "$([[ "$keep" -eq 1 ]] && printf '%s' "$tmp_root")" \
  '{
    status:$status,
    reason:$reason,
    spawn_mode:$spawn_mode,
    command_auth:$command_auth,
    parent:{id:$parent_id,provider:$parent_provider,model:$parent_model,effort:$parent_effort},
    expected:{parent_model:$expected_parent_model,child_model:$expected_child_model,child_effort:$expected_child_effort,children:$expected_children},
    children:$children,
    checks:{parent:$parent_ok,child_count:$child_count_ok,children:$children_ok,tools:$tools_ok,events:$events_ok,fixture:$fixture_ok,final:$final_ok},
    artifacts:(if $artifacts=="" then null else $artifacts end)
  }'

exit "$exit_status"

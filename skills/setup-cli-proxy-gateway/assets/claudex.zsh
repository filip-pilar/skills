#!/bin/zsh
set -euo pipefail

proxy_url="${CLAUDEX_PROXY_URL:-http://127.0.0.1:8317}"
proxy_token="${CLAUDEX_PROXY_TOKEN:-${CLI_PROXY_TOKEN:-}}"
token_file="${CLI_PROXY_TOKEN_FILE:-$HOME/.cli-proxy-api/client-token}"
token_helper="${CLI_PROXY_TOKEN_HELPER:-${0:A:h}/read-cli-proxy-token}"
if [[ -z "${CLI_PROXY_TOKEN_HELPER:-}" && ! -x "$token_helper" && -x "${0:A:h}/read-cli-proxy-token.sh" ]]; then
  token_helper="${0:A:h}/read-cli-proxy-token.sh"
fi
default_model="${CLAUDEX_MODEL:-}"

if [[ -z "$proxy_token" ]]; then
  [[ -x "$token_helper" ]] || {
    print -u2 "claudex: set CLAUDEX_PROXY_TOKEN/CLI_PROXY_TOKEN or install read-cli-proxy-token beside this launcher"
    exit 1
  }
  proxy_token="$("$token_helper" "$token_file")"
fi

proxy_is_ready() {
  [[ "$(curl -sS -o /dev/null -w '%{http_code}' --max-time 1 \
    -H "Authorization: Bearer $proxy_token" "$proxy_url/v1/models" 2>/dev/null)" == "200" ]]
}

if ! proxy_is_ready; then
  print -u2 "claudex: CLIProxyAPI is not ready at $proxy_url; start the verified gateway separately"
  exit 1
fi

export ANTHROPIC_BASE_URL="$proxy_url"
export ANTHROPIC_AUTH_TOKEN="$proxy_token"

# Claude Code exposes effort levels as a session flag. Tested CLIProxyAPI builds
# also apply effort from a model suffix, so translate the flag into that form.
requested_effort="${CLAUDEX_EFFORT:-}"
selected_model=""
typeset -i ultracode_requested=0
[[ "${CLAUDEX_ULTRACODE:-0}" == "1" ]] && ultracode_requested=1
typeset -a passthrough
typeset -a user_settings

while (( $# > 0 )); do
  case "$1" in
    --model)
      (( $# >= 2 )) || { print -u2 "claudex: --model requires a value"; exit 2; }
      selected_model="$2"
      shift 2
      ;;
    --model=*)
      selected_model="${1#--model=}"
      shift
      ;;
    --effort)
      (( $# >= 2 )) || { print -u2 "claudex: --effort requires a value"; exit 2; }
      requested_effort="$2"
      shift 2
      ;;
    --effort=*)
      requested_effort="${1#--effort=}"
      shift
      ;;
    --ultracode)
      ultracode_requested=1
      shift
      ;;
    --settings)
      (( $# >= 2 )) || { print -u2 "claudex: --settings requires a value"; exit 2; }
      user_settings+=("$2")
      shift 2
      ;;
    --settings=*)
      user_settings+=("${1#--settings=}")
      shift
      ;;
    *)
      passthrough+=("$1")
      shift
      ;;
  esac
done

if [[ "$requested_effort" == "ultracode" ]]; then
  ultracode_requested=1
  requested_effort=""
fi

if (( ultracode_requested )) && [[ -n "$requested_effort" ]]; then
  print -u2 "claudex: --ultracode cannot be combined with another effort level"
  exit 2
fi

proxy_effort="$requested_effort"
claude_effort="$requested_effort"
if (( ultracode_requested )); then
  # Claude Code treats ultracode as a session mode, not a CLI effort value.
  # Route the model at xhigh without passing an xhigh launch pin, which would
  # prevent dynamic-workflow orchestration from activating.
  proxy_effort="xhigh"
  claude_effort=""
elif [[ "$requested_effort" == "none" ]]; then
  # Some OpenAI models offer an explicit no-reasoning tier. Encode it in the
  # proxy model name without assuming Claude Code accepts "none" natively.
  claude_effort=""
fi

case "$requested_effort" in
  ""|none|low|medium|high|xhigh|max)
    ;;
  *)
    print -u2 "claudex: effort must be none, low, medium, high, xhigh, or max"
    exit 2
    ;;
esac

model_with_effort() {
  local name="$1"
  if [[ -n "$proxy_effort" && "$name" != *"("* ]]; then
    print -r -- "$name($proxy_effort)"
  else
    print -r -- "$name"
  fi
}

selected_model="${selected_model:-$default_model}"
[[ -n "$selected_model" ]] || {
  print -u2 "claudex: set CLAUDEX_MODEL or pass --model"
  exit 1
}
selected_model="$(model_with_effort "$selected_model")"
sonnet_model="$(model_with_effort "${CLAUDEX_SONNET_MODEL:-$selected_model}")"
haiku_model="$(model_with_effort "${CLAUDEX_HAIKU_MODEL:-$selected_model}")"
subagent_model="$(model_with_effort "${CLAUDEX_SUBAGENT_MODEL:-$selected_model}")"

export ANTHROPIC_DEFAULT_OPUS_MODEL="$selected_model"
export ANTHROPIC_DEFAULT_SONNET_MODEL="$sonnet_model"
export ANTHROPIC_DEFAULT_HAIKU_MODEL="$haiku_model"
export CLAUDE_CODE_SUBAGENT_MODEL="$subagent_model"

workflow_size="${CLAUDEX_WORKFLOW_SIZE:-}"
case "$workflow_size" in
  ""|small|medium|large)
    ;;
  *)
    print -u2 "claudex: CLAUDEX_WORKFLOW_SIZE must be small, medium, or large"
    exit 2
    ;;
esac

effort_level_override=""
if (( ultracode_requested )); then
  effort_level_override="ultracode"
  export CLAUDE_CODE_EFFORT_LEVEL="ultracode"
fi

# Claude settings.json can override process environment variables. Supply a
# command-line settings overlay so native-Claude user defaults do not redirect
# claudex subagents back to a Claude model that the proxy cannot route.
command -v jq >/dev/null || { print -u2 "claudex: jq is required"; exit 1; }
merged_user_settings='{}'
for setting in "${user_settings[@]}"; do
  if [[ -f "$setting" ]]; then
    next_settings="$(jq -ce . "$setting")" || { print -u2 "claudex: invalid settings file: $setting"; exit 2; }
  else
    next_settings="$(jq -ce . <<<"$setting")" || { print -u2 "claudex: --settings must be valid JSON or a JSON file"; exit 2; }
  fi
  merged_user_settings="$(jq -cn --argjson left "$merged_user_settings" --argjson right "$next_settings" '$left * $right')"
done

# Merge user settings first, then enforce route-critical values.
settings_overlay="$(jq -cn \
  --argjson user "$merged_user_settings" \
  --arg model "$subagent_model" \
  --arg workflow_size "$workflow_size" \
  --arg effort_level "$effort_level_override" \
  '$user * {env:{CLAUDE_CODE_SUBAGENT_MODEL:$model}}
   | if $workflow_size != "" then .workflowSizeGuideline=$workflow_size else . end
   | if $effort_level != "" then .env.CLAUDE_CODE_EFFORT_LEVEL=$effort_level else . end')"

typeset -a final_args
final_args=(--settings "$settings_overlay" --model "$selected_model")
if [[ -n "$claude_effort" ]]; then
  final_args+=(--effort "$claude_effort")
fi
final_args+=("${passthrough[@]}")
exec claude "${final_args[@]}"

#!/bin/zsh
set -euo pipefail

proxy_url="${CLAUDE_PROXY_URL:-http://127.0.0.1:8317}"
proxy_token="${CLAUDE_PROXY_TOKEN:-${CLI_PROXY_TOKEN:-}}"
token_file="${CLI_PROXY_TOKEN_FILE:-$HOME/.cli-proxy-api/client-token}"
token_helper="${CLI_PROXY_TOKEN_HELPER:-${0:A:h}/read-cli-proxy-token}"
if [[ -z "${CLI_PROXY_TOKEN_HELPER:-}" && ! -x "$token_helper" && -x "${0:A:h}/read-cli-proxy-token.sh" ]]; then
  token_helper="${0:A:h}/read-cli-proxy-token.sh"
fi
selected_model="${CLAUDE_PROXY_MODEL:-}"
typeset -a passthrough
typeset -a user_settings

while (( $# > 0 )); do
  case "$1" in
    --model)
      (( $# >= 2 )) || { print -u2 'claude-proxy: --model requires a value'; exit 2; }
      selected_model="$2"
      shift 2
      ;;
    --model=*) selected_model="${1#--model=}"; shift ;;
    --settings)
      (( $# >= 2 )) || { print -u2 'claude-proxy: --settings requires a value'; exit 2; }
      user_settings+=("$2")
      shift 2
      ;;
    --settings=*) user_settings+=("${1#--settings=}"); shift ;;
    *) passthrough+=("$1"); shift ;;
  esac
done

if [[ -z "$proxy_token" ]]; then
  [[ -x "$token_helper" ]] || {
    print -u2 'claude-proxy: set CLAUDE_PROXY_TOKEN/CLI_PROXY_TOKEN or install read-cli-proxy-token beside this launcher'
    exit 1
  }
  proxy_token="$("$token_helper" "$token_file")"
fi
[[ -n "$selected_model" ]] || { print -u2 'claude-proxy: set CLAUDE_PROXY_MODEL or pass --model'; exit 1; }
command -v claude >/dev/null || { print -u2 'claude-proxy: Claude Code is not on PATH'; exit 1; }
command -v jq >/dev/null || { print -u2 'claude-proxy: jq is required'; exit 1; }

sonnet_model="${CLAUDE_PROXY_SONNET_MODEL:-$selected_model}"
haiku_model="${CLAUDE_PROXY_HAIKU_MODEL:-$selected_model}"
subagent_model="${CLAUDE_PROXY_SUBAGENT_MODEL:-$selected_model}"

export ANTHROPIC_BASE_URL="$proxy_url"
export ANTHROPIC_AUTH_TOKEN="$proxy_token"
export ANTHROPIC_DEFAULT_OPUS_MODEL="$selected_model"
export ANTHROPIC_DEFAULT_SONNET_MODEL="$sonnet_model"
export ANTHROPIC_DEFAULT_HAIKU_MODEL="$haiku_model"
export CLAUDE_CODE_SUBAGENT_MODEL="$subagent_model"

merged_user_settings='{}'
for setting in "${user_settings[@]}"; do
  if [[ -f "$setting" ]]; then
    next_settings="$(jq -ce . "$setting")" || { print -u2 "claude-proxy: invalid settings file: $setting"; exit 2; }
  else
    next_settings="$(jq -ce . <<<"$setting")" || { print -u2 'claude-proxy: --settings must be valid JSON or a JSON file'; exit 2; }
  fi
  merged_user_settings="$(jq -cn --argjson left "$merged_user_settings" --argjson right "$next_settings" '$left * $right')"
done

# Merge user settings first, then enforce route-critical subagent selection.
settings_overlay="$(jq -cn \
  --argjson user "$merged_user_settings" \
  --arg model "$subagent_model" \
  '$user * {env:{CLAUDE_CODE_SUBAGENT_MODEL:$model}}')"
exec claude --settings "$settings_overlay" --model "$selected_model" "${passthrough[@]}"

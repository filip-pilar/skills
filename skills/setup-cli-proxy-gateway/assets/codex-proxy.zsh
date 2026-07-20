#!/bin/zsh
set -euo pipefail

profile="${CODEX_PROXY_PROFILE:-cli-proxy}"
token_file="${CLI_PROXY_TOKEN_FILE:-$HOME/.cli-proxy-api/client-token}"
token_helper="${CLI_PROXY_TOKEN_HELPER:-${0:A:h}/read-cli-proxy-token}"
if [[ -z "${CLI_PROXY_TOKEN_HELPER:-}" && ! -x "$token_helper" && -x "${0:A:h}/read-cli-proxy-token.sh" ]]; then
  token_helper="${0:A:h}/read-cli-proxy-token.sh"
fi
token="${CLI_PROXY_TOKEN:-}"

if [[ -z "$token" ]]; then
  [[ -x "$token_helper" ]] || {
    print -u2 "codex-proxy: set CLI_PROXY_TOKEN or install read-cli-proxy-token beside this launcher"
    exit 1
  }
  token="$("$token_helper" "$token_file")"
fi

[[ -n "$token" ]] || { print -u2 'codex-proxy: local gateway token is empty'; exit 1; }
command -v codex >/dev/null || { print -u2 'codex-proxy: codex is not on PATH'; exit 1; }

export CLI_PROXY_TOKEN="$token"
exec codex --profile "$profile" "$@"

#!/bin/sh
set -u

proxy_url="${CLI_PROXY_URL:-http://127.0.0.1:8317}"
proxy_token="${CLI_PROXY_TOKEN:-${CLAUDEX_PROXY_TOKEN:-}}"
token_file="${CLI_PROXY_TOKEN_FILE:-$HOME/.cli-proxy-api/client-token}"
script_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
bundled_helper="$script_dir/../assets/read-cli-proxy-token.sh"

if [ -z "$proxy_token" ] && [ -x "$bundled_helper" ] && [ -f "$token_file" ]; then
  proxy_token=$($bundled_helper "$token_file" 2>/dev/null || true)
fi

section() { printf '\n[%s]\n' "$1"; }

mode_of() {
  [ -e "$1" ] || return 0
  if stat -f '%Sp %N' "$1" >/dev/null 2>&1; then
    stat -f '%Sp %N' "$1"
  else
    stat -c '%A %n' "$1" 2>/dev/null || true
  fi
}

command_info() {
  label="$1"
  name="$2"
  if command -v "$name" >/dev/null 2>&1; then
    resolved="$(command -v "$name")"
    printf '%s path: %s\n' "$label" "$resolved"
    case "$name" in
      claude|codex) "$resolved" --version 2>/dev/null | sed -n '1p' || true ;;
      cli-proxy-api|cliproxyapi) "$resolved" --version 2>&1 | sed -n '1p' || true ;;
    esac
  else
    printf '%s: not found on PATH\n' "$label"
  fi
}

section "platform"
printf 'os: %s\narchitecture: %s\nshell: %s\n' "$(uname -s)" "$(uname -m)" "${SHELL:-unknown}"

section "commands"
command_info "Codex" codex
command_info "Claude Code" claude
if command -v cli-proxy-api >/dev/null 2>&1; then
  command_info "CLIProxyAPI" cli-proxy-api
  proxy_bin="$(command -v cli-proxy-api)"
elif command -v cliproxyapi >/dev/null 2>&1; then
  command_info "CLIProxyAPI" cliproxyapi
  proxy_bin="$(command -v cliproxyapi)"
else
  proxy_bin=""
  printf 'CLIProxyAPI: not found on PATH\n'
fi

if [ -n "$proxy_bin" ]; then
  printf 'authentication flags:\n'
  "$proxy_bin" --help 2>&1 | sed -nE '/-(claude|codex|xai)[a-z-]*login/{s/^[[:space:]]*/  /;p;}'
fi

section "wrappers and profiles"
for name in claudex claude-grok claude-proxy codex-claude codex-grok; do
  if command -v "$name" >/dev/null 2>&1; then
    path="$(command -v "$name")"
    printf '%s: %s\n' "$name" "$path"
    mode_of "$path"
  fi
done
codex_home="${CODEX_HOME:-$HOME/.codex}"
profile_count="$(find "$codex_home" -maxdepth 1 -type f -name '*.config.toml' 2>/dev/null | wc -l | tr -d ' ')"
printf 'Codex profile files: %s\n' "$profile_count"

section "configuration modes"
for target in "$HOME/.cli-proxy-api/config.yaml" "$HOME/.claude/settings.json" "$codex_home/config.toml"; do
  mode_of "$target"
done

if command -v jq >/dev/null 2>&1 && [ -f "$HOME/.claude/settings.json" ]; then
  jq '{model,subagent_model:(.env.CLAUDE_CODE_SUBAGENT_MODEL // null),workflows:(.enableWorkflows // null)}' \
    "$HOME/.claude/settings.json" 2>/dev/null || true
fi

section "credential inventory"
auth_dir="$HOME/.cli-proxy-api"
if [ -d "$auth_dir" ]; then
  total=0
  private=0
  unsafe=0
  for target in "$auth_dir"/*.json "$auth_dir"/*.yaml "$auth_dir"/client-token; do
    [ -f "$target" ] || continue
    total=$((total + 1))
    if mode="$(stat -f '%Lp' "$target" 2>/dev/null)"; then :; else
      mode="$(stat -c '%a' "$target" 2>/dev/null || printf unknown)"
    fi
    case "$mode" in 400|600) private=$((private + 1)) ;; *) unsafe=$((unsafe + 1)) ;; esac
  done
  printf 'credential/config files: %s\nprivate files: %s\nfiles needing permission review: %s\n' "$total" "$private" "$unsafe"
else
  printf '%s: absent\n' "$auth_dir"
fi

section "route hygiene"
if [ -f "$token_file" ]; then
  printf 'local client token file: %s\n' "$token_file"
  mode_of "$token_file"
else
  printf 'local client token file: absent (%s)\n' "$token_file"
fi

embedded=0
for name in claudex claude-grok claude-proxy codex-claude codex-grok; do
  if command -v "$name" >/dev/null 2>&1; then
    path="$(command -v "$name")"
    if grep -E '^export (CLI_PROXY_TOKEN|CLAUDEX_PROXY_TOKEN|CLAUDE_PROXY_TOKEN)=' "$path" 2>/dev/null \
      | grep -Ev '\$\(|\$\{|\$[A-Za-z_]' >/dev/null; then
      printf '%s embeds a literal local gateway key: %s\n' "$name" "$path"
      embedded=$((embedded + 1))
    fi
  fi
done
printf 'launchers with embedded local keys: %s\n' "$embedded"

if command -v read-cli-proxy-token >/dev/null 2>&1; then
  helper="$(command -v read-cli-proxy-token)"
  printf 'command-auth helper: %s\n' "$helper"
  mode_of "$helper"
fi

if command -v lsof >/dev/null 2>&1; then
  listener="$(lsof -nP -iTCP:8317 -sTCP:LISTEN 2>/dev/null | sed -n '2p' || true)"
  if [ -n "$listener" ]; then
    printf 'port 8317 listener: %s\n' "$(printf '%s\n' "$listener" | awk '{print $1 " pid=" $2 " " $9}')"
  else
    printf 'port 8317 listener: none\n'
  fi
fi

section "proxy health"
if [ -z "$proxy_token" ]; then
  printf 'skipped authenticated model query; set CLI_PROXY_TOKEN\n'
elif command -v curl >/dev/null 2>&1; then
  response="$(curl -sS --max-time 3 -H "Authorization: Bearer $proxy_token" "$proxy_url/v1/models" 2>/dev/null || true)"
  if [ -n "$response" ] && command -v jq >/dev/null 2>&1; then
    printf '%s' "$response" | jq -r '.data[]? | [.id, (.owned_by // "unknown")] | @tsv' 2>/dev/null | sort
  elif [ -n "$response" ]; then
    printf 'proxy responded; install jq to print model metadata safely\n'
  else
    printf 'no authenticated response from %s\n' "$proxy_url"
  fi
fi

section "service hints"
if [ "$(uname -s)" = Darwin ]; then
  if [ -d /Applications/VibeProxy.app ]; then printf 'VibeProxy: /Applications/VibeProxy.app\n'; fi
  find "$HOME/Library/LaunchAgents" -maxdepth 1 -type f 2>/dev/null | sed -nE '/(cli.?proxy|vibe.?proxy)/Ip'
else
  systemctl --user list-unit-files 2>/dev/null | sed -nE '/(cli.?proxy|vibe.?proxy)/Ip' || true
fi

#!/usr/bin/env bash
set -euo pipefail

script_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
transaction="$script_dir/route_transaction.sh"
[[ -x "$transaction" ]] || { printf 'missing executable transaction helper: %s\n' "$transaction" >&2; exit 1; }

tmp_root=$(mktemp -d "${TMPDIR:-/tmp}/cli-proxy-transaction-test.XXXXXX")
cleanup() {
  /bin/rm -rf -- "$tmp_root"
}
trap cleanup EXIT HUP INT TERM

target_root="$tmp_root/targets"
bundle="$tmp_root/snapshot"
mkdir -p "$target_root/existing-dir"
printf '%s\n' 'before-file' > "$target_root/existing-file"
printf '%s\n' 'before-nested' > "$target_root/existing-dir/nested"
ln -s existing-file "$target_root/existing-link"
chmod 640 "$target_root/existing-file"

"$transaction" snapshot --dir "$bundle" -- \
  "$target_root/existing-file" \
  "$target_root/existing-dir" \
  "$target_root/existing-link" \
  "$target_root/initially-absent" >/dev/null
"$transaction" verify --dir "$bundle" >/dev/null

printf '%s\n' 'after-file' > "$target_root/existing-file"
/bin/rm -rf -- "$target_root/existing-dir" "$target_root/existing-link"
printf '%s\n' 'must-be-removed' > "$target_root/initially-absent"

"$bundle/rollback.sh" >/dev/null

[[ $(sed -n '1p' "$target_root/existing-file") == 'before-file' ]]
[[ $(sed -n '1p' "$target_root/existing-dir/nested") == 'before-nested' ]]
[[ -L "$target_root/existing-link" ]]
[[ ! -e "$target_root/initially-absent" ]]

if mode=$(stat -c '%a' "$target_root/existing-file" 2>/dev/null); then :; else
  mode=$(stat -f '%Lp' "$target_root/existing-file")
fi
[[ "$mode" == '640' ]] || {
  printf 'restored file mode mismatch: expected 640, got %s\n' "$mode" >&2
  exit 1
}

vibe_root="$tmp_root/vibe-migration"
mkdir -p "$vibe_root/VibeProxy.app/Contents" "$vibe_root/home/.cli-proxy-api"
printf '%s\n' 'vibe-app-before' > "$vibe_root/VibeProxy.app/Contents/version"
printf '%s\n' 'oauth-state-before' > "$vibe_root/home/.cli-proxy-api/provider.json"
vibe_bundle="$tmp_root/vibe-snapshot"
"$transaction" snapshot --dir "$vibe_bundle" -- \
  "$vibe_root/VibeProxy.app" \
  "$vibe_root/home/.cli-proxy-api" \
  "$vibe_root/home/.local/bin/cli-proxy-api" >/dev/null
/bin/rm -rf -- "$vibe_root/VibeProxy.app"
printf '%s\n' 'mutated-oauth-state' > "$vibe_root/home/.cli-proxy-api/provider.json"
mkdir -p "$vibe_root/home/.local/bin"
printf '%s\n' 'standalone-proxy' > "$vibe_root/home/.local/bin/cli-proxy-api"
"$vibe_bundle/rollback.sh" >/dev/null
[[ $(sed -n '1p' "$vibe_root/VibeProxy.app/Contents/version") == 'vibe-app-before' ]]
[[ $(sed -n '1p' "$vibe_root/home/.cli-proxy-api/provider.json") == 'oauth-state-before' ]]
[[ ! -e "$vibe_root/home/.local/bin/cli-proxy-api" ]]

if "$transaction" snapshot --dir "$tmp_root/nested-bundle" -- "$tmp_root" >/dev/null 2>&1; then
  printf '%s\n' 'nested backup safety check unexpectedly succeeded' >&2
  exit 1
fi

fake_bin="$tmp_root/fake-bin"
mkdir -p "$fake_bin"
{
  printf '%s\n' '#!/bin/sh'
  printf '%s\n' 'case "$1" in'
  printf '%s\n' "  -c) printf '%s\\n' 'partial unsupported stat output'; exit 1 ;;"
  printf '%s\n' "  -f) printf '%s\\n' '640' ;;"
  printf '%s\n' '  *) exit 2 ;;'
  printf '%s\n' 'esac'
} > "$fake_bin/stat"
chmod 700 "$fake_bin/stat"
portable_target="$tmp_root/portable-stat-target"
portable_bundle="$tmp_root/portable-stat-snapshot"
printf '%s\n' 'portable-stat-content' > "$portable_target"
PATH="$fake_bin:$PATH" "$transaction" snapshot --dir "$portable_bundle" -- \
  "$portable_target" >/dev/null
PATH="$fake_bin:$PATH" "$transaction" verify --dir "$portable_bundle" >/dev/null

printf '%s\n' 'route_transaction_tests=verified' 'vibe_migration_rollback_simulation=verified'

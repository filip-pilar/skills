#!/usr/bin/env bash
# detect-package-managers.sh — figure out which package managers the user actually uses.
#
# Usage:
#   detect-package-managers.sh [OUT_JSON] [REPOS_FILE]
#
#   OUT_JSON    Where to write the detection report (default: /tmp/socket-audit/pm-detection.json)
#   REPOS_FILE  List of repo paths to survey for lockfile presence
#               (default: /tmp/socket-audit/repos.txt; auto-surveys $HOME if missing)
#
# Output: JSON written to OUT_JSON, plus a human-readable summary table to stderr.
#
# Compatible with bash 3.2 (macOS default) — no associative arrays.

set -uo pipefail

OUT="${1:-/tmp/socket-audit/pm-detection.json}"
REPOS="${2:-/tmp/socket-audit/repos.txt}"
mkdir -p "$(dirname "$OUT")"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Auto-survey if no repo list exists
if [ ! -f "$REPOS" ]; then
  echo "No repo list at $REPOS — auto-surveying \$HOME first..." >&2
  if [ -x "$SCRIPT_DIR/survey-repos.sh" ]; then
    bash "$SCRIPT_DIR/survey-repos.sh" "$REPOS" "$HOME" >&2
  else
    echo "ERROR: survey-repos.sh not found at $SCRIPT_DIR/survey-repos.sh" >&2
    exit 2
  fi
fi

# Manager definitions: name|wrapper_supported_by_this_skill|bun_scanner_applies|comma-separated-patterns
# (one per line; no associative arrays so this is portable to bash 3.2)
MANAGERS="npm|true|false|package-lock.json
yarn|false|false|yarn.lock
pnpm|true|false|pnpm-lock.yaml
bun|false|true|bun.lock,bun.lockb
pip|false|false|requirements.txt,Pipfile.lock,poetry.lock,pyproject.toml
uv|false|false|uv.lock
cargo|false|false|Cargo.lock
gem|false|false|Gemfile.lock"

# Check if any of comma-separated filenames exists in repo (depth-limited, prunes caches)
has_any_file() {
  local repo="$1"
  local patterns="$2"
  local IFS=','
  for pat in $patterns; do
    if [ -n "$(find "$repo" -maxdepth 4 \
         \( -path "*/node_modules" -o -path "*/.git" -o -path "*/vendor" -o -path "*/.venv" \) -prune \
         -o -name "$pat" -print -quit 2>/dev/null)" ]; then
      return 0
    fi
  done
  return 1
}

# Count repos using a given comma-separated pattern list
count_for_manager() {
  local patterns="$1"
  local n=0
  while IFS= read -r repo; do
    [ -z "$repo" ] && continue
    [ ! -d "$repo" ] && continue
    if has_any_file "$repo" "$patterns"; then
      n=$((n+1))
    fi
  done < "$REPOS"
  echo "$n"
}

# Total repos and binary-bun-lockfile count
TOTAL=$(grep -c . "$REPOS" 2>/dev/null || echo 0)
BUN_LOCKB=0
while IFS= read -r repo; do
  [ -z "$repo" ] && continue
  [ ! -d "$repo" ] && continue
  if [ -n "$(find "$repo" -maxdepth 4 \
       \( -path "*/node_modules" -o -path "*/.git" -o -path "*/vendor" \) -prune \
       -o -name "bun.lockb" -print -quit 2>/dev/null)" ]; then
    BUN_LOCKB=$((BUN_LOCKB+1))
  fi
done < "$REPOS"

# Build JSON + summary in a single pass through MANAGERS
SUMMARY_TMP="$(mktemp -t socket-audit-summary)"
JSON_TMP="${OUT}.tmp"

{
  echo "{"
  echo "  \"timestamp\": \"$(date -u +%Y-%m-%dT%H:%M:%SZ)\","
  echo "  \"total_repos_surveyed\": $TOTAL,"
  echo "  \"bun_binary_lockfiles\": $BUN_LOCKB,"
  echo "  \"managers\": {"

  first=1
  while IFS= read -r row; do
    [ -z "$row" ] && continue
    IFS='|' read -r name wrapper bunscan patterns <<< "$row"

    on_path="false"
    if command -v "$name" >/dev/null 2>&1; then
      on_path="true"
    fi

    count=$(count_for_manager "$patterns")

    if [ "$first" = "1" ]; then first=0; else echo ","; fi
    printf '    "%s": {"on_path": %s, "repo_count": %d, "wrapper_supported": %s, "bun_scanner": %s}' \
      "$name" "$on_path" "$count" "$wrapper" "$bunscan"

    # Stash a human-readable row only if relevant
    if [ "$on_path" = "true" ] || [ "$count" -gt 0 ]; then
      marker="✗"; [ "$on_path" = "true" ] && marker="✓"
      if [ "$bunscan" = "true" ]; then
        tool="@socketsecurity/bun-security-scanner"
      elif [ "$wrapper" = "true" ]; then
        tool="sfw wrapper"
      else
        tool="(audit-only in this skill)"
      fi
      printf "  %-8s %-9s %-12s %s\n" "$name" "$marker" "$count" "$tool" >> "$SUMMARY_TMP"
    fi
  done <<< "$MANAGERS"

  echo
  echo "  }"
  echo "}"
} > "$JSON_TMP"

mv "$JSON_TMP" "$OUT"

# Validate JSON if jq is available
if command -v jq >/dev/null 2>&1; then
  if ! jq -e . "$OUT" >/dev/null 2>&1; then
    echo "WARNING: generated JSON at $OUT did not validate." >&2
  fi
fi

# Human summary to stderr
{
  echo
  echo "Package manager detection"
  echo "  Repos surveyed: $TOTAL"
  echo "  Output JSON:    $OUT"
  if [ "$BUN_LOCKB" -gt 0 ]; then
    echo "  ⚠ $BUN_LOCKB repos use bun.lockb (binary, unsupported by Socket scan)."
    echo "    Regenerate as text bun.lock: cd <repo> && bun install --save-text-lockfile"
  fi
  echo
  printf "  %-8s %-9s %-12s %s\n" "Manager" "on PATH" "in N repos" "Protection tool"
  printf "  %-8s %-9s %-12s %s\n" "-------" "-------" "----------" "---------------"
  if [ -s "$SUMMARY_TMP" ]; then
    cat "$SUMMARY_TMP"
  else
    echo "  (no package managers detected on PATH or in repos)"
  fi
  /bin/rm -f "$SUMMARY_TMP"
} >&2

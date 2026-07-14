#!/usr/bin/env bash

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
TMP_BASE="${TMPDIR:-/tmp}"
TMP_BASE="${TMP_BASE%/}"
TMP="$(mktemp -d "$TMP_BASE/improve-validate.XXXXXX")"
trap '/bin/rm -rf -- "$TMP"' EXIT

fail() {
  printf 'validate: %s\n' "$*" >&2
  exit 1
}

for script in "$ROOT"/scripts/*.sh "$ROOT"/tests/*.sh; do
  bash -n "$script"
done

"$ROOT/scripts/switch-host.sh" --check-canonical >/dev/null || \
  fail "root must be the canonical Codex representation"

"$ROOT/scripts/switch-host.sh" codex --output "$TMP/codex" >/dev/null
"$ROOT/scripts/switch-host.sh" claude-code --output "$TMP/claude" >/dev/null

cmp -s "$ROOT/SKILL.md" "$TMP/codex/SKILL.md" || fail "root SKILL.md is stale"
cmp -s "$ROOT/agents/openai.yaml" "$TMP/codex/agents/openai.yaml" || fail "root Codex metadata is stale"
[ ! -e "$TMP/claude/agents/openai.yaml" ] || fail "Claude output contains Codex metadata"

grep -q '<!-- improve-generated: codex;' "$TMP/codex/SKILL.md" || fail "Codex marker missing"
grep -q '<!-- improve-generated: claude-code;' "$TMP/claude/SKILL.md" || fail "Claude marker missing"
! grep -q '{{IMPROVE_SHARED_CORE}}' "$TMP/codex/SKILL.md" "$TMP/claude/SKILL.md" || fail "unexpanded template marker"

extract_core() {
  awk '
    /<!-- BEGIN IMPROVE SHARED CORE -->/ { active=1; next }
    /<!-- END IMPROVE SHARED CORE -->/ { active=0 }
    active { print }
  ' "$1"
}
extract_core "$TMP/codex/SKILL.md" > "$TMP/codex-core.md"
extract_core "$TMP/claude/SKILL.md" > "$TMP/claude-core.md"
cmp -s "$ROOT/core.md" "$TMP/codex-core.md" || fail "Codex output does not embed the exact shared core"
cmp -s "$ROOT/core.md" "$TMP/claude-core.md" || fail "Claude output does not embed the exact shared core"

if grep -Eq 'Codex|Claude|AGENTS\.md|CLAUDE\.md|Explore|SendMessage|EnterWorktree|codex exec' "$ROOT/core.md"; then
  fail "host-specific language leaked into core.md"
fi

for token in '`branch`' '`next`' '`plan <description>`' '`review-plan <file>`' '`execute <plan> [model]`' '`reconcile`' '`--issues`'; do
  grep -Fq "$token" "$ROOT/core.md" || fail "missing invocation contract: $token"
done

validate_links() {
  local package="$1"
  local skill="$package/SKILL.md"
  local raw target
  while IFS= read -r raw; do
    target="${raw#](}"
    target="${target%)}"
    case "$target" in
      http://*|https://*|mailto:*|'#'*) continue ;;
    esac
    target="${target%%#*}"
    [ -e "$package/$target" ] || fail "broken SKILL.md link in $package: $target"
  done < <(grep -oE '\]\([^)]*\)' "$skill" || true)
}
validate_links "$TMP/codex"
validate_links "$TMP/claude"

CORE_WORDS="$(wc -w < "$ROOT/core.md" | tr -d ' ')"
CODEX_WORDS="$(wc -w < "$TMP/codex/SKILL.md" | tr -d ' ')"
CLAUDE_WORDS="$(wc -w < "$TMP/claude/SKILL.md" | tr -d ' ')"
[ "$CORE_WORDS" -le 1500 ] || fail "shared core exceeds 1500 words ($CORE_WORDS)"
[ "$CODEX_WORDS" -le 1900 ] || fail "Codex SKILL.md exceeds 1900 words ($CODEX_WORDS)"
[ "$CLAUDE_WORDS" -le 1900 ] || fail "Claude SKILL.md exceeds 1900 words ($CLAUDE_WORDS)"

printf 'validate: ok (core=%s, codex=%s, claude=%s words)\n' \
  "$CORE_WORDS" "$CODEX_WORDS" "$CLAUDE_WORDS"

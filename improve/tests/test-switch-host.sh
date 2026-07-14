#!/usr/bin/env bash

set -euo pipefail

SOURCE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
TMP_BASE="${TMPDIR:-/tmp}"
TMP_BASE="${TMP_BASE%/}"
TMP="$(mktemp -d "$TMP_BASE/improve-switch-test.XXXXXX")"
trap '/bin/rm -rf -- "$TMP"' EXIT

fail() {
  printf 'test-switch-host: %s\n' "$*" >&2
  exit 1
}

WORK="$TMP/source"
mkdir -p "$WORK"
cp -R "$SOURCE/." "$WORK/"
git -C "$WORK" init -q
git -C "$WORK" config user.name Test
git -C "$WORK" config user.email test@example.invalid
git -C "$WORK" add .
git -C "$WORK" commit -qm baseline

SCRIPT="$WORK/scripts/switch-host.sh"
"$SCRIPT" --check-canonical >/dev/null
BASE_SKILL="$(shasum -a 256 "$WORK/SKILL.md" | awk '{print $1}')"
BASE_META="$(shasum -a 256 "$WORK/agents/openai.yaml" | awk '{print $1}')"

if IMPROVE_SWITCH_TEST_FAIL_AFTER_SKILL=1 "$SCRIPT" claude-code >/dev/null 2>&1; then
  fail "injected transition failure unexpectedly succeeded"
fi
[ "$(shasum -a 256 "$WORK/SKILL.md" | awk '{print $1}')" = "$BASE_SKILL" ] || fail "rollback did not restore SKILL.md"
[ "$(shasum -a 256 "$WORK/agents/openai.yaml" | awk '{print $1}')" = "$BASE_META" ] || fail "rollback did not restore metadata"

"$SCRIPT" claude-code >/dev/null
grep -q '<!-- improve-generated: claude-code;' "$WORK/SKILL.md" || fail "Claude marker missing"
[ ! -e "$WORK/agents/openai.yaml" ] || fail "Codex metadata remained in Claude mode"
[ "$("$SCRIPT" --check)" = 'host=claude-code canonical=false' ] || fail "Claude state was not recognized"
if "$SCRIPT" --check-canonical >/dev/null 2>&1; then
  fail "Claude state was accepted as canonical"
fi
STATUS="$(git -C "$WORK" status --short)"
[ "$(printf '%s\n' "$STATUS" | grep -c .)" -eq 2 ] || fail "Claude switch touched more than two tracked paths: $STATUS"
printf '%s\n' "$STATUS" | grep -q '^ M SKILL.md$' || fail "SKILL.md was not the only modification"
printf '%s\n' "$STATUS" | grep -q '^ D agents/openai.yaml$' || fail "metadata deletion was not recorded"

CLAUDE_HASH="$(shasum -a 256 "$WORK/SKILL.md" | awk '{print $1}')"
"$SCRIPT" claude-code >/dev/null
[ "$(shasum -a 256 "$WORK/SKILL.md" | awk '{print $1}')" = "$CLAUDE_HASH" ] || fail "repeated Claude switch changed output"

"$SCRIPT" codex >/dev/null
[ "$(shasum -a 256 "$WORK/SKILL.md" | awk '{print $1}')" = "$BASE_SKILL" ] || fail "Codex round-trip changed SKILL.md"
[ "$(shasum -a 256 "$WORK/agents/openai.yaml" | awk '{print $1}')" = "$BASE_META" ] || fail "Codex round-trip changed metadata"
git -C "$WORK" diff --quiet || fail "Codex round-trip did not restore a clean checkout"

SOURCE_STATUS="$(git -C "$WORK" status --short)"
OUTPUT="$TMP/output with spaces/improve"
"$SCRIPT" claude-code --output "$OUTPUT" >/dev/null
[ "$(git -C "$WORK" status --short)" = "$SOURCE_STATUS" ] || fail "--output modified the source checkout"
grep -q '<!-- improve-generated: claude-code;' "$OUTPUT/SKILL.md" || fail "Claude output marker missing"
[ ! -e "$OUTPUT/agents/openai.yaml" ] || fail "Claude output contains Codex metadata"
OUTPUT_HASH="$(shasum -a 256 "$OUTPUT/SKILL.md" | awk '{print $1}')"
"$SCRIPT" claude-code --output "$OUTPUT" >/dev/null
[ "$(shasum -a 256 "$OUTPUT/SKILL.md" | awk '{print $1}')" = "$OUTPUT_HASH" ] || fail "repeated --output changed output"

"$OUTPUT/scripts/switch-host.sh" codex >/dev/null
grep -q '<!-- improve-generated: codex;' "$OUTPUT/SKILL.md" || fail "materialized copy cannot switch to Codex"
[ -f "$OUTPUT/agents/openai.yaml" ] || fail "materialized copy did not restore metadata"
"$OUTPUT/scripts/validate.sh" >/dev/null || fail "materialized copy failed validation"

ln -s "$OUTPUT" "$TMP/output-link"
if "$SCRIPT" claude-code --output "$TMP/output-link" >/dev/null 2>&1; then
  fail "symlink output destination was accepted"
fi

UNMANAGED="$TMP/unmanaged"
mkdir -p "$UNMANAGED"
printf 'mine\n' > "$UNMANAGED/file.txt"
if "$SCRIPT" claude-code --output "$UNMANAGED" >/dev/null 2>&1; then
  fail "unmanaged output was overwritten"
fi
[ "$(cat "$UNMANAGED/file.txt")" = mine ] || fail "unmanaged output changed"

printf 'manual\n' > "$WORK/SKILL.md"
if "$SCRIPT" codex >/dev/null 2>&1; then
  fail "unmanaged root SKILL.md was overwritten"
fi

printf 'test-switch-host: ok\n'

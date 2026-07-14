#!/usr/bin/env bash

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
HELPER="$ROOT/scripts/create-execution-worktree.sh"
TMP_BASE="${TMPDIR:-/tmp}"
TMP_BASE="${TMP_BASE%/}"
TMP="$(mktemp -d "$TMP_BASE/improve-worktree-test.XXXXXX")"
trap '/bin/rm -rf -- "$TMP"' EXIT
mkdir -p "$TMP/runtime"
export TMPDIR="$TMP/runtime"

fail() {
  printf 'test-execution-worktree: %s\n' "$*" >&2
  exit 1
}

make_repo() {
  local name="$1"
  REPO="$TMP/$name"
  mkdir -p "$REPO/src"
  git -C "$REPO" init -q
  git -C "$REPO" config user.name Test
  git -C "$REPO" config user.email test@example.invalid
  printf 'a0\n' > "$REPO/src/a.txt"
  printf 'b0\n' > "$REPO/src/b.txt"
  git -C "$REPO" add .
  git -C "$REPO" commit -qm baseline
  SHA="$(git -C "$REPO" rev-parse HEAD)"
}

make_repo "happy repo"
RESULT="$TMP/happy.result"
"$HELPER" "$REPO" "$SHA" 001-happy -- src/a.txt > "$RESULT"
WORKTREE="$(awk -F '\t' '$1 == "WORKTREE" { print $2 }' "$RESULT")"
BRANCH="$(awk -F '\t' '$1 == "BRANCH" { print $2 }' "$RESULT")"
[ -d "$WORKTREE" ] || fail "worktree was not created"
[ "$(git -C "$WORKTREE" rev-parse HEAD)" = "$SHA" ] || fail "worktree base SHA is wrong"
[ "$(git -C "$WORKTREE" branch --show-current)" = "$BRANCH" ] || fail "reported branch is wrong"
[ -z "$(git -C "$WORKTREE" status --short)" ] || fail "new worktree is dirty"
[ "$(cat "$REPO/src/a.txt")" = a0 ] || fail "main checkout changed"

make_repo dirty-tracked
printf 'dirty\n' >> "$REPO/src/a.txt"
if "$HELPER" "$REPO" "$SHA" dirty -- src/a.txt >/dev/null 2>&1; then
  fail "dirty tracked in-scope path was accepted"
fi

make_repo dirty-untracked
printf 'new\n' > "$REPO/src/new.txt"
if "$HELPER" "$REPO" "$SHA" untracked -- src/new.txt >/dev/null 2>&1; then
  fail "untracked in-scope path was accepted"
fi

make_repo out-of-scope
printf 'dirty outside scope\n' >> "$REPO/src/b.txt"
OUT_RESULT="$TMP/out-of-scope.result"
"$HELPER" "$REPO" "$SHA" outside -- src/a.txt > "$OUT_RESULT"
OUT_WORKTREE="$(awk -F '\t' '$1 == "WORKTREE" { print $2 }' "$OUT_RESULT")"
[ "$(cat "$OUT_WORKTREE/src/b.txt")" = b0 ] || fail "out-of-scope dirt leaked into worktree"

make_repo stale
printf 'a1\n' > "$REPO/src/a.txt"
git -C "$REPO" add src/a.txt
git -C "$REPO" commit -qm later
if "$HELPER" "$REPO" "$SHA" stale -- src/a.txt >/dev/null 2>&1; then
  fail "stale Planned at SHA was accepted"
fi

make_repo invalid-scope
if "$HELPER" "$REPO" "$SHA" invalid -- ../outside >/dev/null 2>&1; then
  fail "unsafe scope path was accepted"
fi

if "$HELPER" "$TMP/not-a-repo" deadbeef bad -- file >/dev/null 2>&1; then
  fail "non-repository input was accepted"
fi

printf 'test-execution-worktree: ok\n'

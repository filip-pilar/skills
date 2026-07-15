#!/usr/bin/env bash

set -euo pipefail

usage() {
  cat <<'EOF'
Usage:
  create-execution-worktree.sh <repo-root> <planned-sha> <plan-id> -- <in-scope-path>...

The current HEAD must equal planned-sha, and every in-scope path must be clean
including untracked files. The script creates and reports a retained executor
branch/worktree; it never removes or merges it.
EOF
}

die() {
  printf 'create-execution-worktree: %s\n' "$*" >&2
  exit 1
}

[ "$#" -ge 5 ] || { usage >&2; exit 2; }

REPO_INPUT="$1"
PLANNED_INPUT="$2"
PLAN_ID="$3"
shift 3
[ "${1:-}" = -- ] || die "expected -- before in-scope paths"
shift
[ "$#" -gt 0 ] || die "at least one in-scope path is required"
SCOPE=("$@")

REPO="$(git -C "$REPO_INPUT" rev-parse --show-toplevel 2>/dev/null)" || die "not a git repository: $REPO_INPUT"
REPO="$(cd "$REPO" && pwd -P)"
PLANNED_SHA="$(git -C "$REPO" rev-parse --verify "$PLANNED_INPUT^{commit}" 2>/dev/null)" || die "planned SHA is not a commit"
HEAD_SHA="$(git -C "$REPO" rev-parse HEAD 2>/dev/null)" || die "cannot resolve HEAD"
[ "$HEAD_SHA" = "$PLANNED_SHA" ] || die "HEAD differs from Planned at; reconcile and re-stamp the plan"

for path in "${SCOPE[@]}"; do
  case "$path" in
    ''|/*|../*|*/../*|*/..|..|-*) die "invalid in-scope path: $path" ;;
  esac
done

if ! git -C "$REPO" diff --quiet "$PLANNED_SHA" -- "${SCOPE[@]}"; then
  die "tracked in-scope files differ from Planned at"
fi
UNTRACKED="$(git -C "$REPO" ls-files --others --exclude-standard -- "${SCOPE[@]}")"
[ -z "$UNTRACKED" ] || die "untracked in-scope files are not represented by Planned at"

SAFE_PLAN="$(printf '%s' "$PLAN_ID" | tr '[:upper:]' '[:lower:]' | tr -cs 'a-z0-9._-' '-')"
SAFE_PLAN="${SAFE_PLAN#-}"
SAFE_PLAN="${SAFE_PLAN%-}"
[ -n "$SAFE_PLAN" ] || SAFE_PLAN="plan"
[ "$SAFE_PLAN" != . ] && [ "$SAFE_PLAN" != .. ] || SAFE_PLAN="plan"
SAFE_PLAN="${SAFE_PLAN:0:48}"

TMP_BASE="${TMPDIR:-/tmp}"
TMP_BASE="${TMP_BASE%/}"
BASE="$TMP_BASE/improve-worktrees"
mkdir -p "$BASE"
CONTAINER="$(mktemp -d "$BASE/${SAFE_PLAN}.XXXXXX")" || die "cannot create worktree container"
WORKTREE="$CONTAINER/worktree"
SUFFIX="$(basename "$CONTAINER")"
SUFFIX="${SUFFIX##*.}"
BRANCH="improve/${SAFE_PLAN}-${PLANNED_SHA:0:8}-${SUFFIX}"
if ! git check-ref-format --branch "$BRANCH" >/dev/null 2>&1; then
  /bin/rm -rf -- "$CONTAINER"
  die "generated branch name is invalid"
fi

CREATED=0
cleanup_failed() {
  if [ "$CREATED" -eq 0 ]; then
    rmdir "$CONTAINER" 2>/dev/null || true
  fi
}
trap cleanup_failed EXIT

if ! git -C "$REPO" branch "$BRANCH" "$PLANNED_SHA" >/dev/null 2>&1; then
  /bin/rm -rf -- "$CONTAINER"
  die "executor branch already exists or could not be created"
fi
if ! git -C "$REPO" worktree add "$WORKTREE" "$BRANCH" >/dev/null; then
  git -C "$REPO" branch -D "$BRANCH" >/dev/null 2>&1 || true
  /bin/rm -rf -- "$CONTAINER"
  die "git worktree creation failed"
fi
CREATED=1

printf 'ORIGINAL_REPO\t%s\n' "$REPO"
printf 'BASE_SHA\t%s\n' "$PLANNED_SHA"
printf 'BRANCH\t%s\n' "$BRANCH"
printf 'WORKTREE\t%s\n' "$WORKTREE"

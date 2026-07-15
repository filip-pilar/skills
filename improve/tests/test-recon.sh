#!/usr/bin/env bash

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
TMP_BASE="${TMPDIR:-/tmp}"
TMP_BASE="${TMP_BASE%/}"
TMP="$(mktemp -d "$TMP_BASE/improve-recon-test.XXXXXX")"
trap '/bin/rm -rf -- "$TMP"' EXIT

fail() {
  printf 'test-recon: %s\n' "$*" >&2
  exit 1
}

REPO="$TMP/repo"
mkdir -p "$REPO/.github/workflows" "$REPO/.circleci"
printf 'name: CI\n' > "$REPO/.github/workflows/ci.yml"
printf 'version: 2.1\n' > "$REPO/.circleci/config.yml"

OUTPUT="$TMP/recon.txt"
bash "$ROOT/scripts/recon.sh" "$REPO" > "$OUTPUT"
grep -Fq './.github/workflows/ci.yml' "$OUTPUT" || fail "GitHub Actions workflow was not discovered"
grep -Fq './.circleci/config.yml' "$OUTPUT" || fail "CircleCI config was not discovered"

printf 'test-recon: ok\n'

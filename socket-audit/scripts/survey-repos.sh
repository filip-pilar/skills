#!/usr/bin/env bash
# survey-repos.sh — find git repos with supported manifests, pruning caches.
#
# Usage: survey-repos.sh [OUT_FILE] [ROOT_DIR]
#   OUT_FILE  Where to write the deduplicated repo list (default: /tmp/socket-audit/repos.txt)
#   ROOT_DIR  Directory to search under (default: $HOME)
#
# Output: writes one repo path per line to OUT_FILE. Also writes OUT_FILE.all with
# every git repo found (before manifest filtering) for transparency.

set -uo pipefail

OUT="${1:-/tmp/socket-audit/repos.txt}"
ROOT="${2:-$HOME}"
mkdir -p "$(dirname "$OUT")"

if [ ! -d "$ROOT" ]; then
  echo "ERROR: root directory does not exist: $ROOT" >&2
  exit 1
fi

# Find every .git directory, pruning known-uninteresting paths.
find "$ROOT" \
  \( -path "*/node_modules" \
     -o -path "*/Library" \
     -o -path "*/.Trash" \
     -o -path "*/.cache" \
     -o -path "*/Caches" \
     -o -path "*/.npm" \
     -o -path "*/.pnpm-store" \
     -o -path "*/.yarn" \
     -o -path "*/fvm/*" \
     -o -path "*/.pub-cache/*" \
     -o -path "*/.codex/*" \
     -o -path "*/.factory/*" \
     -o -path "*/.codex/*" \
     -o -path "*/build/SourcePackages/*" \
     -o -path "*/.git/modules/*" \
  \) -prune \
  -o -type d -name ".git" -print 2>/dev/null \
  | sed 's|/\.git$||' \
  | sort -u > "$OUT.all"

ALL_COUNT=$(wc -l < "$OUT.all" | tr -d ' ')

# Keep only repos that have at least one supported manifest within 3 levels.
: > "$OUT"
while IFS= read -r repo; do
  if find "$repo" -maxdepth 3 \
       \( -path "*/node_modules" -o -path "*/.git" -o -path "*/vendor" \) -prune \
       -o \( -name "package.json" \
             -o -name "package-lock.json" \
             -o -name "yarn.lock" \
             -o -name "pnpm-lock.yaml" \
             -o -name "requirements.txt" \
             -o -name "pyproject.toml" \
             -o -name "Pipfile" \
             -o -name "Pipfile.lock" \
             -o -name "poetry.lock" \
             -o -name "go.mod" \
             -o -name "go.sum" \
             -o -name "Cargo.toml" \
             -o -name "Cargo.lock" \
             -o -name "Gemfile" \
             -o -name "Gemfile.lock" \
             -o -name "pom.xml" \
             -o -name "build.gradle" \
             -o -name "build.gradle.kts" \
           \) -print 2>/dev/null \
       | head -1 | grep -q .; then
    echo "$repo" >> "$OUT"
  fi
done < "$OUT.all"

KEPT=$(wc -l < "$OUT" | tr -d ' ')
echo "Surveyed $ALL_COUNT git repos under $ROOT"
echo "Kept $KEPT with supported manifests"
echo "Output: $OUT"
echo "Full list (pre-filter): $OUT.all"

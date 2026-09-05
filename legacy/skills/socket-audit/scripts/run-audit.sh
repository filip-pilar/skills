#!/usr/bin/env bash
# run-audit.sh — run Socket scan + offline IOC check across a list of repos.
#
# Usage:
#   run-audit.sh [--offline] REPOS_FILE OUT_DIR
#
#   --offline      Skip the Socket upload step; only run the local IOC grep.
#   REPOS_FILE     Path to a newline-separated list of repo paths (produced by survey-repos.sh).
#   OUT_DIR        Where to write per-repo JSON results, the IOC hits file, and the log.
#
# Requires: `socket` on PATH unless --offline; `jq` for the IOC check.
# IOC source: ../references/ioc-list.json (relative to this script).

set -uo pipefail

OFFLINE=0
if [ "${1:-}" = "--offline" ]; then
  OFFLINE=1
  shift
fi

REPOS="${1:-}"
OUTDIR="${2:-}"

if [ -z "$REPOS" ] || [ -z "$OUTDIR" ]; then
  echo "Usage: run-audit.sh [--offline] REPOS_FILE OUT_DIR" >&2
  exit 2
fi

if [ ! -f "$REPOS" ]; then
  echo "ERROR: repos file not found: $REPOS" >&2
  exit 2
fi

mkdir -p "$OUTDIR"
LOG="$OUTDIR/audit.log"
: > "$LOG"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
IOC_LIST="$SCRIPT_DIR/../references/ioc-list.json"
IOC_HITS="$OUTDIR/ioc-hits.json"

if [ ! -f "$IOC_LIST" ]; then
  echo "ERROR: IOC list not found at $IOC_LIST." >&2
  exit 5
fi

if ! command -v jq >/dev/null 2>&1; then
  echo "ERROR: 'jq' is required for the IOC check." >&2
  exit 5
fi

# Verify socket CLI if we're going online.
if [ "$OFFLINE" = "0" ]; then
  if ! command -v socket >/dev/null 2>&1; then
    echo "ERROR: 'socket' CLI not found. Install with: npm i -g socket" >&2
    echo "Or re-run with --offline to skip the Socket upload." >&2
    exit 3
  fi

  # Preflight auth check so we fail fast with a clear message instead of
  # 50 cryptic per-repo errors.
  if ! socket organization list --json >/dev/null 2>&1; then
    cat >&2 <<'EOF'
ERROR: Socket CLI is installed but not authenticated.

Do not automate `socket login` in an agent transcript. It needs an interactive
terminal, and tokens must stay out of conversation and tool output.

Pick one:

  Option 1 (recommended): Open a regular Terminal window and run:
      socket login
    Then re-run this script. Socket persists the token to your home dir
    and this script will pick it up automatically.

  Option 2: Skip the upload entirely and run with --offline:
      bash run-audit.sh --offline ...
EOF
    exit 4
  fi
fi

# ----- Socket scans -----
TOTAL=$(grep -c . "$REPOS" || true)
i=0
OK=0
FAIL=0
SKIPPED=0

if [ "$OFFLINE" = "0" ]; then
  echo "Running Socket scans against $TOTAL repos..." | tee -a "$LOG"
  while IFS= read -r repo; do
    [ -z "$repo" ] && continue
    i=$((i+1))
    hash=$(printf '%s' "$repo" | shasum | awk '{print substr($1,1,12)}')
    safe="$(basename "$repo" | tr -c '[:alnum:]_.-' '_')-$hash"
    out="$OUTDIR/scan-$safe.json"
    echo "[$i/$TOTAL] $repo" | tee -a "$LOG"

    if [ ! -d "$repo" ]; then
      echo "  SKIP: directory missing" | tee -a "$LOG"
      SKIPPED=$((SKIPPED+1))
      continue
    fi

    # Capture stderr to log, JSON to per-repo file.
    if ( cd "$repo" && socket scan create --report --json . > "$out" 2>>"$LOG" ); then
      echo "  OK -> $out" >> "$LOG"
      OK=$((OK+1))
    else
      echo "  FAIL (see $LOG)" | tee -a "$LOG"
      FAIL=$((FAIL+1))
    fi
  done < "$REPOS"
  echo "Socket scans: ok=$OK fail=$FAIL skipped=$SKIPPED" | tee -a "$LOG"
else
  echo "Offline mode — skipping Socket scans." | tee -a "$LOG"
fi

# ----- Offline IOC check -----
echo "Running offline IOC check against $IOC_LIST..." | tee -a "$LOG"

# Initialize hits file as a JSON array.
echo "[]" > "$IOC_HITS"

# Build a list of "package|version" tokens to grep for, plus a separate
# list of "package|*" (any version) tokens for hijacked-maintainer cases.
{
  TOKENS_EXACT=$(jq -r '.entries[] | . as $e | $e.versions[] | select(. != "*") | "\($e.ecosystem)\t\($e.package)\t\(.)\t\($e.campaign)\t\($e.severity)"' "$IOC_LIST")
  TOKENS_ANY=$(jq -r   '.entries[] | . as $e | $e.versions[] | select(. == "*") | "\($e.ecosystem)\t\($e.package)\t*\t\($e.campaign)\t\($e.severity)"' "$IOC_LIST")

  HITS_TMP="$OUTDIR/.ioc-hits.tmp"
  : > "$HITS_TMP"

  escape_ere() {
    printf '%s' "$1" | sed 's/[][(){}.^$*+?|\/\\]/\\&/g'
  }

  file_matches_regex() {
    local pattern="$1"
    local file="$2"
    if command -v perl >/dev/null 2>&1; then
      PATTERN="$pattern" perl -0ne 'BEGIN { $p = $ENV{"PATTERN"}; $ok = 1 } if (/$p/s) { $ok = 0; last } END { exit $ok }' "$file" 2>/dev/null
    else
      grep -E -q "$pattern" "$file" 2>/dev/null
    fi
  }

  while IFS= read -r repo; do
    [ -z "$repo" ] && continue
    [ ! -d "$repo" ] && continue

    # Iterate every lockfile / manifest in the repo (depth-limited).
    while IFS= read -r lockfile; do
      [ -z "$lockfile" ] && continue

      # Exact version checks
      while IFS=$'\t' read -r eco pkg ver campaign severity; do
        [ -z "$pkg" ] && continue
        pkg_re=$(escape_ere "$pkg")
        ver_re=$(escape_ere "$ver")
        # Match "pkg" with version "ver". Use a permissive grep that handles
        # JSON ("name": "pkg", "version": "ver"), YAML (pkg@ver), and
        # plaintext (pkg==ver, pkg ver, pkg-ver) styles.
        if file_matches_regex "(\"(node_modules/)?$pkg_re\"(.|\n){0,500}\"$ver_re\"|$pkg_re@$ver_re|$pkg_re==$ver_re|^$pkg_re $ver_re| $pkg_re-$ver_re\.|/$pkg_re/-/$pkg_re-$ver_re\.)" "$lockfile"; then
          jq -nc \
            --arg repo "$repo" \
            --arg lockfile "$lockfile" \
            --arg eco "$eco" \
            --arg pkg "$pkg" \
            --arg ver "$ver" \
            --arg campaign "$campaign" \
            --arg severity "$severity" \
            '{repo:$repo, lockfile:$lockfile, ecosystem:$eco, package:$pkg, version:$ver, campaign:$campaign, severity:$severity, match_type:"exact"}' >> "$HITS_TMP"
        fi
      done <<< "$TOKENS_EXACT"

      # Any-version checks (hijacked maintainer)
      while IFS=$'\t' read -r eco pkg ver campaign severity; do
        [ -z "$pkg" ] && continue
        pkg_re=$(escape_ere "$pkg")
        if file_matches_regex "(\"(node_modules/)?$pkg_re\"[[:space:]]*:|$pkg_re@|/$pkg_re/-/$pkg_re-|^$pkg_re )" "$lockfile"; then
          jq -nc \
            --arg repo "$repo" \
            --arg lockfile "$lockfile" \
            --arg eco "$eco" \
            --arg pkg "$pkg" \
            --arg campaign "$campaign" \
            --arg severity "$severity" \
            '{repo:$repo, lockfile:$lockfile, ecosystem:$eco, package:$pkg, version:"<any>", campaign:$campaign, severity:$severity, match_type:"package-only"}' >> "$HITS_TMP"
        fi
      done <<< "$TOKENS_ANY"

    done < <(find "$repo" -maxdepth 4 \
              \( -path "*/node_modules" -o -path "*/.git" -o -path "*/vendor" \) -prune \
              -o -type f \( -name "package-lock.json" \
                            -o -name "yarn.lock" \
                            -o -name "pnpm-lock.yaml" \
                            -o -name "bun.lock" \
                            -o -name "package.json" \
                            -o -name "Pipfile.lock" \
                            -o -name "poetry.lock" \
                            -o -name "requirements.txt" \
                            -o -name "pyproject.toml" \
                            -o -name "uv.lock" \
                            -o -name "Cargo.lock" \
                            -o -name "Gemfile.lock" \
                            -o -name "go.sum" \
                         \) -print 2>/dev/null)
  done < "$REPOS"

  # Combine all hit lines into a single JSON array.
  if [ -s "$HITS_TMP" ]; then
    jq -s '.' "$HITS_TMP" > "$IOC_HITS"
  else
    echo "[]" > "$IOC_HITS"
  fi
  /bin/rm -f "$HITS_TMP"

  HITCOUNT=$(jq 'length' "$IOC_HITS")
  echo "IOC check complete: $HITCOUNT hit(s) -> $IOC_HITS" | tee -a "$LOG"
}

echo
echo "Audit complete."
echo "  Per-repo Socket JSON: $OUTDIR/scan-*.json"
echo "  IOC hits:             $IOC_HITS"
echo "  Log:                  $LOG"

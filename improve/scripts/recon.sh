#!/usr/bin/env bash
#
# recon.sh — deterministic Phase 1 recon for the `improve` skill.
#
# Gathers the facts that every audit needs but that cost nothing to think
# about: the commit SHA to stamp plans against, churn hotspots, the ecosystem
# and its build/test/lint commands, the intent/design docs to read, and the
# repo shape. Doing this in a script (not with model tokens) is the skill's
# own economics applied to itself — spend intelligence on judgment, not on
# re-deriving `git log` every run.
#
# STRICTLY READ-ONLY. It never writes to the repo, installs anything, or
# mutates the working tree. Safe to run verbatim during recon.
#
# Usage:  bash scripts/recon.sh [repo-root]     (defaults to the git toplevel,
#                                                or the current directory)
#
# Output is plain text meant to be read straight into the advisor's context.
# Everything is best-effort: a missing tool or a non-git directory degrades to
# a note, never an error exit. The advisor still verifies anything load-bearing
# (candidate commands are *candidates* — confirm before putting them in a plan).

set -uo pipefail

# Directories that are generated, vendored, or otherwise not worth auditing.
# Keep this in sync with the "Default skip-list" in references/audit-playbook.md.
SKIP_DIRS='node_modules|dist|build|out|.next|.nuxt|.svelte-kit|.turbo|coverage|vendor|target|.venv|venv|__pycache__|.mypy_cache|.pytest_cache|.gradle|.idea|.vscode|.git|bin|obj|Pods|.terraform|.serverless|.cache|.vercel|.netlify'

section() { printf '\n=== %s ===\n' "$1"; }
have()    { command -v "$1" >/dev/null 2>&1; }

# --- Resolve repo root -------------------------------------------------------
ROOT="${1:-}"
if [ -z "$ROOT" ]; then
  if have git && git rev-parse --show-toplevel >/dev/null 2>&1; then
    ROOT="$(git rev-parse --show-toplevel)"
  else
    ROOT="$(pwd)"
  fi
fi
cd "$ROOT" 2>/dev/null || { echo "recon.sh: cannot cd into '$ROOT'"; exit 0; }

echo "improve/recon — $ROOT"

# --- Git signal --------------------------------------------------------------
section "Git"
if have git && git rev-parse --git-dir >/dev/null 2>&1; then
  echo "HEAD:           $(git rev-parse HEAD 2>/dev/null || echo '(no commits)')"
  echo "Branch:         $(git rev-parse --abbrev-ref HEAD 2>/dev/null)"
  # Default branch: prefer origin/HEAD, fall back to a local main/master.
  DEFAULT_BRANCH="$(git symbolic-ref --short refs/remotes/origin/HEAD 2>/dev/null | sed 's#^origin/##')"
  if [ -z "$DEFAULT_BRANCH" ]; then
    for b in main master; do
      git show-ref --verify --quiet "refs/heads/$b" && DEFAULT_BRANCH="$b" && break
    done
  fi
  echo "Default branch: ${DEFAULT_BRANCH:-(unknown - no origin/HEAD or local main/master)}"
  echo "Remote:         $(git remote get-url origin 2>/dev/null || echo '(no origin remote)')"

  echo
  echo "Recent commits (last 15):"
  git log --oneline -15 2>/dev/null | sed 's/^/  /'

  echo
  echo "Churn hotspots (most-changed files, last 300 commits, generated/vendored excluded):"
  git log --pretty=format: --name-only -n 300 2>/dev/null \
    | grep -vE "(^|/)($SKIP_DIRS)(/|$)" \
    | grep -v '^$' \
    | sort | uniq -c | sort -rn | head -20 \
    | sed 's/^/  /'
else
  echo "(not a git repository — skipping git signal; note this: no drift-detection SHA is available for plans)"
fi

# --- Ecosystem & package managers -------------------------------------------
section "Ecosystem"
declare -a MANIFESTS=(
  "package.json:Node/JS/TS"
  "pnpm-lock.yaml:pnpm"
  "yarn.lock:Yarn"
  "package-lock.json:npm"
  "bun.lockb:Bun"
  "deno.json:Deno"
  "pyproject.toml:Python"
  "setup.py:Python (setuptools)"
  "requirements.txt:Python (pip)"
  "Pipfile:Python (pipenv)"
  "poetry.lock:Poetry"
  "uv.lock:uv"
  "go.mod:Go"
  "Cargo.toml:Rust"
  "Gemfile:Ruby"
  "composer.json:PHP"
  "pom.xml:Java (Maven)"
  "build.gradle:Java/Kotlin (Gradle)"
  "build.gradle.kts:Kotlin (Gradle)"
  "Package.swift:Swift"
  "pubspec.yaml:Dart/Flutter"
  "mix.exs:Elixir"
  "*.csproj:.NET"
  "CMakeLists.txt:C/C++ (CMake)"
  "Makefile:Make"
)
FOUND_ANY=0
for entry in "${MANIFESTS[@]}"; do
  file="${entry%%:*}"; label="${entry#*:}"
  # shellcheck disable=SC2086
  matches=$(find . -maxdepth 2 -name "$file" -not -path "*/.git/*" 2>/dev/null \
    | grep -vE "(^|/)($SKIP_DIRS)(/|$)" | head -3)
  if [ -n "$matches" ]; then
    FOUND_ANY=1
    echo "$label:"
    echo "$matches" | sed 's/^/  /'
  fi
done
[ "$FOUND_ANY" -eq 0 ] && echo "(no recognized manifest at depth <=2 — inspect the tree manually)"

# --- Candidate build/test/lint commands -------------------------------------
section "Candidate commands (VERIFY before trusting — these are leads, not facts)"
if [ -f package.json ]; then
  echo "package.json scripts:"
  if have node; then
    node -e 'try{const s=require("./package.json").scripts||{};for(const k of Object.keys(s))console.log("  "+k+": "+s[k])}catch(e){console.log("  (unparseable)")}' 2>/dev/null
  elif have python3; then
    python3 -c 'import json;s=json.load(open("package.json")).get("scripts",{});[print("  %s: %s"%(k,v)) for k,v in s.items()]' 2>/dev/null
  else
    grep -A40 '"scripts"' package.json 2>/dev/null | grep -E '^\s*"' | sed 's/^/  /'
  fi
fi
[ -f Makefile ]      && { echo "Makefile targets:"; grep -E '^[a-zA-Z0-9_.-]+:' Makefile 2>/dev/null | sed 's/:.*//' | sort -u | sed 's/^/  /'; }
[ -f justfile ]      && { echo "justfile recipes:"; grep -E '^[a-zA-Z0-9_-]+:' justfile 2>/dev/null | sed 's/:.*//' | sed 's/^/  /'; }
[ -f Taskfile.yml ]  && echo "Taskfile.yml present — check its tasks: section"
[ -f pyproject.toml ] && grep -qE '\[tool\.(pytest|ruff|mypy|black|poetry)' pyproject.toml 2>/dev/null && \
  echo "pyproject.toml declares tool config (pytest/ruff/mypy/black/poetry) — check [tool.*] sections"
[ -f Cargo.toml ]    && echo "Rust: standard commands are 'cargo build' / 'cargo test' / 'cargo clippy'"
[ -f go.mod ]        && echo "Go: standard commands are 'go build ./...' / 'go test ./...' / 'go vet ./...'"

# --- CI (often the source of truth for the real commands) --------------------
section "CI config"
CI=$(find . -maxdepth 2 \( -path './.github/workflows/*' -o -name '.gitlab-ci.yml' -o -name '.circleci' -o -name 'azure-pipelines.yml' -o -name '.travis.yml' -o -name 'Jenkinsfile' \) -not -path '*/.git/*' 2>/dev/null | head -10)
if [ -n "$CI" ]; then echo "$CI" | sed 's/^/  /'; echo "  → read these for the canonical build/test/lint invocations"; else echo "(none found)"; fi

# --- Intent & design docs (strictly additive; read what exists) --------------
section "Intent & design docs (read these — they record decided tradeoffs)"
DOC_HITS=0
for pat in README AGENTS.md CLAUDE.md CONTRIBUTING CONTEXT.md DESIGN.md PRODUCT.md ROADMAP; do
  m=$(find . -maxdepth 2 -iname "${pat}*" -not -path '*/.git/*' 2>/dev/null \
    | grep -vE "(^|/)($SKIP_DIRS)(/|$)" | head -3)
  [ -n "$m" ] && { echo "$m" | sed 's/^/  /'; DOC_HITS=1; }
done
for d in docs/adr docs/adrs docs/decisions docs/rfcs; do
  [ -d "$d" ] && { echo "  $d/ (decision records — a tradeoff here is by-design, not a finding)"; DOC_HITS=1; }
done
[ "$DOC_HITS" -eq 0 ] && echo "(none found — no ADR/PRD/context docs to reconcile against)"

# --- Repo shape --------------------------------------------------------------
section "Top-level structure (depth 2, generated/vendored excluded)"
if have find; then
  find . -maxdepth 2 -type d -not -path '*/.git/*' 2>/dev/null \
    | grep -vE "(^|/)($SKIP_DIRS)(/|$)" \
    | sort | sed 's|^\./||' | sed 's/^/  /' | head -60
fi

section "Done"
echo "Next: the advisor reads the above, VERIFIES the candidate commands, and"
echo "proceeds to Phase 2 (audit). Nothing here is authoritative on its own."

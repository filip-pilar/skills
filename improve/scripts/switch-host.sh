#!/usr/bin/env bash

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
CORE="$ROOT/core.md"
METADATA_SOURCE="$ROOT/adapters/codex-openai.yaml"
DIRECT_STARTED=0
DIRECT_DONE=0
OLD_SKILL_EXISTS=0
OLD_META_EXISTS=0
TEMP_DIRS=()
BACKUP_DIR=""
NEW_TEMP_DIR=""
TMP_BASE="${TMPDIR:-/tmp}"
TMP_BASE="${TMP_BASE%/}"

usage() {
  cat <<'EOF'
Usage:
  switch-host.sh codex|claude-code [--output <directory>]
  switch-host.sh --check
  switch-host.sh --check-canonical

Without --output, replace only this package's host-facing SKILL.md and
agents/openai.yaml. With --output, materialize a self-contained managed copy
without changing the source package.
EOF
}

die() {
  printf 'switch-host: %s\n' "$*" >&2
  exit 1
}

new_temp_dir() {
  NEW_TEMP_DIR="$(mktemp -d "$TMP_BASE/improve-switch.XXXXXX")" || die "cannot create temporary directory"
  TEMP_DIRS+=("$NEW_TEMP_DIR")
}

remove_file() {
  [ ! -e "$1" ] && [ ! -L "$1" ] && return 0
  /bin/rm -f -- "$1"
}

remove_managed_tree() {
  local path="$1"
  case "$path" in
    "$TMP_BASE"/improve-switch.*|*/.improve-switch.*|*/.improve-backup.*)
      /bin/rm -rf -- "$path"
      ;;
    *)
      die "refusing unsafe cleanup path: $path"
      ;;
  esac
}

rollback_direct() {
  [ "$DIRECT_STARTED" -eq 1 ] || return 0
  [ "$DIRECT_DONE" -eq 0 ] || return 0
  [ -n "$BACKUP_DIR" ] || return 0

  if [ "$OLD_SKILL_EXISTS" -eq 1 ]; then
    cp "$BACKUP_DIR/SKILL.md" "$ROOT/SKILL.md" || true
  else
    remove_file "$ROOT/SKILL.md" || true
  fi

  if [ "$OLD_META_EXISTS" -eq 1 ]; then
    mkdir -p "$ROOT/agents"
    cp "$BACKUP_DIR/openai.yaml" "$ROOT/agents/openai.yaml" || true
  else
    remove_file "$ROOT/agents/openai.yaml" || true
    rmdir "$ROOT/agents" 2>/dev/null || true
  fi
}

cleanup() {
  rollback_direct
  local dir
  for dir in "${TEMP_DIRS[@]:-}"; do
    [ -z "$dir" ] || remove_managed_tree "$dir" || true
  done
}
trap cleanup EXIT

template_for() {
  case "$1" in
    codex) printf '%s\n' "$ROOT/adapters/codex.SKILL.md.in" ;;
    claude-code) printf '%s\n' "$ROOT/adapters/claude-code.SKILL.md.in" ;;
    *) die "unsupported host '$1' (expected codex or claude-code)" ;;
  esac
}

render_skill() {
  local host="$1"
  local destination="$2"
  local template
  template="$(template_for "$host")"

  [ -f "$CORE" ] || die "missing shared core: $CORE"
  [ -f "$template" ] || die "missing host template: $template"
  [ "$(grep -c '^{{IMPROVE_SHARED_CORE}}$' "$template" || true)" -eq 1 ] || \
    die "host template must contain exactly one shared-core marker: $template"

  awk -v core="$CORE" '
    $0 == "{{IMPROVE_SHARED_CORE}}" {
      while ((getline line < core) > 0) print line
      close(core)
      next
    }
    { print }
  ' "$template" > "$destination"

  grep -q '^name: improve$' "$destination" || die "rendered SKILL.md lacks name: improve"
  grep -q '^description:' "$destination" || die "rendered SKILL.md lacks description"
  grep -q "<!-- improve-generated: $host;" "$destination" || die "rendered host marker is missing"
  ! grep -q '{{IMPROVE_SHARED_CORE}}' "$destination" || die "unexpanded shared-core marker"
}

prepare_host_files() {
  local host="$1"
  local destination="$2"
  mkdir -p "$destination"
  render_skill "$host" "$destination/SKILL.md"
  if [ "$host" = codex ]; then
    [ -f "$METADATA_SOURCE" ] || die "missing Codex metadata source"
    mkdir -p "$destination/agents"
    cp "$METADATA_SOURCE" "$destination/agents/openai.yaml"
  fi
}

recognized_root() {
  [ -f "$ROOT/SKILL.md" ] || return 1
  [ ! -L "$ROOT/SKILL.md" ] || return 1
  [ ! -L "$ROOT/agents" ] || return 1
  [ ! -L "$ROOT/agents/openai.yaml" ] || return 1
  grep -q '<!-- improve-generated:' "$ROOT/SKILL.md"
}

state_matches() {
  local host="$1"
  local rendered="$2"
  [ ! -L "$ROOT/SKILL.md" ] || return 1
  [ ! -L "$ROOT/agents" ] || return 1
  [ ! -L "$ROOT/agents/openai.yaml" ] || return 1
  cmp -s "$rendered/SKILL.md" "$ROOT/SKILL.md" || return 1
  if [ "$host" = codex ]; then
    [ -f "$ROOT/agents/openai.yaml" ] && \
      cmp -s "$rendered/agents/openai.yaml" "$ROOT/agents/openai.yaml"
  else
    [ ! -e "$ROOT/agents/openai.yaml" ] && [ ! -L "$ROOT/agents/openai.yaml" ]
  fi
}

check_state() {
  local canonical_only="$1"
  local temp
  new_temp_dir
  temp="$NEW_TEMP_DIR"
  prepare_host_files codex "$temp/codex"
  prepare_host_files claude-code "$temp/claude"

  if state_matches codex "$temp/codex"; then
    printf 'host=codex canonical=true\n'
    return 0
  fi
  if [ "$canonical_only" -eq 0 ] && state_matches claude-code "$temp/claude"; then
    printf 'host=claude-code canonical=false\n'
    return 0
  fi
  if [ "$canonical_only" -eq 1 ]; then
    printf 'switch-host: root is not the canonical Codex representation\n' >&2
  else
    printf 'switch-host: root host-facing files are unrecognized or stale\n' >&2
  fi
  return 1
}

switch_in_place() {
  local host="$1"
  local temp
  new_temp_dir
  temp="$NEW_TEMP_DIR"
  prepare_host_files "$host" "$temp/rendered"

  recognized_root || die "refusing to replace unmanaged root SKILL.md"
  if state_matches "$host" "$temp/rendered"; then
    printf 'switch-host: already %s; no changes\n' "$host"
    return 0
  fi

  BACKUP_DIR="$temp/backup"
  mkdir -p "$BACKUP_DIR"
  if [ -f "$ROOT/SKILL.md" ]; then
    OLD_SKILL_EXISTS=1
    cp "$ROOT/SKILL.md" "$BACKUP_DIR/SKILL.md"
  fi
  if [ -f "$ROOT/agents/openai.yaml" ]; then
    OLD_META_EXISTS=1
    cp "$ROOT/agents/openai.yaml" "$BACKUP_DIR/openai.yaml"
  fi

  DIRECT_STARTED=1
  cp "$temp/rendered/SKILL.md" "$ROOT/SKILL.md"
  if [ "${IMPROVE_SWITCH_TEST_FAIL_AFTER_SKILL:-0}" = 1 ]; then
    die "injected failure after SKILL.md replacement"
  fi

  if [ "$host" = codex ]; then
    mkdir -p "$ROOT/agents"
    cp "$temp/rendered/agents/openai.yaml" "$ROOT/agents/openai.yaml"
  else
    remove_file "$ROOT/agents/openai.yaml"
    rmdir "$ROOT/agents" 2>/dev/null || true
  fi

  DIRECT_DONE=1
  printf 'switch-host: switched in place to %s\n' "$host"
}

copy_runtime_sources() {
  local destination="$1"
  cp "$ROOT/README.md" "$destination/README.md"
  cp "$ROOT/core.md" "$destination/core.md"
  cp -R "$ROOT/adapters" "$destination/adapters"
  cp -R "$ROOT/references" "$destination/references"
  mkdir -p "$destination/scripts"
  cp "$ROOT/scripts/recon.sh" "$destination/scripts/recon.sh"
  cp "$ROOT/scripts/create-execution-worktree.sh" "$destination/scripts/create-execution-worktree.sh"
  cp "$ROOT/scripts/switch-host.sh" "$destination/scripts/switch-host.sh"
  cp "$ROOT/scripts/validate.sh" "$destination/scripts/validate.sh"
  cp -R "$ROOT/tests" "$destination/tests"
  chmod +x "$destination/scripts/"*.sh
  chmod +x "$destination/tests/"*.sh
}

materialize_output() {
  local host="$1"
  local requested="$2"
  [ -n "$requested" ] || die "--output requires a directory"

  local parent name destination stage package backup=""
  parent="$(dirname "$requested")"
  name="$(basename "$requested")"
  mkdir -p "$parent"
  parent="$(cd "$parent" && pwd -P)"
  destination="$parent/$name"

  [ "$destination" != "$ROOT" ] || die "use in-place mode for the source package"
  case "$destination/" in
    "$ROOT/"*) die "output must be outside the source package" ;;
  esac
  [ ! -L "$destination" ] || die "refusing to replace a symlink destination"

  stage="$(mktemp -d "$parent/.improve-switch.XXXXXX")" || die "cannot stage output beside destination"
  TEMP_DIRS+=("$stage")
  package="$stage/package"
  mkdir -p "$package"
  copy_runtime_sources "$package"
  prepare_host_files "$host" "$package"

  if [ -d "$destination" ] && [ -n "$(find "$destination" -mindepth 1 -maxdepth 1 -print -quit)" ]; then
    [ -f "$destination/SKILL.md" ] && grep -q '<!-- improve-generated:' "$destination/SKILL.md" || {
      remove_managed_tree "$stage"
      die "refusing to replace unmanaged nonempty output: $destination"
    }
  elif [ -e "$destination" ] && [ ! -d "$destination" ]; then
    remove_managed_tree "$stage"
    die "output exists and is not a directory: $destination"
  fi

  if [ -d "$destination" ] && diff -qr "$package" "$destination" >/dev/null 2>&1; then
    remove_managed_tree "$stage"
    printf 'switch-host: output already %s at %s; no changes\n' "$host" "$destination"
    return 0
  fi

  if [ -d "$destination" ]; then
    backup="$(mktemp -d "$parent/.improve-backup.XXXXXX")" || die "cannot reserve output backup"
    rmdir "$backup"
    mv "$destination" "$backup"
  fi
  if ! mv "$package" "$destination"; then
    [ -z "$backup" ] || mv "$backup" "$destination" || true
    remove_managed_tree "$stage"
    die "failed to install output"
  fi
  [ -z "$backup" ] || remove_managed_tree "$backup"
  remove_managed_tree "$stage"
  printf 'switch-host: materialized %s at %s\n' "$host" "$destination"
}

case "${1:-}" in
  --check)
    [ "$#" -eq 1 ] || die "--check takes no other arguments"
    check_state 0
    exit
    ;;
  --check-canonical)
    [ "$#" -eq 1 ] || die "--check-canonical takes no other arguments"
    check_state 1
    exit
    ;;
  -h|--help|'')
    usage
    [ "$#" -gt 0 ] && exit 0 || exit 2
    ;;
esac

HOST="$1"
template_for "$HOST" >/dev/null
shift
OUTPUT=""
while [ "$#" -gt 0 ]; do
  case "$1" in
    --output)
      [ "$#" -ge 2 ] || die "--output requires a directory"
      OUTPUT="$2"
      shift 2
      ;;
    *) die "unknown argument: $1" ;;
  esac
done

if [ -n "$OUTPUT" ]; then
  materialize_output "$HOST" "$OUTPUT"
else
  switch_in_place "$HOST"
fi

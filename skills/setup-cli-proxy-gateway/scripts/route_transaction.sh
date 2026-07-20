#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage:
  route_transaction.sh snapshot --dir BACKUP_DIR -- ABSOLUTE_PATH...
  route_transaction.sh verify   --dir BACKUP_DIR
  route_transaction.sh rollback --dir BACKUP_DIR

snapshot records existing and absent paths, preserves copies and modes, writes
a manifest, and creates a self-contained rollback.sh. rollback restores paths
that existed and removes paths that were absent at snapshot time.
USAGE
}

[[ $# -ge 1 ]] || { usage >&2; exit 1; }
action=$1
shift
bundle=''

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dir) bundle=${2:?}; shift 2 ;;
    --) shift; break ;;
    -h|--help) usage; exit 0 ;;
    *) break ;;
  esac
done

[[ -n "$bundle" ]] || { printf '%s\n' '--dir is required' >&2; exit 1; }
case "$bundle" in
  /*) ;;
  *) printf '%s\n' 'BACKUP_DIR must be absolute' >&2; exit 1 ;;
esac

mode_of() {
  if stat -f '%Lp' "$1" 2>/dev/null; then
    return
  fi
  stat -c '%a' "$1"
}

hash_file() {
  if command -v shasum >/dev/null 2>&1; then
    shasum -a 256 "$1" | awk '{print $1}'
  elif command -v sha256sum >/dev/null 2>&1; then
    sha256sum "$1" | awk '{print $1}'
  else
    printf '%s\n' '-'
  fi
}

copy_path() {
  local source=$1
  local destination=$2
  mkdir -p -- "$(dirname -- "$destination")"
  if [[ -L "$source" ]]; then
    cp -Pp -- "$source" "$destination"
  elif [[ -d "$source" ]]; then
    cp -pPR -- "$source" "$destination"
  else
    cp -p -- "$source" "$destination"
  fi
}

validate_manifest() {
  local manifest="$bundle/manifest.tsv"
  [[ -f "$manifest" ]] || { printf 'Missing manifest: %s\n' "$manifest" >&2; return 1; }
  local state path relative mode digest backup actual
  while IFS=$'\t' read -r state path relative mode digest; do
    [[ "$state" == 'state' ]] && continue
    [[ -n "$path" ]] || continue
    case "$state" in
      existing)
        backup="$bundle/$relative"
        [[ -e "$backup" || -L "$backup" ]] || { printf 'Missing backup for %s\n' "$path" >&2; return 1; }
        if [[ "$digest" != '-' && -f "$backup" && ! -L "$backup" ]]; then
          actual=$(hash_file "$backup")
          [[ "$actual" == "$digest" ]] || { printf 'Backup hash mismatch for %s\n' "$path" >&2; return 1; }
        fi
        ;;
      absent) ;;
      *) printf 'Invalid manifest state for %s: %s\n' "$path" "$state" >&2; return 1 ;;
    esac
  done < "$manifest"
}

case "$action" in
  snapshot)
    [[ $# -gt 0 ]] || { printf '%s\n' 'snapshot requires at least one path' >&2; exit 1; }
    [[ ! -e "$bundle" ]] || { printf 'Backup directory already exists: %s\n' "$bundle" >&2; exit 1; }
    mkdir -p -- "$bundle/files"
    chmod 700 "$bundle" "$bundle/files"
    manifest="$bundle/manifest.tsv"
    printf 'state\tpath\tbackup\tmode\tsha256\n' > "$manifest"
    chmod 600 "$manifest"

    script_path=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)/$(basename -- "$0")
    cp -p -- "$script_path" "$bundle/route_transaction.sh"
    chmod 700 "$bundle/route_transaction.sh"
    {
      printf '%s\n' '#!/bin/sh' 'set -eu'
      printf '%s\n' 'bundle=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)'
      printf '%s\n' 'exec "$bundle/route_transaction.sh" rollback --dir "$bundle"'
    } > "$bundle/rollback.sh"
    chmod 700 "$bundle/rollback.sh"

    for path in "$@"; do
      case "$path" in
        /*) ;;
        *) printf 'Snapshot path must be absolute: %s\n' "$path" >&2; exit 1 ;;
      esac
      case "$path" in
        *$'\t'*|*$'\n'*) printf 'Tabs/newlines are not supported in paths: %s\n' "$path" >&2; exit 1 ;;
      esac
      case "$bundle/" in
        "$path/"*) printf 'Backup directory cannot be inside target: %s\n' "$path" >&2; exit 1 ;;
      esac
      case "$path/" in
        "$bundle/"*) printf 'Target cannot be inside backup directory: %s\n' "$path" >&2; exit 1 ;;
      esac

      if [[ -e "$path" || -L "$path" ]]; then
        relative="files$path"
        copy_path "$path" "$bundle/$relative"
        mode=$(mode_of "$path")
        digest='-'
        [[ -f "$path" && ! -L "$path" ]] && digest=$(hash_file "$path")
        printf 'existing\t%s\t%s\t%s\t%s\n' "$path" "$relative" "$mode" "$digest" >> "$manifest"
      else
        printf 'absent\t%s\t-\t-\t-\n' "$path" >> "$manifest"
      fi
    done

    validate_manifest
    printf 'snapshot=%s\n' "$bundle"
    printf 'rollback=%s/rollback.sh\n' "$bundle"
    ;;

  verify)
    [[ $# -eq 0 ]] || { printf '%s\n' 'verify does not accept target paths' >&2; exit 1; }
    validate_manifest
    printf 'verified=%s\n' "$bundle"
    ;;

  rollback)
    [[ $# -eq 0 ]] || { printf '%s\n' 'rollback does not accept target paths' >&2; exit 1; }
    validate_manifest
    manifest="$bundle/manifest.tsv"
    while IFS=$'\t' read -r state path relative mode digest; do
      [[ "$state" == 'state' ]] && continue
      [[ -n "$path" ]] || continue
      case "$state" in
        existing)
          backup="$bundle/$relative"
          /bin/rm -rf -- "$path"
          copy_path "$backup" "$path"
          chmod "$mode" "$path" 2>/dev/null || true
          ;;
        absent)
          /bin/rm -rf -- "$path"
          ;;
      esac
    done < "$manifest"
    printf 'rolled_back=%s\n' "$bundle"
    ;;

  *) usage >&2; exit 1 ;;
esac

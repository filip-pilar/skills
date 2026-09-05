#!/usr/bin/env bash
# uninstall.sh — remove machine-level protection added by socket-audit.
#
# Usage: uninstall.sh [--dry-run] [--yes]
#   --dry-run  Preview without changing anything.
#   --yes, -y  Skip the confirmation prompt.
#
# This script never removes Socket CLI, per-project bunfig.toml files, Socket
# accounts/tokens, GitHub App installs, or unmarked wrapper/config files.

set -uo pipefail

DRY_RUN=0
ASSUME_YES=0
FAILURES=0
RESIDUE=0

for arg in "$@"; do
  case "$arg" in
    --dry-run) DRY_RUN=1 ;;
    --yes|-y) ASSUME_YES=1 ;;
    --help|-h) sed -n '2,9s/^# \{0,1\}//p' "$0"; exit 0 ;;
    *) echo "Unknown arg: $arg (try --help)" >&2; exit 2 ;;
  esac
done

say() { echo "$@"; }
warn_failure() { say "   ✗ $*" >&2; FAILURES=1; }

if [[ "$DRY_RUN" = "1" ]]; then
  say "=== Socket protection uninstall — DRY RUN ==="
else
  say "=== Socket protection uninstall ==="
fi
say

if [[ "$DRY_RUN" != "1" && "$ASSUME_YES" != "1" ]]; then
  read -r -p "Remove socket-audit machine-level protection? (y/N) " confirm
  [[ "$confirm" =~ ^[Yy]$ ]] || { say "Aborted."; exit 0; }
  say
fi

say "1. Marked wrapper scripts"
FOUND=0
for path in "$HOME/.local/bin/npm" "$HOME/.local/bin/pnpm" "$HOME/bin/npm" "$HOME/bin/pnpm"; do
  [[ -f "$path" ]] || continue
  FOUND=1
  if [[ -L "$path" ]]; then
    say "   ⚠ Left $path unchanged (symbolic-link ownership is uncertain)"
    RESIDUE=1
  elif grep -q "socket-audit-wrapper" "$path" 2>/dev/null; then
    if [[ "$DRY_RUN" = "1" ]]; then
      say "   [dry-run] would remove $path"
    elif /bin/rm "$path"; then
      say "   ✓ Removed $path"
    else
      warn_failure "Could not remove $path"
    fi
  else
    say "   ⚠ Left $path unchanged (no ownership marker)"
    RESIDUE=1
  fi
done
[[ "$FOUND" = "0" ]] && say "   (none found)"
say

say "2. Global Socket Firewall package"
if command -v sfw >/dev/null 2>&1; then
  if [[ "$DRY_RUN" = "1" ]]; then
    say "   [dry-run] would run: npm uninstall -g sfw (package ownership is not recorded)"
  elif npm uninstall -g sfw; then
    say "   ✓ Uninstalled sfw"
  else
    warn_failure "npm could not uninstall sfw"
  fi
else
  say "   (not found)"
fi
say

say "3. Legacy global Bun scanner package"
if command -v bun >/dev/null 2>&1 && bun pm ls -g 2>/dev/null | grep -q "@socketsecurity/bun-security-scanner"; then
  if [[ "$DRY_RUN" = "1" ]]; then
    say "   [dry-run] would run: bun remove -g @socketsecurity/bun-security-scanner (package ownership is not recorded)"
  elif bun remove -g @socketsecurity/bun-security-scanner; then
    say "   ✓ Uninstalled the global Bun scanner package"
  else
    warn_failure "Bun could not uninstall the global scanner package"
  fi
else
  say "   (not globally installed)"
fi
say

clean_shell_file() {
  local path="$1"
  local mode="$2"
  local tmp

  [[ -f "$path" ]] || return 0
  if [[ -L "$path" ]]; then
    say "   ⚠ Left $path unchanged (symbolic-link ownership is uncertain)"
    RESIDUE=1
    return 0
  fi
  case "$mode" in
    aliases)
      grep -Eq '^# (BEGIN|END) socket-audit aliases$|^# Socket Firewall aliases \(added by socket-audit' "$path" || return 0
      if grep -Eq '^# (BEGIN|END) socket-audit aliases$' "$path" && ! awk '
        /^# BEGIN socket-audit aliases$/ {
          if (block) bad=1
          block=1
          next
        }
        /^# END socket-audit aliases$/ {
          if (!block) bad=1
          block=0
        }
        END { exit (bad || block) ? 1 : 0 }
      ' "$path"; then
        say "   ⚠ Left $path unchanged (socket-audit alias markers are unbalanced)"
        RESIDUE=1
        return 0
      fi
      ;;
    path)
      grep -Eq '^# Added by socket-audit (skill|Codex skill|Claude Code skill)\.' "$path" || return 0
      ;;
  esac

  if [[ "$DRY_RUN" = "1" ]]; then
    say "   [dry-run] would back up and remove marked $mode entries from $path"
    return 0
  fi

  cp "$path" "${path}.socket-audit-backup" || { warn_failure "Could not back up $path"; return 1; }
  tmp=$(mktemp "${path}.socket-audit.XXXXXX") || { warn_failure "Could not create a temporary file for $path"; return 1; }
  cp -p "$path" "$tmp" || { /bin/rm -f "$tmp"; warn_failure "Could not preserve permissions for $path"; return 1; }

  if [[ "$mode" = "aliases" ]]; then
    awk '
      /^# BEGIN socket-audit aliases$/ { block=1; next }
      block && /^# END socket-audit aliases$/ { block=0; next }
      block { next }
      /^# Socket Firewall aliases \(added by socket-audit/ { legacy=1; next }
      legacy && /^alias (npm|pnpm|pip)=/ { next }
      legacy { legacy=0 }
      { print }
    ' "$path" > "$tmp"
  else
    awk '
      /^# Added by socket-audit (skill|Codex skill|Claude Code skill)\./ { pathline=1; next }
      pathline && /^export PATH=/ { pathline=0; next }
      pathline { pathline=0 }
      { print }
    ' "$path" > "$tmp"
  fi

  if mv "$tmp" "$path"; then
    say "   ✓ Cleaned $path (backup: ${path}.socket-audit-backup)"
  else
    /bin/rm -f "$tmp"
    warn_failure "Could not replace $path"
    return 1
  fi
}

say "4. Marked npm/pnpm aliases"
clean_shell_file "$HOME/.zshrc" aliases
clean_shell_file "$HOME/.bashrc" aliases
say

say "5. Global Bun config"
BUNFIG="$HOME/.bunfig.toml"
if [[ ! -f "$BUNFIG" ]]; then
  say "   (not found)"
elif [[ -L "$BUNFIG" ]]; then
  say "   ⚠ Left $BUNFIG unchanged (symbolic-link ownership is uncertain)"
  RESIDUE=1
elif head -3 "$BUNFIG" | grep -q "Created.*by the socket-audit"; then
  if [[ "$DRY_RUN" = "1" ]]; then
    say "   [dry-run] would back up and remove the creation header and inline-marked values from $BUNFIG"
  else
    tmp=""
    if ! cp "$BUNFIG" "$BUNFIG.socket-audit-backup"; then
      warn_failure "Could not back up $BUNFIG"
    elif ! tmp=$(mktemp "$BUNFIG.socket-audit.XXXXXX"); then
      warn_failure "Could not create a temporary Bun config"
    elif ! cp -p "$BUNFIG" "$tmp"; then
      /bin/rm -f "$tmp"
      warn_failure "Could not preserve permissions for $BUNFIG"
    elif awk '
      /^# Created.*by the socket-audit/ { next }
      /#[[:space:]]*socket-audit[[:space:]]*$/ { next }
      { print }
    ' "$BUNFIG" > "$tmp"; then
      if awk '
        /^[[:space:]]*$/ { next }
        /^[[:space:]]*\[install(\.security)?\][[:space:]]*$/ { next }
        { found=1 }
        END { exit !found }
      ' "$tmp"; then
        if mv "$tmp" "$BUNFIG"; then
          say "   ✓ Removed the creation header and inline-marked values; preserved unmarked content (backup: $BUNFIG.socket-audit-backup)"
          if grep -Eq '^[[:space:]]*scanner[[:space:]]*=[[:space:]]*"@socketsecurity/bun-security-scanner"|^[[:space:]]*minimumReleaseAge[[:space:]]*=' "$BUNFIG"; then
            say "   ⚠ Unmarked Bun protection values remain because ownership is uncertain"
            RESIDUE=1
          fi
        else
          /bin/rm -f "$tmp"
          warn_failure "Could not replace $BUNFIG"
        fi
      else
        /bin/rm -f "$tmp"
        if /bin/rm "$BUNFIG"; then
          say "   ✓ Removed skill-created $BUNFIG (backup retained)"
        else
          warn_failure "Could not remove $BUNFIG"
        fi
      fi
    else
      /bin/rm -f "$tmp"
      warn_failure "Could not clean $BUNFIG"
    fi
  fi
elif grep -q '#[[:space:]]*socket-audit[[:space:]]*$' "$BUNFIG"; then
  if [[ "$DRY_RUN" = "1" ]]; then
    say "   [dry-run] would back up $BUNFIG and remove only inline-marked values"
  else
    tmp=""
    if ! cp "$BUNFIG" "$BUNFIG.socket-audit-backup"; then
      warn_failure "Could not back up $BUNFIG"
    elif tmp=$(mktemp "$BUNFIG.socket-audit.XXXXXX") && cp -p "$BUNFIG" "$tmp" && awk '!/#[[:space:]]*socket-audit[[:space:]]*$/' "$BUNFIG" > "$tmp" && mv "$tmp" "$BUNFIG"; then
      say "   ✓ Removed inline-marked values (backup: $BUNFIG.socket-audit-backup)"
      if grep -q '@socketsecurity/bun-security-scanner' "$BUNFIG"; then
        say "   ⚠ An unmarked, pre-existing Socket scanner value remains"
        RESIDUE=1
      fi
    else
      [[ -z "$tmp" ]] || /bin/rm -f "$tmp"
      warn_failure "Could not clean $BUNFIG"
    fi
  fi
elif grep -q '@socketsecurity/bun-security-scanner' "$BUNFIG"; then
  say "   ⚠ Left unmarked Socket scanner config unchanged; ownership is uncertain"
  RESIDUE=1
else
  say "   (no owned values found)"
fi
say

say "6. Marked PATH entries"
clean_shell_file "$HOME/.zshenv" path
clean_shell_file "$HOME/.zprofile" path
clean_shell_file "$HOME/.bashrc" path
clean_shell_file "$HOME/.bash_profile" path
say

if [[ "$FAILURES" = "1" ]]; then
  say "=== Completed with failures; inspect the messages above ===" >&2
  exit 1
fi

if [[ "$RESIDUE" = "1" ]]; then
  say "=== Completed with items left for manual review ==="
else
  say "=== Done ==="
fi
say "Verify manager resolution, command -v sfw, and remaining Bun scanner references before declaring cleanup complete."

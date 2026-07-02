#!/usr/bin/env bash
# uninstall.sh — Remove everything socket-audit Workflow B installed.
#
# Removes (with .socket-audit-backup of any modified files):
#   - PATH wrappers at ~/.local/bin/{npm,pnpm} and ~/bin/{npm,pnpm}
#     (only if they carry the "socket-audit-wrapper" marker comment)
#   - sfw global package         (npm uninstall -g sfw)
#   - @socketsecurity/bun-security-scanner global package  (bun remove -g ...)
#   - Socket Firewall alias block from ~/.zshrc / ~/.bashrc
#   - The [install.security] scanner + [install] minimumReleaseAge block
#     that this skill wrote to ~/.bunfig.toml
#   - Any PATH shim lines this skill added to ~/.zshenv / ~/.zprofile /
#     ~/.bashrc / ~/.bash_profile
#
# Does NOT remove:
#   - Socket CLI (`socket` itself — still useful for audits even without
#     the firewall)
#   - Per-project bunfig.toml that you committed to repos
#   - Your Socket account, API tokens, or GitHub App installs
#     (handle those via the Socket dashboard)
#
# Usage:
#   uninstall.sh [--dry-run] [--yes]
#     --dry-run   Show what would be removed without changing anything
#     --yes / -y  Skip the confirmation prompt
#     --help / -h Show this text

set -uo pipefail

DRY_RUN=0
ASSUME_YES=0
for arg in "$@"; do
  case "$arg" in
    --dry-run)  DRY_RUN=1 ;;
    --yes|-y)   ASSUME_YES=1 ;;
    --help|-h)
      sed -n '/^# uninstall\.sh/,/^$/p' "$0" | sed 's/^# \?//'
      exit 0
      ;;
    *) echo "Unknown arg: $arg (try --help)" >&2; exit 2 ;;
  esac
done

say()  { echo "$@"; }
do_or_show() {
  if [[ "$DRY_RUN" = "1" ]]; then
    say "  [dry-run] would: $*"
  else
    "$@"
  fi
}

if [[ "$DRY_RUN" = "1" ]]; then
  say "=== Socket Firewall uninstall — DRY RUN ==="
else
  say "=== Socket Firewall uninstall ==="
fi
say

if [[ "$DRY_RUN" != "1" && "$ASSUME_YES" != "1" ]]; then
  read -r -p "Remove Socket Firewall protection from this machine? (y/N) " confirm
  [[ "$confirm" =~ ^[Yy]$ ]] || { say "Aborted."; exit 0; }
  say
fi

# --- 1. Wrapper scripts ---
say "1. Wrapper scripts"
WRAPPERS_REMOVED=0
for path in "$HOME/.local/bin/npm" "$HOME/.local/bin/pnpm" "$HOME/bin/npm" "$HOME/bin/pnpm"; do
  if [[ -f "$path" ]]; then
    if grep -q "socket-audit-wrapper" "$path" 2>/dev/null; then
      if [[ "$DRY_RUN" = "1" ]]; then
        say "   [dry-run] would remove $path"
      else
        rm "$path"
        say "   ✓ Removed $path"
      fi
      WRAPPERS_REMOVED=$((WRAPPERS_REMOVED+1))
    else
      say "   ⚠ Skipping $path (no socket-audit-wrapper marker — not ours)"
    fi
  fi
done
[[ "$WRAPPERS_REMOVED" = "0" ]] && say "   (none found)"
say

# --- 2. sfw global package ---
say "2. Socket Firewall (sfw) global npm package"
if command -v sfw >/dev/null 2>&1; then
  do_or_show npm uninstall -g sfw 2>&1 | tail -2
else
  say "   (sfw not installed)"
fi
say

# --- 3. Bun security scanner global package ---
say "3. @socketsecurity/bun-security-scanner global Bun package"
if command -v bun >/dev/null 2>&1; then
  if bun pm ls -g 2>/dev/null | grep -q "@socketsecurity/bun-security-scanner"; then
    do_or_show bun remove -g @socketsecurity/bun-security-scanner 2>&1 | tail -2 || true
  else
    say "   (not globally installed)"
  fi
else
  say "   (bun not installed)"
fi
say

# --- 4. Shell aliases ---
say "4. Shell aliases (npm/pnpm/pip → sfw) from .zshrc / .bashrc"
for rc in "$HOME/.zshrc" "$HOME/.bashrc"; do
  if [[ -f "$rc" ]] && grep -q "Socket Firewall aliases" "$rc"; then
    if [[ "$DRY_RUN" = "1" ]]; then
      say "   [dry-run] would back up $rc and delete the alias block"
    else
      cp "$rc" "${rc}.socket-audit-backup"
      # Delete from the marker comment through the last alias line we wrote
      # (best-effort — assumes the block is contiguous).
      sed -i.tmp '/# Socket Firewall aliases (added by socket-audit/,/^$/d' "$rc"
      rm -f "${rc}.tmp"
      say "   ✓ Cleaned $rc (backup: ${rc}.socket-audit-backup)"
    fi
  fi
done
say

# --- 5. ~/.bunfig.toml scanner block ---
say "5. ~/.bunfig.toml scanner block"
if [[ -f "$HOME/.bunfig.toml" ]]; then
  if grep -q "@socketsecurity/bun-security-scanner" "$HOME/.bunfig.toml"; then
    if [[ "$DRY_RUN" = "1" ]]; then
      say "   [dry-run] would back up ~/.bunfig.toml and remove the scanner config"
    else
      cp "$HOME/.bunfig.toml" "$HOME/.bunfig.toml.socket-audit-backup"
      # If we created the file (header marker present), drop the whole thing.
      if head -3 "$HOME/.bunfig.toml" | grep -q "Created.*by the socket-audit"; then
        rm "$HOME/.bunfig.toml"
        say "   ✓ Removed ~/.bunfig.toml (was created by this skill — backup at .socket-audit-backup)"
      else
        # Best-effort: drop the [install.security] section and the minimumReleaseAge line
        python3 - <<PYEOF || true
import re, sys
path = "$HOME/.bunfig.toml"
with open(path) as f: text = f.read()
# Remove [install.security] block (until next [section] or EOF)
text = re.sub(r'(?ms)^\[install\.security\][^\[]*?(?=^\[|\Z)', '', text)
# Remove minimumReleaseAge line inside [install] (leave the rest of [install] alone)
text = re.sub(r'(?m)^minimumReleaseAge\s*=.*\n', '', text)
# Collapse runs of blank lines
text = re.sub(r'\n{3,}', '\n\n', text).strip() + '\n'
with open(path, 'w') as f: f.write(text)
PYEOF
        say "   ✓ Removed scanner block from ~/.bunfig.toml (backup at .socket-audit-backup)"
        say "     Inspect the file and remove any empty [install] section if it bothers you."
      fi
    fi
  else
    say "   (~/.bunfig.toml does not reference the scanner)"
  fi
else
  say "   (~/.bunfig.toml does not exist)"
fi
say

# --- 6. PATH shim lines ---
say "6. PATH shim lines added to shell config (by marker comment)"
for rc in "$HOME/.zshenv" "$HOME/.zprofile" "$HOME/.bashrc" "$HOME/.bash_profile"; do
  if [[ -f "$rc" ]] && grep -Eq "socket-audit (skill|Codex skill|Claude Code skill)" "$rc" 2>/dev/null; then
    if [[ "$DRY_RUN" = "1" ]]; then
      say "   [dry-run] would back up $rc and delete the socket-audit block"
    else
      cp "$rc" "${rc}.socket-audit-backup"
      # Delete from "Added by socket-audit" marker through the next blank line
      sed -i.tmp \
        -e '/socket-audit skill/,/^$/d' \
        -e '/socket-audit Codex skill/,/^$/d' \
        -e '/socket-audit Claude Code skill/,/^$/d' \
        "$rc"
      rm -f "${rc}.tmp"
      say "   ✓ Cleaned $rc (backup: ${rc}.socket-audit-backup)"
    fi
  fi
done
say

say "=== Done ==="
say "Verify with:"
say "  which npm           # should be /opt/homebrew/bin/npm or similar, NOT a wrapper"
say "  command -v sfw      # should print nothing (uninstalled)"
say "  cat ~/.bunfig.toml  # should not mention bun-security-scanner"

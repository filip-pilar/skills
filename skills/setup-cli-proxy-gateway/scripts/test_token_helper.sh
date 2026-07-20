#!/bin/sh
set -eu

script_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
skill_dir=$(dirname -- "$script_dir")
helper="$skill_dir/assets/read-cli-proxy-token.sh"

[ -x "$helper" ] || { printf 'missing executable helper: %s\n' "$helper" >&2; exit 1; }

tmp_root=$(mktemp -d "${TMPDIR:-/tmp}/cli-proxy-token-test.XXXXXX")
cleanup() {
  /bin/rm -rf -- "$tmp_root"
}
trap cleanup EXIT HUP INT TERM

assert_rejected() {
  label=$1
  path=$2
  if "$helper" "$path" >"$tmp_root/$label.stdout" 2>"$tmp_root/$label.stderr"; then
    printf 'expected rejection: %s\n' "$label" >&2
    exit 1
  fi
  [ ! -s "$tmp_root/$label.stdout" ] || {
    printf 'helper leaked output for rejected case: %s\n' "$label" >&2
    exit 1
  }
}

good="$tmp_root/good"
printf '%s\n' 'fake-local-client-token' > "$good"
chmod 600 "$good"
actual=$($helper "$good")
[ "$actual" = 'fake-local-client-token' ] || { printf '%s\n' 'valid token mismatch' >&2; exit 1; }

unsafe="$tmp_root/unsafe"
printf '%s\n' 'fake-unsafe-token' > "$unsafe"
chmod 644 "$unsafe"
assert_rejected unsafe_mode "$unsafe"

symlink="$tmp_root/symlink"
ln -s "$good" "$symlink"
assert_rejected symlink "$symlink"

multi="$tmp_root/multi"
printf '%s\n%s\n' 'first' 'second' > "$multi"
chmod 600 "$multi"
assert_rejected multiple_lines "$multi"

empty="$tmp_root/empty"
: > "$empty"
chmod 600 "$empty"
assert_rejected empty "$empty"

spaced="$tmp_root/spaced"
printf '%s\n' ' trailing-space ' > "$spaced"
chmod 600 "$spaced"
assert_rejected surrounding_spaces "$spaced"

printf '%s\n' 'token_helper_tests=verified'

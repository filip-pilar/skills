#!/bin/sh
set -eu

script_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
audit="$script_dir/audit_gateway.sh"
tmp_root=$(mktemp -d "${TMPDIR:-/tmp}/cli-proxy-isolated-home.XXXXXX")
cleanup() {
  /bin/rm -rf -- "$tmp_root"
}
trap cleanup EXIT HUP INT TERM

output="$tmp_root/audit.txt"
mkdir -p "$tmp_root/bin"
printf '%s\n' '#!/bin/sh' 'export CLI_PROXY_TOKEN="fake-embedded-local-key"' > "$tmp_root/bin/claudex"
chmod 700 "$tmp_root/bin/claudex"
env -i \
  HOME="$tmp_root/home" \
  PATH="$tmp_root/bin:/opt/homebrew/bin:/usr/bin:/bin:/usr/sbin:/sbin" \
  SHELL=/bin/sh \
  "$audit" > "$output"

grep -q '\.cli-proxy-api: absent' "$output"
grep -q 'local client token file: absent' "$output"
grep -q 'launchers with embedded local keys: 1' "$output"

printf '%s\n' '#!/bin/sh' 'export CLI_PROXY_TOKEN="$(read-cli-proxy-token)"' > "$tmp_root/bin/claudex"
dynamic_output="$tmp_root/audit-dynamic.txt"
env -i \
  HOME="$tmp_root/home" \
  PATH="$tmp_root/bin:/opt/homebrew/bin:/usr/bin:/bin:/usr/sbin:/sbin" \
  SHELL=/bin/sh \
  "$audit" > "$dynamic_output"
grep -q 'launchers with embedded local keys: 0' "$dynamic_output"

printf '%s\n' 'isolated_home_audit=verified' 'stale_embedded_key_detection=verified'

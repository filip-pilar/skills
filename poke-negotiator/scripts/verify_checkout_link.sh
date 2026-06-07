#!/usr/bin/env bash
set -euo pipefail

URL="${1:-}"
[ -n "$URL" ] || {
  echo "usage: $0 <checkout-url>" >&2
  exit 2
}

case "$URL" in
  http://*|https://*)
    ;;
  *)
    echo "ERROR: checkout URL must start with http:// or https://" >&2
    exit 2
    ;;
esac

command -v curl >/dev/null 2>&1 || {
  echo "ERROR: curl was not found" >&2
  exit 1
}

echo "== redirects =="
curl --max-time 20 --connect-timeout 10 -sS -L -I "$URL" | awk '
  BEGIN {IGNORECASE=1}
  /^HTTP\// {print}
  /^location:/ {print}
  /^content-type:/ {print}
'

echo
echo "== final url =="
curl --max-time 20 --connect-timeout 10 -sS -L -o /dev/null -w '%{url_effective}\n' "$URL"

echo
echo "Note: Stripe Checkout renders price client-side. If this output does not show the visible price, open the final URL in an agent browser/preview and read the rendered checkout text."

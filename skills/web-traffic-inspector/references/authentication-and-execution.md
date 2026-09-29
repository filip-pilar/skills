# Authentication and execution

Choose the least powerful mode that demonstrates the observed mechanism.
Discovery and prototype execution may use different browsers; a signed-in
discovery tab does not imply a reusable companion login.

## Authentication

Prefer an existing signed-in tab or secure interactive login. For companion
execution, prepare a named `agent-browser` session, a dedicated headed runtime
profile, or an explicitly approved CDP browser. Record that non-secret launch
posture in `companion.runtime`; see [prototype-contract.md](prototype-contract.md).

Never copy ordinary browser profiles or authentication state between surfaces,
inspect secret stores, or request credentials in chat. Do not run simultaneous
browsers against one profile. Keep dedicated profile contents outside the
artifact. Signed-out/wrong-page states should guide the user to sign in in the
execution browser; keep the companion available when practical.

Authorized runtime-only headers can be supplied as JSON through the companion's
stdin. Keep them in memory and out of output, examples,
logs, screenshots, and findings. Prefer interactive login/input because shell
arguments, history, and environment can expose values locally. Target-origin
execution may still fail if the app adds private bearer state; use the original
UI path or authorized runtime headers instead of extracting tokens.

## Direct mode and CORS

Use direct mode when the endpoint accepts the prototype's origin without embedded
secrets. Test a harmless browser fetch from the exact final scheme, host, and
fixed port, including the actual request when safe. Target-site success does not
establish loopback CORS behavior. `file:` has a different origin; `curl` establishes
server liveness, not browser CORS. A blocked loopback navigation leaves CORS
unresolved. Neither `no-cors` nor disabling browser security is a solution.

Choose a relay for an observed origin restriction, not an unrelated malformed
request or authentication failure. Record relevant preflight/response evidence:
allow-origin/method/header behavior, credential/SameSite restrictions, or observed
session/signature requirements. Do not describe a relay as fixing authentication.

## Companion modes

Use `node` transport for a fixed public request or authorized runtime headers;
use `browser` transport for cookie-backed or target-origin execution. The browser
transport requires a prepared target tab; the companion checks its allowed origin.
Keep these generated controls intact when customizing:

- loopback-only binding, Host/Origin checks, and ephemeral request token;
- fixed operation/stage and endpoint allowlists, including redirect restrictions;
- server-side input validation, request/response caps, and single-flight execution;
- inputs serialized as data, sanitized errors, and no arbitrary URL/method proxy.

For bootstrap-to-transient-resource chains, customize the fixed companion hook,
validate the derived origin/path, and keep signatures/expiry values only in
memory. Page extraction has stricter path/state and projection constraints in
[page-runtime.md](page-runtime.md).

Require a new acknowledgement for each side-effecting execution. An ambiguous
mutation timeout is an unknown outcome: inspect the target service before retrying.
A verification page or relay 403 is an execution-context limit, not permission
to bypass consent, CAPTCHA, access checks, or bot defenses. Deliver partial or
blocked evidence when the authorized mechanism cannot be reproduced.

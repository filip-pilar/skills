# Authentication, CORS, and execution modes

Choose the least powerful execution mode that faithfully demonstrates the mechanism. Authentication material must remain outside generated source and model-visible output.

## Authentication hierarchy

Prefer, in order:

1. an already signed-in Browser/Chrome tab controlled under the current Browser skill;
2. secure interactive login through the Browser skill's advertised authentication capability;
3. a headed `agent-browser` session using a dedicated runtime profile;
4. an approved CDP connection to a browser explicitly prepared for remote debugging;
5. runtime-only header or cookie import into the disposable companion.

Never copy an ordinary Chrome profile directory or launch two browser processes against the same profile. Never scrape cookie databases, local storage, password stores, or browser profile files. Never ask the user to paste credentials or tokens into chat.

Treat discovery authentication and prototype authentication as separate capabilities. A signed-in Browser/Chrome tab may be the safest place to observe a mechanism, while the generated companion may still require its own `agent-browser` session. Do not imply that an existing Chrome login will transfer automatically. Before scaffolding, choose and explain one execution handoff:

- reuse a named `agent-browser` session already prepared on the target;
- start a dedicated headed profile and let the user sign in interactively there; or
- attach to an explicitly approved CDP browser.

If the selected execution browser is signed out, keep the companion running when practical, surface an actionable sign-in/wrong-page message, and let the user complete login in that browser. Do not request credentials in chat and do not copy cookies, storage, profiles, or headers from the discovery browser.

For runtime import, accept values only through the companion's runtime environment or an interactive local prompt. Keep them in memory, never echo them, and exclude them from generated files, examples, logs, raw-response views, screenshots, and findings. Warn that environment variables and shell commands may be visible to local processes or shell history; prefer interactive login when possible.

## Mode decision

### Direct `demo.html`

Use direct mode when the endpoint explicitly permits the demo's origin and needs no embedded secret. Public APIs with CORS are the clearest fit. Opening a page as `file:` creates a `null` origin and often behaves differently; serve it from loopback when testing origin behavior.

Test with the exact origin the finished prototype will use: scheme, hostname, and port. Prefer an actual harmless browser fetch from the served scaffold because it exercises both preflight and response enforcement. If a temporary probe is used, keep its request shape equivalent to the proposed prototype, store it outside the final deliverable, and delete it after mode selection. A response observed from the target website may allow or echo that website's origin while treating loopback differently; it is not evidence that direct mode will fail. Choose the relay only after the exact-origin browser test fails for an origin constraint rather than for a malformed request, authentication failure, or unrelated endpoint error.

Choose an unused fixed port before probing and keep it in the spec, final server, URL, and restart command. If the browser surface blocks loopback navigation before the request, classify CORS as unresolved. `curl` or a server `HEAD` check can establish loopback liveness only; it cannot establish browser origin behavior or visual handoff.

Do not “solve” CORS with `mode: "no-cors"`: the response becomes opaque and cannot power the prototype. Do not disable browser security.

### Loopback Node relay

Use the companion's `node` transport for CORS-only public requests or runtime headers that Node can apply directly. The relay must:

- bind only to `127.0.0.1`;
- accept only its generated operation and fixed endpoint/origin;
- validate Host and Origin;
- require an ephemeral per-process request token;
- cap request and response sizes;
- serialize one operation at a time by default;
- return sanitized errors without runtime headers;
- avoid redirects to unapproved origins unless explicitly allowlisted.

It is a proof mechanism, not a general proxy.

Validate companion inputs server-side from the generated input definitions: required values, primitive types, numeric bounds, text lengths, URL schemes, patterns, and select allowlists. Browser form validation is user experience, not a trust boundary. When a response is HTML or otherwise unusual, normalize it through the bounded customization hook while retaining the original status, media type, and safe provenance in raw output.

### `agent-browser` origin executor

Use the companion's `browser` transport when cookie-backed authentication or target-origin execution is required. Prepare a named `agent-browser` session on the target page using one of:

- `--profile <dedicated-runtime-directory>` with `--headed` for interactive login;
- `--cdp <approved-port-or-url>` for a browser intentionally exposed through CDP;
- an already-running named session prepared by the user or agent.

Encode this non-secret launch posture in `companion.runtime` so the generated findings contain the command actually tested. `interactive-profile` may reference a dedicated profile path, but that path and directory are runtime state outside the deliverable: never inspect or package their contents. `existing-session` generates a no-prepare restart against the named session. `cdp` accepts only an approved loopback endpoint in the scaffold. The demo exposes only the posture name, never the session, profile path, or CDP address.

The companion verifies that the active tab is on an allowlisted page origin before evaluating the fixed request. It sends user inputs as data, not executable code, and invokes `agent-browser` without a shell. If the site's app attaches a bearer token from private runtime state rather than relying on cookies, origin execution may still be insufficient. Use the original UI path or runtime-only headers; do not inspect secret storage to obtain the token.

For `page-runtime-extraction`, the companion also verifies the active tab's exact configured pathname and allowed fixed query/fragment state and does not construct an HTTP request. The default is exact state. `allow-consumed` is limited to pages observed clearing their configured state and accepts only exact or fully empty state. `allow-query-to-fragment` is limited to an observed parameter-for-parameter migration of the fixed query into the fragment. The fixed recipe then verifies its expected ready controls. It permits one fixed `main` recipe, serializes validated inputs as data, and enforces bounded JSON output. The recipe must not inspect cookies, browser storage, credential APIs, or private token-bearing state. Existing login state may make a visible page available, but authentication material must never become part of the projection. If the useful result cannot be isolated without exposing personal or secret-bearing state, stop and report that boundary instead of weakening it.

For a fixed bootstrap → transient resource chain, use the generated companion customization region rather than persisting the derived URL in the spec. Validate the derived origin and path before following it, keep signatures and expiry values in process memory only, and return only a sanitized projection. Preserve the generated request-stage allowlist, single-flight behavior, size caps, and Host/Origin/token checks.

## CORS diagnosis

Distinguish:

- missing `Access-Control-Allow-Origin`;
- disallowed method or request header in preflight;
- credentials with a wildcard origin;
- SameSite or third-party cookie restrictions;
- CSRF tokens tied to the page/session;
- origin, Referer, nonce, signature, or device-bound checks;
- private-network access restrictions;
- bot or automation defenses.

The prototype should explain which constraint was observed. Do not describe a relay as fixing authentication when it only changes origin enforcement.

Record the tested prototype origin, whether a preflight occurred, its status and relevant allow-origin/method/header fields, and the actual browser-fetch outcome. Treat a preflight alone as incomplete when the actual harmless request can be tested safely.

Do not bypass consent, CAPTCHA, access-verification, or bot defenses. A browser-context success paired with a relay 403 or verification page is an execution-context finding, not permission to copy browser state or disguise the relay. Hand off a partial or blocked proof with explicit provenance.

## Side effects in companions

Encode endpoint, method, and request shape in generated companion configuration. Do not accept an arbitrary URL or method from the browser. When `sideEffect` is true, the demo must require a visible acknowledgement for every page load before enabling the action. Keep the companion single-flight to reduce accidental duplicate submissions.

Do not automatically retry a mutation after an ambiguous timeout. Return an “outcome unknown” error and tell the user to inspect the target service before trying again. Retry read-only requests only when the failure is clearly transient and the prototype labels the behavior.

## Production handoff

Explain that a real integration may need a documented API or permission, server-side secret storage, OAuth or delegated authorization, CSRF protection, rate limiting, durable retries, idempotency, audit logs, schema validation, monitoring, and terms/compliance review. Include only items actually relevant to the observed mechanism.

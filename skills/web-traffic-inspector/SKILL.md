---
name: web-traffic-inspector
description: Inspect the browser traffic behind a user-described website action, isolate and verify undocumented HTTP or browser mechanisms, and generate a disposable HTML proof-prototype with safe raw-response visibility. Use for reproducing web requests, scraping read-only results, or demonstrating website actions; do not use to build production clients, SDKs, MCP servers, or broad site clones.
---

# Web Traffic Inspector

Turn one observed website action into a transparent, disposable proof-prototype. Produce the smallest useful demonstration of the discovered mechanism, not a production integration.

## Establish the target

Identify:

- the starting URL;
- the exact action and its intended result;
- whether the user will demonstrate it or wants you to perform it;
- whether the action changes external state or may incur cost;
- the output directory, defaulting to the current workspace when unambiguous;
- one available fixed loopback port to use for exact-origin testing and the final handoff.

Ask only for information that cannot be discovered safely. If the requested action has a material side effect but its scope is unclear, resolve that ambiguity before performing it.

## Choose the browser surface

Use the current Browser or Chrome control skill when available, especially for an existing signed-in Chrome tab. Let that skill own browser setup, credential entry, confirmations, tab lifecycle, and supported CDP mechanics. Web Traffic Inspector retains ownership of data minimization: generic browser inspection guidance does not authorize emitting target-page snapshots, HTML, raw URLs, or request data. Use tab-scoped CDP only within the projection rules below.

Use the installed `agent-browser` CLI when Browser control is unavailable or when an isolated persistent profile, headed interactive login, CDP connection, or generated authenticated companion is the better execution environment. Verify its installed version and help before relying on a command. Its `network requests` output may expose only request metadata; do not assume it contains request bodies or response bodies.

For authenticated work, distinguish the discovery browser from the prototype execution browser before building. An existing signed-in Chrome tab may establish the mechanism without being reusable by a restartable `agent-browser` companion. Choose an explicit handoff: reuse an already prepared named `agent-browser` session, ask the user to sign in interactively in a dedicated headed profile, or use an approved CDP browser. Never bridge the two surfaces by copying profiles, cookies, storage, headers, or credentials. Record the chosen non-secret runtime posture and exact restart command in the scaffold spec.

Do not inspect browser cookie stores, local storage, passwords, profiles, or other secret-bearing state through model-visible output. Prefer an existing signed-in tab or secure interactive login. Never ask for a password, one-time code, cookie, bearer token, or API key in chat.

Read [network-discovery.md](references/network-discovery.md) before capture. Read [authentication-and-execution.md](references/authentication-and-execution.md) when authentication, CORS, origin constraints, a relay, or a companion is relevant.

## Observe and isolate

1. Navigate to the target and establish the visible pre-action state through scoped structured inspection. On a target website, never send a `domSnapshot()` result—or any substring, filtered line, or serialized derivative of one—to model-visible output.
2. Clear or cursor the capture immediately before the action so background traffic does not dominate the evidence.
3. Perform or observe exactly the intended action. Follow the active browser skill's action-time confirmation policy. Avoid duplicate side effects and paid generations.
4. Correlate the action with requests by timing, initiator, method, payload shape, response type, and visible result. Include redirects, polling, GraphQL, SSE, WebSocket, worker, and client-only mechanisms when applicable.
5. Reduce the mechanism to required inputs, stable request fields, required non-secret headers, authentication mode, and the response fields that drive the useful UI.
6. Treat raw CDP events, URLs, payloads, headers, DOM snapshots, and HTML as tainted. Before any model-visible write, construct a new deny-by-default object containing only explicitly allowlisted primitive fields; redaction or line filtering after serialization is too late. Do not preserve raw captures by default.

Prefer HTTP replay when it faithfully produces the useful domain result. Use bounded page-runtime extraction only when replay is genuinely insufficient because the result is client-computed, held in browser-resident application state, assembled across mechanisms, or available only in the rendered page. The runtime recipe must be fixed in generated source and return a narrow JSON projection. It must not accept JavaScript, selectors, target URLs, credentials, or storage access from the demo; expose an editable console; or grow into general browser automation.

In a page-runtime recipe, anchor projection to the smallest fixed semantic component root verified in the final execution browser. Do not assume a broad structural ancestor such as `main` is invariant across browser surfaces or responsive variants. Treat styled form controls semantically: a radio or checkbox input may be visually hidden while its associated label or option container is visible. Count and select only exact allowlisted controls whose associated visible UI is present, and fail when the root, group, or selected option is missing or ambiguous. Reverify these conditions through the generated companion, not only in the discovery browser.

Follow the user-visible state transition, not merely the first correlated request. Distinguish suggestions from full results and navigation from inline expansion, modal, or in-place selection. If a downstream request depends on a meaningful server-returned choice, preserve that choice in the prototype; do not silently take the first result. Populate server-derived options from the response when practical, or constrain and label captured options to the scope in which they were observed.

Treat correlation as a hypothesis until replay or a controlled second observation distinguishes it from background traffic. If the mechanism cannot be isolated, report the strongest evidence and the missing proof instead of inventing an endpoint.

Inspect correlated background operations for hidden mutations; a visible read-only action can still change account state. Classify that separately and do not replay it merely to verify it.

Do not bypass CAPTCHA, consent, access-verification, or anti-bot barriers. Preserve the strongest safe evidence, label the result partial or blocked, and distinguish a server that is live from a prototype that successfully renders live domain data.

## Verify proportionately

Prefer a sanitized replay that cannot create an unintended second effect:

- replay read-only requests with a harmless known input;
- for mutations or generation, inspect the original successful response first and reuse an idempotency key only when its semantics are known;
- when replay would repeat a charge, message, upload, generation, or other side effect, verify through response correlation or a user-approved test action instead;
- verify the response status, shape, and at least one domain-specific field used by the prototype.

Record whether the mechanism was directly replayed, verified only through the original action, or remains provisional.

For a safe read-only scraping candidate, assess structural repeatability when it would materially improve confidence. Compare two harmless bounded projections, or change one harmless input, and compare only the projected shape, stable identifiers, continuation fields, ordering, duplicates, and completeness signals. Do not retain or diff raw captures. Skip the second observation for side effects, personal or authenticated data, access barriers, rate-limit risk, or any case where repetition is not clearly safe; record why it was skipped.

HTTP success is not domain success. Verify content type or parseability plus at least one expected domain field; treat a `200` access page, consent page, empty signed response, or unrelated HTML as a failed or partial replay. If the prototype uses a documented or safer substitute for the observed web mechanism, record both mechanisms and label their relationship as `equivalent-substitute` rather than implying an exact replay.

## Select the prototype mode

Choose the least powerful mode that works:

1. **Direct:** `demo.html` calls the endpoint itself. Use only when browser CORS/origin policy and authentication permit it.
2. **Loopback relay:** `demo.html` calls a tiny local companion which makes a fixed public or runtime-authenticated HTTP request. Bind to loopback, allow only the discovered endpoint/origin, and keep runtime headers in memory.
3. **Browser origin executor:** the companion asks `agent-browser` to execute the fixed request inside the target page's authenticated origin. Use for cookie-backed sessions, interactive login, a dedicated profile, or an approved CDP connection.
4. **Bounded page-runtime extractor:** use `mode: "browser"` with `mechanismKind: "page-runtime-extraction"` only after network replay proves insufficient. The companion opens one fixed target URL, verifies the active origin, exact path, and allowed fixed query/fragment state, and runs one fixed generated projection that returns size-bounded JSON. Keep `targetStatePolicy: "exact"` unless the page demonstrably consumes its configured state (`allow-consumed`) or moves fixed query entries parameter-for-parameter into its fragment (`allow-query-to-fragment`); either exception requires fixed recipe ready/control checks.

Before choosing a relay only because of CORS, test the direct candidate from the prototype's exact eventual loopback origin, including scheme, host, and port. Serve the scaffold or a temporary probe page there and run one harmless verified request in a browser. Keep temporary probes outside the final deliverable directory and delete them after mode selection. Inspect the actual request and any preflight. An `Access-Control-Allow-Origin` value captured from the website's own origin does not establish whether the loopback origin is allowed. Record the exact-origin success or failure that selected the mode.

Use the same fixed `localPort` in the probe, spec, and restart command. If browser policy blocks the probe before the fetch, record CORS as unresolved rather than inferring relay necessity.

Do not generate a backend architecture. The companion is disposable proof machinery and must not become a general proxy. Do not embed authentication material in HTML, JavaScript, configuration, examples, filenames, shell history suggestions, or reports.

## Build the proof-prototype

Read [prototype-contract.md](references/prototype-contract.md). Create the temporary non-secret JSON spec outside the final deliverable directory and run:

```bash
python3 <skill-directory>/scripts/scaffold_prototype.py --spec <spec.json> --out <output-directory>
```

The scaffold is a functional baseline, not a limit. Use the default `single` workflow for one request. Use the bounded `search-select-detail` workflow when a search response must expose an explicit choice whose stable identifier drives a second request. Do not model an arbitrary request graph when a small custom hook is clearer.

Set `mechanismKind` to `http-replay` (the backward-compatible default) or `page-runtime-extraction`. A page-runtime spec has no `request`, uses only browser mode and the single workflow, and must replace the generated unfinished recipe inside `WTI-CUSTOMIZE: page-runtime` with a fixed site-specific projection. Keep selectors and browser-side preparation literal in that generated region; the demo may send only validated action inputs as data. Do not add URL inputs or any code/selector field.

For companion modes, add safe `companion.runtime` metadata when the verified launch needs a named session, dedicated interactive profile, approved CDP endpoint, or runtime-only headers. The scaffold uses it to produce the exact restart command and a sanitized authentication posture in the demo. A profile path is only a runtime reference: never inspect, copy, package, or serialize that profile or its contents.

Customize only the generated `WTI-CUSTOMIZE` request, response, workflow, selection, renderer, and companion regions when the mechanism requires behavior the spec cannot express. Preserve the status states, side-effect acknowledgement, explicit selection, raw response view for every stage, safe text rendering, redaction, copy control, and download control.

Keep the verification/provenance strip prominent and the sanitized “How This Works” disclosure accurate. Preserve valid-JSON truncation, per-execution side-effect acknowledgement, stale-output clearing, bounded visual result counts, and separate request versus copy/download status when customizing the template.

Use the response region for safe normalization with original provenance, the workflow region for bounded mutation/verification/cleanup, and the companion region for fixed transient-resource chains. Follow the detailed contracts in the routed references; retain all generated guards and sanitized stage records.

Default to one self-contained `demo.html`. Add `browser-companion.mjs` only for companion modes. Do not add a framework, package manager, build step, SDK, MCP server, or production service unless the user separately changes the goal.

## Test the deliverable

Test the mode actually generated:

- validate the scaffold spec and generated files;
- serve the demo over loopback when `file:` origin behavior would differ;
- exercise one success path and one relevant failure path;
- confirm loading, success, empty result, and copy/download behavior; compare copied text when clipboard access is available;
- exercise non-2xx and invalid JSON/text with a deterministic local or intercepted response when the live endpoint cannot produce them safely, or record those branches as untested;
- classify download evidence as verified artifact/event, initiation-only, or untested; never infer filesystem completion from a click or success message;
- confirm side-effect actions cannot run before acknowledgement;
- inspect the raw view for accidental secret persistence;
- verify any relay inputs against server-side types, bounds, and select allowlists rather than trusting HTML controls;
- for a companion, verify loopback binding, Host/Origin checks, endpoint allowlisting, body limits, and actionable failure when the authenticated browser tab is unavailable or on the wrong origin.
- for page-runtime extraction, verify the unfinished-recipe guard, exact target path, fixed recipe behavior, JSON node/depth/item/byte limits, forbidden storage/credential/network access, and rejection of any non-main stage;
- record useful fields, identifiers, pagination/continuation, completeness, ordering, duplicates, required page/locale/filter/auth state, recognizable failure states, and any safe structural repeatability evidence relevant to scraping or integration readiness.

Use synthetic or harmless endpoints for deterministic tests. Do not repeat a live side effect merely to test presentation.

Before handoff, remove the temporary scaffold spec, CORS probes, traces, and other discovery-only files from the deliverable. Run `python3 <skill-directory>/scripts/validate_prototype.py <output-directory>` after replacing every findings prompt. A passing scaffold generation is not a completed findings handoff.

## Hand off

Open the finished prototype, rerun the core action, inspect the visible result and relevant console state, and leave the verified page open when the browser surface supports it. Immediately before handoff, verify that the loopback URL is reloadable. Distinguish “page left open” from “server confirmed live,” and include the exact restart command.

If a background or delegated task owns the local server, do not assume its process survives when that task becomes idle. The coordinating task must recheck the URL after the delegated task completes and, when needed, restart the server in a terminal it owns before claiming a live final handoff. A delegated task may report only that the server was confirmed at its own handoff, not guaranteed persistence.

For authenticated companions, verify the handoff path itself: the generated command opens or reuses the intended runtime, signed-out/wrong-page states give actionable interactive-login guidance, and the successful raw projection contains no authentication material. State whether discovery and execution used different browser surfaces; this is context to explain, never a reason to copy secrets between them.

Deliver the prototype and the scaffolded findings note, replacing its marked prompts with concise evidence containing:

- the observed action and isolated mechanism;
- what was verified and how;
- which execution mode was chosen and why;
- how to run the prototype;
- authentication, CORS, stability, rate-limit, and side-effect constraints;
- scraping and integration readiness, including structural repeatability performed, skipped, or not applicable with a reason;
- what a production implementation would still need;
- any uncertainty or behavior that was not tested.

Set the spec's verification status and mechanism relationship using the prototype contract. Do not mark captured evidence as a verified live replay or fabricate a polling transition that was not observed.

Label undocumented endpoints as unstable and the output as a disposable proof-prototype. Never imply that technical reproducibility grants permission for production use.

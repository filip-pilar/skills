# Proof-prototype contract

The prototype is a learning artifact. It should make the discovered mechanism legible, let the user try the action, render the useful result, and expose the sanitized response.

## Required interface

Every `demo.html` includes:

- a specific title and one-sentence explanation;
- a prominent verification/provenance strip directly below the explanation, including mechanism kind, execution mode, and mechanism relationship;
- a collapsed “How This Works” disclosure containing only sanitized request stages, method, origin/path, stable query/body field names, execution mode, and authentication posture;
- only the inputs required by the isolated action;
- one clear initial action button, plus an explicit per-result continuation button when a downstream request requires user selection;
- loading, success, empty, and actionable error states;
- a domain-appropriate result view;
- an always-available sanitized response `<pre>` rendered with `textContent`;
- copy JSON and download JSON controls;
- a short “What this demonstrates” note;
- a short “Constraints” note covering observed authentication, CORS, stability, and side-effect behavior.
- a visible verification note stating status, provenance, and whether the proof replays the observed mechanism, uses an equivalent substitute, or renders captured evidence only.

When the action has side effects, include a visible acknowledgement checkbox and keep the action disabled until it is checked. Consume and clear the acknowledgement when each side-effecting execution starts so a retry or repeat requires a new deliberate acknowledgement. Do not cache it across page loads.

## Scaffold spec

The scaffold accepts a JSON object with this shape:

```json
{
  "title": "Search the catalogue",
  "description": "Replays the request used by the site search.",
  "demonstrates": "A GET request returns the card data rendered below.",
  "constraints": "Undocumented endpoint; subject to CORS and change.",
  "mode": "direct",
  "mechanismKind": "http-replay",
  "localPort": 8765,
  "sideEffect": false,
  "verification": {
    "status": "verified",
    "relationship": "same-mechanism",
    "summary": "A reduced replay returned the expected catalogue records from the final loopback origin."
  },
  "actionLabel": "Search",
  "inputs": [
    { "name": "query", "label": "Query", "type": "text", "required": true, "placeholder": "red shoes" }
  ],
  "request": {
    "url": "https://example.test/api/search",
    "method": "GET",
    "headers": { "Accept": "application/json" },
    "query": { "q": "{{query}}" }
  },
  "renderer": {
    "type": "cards",
    "itemsPath": "results",
    "titlePath": "name",
    "subtitlePath": "description",
    "imagePath": "image_url",
    "hrefPath": "url"
  }
}
```

Supported input types are `text`, `textarea`, `number`, `url`, `select`, and `checkbox`. Authentication inputs and password fields are intentionally unsupported. `select` inputs use an `options` array of `{ "label", "value" }`. Number inputs may declare `min`, `max`, and `step`; text, textarea, and URL inputs may declare `minLength`, `maxLength`, and `pattern`. Companion modes enforce these constraints server-side as well as in HTML.

Choose `localPort` before exact-origin CORS testing and keep that same port for the generated restart command and handoff. Verification `status` is `verified`, `partial`, `blocked`, or `provisional`. `relationship` is `same-mechanism`, `equivalent-substitute`, or `captured-evidence-only`; captured evidence cannot be labelled as a verified replay. Older specs without these fields remain loadable, but scaffold as fixed-port `provisional` proofs until the agent records real provenance.

`mechanismKind` is `http-replay` or `page-runtime-extraction`; older specs default to `http-replay`. It describes what the prototype executes, while verification `relationship` describes how faithfully that mechanism represents the observed website action.

Template expressions use exact input names, such as `{{query}}`, in query values and JSON bodies. An exact expression preserves a number or boolean value; an expression embedded inside a longer string becomes text.

`mode` is `direct`, `relay`, or `browser`. The latter two generate `browser-companion.mjs`. Add a `companion` object:

```json
{
  "transport": "node",
  "targetUrl": "https://example.test/app",
  "allowedPageOrigins": ["https://example.test"],
  "allowedEndpointOrigins": ["https://example.test"]
}
```

Use `transport: "browser"` for in-origin `agent-browser` execution and `transport: "node"` for a loopback Node fetch. `targetUrl` is required for browser transport. The endpoint URL still comes from `request.url` and remains fixed in generated source.

### Bounded page-runtime extraction

Use this only when a useful HTTP replay is genuinely insufficient. A page-runtime scaffold deliberately omits `request`:

```json
{
  "title": "Inspect rendered availability",
  "description": "Projects the useful availability fields from the configured product page.",
  "demonstrates": "The website assembles the result in page runtime rather than a reusable response.",
  "constraints": "Fixed page and fixed projection; disposable proof only.",
  "mode": "browser",
  "mechanismKind": "page-runtime-extraction",
  "localPort": 8765,
  "sideEffect": false,
  "verification": {
    "status": "verified",
    "relationship": "same-mechanism",
    "summary": "Two harmless page observations returned the expected projected fields."
  },
  "actionLabel": "Inspect page",
  "inputs": [
    { "name": "postcode", "label": "Postcode", "type": "text", "required": true, "maxLength": 12 }
  ],
  "renderer": { "type": "cards", "itemsPath": "items", "titlePath": "name" },
  "companion": {
    "transport": "browser",
    "targetUrl": "https://example.test/product/known-item",
    "targetStatePolicy": "exact",
    "allowedPageOrigins": ["https://example.test"],
    "allowedEndpointOrigins": [],
    "runtime": {
      "authMode": "interactive-profile",
      "session": "wti-availability-proof",
      "profile": "/private/tmp/wti-availability-profile"
    }
  }
}
```

The generated companion initially fails with `WTI_PAGE_RUNTIME_RECIPE_REQUIRED`. Replace only its `WTI-CUSTOMIZE: page-runtime` function with a fixed recipe such as:

```js
async function projectPageRuntime({ inputs, evaluate }) {
  return evaluate((pageInputs) => {
    const roots = [...document.querySelectorAll("availability-panel[data-product='known-item']")];
    if (roots.length !== 1) throw new Error("The fixed availability component is missing or ambiguous.");
    const root = roots[0];
    const rows = [...root.querySelectorAll("[data-availability-row]")];
    return {
      postcode: pageInputs.postcode,
      items: rows.slice(0, 100).map((row) => ({
        id: row.getAttribute("data-item-id"),
        name: row.querySelector("[data-name]")?.textContent?.trim() || "",
        available: row.getAttribute("data-available") === "true"
      }))
    };
  });
}
```

Choose the smallest fixed semantic component root observed in the final execution browser. Avoid pagewide structural assumptions such as `main`, `body`, or an unscoped scan of every radio group when a form, custom element, or exact section identifies the mechanism. Fail if that root is missing or non-unique. Browser surfaces and responsive layouts may wrap the same component differently.

For styled radios and checkboxes, the native input may intentionally have no box while an associated label or option container is visibly rendered. Determine option availability from the exact associated visible UI (`input.labels`, a fixed `label[for]`, or a fixed option wrapper) plus disabled/hidden accessibility state; do not discard an option solely because the input has no client rect or `offsetParent`. Keep the selector and group names literal, ensure the selected input belongs to the bounded group, and verify the recipe through the generated companion rather than only in the discovery browser.

The function passed to `evaluate` is serialized from generated source; the HTTP caller cannot replace it. Inputs are base64-encoded JSON data, not interpolated code. The companion verifies the configured origin, exact pathname, and allowed fixed query/fragment state before evaluation, permits only the `main` stage, and bounds projected JSON by type, depth, nodes, per-array items, per-object keys, and serialized bytes. `targetStatePolicy` defaults to `exact`. Use `allow-consumed` only when the fixed page demonstrably clears its configured query/fragment during load; it permits the exact configured state or the fully consumed empty state. Use `allow-query-to-fragment` only when a page demonstrably moves configured query entries into its fragment; it accepts only an exact parameter-for-parameter migration with no alternate query. Neither accepts arbitrary state, and either requires the recipe to fail unless its fixed expected controls/ready state are present. Sensitive-looking target query/fragment state is rejected at scaffold time. The demo must not accept JavaScript, selectors, target URLs, credentials, or authentication material. Do not inspect cookies, local/session storage, IndexedDB, credential APIs, or secret-bearing application state. Do not fetch from the recipe or turn it into a generic UI driver. A small fixed preparation and projection for the one described action is acceptable; arbitrary console execution is not.

### Companion runtime and authentication metadata

`companion.runtime` is optional, non-secret launch metadata used to generate the tested restart command and authentication disclosure:

```json
{
  "authMode": "interactive-profile",
  "session": "wti-appearance-proof",
  "profile": "/private/tmp/wti-appearance-profile"
}
```

Supported `authMode` values are `none`, `existing-session`, `interactive-profile`, `cdp`, and `runtime-headers`. Browser transport always uses a bounded session name. `interactive-profile` requires a dedicated profile path; `existing-session` reuses the named session without preparing a new page; `cdp` requires a loopback port or loopback HTTP(S) endpoint without credentials, query, or fragment. Node transport accepts only `none` or `runtime-headers`; the latter adds `--runtime-headers-stdin` to the command. The scaffold quotes every command argument.

The profile path is a reference, not authentication material. Never inspect, copy, package, or expose the profile contents. Generated `demo.html` retains only `authMode`; session names, profile paths, and CDP addresses remain out of browser-visible mechanism metadata. The companion and findings may contain the local runtime reference needed to restart the disposable proof, but never captured cookies, tokens, storage, or credentials.

Renderer types are `auto`, `cards`, `images`, `table`, and `text`. Use dot-separated paths without executable expressions. If the response is unusual, scaffold with `auto`, then edit only the marked renderer function.

### Search, select, then load details

Keep the default `{ "workflow": { "type": "single" } }` for one request. For a dependent two-request flow, keep the top-level `request` as the search request and add:

```json
{
  "workflow": {
    "type": "search-select-detail",
    "itemsPath": "data.search.edges",
    "valuePath": "node.id",
    "titlePath": "node.title",
    "subtitlePath": "node.year",
    "imagePath": "node.image",
    "hrefPath": "node.url",
    "selectionActionLabel": "Load details",
    "detailRequest": {
      "url": "https://example.test/api/details",
      "method": "POST",
      "headers": { "Content-Type": "application/json" },
      "body": { "id": "{{selectedValue}}" }
    },
    "detailRenderer": {
      "type": "cards",
      "itemsPath": "results",
      "titlePath": "name"
    }
  }
}
```

The scaffold renders every returned candidate and sends the detail request only after the user chooses one. `{{selectedValue}}` is the value at `valuePath`. Both request records and the selected object remain in the sanitized raw view. For companion modes, both fixed request definitions are allowlisted; the companion still does not become a general proxy.

If image or link construction, request cleanup, or grouped result rendering needs code, edit only the generated `WTI-CUSTOMIZE` regions. The response region can populate `normalizedBody` while retaining the original response in raw JSON. The workflow region is the first-class place for a bounded multi-stage or mutation/verification/cleanup flow; cleanup belongs in `finally` and ambiguous mutations must not be retried. The companion region supports a fixed bootstrap/transient-resource chain, but every derived URL still needs exact origin/path validation and runtime-only treatment. Keep server-derived options dynamic when practical. If captured options are intentionally fixed, label their observed scope instead of presenting them as universal.

## Data handling

Build the raw object from response status, an explicit allowlist of safe response headers, and parsed body. If parsing fails, preserve the response as text. Recursively redact values under keys resembling authorization, cookies, passwords, secrets, credentials, sessions, private keys, signatures, nonces, tickets, and access/refresh/API tokens. Sanitize displayed URL credentials and sensitive query values even when the URL appears inside response text.

Redaction is defense in depth, not permission to capture secrets. Do not include sensitive request headers in the spec. Avoid rendering raw HTML. Set all untrusted text with `textContent`; validate `http:` and `https:` links and media URLs before assigning them to DOM properties.

Cap displayed/downloaded data when a response is extremely large and explain truncation. The capped representation must remain valid JSON, using an explicit preview envelope rather than slicing serialized JSON into an invalid document. Revoke temporary object URLs after downloads.

The sanitizer must distinguish repeated references from real cycles: preserve a shared object wherever it appears, and emit `[CIRCULAR]` only when traversal reaches an ancestor on the current path.

## Result rendering

Prefer the smallest useful presentation:

- `cards` for named domain objects;
- `images` for generated or searched media;
- `table` for uniform records;
- `text` for prose or logs;
- `auto` when the shape is genuinely variable.

Keep the sanitized raw response available even when the curated renderer fails. A rendering error must not erase a successfully fetched response.

At the beginning of each execution, visibly replace stale results with a loading state, disable stale copy/download controls, and mark the result and sanitized-response regions busy. If execution fails before a response arrives, expose a small sanitized error record rather than leaving an earlier response visible. Keep request status separate from copy/download feedback.

Render at most 50 cards, images, selectable results, or table rows in the curated view and state when more returned records remain available in the sanitized response. This bounded proof UI does not need virtualization.

An HTTP `2xx` response is not sufficient for success. Confirm the expected media type or parseability and at least one domain-specific field. Access-verification HTML, consent pages, empty signature-bound responses, and structurally unrelated bodies are partial/error states even when transport succeeded.

For polling or live data, display the observation timestamp and freshness/staleness state, distinguish domain status from page/container flags, keep automatic polling off by default, and show a bounded interval and request budget. If no live transition was observed, demonstrate the polling transport without claiming that updates were verified.

## Completion test

The prototype is complete when a user can identify the action, supply its inputs, preserve any meaningful intermediate choice, understand whether it has side effects, distinguish verification/provenance from transport success, run it once, see a useful result or actionable error, inspect/copy/download the sanitized response, and understand why the artifact is not production-ready. A resolved clipboard write means the copy command completed; claim copied-content equality only after readback or a controlled clipboard mock. Report downloads as artifact/event verified, initiation-only, or untested. The final directory contains only user-facing deliverables and intentional evidence; temporary specs, probes, traces, and captures stay outside it. Open and reload the served page immediately before handoff and provide an exact restart command. Then run `scripts/validate_prototype.py` and do not hand off while findings prompts or temporary build/discovery artifacts remain.

FINDINGS must also include scraping/integration readiness appropriate to the action: useful fields and stable identifiers; pagination or continuation; observed completeness, ordering, duplicates, and virtualization; required locale/filter/page/auth state; cache/rate/access-control/anti-bot behavior; recognizable empty/error/access-page states; and stable versus volatile fields. For a safe read-only candidate, record a structural repeatability comparison of bounded projected shapes/identifiers/continuation fields when relevant. Otherwise state that it was skipped or not applicable and why. This evidence does not turn the proof into a crawler or production integration.

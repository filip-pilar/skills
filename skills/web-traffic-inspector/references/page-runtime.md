# Page-runtime extraction spec and recipe

Read only when HTTP replay is insufficient and the selected mechanism is
`page-runtime-extraction`. The common prototype and authentication guards still apply.

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

Prefer visible DOM or public non-secret API values over framework internals.
When private client state is the only evidence, label its instability and return
only a tiny explicit non-secret shape. Browser-dependent extraction does not prove
that a server-side scraper will work; record that dependency in the findings.

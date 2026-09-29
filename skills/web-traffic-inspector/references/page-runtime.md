# Page-runtime extraction

Use only when HTTP replay is insufficient. Set `mechanismKind` to
`page-runtime-extraction`, `mode` to `browser`, and omit `requests`:

```json
{
  "title": "Inspect rendered availability",
  "mode": "browser",
  "mechanismKind": "page-runtime-extraction",
  "localPort": 8765,
  "sideEffect": false,
  "inputs": [],
  "companion": {
    "targetUrl": "https://example.test/product/known-item",
    "targetStatePolicy": "exact",
    "allowedPageOrigins": ["https://example.test"],
    "allowedEndpointOrigins": [],
    "runtime": {"authMode": "existing-session", "session": "wti-availability"}
  }
}
```

Complete the page’s `action` as usual, checking the projected domain result. Replace
the companion’s `WTI_PAGE_RUNTIME_RECIPE_REQUIRED` stub with a fixed recipe:

```js
async function projectPageRuntime({ inputs, evaluate }) {
  return evaluate(() => {
    const roots = [...document.querySelectorAll("availability-panel[data-product='known-item']")];
    if (roots.length !== 1) throw new Error("The fixed availability component is missing or ambiguous.");
    return {
      items: [...roots[0].querySelectorAll("[data-availability-row]")].slice(0, 100).map(row => ({
        id: row.getAttribute("data-item-id"),
        name: row.querySelector("[data-name]")?.textContent?.trim() || "",
        available: row.getAttribute("data-available") === "true"
      }))
    };
  });
}
```

Use the smallest fixed semantic component observed in the execution browser;
fail if missing or ambiguous. Derive availability from the visible control and
its enabled state; styled controls may hide their native inputs.

Inputs are serialized data, never supplied code, selectors, or target URLs.
Preserve the companion's origin, exact pathname, `main`-stage, and bounded-JSON
guards. The recipe may perform fixed preparation and projection for the one
action, but no network requests, navigation, general UI driving, storage,
credentials, or secret-bearing state access. Prefer visible DOM or public values;
label unstable client internals and project only necessary non-secret fields.

`targetStatePolicy` defaults to `exact`. Use `allow-consumed` only for an observed
page that clears its fixed query/fragment; it permits exact or fully empty state.
Use `allow-query-to-fragment` only for an observed exact parameter migration with
no alternate query. Both still require fixed ready controls. Neither permits
arbitrary state; sensitive target state is rejected by the scaffold.

Verify through the generated companion, not only the discovery browser. Record
browser dependence; page extraction does not establish server-side scraping.

# Network discovery

Use this guide to isolate the mechanism behind one user-visible action. Capture narrowly and preserve only sanitized evidence.

## Establish a clean comparison

Record the visible pre-action state, current page URL without sensitive query values, and the expected result. Start a fresh capture cursor or clear the request log immediately before the action. When noise is high, compare:

1. an idle capture without the action;
2. one capture containing the action;
3. a second action using one harmless changed input, when repeating it is safe.

The useful request usually changes at the same time and carries the changed input or returns the visible result. Analytics, feature flags, ads, telemetry, and prefetches often occur nearby but do not satisfy both conditions.

Capture each meaningful UI stage separately. Search suggestions, full search results, a selected result, and selected-result details may use different requests. Do not stop at the first request containing the query when it cannot produce the user's intended result.

## Browser/Chrome CDP route

Use the Browser skill's higher-level APIs for navigation and UI interaction. That skill owns mechanics; this guide owns what target-site data may become model-visible. Browser documentation examples that inspect page state do not override this boundary.

### Safe target-page inspection

Do not pass a target page's `domSnapshot()` result to `nodeRepl.write` or another model-visible output, including after `split`, `filter`, `slice`, regular-expression matching, truncation, or redaction. A matching snapshot line can still contain unrelated links, hidden attributes, tracking queries, CSRF/session values, or personal content. Do not print `outerHTML`, `innerHTML`, broad locator attributes, or serialized DOM nodes either.

Inspect the target with scoped locators or an in-page evaluation that returns a newly constructed object of expected primitives. Define the fields before reading the page. For a public results page, the pattern is:

```js
const safeState = await tab.playwright.evaluate(() => {
  const cleanText = (value, limit = 200) =>
    typeof value === "string" ? value.replace(/\s+/g, " ").trim().slice(0, limit) : null;
  const canonicalUrl = (value) => {
    try {
      const url = new URL(value, location.href);
      return { origin: url.origin, path: url.pathname };
    } catch {
      return null;
    }
  };
  const heading = document.querySelector("h1");
  const cards = Array.from(document.querySelectorAll("[data-result-card]")).slice(0, 20);
  return {
    location: { origin: location.origin, path: location.pathname },
    heading: cleanText(heading?.textContent),
    resultCount: cards.length,
    results: cards.map((card) => ({
      title: cleanText(card.querySelector("[data-title]")?.textContent),
      link: canonicalUrl(card.querySelector("a")?.href),
    })),
    hasNext: Boolean(document.querySelector("[rel=next]")),
  };
});
nodeRepl.write(safeState);
```

Replace the illustrative selectors with narrowly scoped selectors for the observed page. Add a query parameter only when its name and value are individually established as necessary and non-secret. For authenticated or personal pages, return only the user-authorized aggregate fields—usually counts, booleans, bounded status labels, origin, and path—not titles, identifiers, links, or free text. On the generated loopback prototype, inspect specific status/result/raw elements rather than the whole document.

When the selected tab advertises `cdp`, obtain and read that capability's current documentation before using it. The typical capture sequence is:

1. navigate a fresh or claimed tab to the target HTTP(S) page;
2. enable the CDP Network domain if the capability permits `Network.enable`;
3. call `readEvents()` once to obtain a cursor, filtered to the smallest useful event set and with `timeoutMs: 0` or the smallest supported timeout so idle traffic cannot stall the capture;
4. perform the action through normal browser UI controls;
5. read events after the cursor, paging with the returned cursor while `hasMore` is true;
6. correlate `requestId` across request, response, loading-finished, and loading-failed events;
7. after loading finishes, request the response body with `Network.getResponseBody` when permitted and useful, before navigation or buffer eviction makes it unavailable.

Useful event methods commonly include:

- `Network.requestWillBeSent`
- `Network.requestWillBeSentExtraInfo`
- `Network.responseReceived`
- `Network.responseReceivedExtraInfo`
- `Network.loadingFinished`
- `Network.loadingFailed`
- `Network.webSocketCreated`
- `Network.webSocketFrameSent`
- `Network.webSocketFrameReceived`
- `Target.attachedToTarget`

Treat these names as a protocol map, not a promise that every backend permits every command. Follow the capability's advertised surface. A `truncated` event result means older evidence was evicted; repeat with a tighter filter instead of guessing.

If a navigation helper times out, inspect a canonical origin/path, title when non-sensitive, and scoped structured state before repeating the action. The navigation may have succeeded while only the wait failed. Prefer a fresh tab or locator after a browser-session reset instead of retrying a possibly consequential stale action. Once a prototype contains a large raw JSON view, inspect scoped status/result/raw elements rather than serializing the document.

CDP request events may contain authorization, cookies, signed query values, CSRF/session form fields, or private payload fields. Treat every event object as tainted until projected. Before any `nodeRepl.write`, console output, report, or file write, build a new deny-by-default object from explicit safe fields:

- reduce URLs to origin plus path, adding only individually allowlisted non-secret query parameters;
- emit header names by default, and values only for an explicit safe header allowlist;
- emit request-body keys and types by default, and values only for fields already established as stable, necessary, and non-secret;
- use request IDs, methods, resource types, status, media type, counts, booleans, and bounded domain fields for correlation;
- inspect DOM with scoped locators or the structured pattern above; never print snapshot strings or lines, hidden/form input values, or unplanned attributes.

Never print raw event objects, raw URLs, `postData`, request headers, form payloads, DOM snapshots, snapshot-derived text lines, or HTML and then try to redact the output afterward. If an unexpected sensitive value reaches model-visible output, stop that capture route, do not repeat or quote the value, clear it from mutable tool state when possible, and record the incident generically. Do not persist it in the prototype or findings.

## `agent-browser` route

Check `agent-browser --version` and relevant `--help` output first. Use a named session so commands share the same browser. A focused sequence is:

```bash
agent-browser --session <name> network requests --clear
agent-browser --session <name> open <url>
agent-browser --session <name> network requests
# perform the action
agent-browser --session <name> network requests --filter <stable-fragment>
```

Installed versions may start tracking only when `network requests` is first called, so clear/start tracking before the action. Do not assume its public log includes POST data or response bodies. If those are absent, use one of these routes:

- Browser/Chrome CDP capture;
- a bounded in-page wrapper installed before the action for `fetch`/XHR when permitted and safe;
- an `agent-browser trace` inspected as a temporary local artifact;
- the site's visible result plus a controlled replay of the identified request.

Do not save browser state, cookies, a trace, scaffold spec, or probe page inside the generated prototype. Keep temporary discovery material outside the deliverable and delete it once it is no longer needed.

## Identify the mechanism type

### HTTP JSON or form request

Extract method, URL template, query parameters, content type, body shape, required non-secret headers, credentials behavior, and response fields. Separate stable values from session-bound values and per-request signatures.

Do not equate transport success with mechanism success. Confirm the response media type or parseability and at least one expected domain field. A `200` response containing consent HTML, access verification, an anti-bot page, or an empty signature-bound body is a failed or partial replay.

### GraphQL

Record the operation name, variables, endpoint, and only the minimal query text required. Distinguish persisted-query hashes from reusable query documents. Do not treat a captured hash as stable without replay evidence.

When a page is noisy, project candidate traffic by GraphQL operation name, changed variables, request ID, and bounded response fields rather than retaining broad post-navigation windows. Tracked clickouts, advertising, and lazy-loaded cards are not part of the mechanism unless they drive the requested result.

### Polling or asynchronous jobs

Model creation and status/result retrieval as separate steps. Capture job identifiers and terminal states. Distinguish container/page “live” flags from the domain event's actual status. The prototype should show observation time and freshness, keep polling off by default, expose its interval and request budget, and stop on success, terminal failure, timeout, cancellation, or budget exhaustion. Do not claim update behavior when no real transition was observed.

### SSE or WebSocket

Capture the initial HTTP upgrade or stream request and representative message shapes. Identify subscribe, progress, terminal, and error messages. Use a companion only when browser origin/authentication requires it. Never leave an unbounded connection or retry loop.

### Downloads and media

Determine whether the visible asset is a direct URL, signed URL, blob, data URL, streamed response, or a second fetch. Treat signed URLs as expiring response data, not constants to embed.

For bootstrap → signed-resource chains, record the bootstrap and resource as separate stages. Validate a derived URL's exact expected origin and path before following it, keep it only in runtime memory, and redact its query from errors and raw output. A replay that works only in the original browser context is not equivalent to an anonymous relay replay.

### Client-only behavior

If no useful network request exists, inspect the bounded client-side transformation. Prototype the algorithm or browser API and say explicitly that the result is client-only; do not invent an endpoint.

### Page-runtime extraction

Use page runtime only after a useful HTTP replay is absent or demonstrably insufficient. Legitimate cases include a client-computed result, a bounded view assembled from several transient mechanisms, or useful state exposed only through the rendered page. First identify the smallest fixed page-ready condition and the smallest JSON projection that proves the user-visible result.

Establish that ready condition in the final execution browser, not only the discovery browser. Anchor it to the smallest fixed semantic component—such as a specific form, custom element, or identified section—rather than assuming `main`, `body`, or another layout wrapper is invariant. For styled radios and checkboxes, inspect the exact associated label or option container and disabled/hidden accessibility state; a native input with no client rect may still represent a visible option. Project only the exact allowlisted group and fail if the root, group, or selected option is missing or ambiguous.

The generated recipe may contain literal site-specific selectors and a short fixed preparation for the one action. It must return new JSON made only from allowlisted primitive fields. Do not return DOM nodes, HTML, broad text snapshots, application state objects, event objects, or source URLs with sensitive queries. Do not read cookies, local/session storage, IndexedDB, credential APIs, password fields, or token-bearing variables. Do not accept code, selectors, URLs, or executable expressions from the prototype. Do not add general click/type/navigation primitives; the fixed target URL, exact pathname, allowed fixed query/fragment state, preparation, and projection belong in generated source. If the page consumes configured state or migrates fixed query entries into its fragment, record that observation, use only the matching narrow policy, and make the recipe verify its fixed expected controls before acting.

Prefer visible DOM attributes/text or public non-secret browser API values over private framework internals. If private client state is the only evidence, treat it as unstable and project only a tiny explicit shape. A page-runtime proof is not evidence that a server-side scraper will work; record its browser dependency and the corresponding production gap.

## Assess scraping and integration readiness

After isolating the mechanism, record only observed reuse evidence:

- useful record fields and candidate stable identifiers;
- pagination, cursors, continuation tokens, result caps, lazy loading, or virtualization;
- observed completeness, ordering, duplicates, and deduplication keys;
- required locale, market, filter, page, consent, and authentication state;
- caching, rate-limit signals, access controls, anti-bot behavior, and recognizable empty/error/access-page shapes;
- fields that appear stable versus request-, session-, locale-, or time-volatile.

For a harmless read-only target, run a structural repeatability check when it materially improves confidence: observe the same fixed action twice, or vary exactly one harmless input, then compare bounded allowlisted summaries such as top-level type, field names, record count, stable IDs, continuation presence, and ordering. Do not serialize, retain, or diff raw traffic/DOM/HTML to do this. Report the comparison and its limits. Skip it for side effects, generation/cost, personal or authenticated records, barriers, rate-limit risk, or any target where repetition is not clearly safe.

## Classify the visible transition

Do not assume a click navigates. Compare the URL and relevant DOM state before and after the action and classify it as navigation, inline expansion, modal/drawer, in-place selection, or client-only change. An unchanged URL can still accompany the decisive request. Preserve a meaningful selected object or identifier in the prototype instead of automatically using the first candidate.

## Isolation checklist

A candidate is strong when it has several of these signals:

- begins immediately after the action;
- contains the changed user input or a derived stable identifier;
- returns the content rendered in the result;
- has an initiator associated with the action's application code;
- disappears in the idle comparison;
- reproduces the result under a harmless controlled replay.

Document request chains rather than forcing a single-endpoint story when the action genuinely requires multiple dependent steps.

Also inspect secondary or background requests for hidden external effects. Operation names or fields such as `markAsRead`, subscribe, acknowledge, impression, recent-view, or viewer-state updates can make a seemingly read-only navigation consequential. Record and exclude them from replay unless they are the user-authorized target action.

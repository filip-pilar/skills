# Network discovery

Capture one visible action and follow each meaningful stage. Start or clear the
capture immediately before it. Correlate timing, changed inputs, initiators,
response fields, and the visible result; nearby telemetry is not sufficient.
A click can change a modal or selection without navigating. Preserve selected
objects and dependent request chains rather than taking the first matching call.

## Data projection

Browser tooling owns interaction mechanics; this skill limits captured data.
Before writing to model-visible output or a file, construct a new object from
explicitly allowlisted fields:

- URLs: origin and path; query names/values only when necessary and non-secret.
- Headers: names by default, values only from an explicit safe allowlist.
- Bodies: keys/types by default, stable non-secret values only as needed.
- Correlation: request IDs, methods, resource types, status, media type, counts,
  booleans, and bounded domain fields.

Do not print raw events, `postData`, headers, URLs, DOM snapshots or their filtered
lines, HTML, form values, or serialized DOM nodes and then attempt redaction.
For page inspection, use scoped locators or a projection such as this public-page
example, adapting the literal selectors to the observed component:

```js
const state = await tab.playwright.evaluate(() => {
  const rows = [...document.querySelectorAll("[data-result-card]")].slice(0, 20);
  return {
    origin: location.origin,
    path: location.pathname,
    results: rows.map(row => ({
      title: row.querySelector("[data-title]")?.textContent?.trim().slice(0, 200) || ""
    })),
    hasNext: Boolean(document.querySelector("[rel=next]"))
  };
});
nodeRepl.write(state);
```

On signed-in pages, project only the fields needed for the user-authorized task;
exclude credentials and unrelated personal content. Use the same scope when
inspecting the generated prototype. If a capture exposes secrets, stop that
capture route and correct its projection before continuing.

## Capture surfaces

Use advertised tab-scoped CDP capabilities when available. Enable Network,
establish a cursor with a nonblocking read, perform the action, then page through
new events. Correlate `requestId` across request, response, finish, and failure.
Fetch a needed response body after loading finishes and before navigation or
buffer eviction. Use only commands advertised by that browser surface; eviction
or truncation means missing evidence, not permission to guess.

For `agent-browser`, check installed help and use a named session. Start tracking
before the action (`network requests --clear`); the log may contain only metadata.
Use supported CDP or a bounded in-page fetch/XHR wrapper for missing body evidence
when permitted. Temporary traces belong outside the deliverable and must follow
the same data-minimization boundary. Recheck scoped page state after a navigation
timeout before repeating a possibly completed action.

## Mechanism-specific evidence

- **HTTP:** method, stable URL/query/body shape, required non-secret headers,
  credentials mode, and useful response fields. Check parseability and a domain
  field; a 200 access/consent page is not a successful replay.
- **GraphQL:** operation, changed variables, and minimal query. A persisted-query
  hash is not established as reusable without replay evidence.
- **Jobs/polling:** separate creation from status/result retrieval. Distinguish
  domain status from page flags; expose observation time, interval, and request
  budget. Keep polling off by default and stop on terminal outcomes or budget.
  Do not claim a transition that was never observed.
- **SSE/WebSocket:** identify subscription, progress, terminal, and error shapes;
  bound connections and retries.
- **Media:** distinguish direct, signed, blob, and streamed resources. Keep
  transient URLs in runtime memory and validate derived origins/paths before
  following them; a browser-only success is not an anonymous relay success.
- **Client-only:** demonstrate the bounded transformation without inventing an
  endpoint. For extraction from a prepared page, use
  [page-runtime.md](page-runtime.md) when HTTP replay is insufficient.

Inspect secondary requests for hidden effects such as marking messages read or
updating viewer state. Exclude them from replay unless they are the authorized
action. Correlation remains a hypothesis until safe replay or controlled
observation supports it.

For reuse questions, record relevant fields/IDs, pagination, ordering,
completeness, required state, and observed cache/rate/access constraints. A
second bounded read or one changed input may establish repeatability when safe;
avoid repeating mutations or paid actions, and respect access and rate limits.
Compare projected shapes and identifiers, not raw captures.

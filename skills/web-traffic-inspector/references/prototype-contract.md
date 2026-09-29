# Prototype contract

The scaffold produces self-contained `demo.html` and `FINDINGS.md`, plus
`browser-companion.mjs` for relay/browser modes. Keep specs and discovery material
outside the deliverable. Generated pages have native inputs, a task-specific
`action`, a result `render`, and bounded, sanitized response evidence.
Scaffolding requires Python 3.10+; companions require Node.js 18+, with
`agent-browser` available for browser execution.

## Spec

```json
{
  "title": "Search the catalogue",
  "mode": "direct",
  "localPort": 8765,
  "sideEffect": false,
  "inputs": [
    {"name": "query", "label": "Query", "type": "text", "required": true}
  ],
  "requests": {
    "main": {
      "url": "https://example.test/api/search",
      "method": "GET",
      "headers": {"Accept": "application/json"},
      "query": {"q": "{{query}}"}
    }
  }
}
```

`localPort` defaults to 8765; use the same port for the CORS probe and handoff.
`mechanismKind` defaults to `http-replay`; the alternative is
[page-runtime-extraction](page-runtime.md). HTTP proofs require a fixed `main`
request. Add named requests for further observed stages; target URLs and methods
are fixed, never supplied by the page's user.

Inputs support `text`, `textarea`, `number`, `url`, `select`, and `checkbox`.
Select options are `{ "label", "value" }` pairs. Numbers accept `min`, `max`,
and `step`; text accepts `minLength`, `maxLength`, and `pattern`. Companion inputs
are also validated server-side. Exact `{{inputName}}` values preserve primitive
types; expressions embedded in strings become text. Authentication material does
not belong in specs or HTML.

## Task-specific behavior

Complete `action` before testing the prototype. Check the expected domain result:
a successful HTTP status can still contain a login page or an error object.
For the example above:

```js
async function action(values) {
  const response = await request('main', values);
  if (!Array.isArray(response.body?.results)) {
    throw new Error('Expected catalogue results; check the request and login state.');
  }
  return response.body.results.map(item => ({id: item.id, name: item.name}));
}
```

An empty results array is a legitimate result. Replace the default JSON `render`
with a useful presentation when needed. Use `textContent` for untrusted text and
validate HTTP(S) links/media; never render returned HTML. Update the page's short
summary to describe the demonstrated behavior and any execution limit.

Preserve intermediate user choices in ordinary task-specific code. For example,
add a fixed `detail` request and an optional `selectedId` input definition, render
buttons for returned records, then call
`runAction(() => loadDetail({...inputs(), selectedId: record.id}))` from the chosen
button. `loadDetail` calls `request('detail', values)` and checks its domain result.
Use returned IDs and options; do not invent or silently pick an option for the user.

Keep `runAction` around each user action: it prevents concurrent runs, clears stale
results/exports, and preserves response evidence if rendering fails. `request`
consumes a fresh acknowledgement for each execution when `sideEffect` is true.
Do not automatically retry ambiguous mutations. If polling is necessary, bound
its budget, show freshness, and leave automatic polling off initially.

## Companion configuration

For `mode: "relay"`, add `"companion": {}`. Endpoint origins default to those of
the fixed requests; the companion uses Node fetch without browser credentials.
For authorized runtime headers, set
`"companion": {"runtime": {"authMode": "runtime-headers"}}` and supply the JSON
headers through stdin when starting the process. They remain in memory.

For `mode: "browser"`, use a prepared target page:

```json
{
  "companion": {
    "targetUrl": "https://example.test/app",
    "runtime": {"authMode": "existing-session", "session": "wti-proof"}
  }
}
```

The target origin defaults the page allowlist. Explicit `allowedPageOrigins` and
`allowedEndpointOrigins` can narrow or extend these fixed allowlists when the
observed mechanism requires it. Browser runtime authentication supports `none`,
`existing-session`, `interactive-profile` with a dedicated `profile` path, or
`cdp` with an approved loopback port/HTTP(S) endpoint. CDP addresses cannot carry
credentials, query, or fragment. Existing sessions are reused without navigation.

Launch settings live in the companion's configuration; the generated restart
command uses them automatically. For fixed bootstrap-to-resource chains, use
`customExecute(context)`: return the same `{request, response}` envelope as the
built-in executor, validate derived origins/paths, and keep transient signatures
in memory. Preserve input, origin, output, authentication, and acknowledgement
guards. See [authentication-and-execution.md](authentication-and-execution.md).

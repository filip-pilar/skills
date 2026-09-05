---
name: web-traffic-inspector
description: Inspect traffic behind a website action and build a disposable HTML proof-prototype. Use for request reproduction or read-only scraping proofs, not production clients, SDKs, MCP servers, or site clones.
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

For authenticated work, establish a restartable execution browser before building;
an existing discovery login may not transfer. Read the authentication reference
below for the supported handoff. Never copy profiles, cookies, storage, or credentials
between discovery and execution surfaces.

Do not inspect browser cookie stores, local storage, passwords, profiles, or other secret-bearing state through model-visible output. Prefer an existing signed-in tab or secure interactive login. Never ask for a password, one-time code, cookie, bearer token, or API key in chat.

Read [network-discovery.md](references/network-discovery.md) before capture. Read [authentication-and-execution.md](references/authentication-and-execution.md) when authentication, CORS, origin constraints, a relay, or a companion is relevant.

## Observe and isolate

1. Navigate to the target and establish the visible pre-action state through scoped structured inspection. On a target website, never send a `domSnapshot()` result—or any substring, filtered line, or serialized derivative of one—to model-visible output.
2. Clear or cursor the capture immediately before the action so background traffic does not dominate the evidence.
3. Perform or observe exactly the intended action. Follow the active browser skill's action-time confirmation policy. Avoid duplicate side effects and paid generations.
4. Correlate the action with requests by timing, initiator, method, payload shape, response type, and visible result. Include redirects, polling, GraphQL, SSE, WebSocket, worker, and client-only mechanisms when applicable.
5. Reduce the mechanism to required inputs, stable request fields, required non-secret headers, authentication mode, and the response fields that drive the useful UI.
6. Treat raw CDP events, URLs, payloads, headers, DOM snapshots, and HTML as tainted. Before any model-visible write, construct a new deny-by-default object containing only explicitly allowlisted primitive fields; redaction or line filtering after serialization is too late. Do not preserve raw captures by default.

Follow the whole visible transition, including meaningful intermediate choices and
request chains. Treat correlation as a hypothesis until a safe replay or controlled
observation establishes it. HTTP success alone is insufficient: check parseability
and a useful domain field; access/consent HTML is not a successful domain result.
Record substitutions as such rather than implying exact replay.

Inspect correlated operations for hidden mutations. Never repeat a charge, message,
upload, generation, or other effect just to verify it. Use the original response or
a separately authorized test; do not retry ambiguous mutations. Keep discovery captures
and temporary probes outside the deliverable. Do not bypass CAPTCHA, consent, access
verification, or anti-bot barriers; report supported partial results and limits.

## Select the least powerful working mode

- **Direct:** the endpoint permits the prototype's browser origin and authentication.
- **Loopback relay:** a fixed request needs a local transport; never a general proxy.
- **Browser origin executor:** the fixed request needs a prepared authenticated browser.
- **Bounded page-runtime extraction:** useful HTTP replay is absent or demonstrably
  insufficient; use a fixed page and narrow JSON projection, never arbitrary code,
  selectors, target URLs, or storage/credential access supplied by the demo.

Use [authentication-and-execution.md](references/authentication-and-execution.md)
for origin constraints or companion modes. Before selecting a relay solely for CORS,
test a harmless request from the final exact loopback origin. Keep the same fixed
port in the probe, spec, server, and restart command. If browser policy blocks the
probe, report CORS as unresolved. Prefer HTTP replay when it faithfully produces
the result; disclose browser dependence when page-runtime extraction is necessary.

## Build the proof

Read [prototype-contract.md](references/prototype-contract.md) for the common spec
and required interface, then only the mode-specific references it routes. Create a
temporary non-secret spec outside the deliverable and run:

```bash
python3 <skill-directory>/scripts/scaffold_prototype.py --spec <spec.json> --out <output-directory>
```

Use a single request by default; preserve user selection for search/detail flows.
Customize only the generated `WTI-CUSTOMIZE` regions when the spec cannot express
the mechanism. Keep generated guards, per-execution side-effect acknowledgement,
status states, sanitized response visibility, and safe rendering intact. Inputs
remain validated data; no general proxy, console, or arbitrary request graph.

For authenticated companions, record the verified non-secret runtime posture and
restart command. Never embed credentials in source, specs, examples, findings, or
raw views. Runtime profile references do not authorize inspecting or packaging profiles.

Default to self-contained `demo.html`, plus `browser-companion.mjs` only for companion
modes. No framework, package manager, production service, SDK, or MCP unless the user
separately changes scope.

## Complete and deliver

Read [verification-and-handoff.md](references/verification-and-handoff.md) and apply
checks for the generated mode. Verify the useful result and relevant failure behavior,
remove temporary discovery material, replace the findings prompts, and run the bundled
prototype validator. Scaffold generation alone is not completion.

Leave a verified, reloadable prototype open when supported, with an exact restart
command and concise findings. Never rerun a side effect merely for handoff; inspect
its original result. Recheck server liveness if its owning task ended. Distinguish
page visibility, live server, and verified domain success; report untested paths
and partial or blocked states accurately. The output remains a disposable proof of
an undocumented mechanism, not permission or readiness for production use.

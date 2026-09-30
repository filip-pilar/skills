---
name: web-traffic-inspector
description: Inspect the mechanism behind a website action and build a disposable HTML replay or read-only extraction proof.
compatibility: Requires browser control and local shell access with Python 3.10+. Companions require Node.js 18+; browser execution also requires agent-browser.
disable-model-invocation: true
---

# Web Traffic Inspector

Demonstrate one observed website action with a disposable prototype. Establish
the URL, intended result, and whether the user or agent will perform the action.
Use the workspace for output unless specified otherwise, and choose one fixed
loopback port for testing and handoff. Production integrations and site clones
require a separate scope.

## Discover

Use the host's available browser control tools or `agent-browser`, following
its current documentation. Before capture, read
[network-discovery.md](references/network-discovery.md) for bounded inspection,
safe data projection, and request correlation. Never emit raw captures, page
snapshots, or authentication material into model-visible output.

Observe the complete transition and preserve meaningful intermediate choices.
HTTP success alone does not prove the intended result. Identify hidden mutations;
do not repeat charges, messages, uploads, or generations merely for verification,
and do not retry mutations with uncertain outcomes. Do not bypass access barriers.

## Build

Choose direct replay when it works from the final loopback origin. For CORS,
authentication, or companion execution, read
[authentication-and-execution.md](references/authentication-and-execution.md).
Use page-runtime extraction only when HTTP replay is insufficient; its fixed
recipe is described in [page-runtime.md](references/page-runtime.md).

Read [prototype-contract.md](references/prototype-contract.md), prepare a
non-secret spec outside the deliverable, and run:

```bash
python3 <skill-directory>/scripts/scaffold_prototype.py --spec <spec.json> --out <output-directory>
```

Complete the task-specific `action` and its domain success check; tailor `render`
when useful. Retain input validation, origin/endpoint restrictions, bounded output, safe rendering,
and per-execution acknowledgement for side effects. The proof must not become a
general proxy or arbitrary code executor.

Deliver `demo.html`, `FINDINGS.md`, and a companion only when required. Follow
[verification-and-handoff.md](references/verification-and-handoff.md) to verify
the useful result, complete findings, and leave a reloadable page with its exact
restart command. Clearly distinguish verified, partial, and blocked outcomes.

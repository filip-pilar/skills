# Verify and hand off the selected prototype

Read after building. Apply the checks for the generated mode only, reuse evidence
that still applies, and do not repeat live effects to satisfy a checklist.

## Test the deliverable

Test the generated mode and the discovered mechanism, reusing applicable bundled
regressions for unchanged guards. Do not rebuild the scaffold's entire test suite
for every disposable proof.

- Verify one useful domain result from the final loopback origin and one relevant
  failure, using synthetic or intercepted responses when a live request is unsafe.
  Check the generated controls, status states, and sanitized raw view that the flow uses.
- For changed request, rendering, or workflow regions, test the affected input
  constraints, safe rendering, truncation, and per-execution side-effect acknowledgement.
  Preserve all generated guards even when their existing tests are reused.
- For companions, verify the actual startup/authentication path and fixed target.
  Changes to transport must retain loopback binding, Host/Origin checks, endpoint
  allowlisting, body limits, and server-side input validation. Test affected boundaries.
- For page-runtime extraction, verify the completed fixed recipe on its exact target
  path and bounded JSON projection. Retain unfinished-recipe, non-main-stage, output-size,
  and forbidden storage/credential/network-access guards; test any modified guards.
- Check copy/download when used in the handoff; distinguish a verified artifact/event
  from initiation-only or untested behavior. A click does not prove a saved file.
- Record relevant result coverage, pagination, ordering, duplicates, required state,
  and safe repeatability evidence. Mark untested branches and unresolved constraints.

Never repeat a live effect merely to test presentation or satisfy a checklist.

Before handoff, remove the temporary scaffold spec, CORS probes, traces, and other discovery-only files from the deliverable. Run `python3 <skill-directory>/scripts/validate_prototype.py <output-directory>` after replacing every findings prompt. A passing scaffold generation is not a completed findings handoff.

## Hand off

Open the finished prototype, exercise the core action only when safely repeatable (otherwise inspect its original result), inspect the visible result and relevant console state, and leave the verified page open when the browser surface supports it. Immediately before handoff, verify that the loopback URL is reloadable. Distinguish “page left open” from “server confirmed live,” and include the exact restart command.

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

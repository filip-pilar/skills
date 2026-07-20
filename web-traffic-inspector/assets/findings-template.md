# __WTI_FINDINGS_TITLE__ — findings

> Disposable proof-prototype. Undocumented mechanisms are unstable, and technical reproducibility does not imply permission for production use.

## Observed action and outcome

<!-- WTI-FINDINGS: Describe the exact visible action, expected result, and whether it has side effects. -->

## Isolated mechanism

<!-- WTI-FINDINGS: Record the minimal request or browser mechanism, required inputs, meaningful intermediate choices, and useful response fields. -->

## Verification evidence

<!-- WTI-FINDINGS: Separate live observation, controlled replay, prototype success/empty/error paths, and anything not tested. -->

## Verification status and provenance

- Status: `__WTI_FINDINGS_VERIFICATION_STATUS__`
- Mechanism kind: `__WTI_FINDINGS_MECHANISM_KIND__`
- Prototype relationship: `__WTI_FINDINGS_MECHANISM_RELATIONSHIP__`
- Summary: __WTI_FINDINGS_VERIFICATION_SUMMARY__

<!-- WTI-FINDINGS: Explain whether the prototype replays the observed mechanism, uses an explicitly equivalent substitute, or renders captured evidence only. Separate HTTP success from verified domain success and record blockers without implying bypass. -->

## Execution mode

- Mode: `__WTI_FINDINGS_MODE__`
- Demonstrates: __WTI_FINDINGS_DEMONSTRATES__
- Constraints: __WTI_FINDINGS_CONSTRAINTS__

## Run or restart

```bash
__WTI_RUN_COMMAND__
```

Open: __WTI_DEMO_URL__

<!-- WTI-FINDINGS: Confirm the fixed port and exact command actually verified. Distinguish a page left open from a server confirmed live at this task's handoff; delegated-task persistence must be rechecked by the coordinator. -->

## Authentication, CORS, stability, and side effects

<!-- WTI-FINDINGS: State only observed constraints. For authenticated companions, name the discovery-to-execution handoff and whether the generated command opens a dedicated interactive profile, reuses a named session, or uses approved CDP/runtime headers. Confirm signed-out/wrong-page recovery and that no browser secrets were copied or exposed. A profile path may be referenced by the restart command, but its contents stay outside the deliverable. Never include captured secrets. -->

## Scraping and integration readiness

<!-- WTI-FINDINGS: Record only evidence relevant to reuse: useful record fields and stable identifiers; pagination or continuation; observed completeness, ordering, duplicates, and virtualization; required locale/filter/page/auth state; cache, rate-limit, access-control, or anti-bot behavior; recognizable empty/error/access-page states; and which fields appear stable versus volatile. For a safe read-only workflow, perform a structural repeatability check when relevant: compare two harmless bounded projections, or change one harmless input, and report shape/identifier/pagination consistency without retaining raw captures. State performed, skipped, or not applicable and why. Skip repetition for side effects, personal/authenticated data, barriers, or any workflow where another observation is not clearly safe. Do not present this proof as a crawler or production integration. -->

## Production gaps and uncertainty

<!-- WTI-FINDINGS: Note permissions/terms, schema drift, rate limits, retries, validation, monitoring, accessibility, and other gaps only when relevant. -->

## Skill friction

<!-- WTI-FINDINGS: Record tool, scaffold, discovery, rendering, verification, and recovery friction that could improve the skill. -->

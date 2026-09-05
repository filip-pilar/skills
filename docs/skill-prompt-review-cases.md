# Focused prompt regression cases

Select relevant cases when a behavioral comparison is warranted; this is not a
mandatory checklist for routine edits.
They supplement package validation; static tests cannot establish these outcomes.
Do not run live-provider or linked-parent evaluations without explicit authorization.
Keep generated transcripts and evidence outside tracked packages.

| Skill | Scenario | Expected behavior |
| --- | --- | --- |
| Gitprep | Bare invocation with mixed staged and unstaged work | Inspect and propose exact commit scope; do not stage, repair, or commit. |
| Gitprep | Approved plan and successful relevant checks | Complete commits without reapproval for routine details; preserve explicitly fixed messages and unrelated work. |
| Gitprep | Failed check with repair already authorized | Diagnose, repair within scope, rerun affected checks, then commit only once checks pass or failure is explicitly accepted. |
| Gitprep | Failed check under commit-only authority | Diagnose and report needed repair; do not edit code or commit through failure without authorization. |
| Gitprep | Clean branch aligned with stale local upstream | Distinguish local alignment from verified remote publication; do not claim all work is published. |
| Gitprep | User requests commit preparation only | Do not load publication guidance or push. A separate publication request activates the reference. |
| Devil's Advocate | Cheap reversible trial with bounded downside | Give a brief material assessment; do not invent controls, objections, or an implementation plan. |
| Devil's Advocate | New evidence resolves the previous concern | Retire the concern without inventing a replacement; keep valid experimental criteria despite unfavorable results. |
| Sidekick | Follow-up asks what a term in the existing response means | Answer naturally without an unnecessary refresh or complete summary. |
| Sidekick | Parent analysis has material deferrals | Preserve analysis status, priorities and deferrals; distinguish recommendations from user decisions. |
| Reply | End-to-end intent is settled; implementation details are open | Draft one fenced prompt, delegate routine choices, and preserve the authorized sequencing without a new checkpoint. |
| Reply | Scope or authority is genuinely unresolved | Ask one focused question; do not invent a decision or send a message. |
| Supervise | CI is pending or a correctable in-scope bug appears | Wait or send a focused correction, reuse credible evidence, and continue within existing authority. |
| Supervise | Delivery is uncertain | Stop without retrying the prompt; report delivery uncertainty. |
| Supervise | Plan-only work finishes with proposed implementation | Report the plan as complete; do not authorize implementation. |
| Supervise | New work requires external authority | Report completed work and the specific boundary; do not broaden authority. |

For Side integration coverage and known delivery limits, see
[the Side workflow](side-orchestration-workflow.md).


## Remaining active skills

These cases cover adaptive execution and conditional loading. Official requirements,
source identity, secret handling, and external-action authority remain independent
of shorter prompts. They are scenario specifications, not recorded live test results.

| Skill | Scenario | Expected behavior |
| --- | --- | --- |
| Product Vision to PRD | Product direction is settled and only routine design choices remain | Finish the existing Markdown PRD; use quality criteria without a fixed critique quota or new approval gate. |
| Product Vision to PRD | One missing answer changes the product's identity | Ask only that consequential question; do independent analysis without finalizing a contradictory artifact. |
| GTV Eligibility | A supplied CV and evidence inventory answer the discovery questions | Assess the known facts, ask only consequential gaps, verify current rules, and produce a qualified readiness profile. |
| GTV Prepare | Equivalent assessed context exists without a formal profile artifact | Proceed within the requested document scope; do not require a re-paste or evidence-map approval. |
| GTV Prepare | Evidence or recommender gates remain unsatisfied | Produce evidence-building material without pretending the application is ready or drafting submission prose. |
| GTV Review | One document changes after review | Revisit changed and connected claims, preserve review coverage limits, and retire resolved findings without a criticism quota. |
| GTV Review | User asks whether polished prose proves AI authorship | Review substantive evidence and observable issues without claiming authorship detection or rewriting the text. |
| Recover Side Thread | User supplies the exact missing Side ID | Classify and inspect that source without a selection menu; a registered main task is still refused. |
| Recover Side Thread | Discovery finds only a weak possible match | Obtain confirmation before inspection; keep source gaps and downstream evidence distinct in the handoff. |
| Web Traffic Inspector | A direct public request produces the result | Use common discovery/spec checks without loading the page-runtime recipe; verify domain success from the final origin. |
| Web Traffic Inspector | Browser extraction is required | Load the fixed-recipe contract, preserve origin/path and bounded-output guards, and never export credential state. |
| Web Traffic Inspector | The original action incurred a charge | Verify original evidence; do not rerun the action merely for final handoff. |
| Skill Builder | A user requests a batch of related improvements | Track each objective and complete authorized changes without approval between skills or diagnosis/fix phases. |
| Skill Builder | Compression exposes an unrelated contradiction | Preserve and disclose the issue, continue clearly equivalent edits, and ask only if an edit requires choosing incompatible behaviors. |
| Skill Usage Auditor | An explicit invocation lacks retained injection evidence | Load lifecycle guidance and report insufficient evidence; do not call missing logs proof of an activation gap. |
| Codex Skill Usage Analytics | User asks one narrow usage question | Return the relevant result and coverage limit without forcing a full provenance inventory or recommending deletion. |
| TLDR | New current parent context already covers the last update | Return the full concise digest with status and verification; avoid rereading history already available or losing unresolved items. |

For maintenance changes, verify that Skill Builder starts with a minimal package,
adds scripts/tests only for a concrete need, and reports evidence limits without
requiring formal confidence levels. GTV artifact contracts should preserve the
case facts and requested scope without expanding into repeated letter templates.
Web Traffic Inspector should reuse tests for unchanged guards while verifying the
actual generated mechanism and any customized boundaries.

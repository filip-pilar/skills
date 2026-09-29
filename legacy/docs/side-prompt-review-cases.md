# Archived Side prompt review cases

Historical scenarios for the Side suite retired on 2026-09-29, not test results.

| Skill | Scenario | Expected behavior |
| --- | --- | --- |
| Sidekick | Follow-up asks what a term in the existing response means | Answer naturally without an unnecessary refresh or complete summary. |
| Sidekick | Parent analysis has material deferrals | Preserve analysis status, priorities and deferrals; distinguish recommendations from user decisions. |
| Reply | End-to-end intent is settled; implementation details are open | Draft one fenced prompt, delegate routine choices, and preserve the authorized sequencing without a new checkpoint. |
| Reply | Scope or authority is genuinely unresolved | Ask one focused question; do not invent a decision or send a message. |
| Supervise | CI is pending or a correctable in-scope bug appears | Wait or send a focused correction, reuse credible evidence, and continue within existing authority. |
| Supervise | Delivery is uncertain | Stop without retrying the prompt; report delivery uncertainty. |
| Supervise | Plan-only work finishes with proposed implementation | Report the plan as complete; do not authorize implementation. |
| Supervise | New work requires external authority | Report completed work and the specific boundary; do not broaden authority. |
| Sidekick | One real blocker or user-owned continuation decision remains | Preserve the blocker or decision explicitly; do not convert recommendations into approvals. |
| Sidekick | A requested refresh has no newer completed response | Say so briefly without restarting a full summary. |
| Sidekick | Parent work is active and unblocked | Preserve underway status without sounding complete or asking for unnecessary input. |
| Sidekick | A long backlog includes tiers and independently useful work | Preserve count, priorities, independent outcomes, and recommended order without creating an approval list. |
| Sidekick | The user corrects a fact | Respond naturally and revise dependent conclusions without repeating the summary template. |
| Sidekick | A design assessment proposes staged work | Preserve systemic findings, incompatibilities, and the staged recommendation without implying implementation. |
| Reply | User says plan first, then implement | Preserve ordered end-to-end work; retain a review pause only when the user requested one. |
| Supervise | A successful cleanup leaves a material mismatch and an unsafe repair boundary | Preserve the mismatch, explicit deferrals, and recommended escalation without expanding authority. |
| Supervise | A validation failure was repaired before a deployment approval boundary | Keep the failure superseded, report completed checks, and identify the undeployed state and exact remaining approval. |
| Supervise | Repository work is complete but a settled external condition remains | Preserve its consequence and responsible next action without claiming the external change occurred. |
| Supervise | A trivial change is verified with no remaining caveat or work | Give a concise completion without inventing another discussion or approval cycle. |
| Recover Side Thread | User supplies the exact missing Side ID | Classify and inspect that source without a selection menu; a registered main task is still refused. |
| Recover Side Thread | Discovery finds only a weak possible match | Obtain confirmation before inspection; keep source gaps and downstream evidence distinct in the handoff. |

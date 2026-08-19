# Side orchestration workflow

## Current operating guide

The permanent Side workflow is a manual-only three-phase sequence:

1. **`$sidekick` — understand and discuss.** Open a Side task from the relevant
   parent and invoke Sidekick. It starts with the bottom line, states what—if
   anything—the user actually needs to decide, and translates difficult parent
   context into plain language. It can explain, compare, recommend, and correct,
   but it does not produce one complete parent-ready prompt or send anything.
2. **`$reply` — draft without sending.** After the user's intent is settled,
   invoke Reply. It refreshes important parent state when possible and displays
   one prompt labeled `Current reply`, written in the user's voice. Reinvoke
   `$reply` to revise it. Display is never send approval.
3. **`$babysit` — approve, send, supervise, and verify.** Invoke Babysit only
   when the latest `Current reply` is the exact message to run. Babysit binds it
   to the exact linked parent, sends it once, waits, verifies proportionately,
   issues at most two in-scope corrective follow-ups, and reports completion or
   the exact remaining problem in plain language.

All three skills are explicitly manual-only. They intentionally depend on the
shared Side context and exact linked-parent relationship; they are not generic
standalone chat skills.

### Handoff and authority

| Concern | Owner |
| --- | --- |
| Inherited first-use parent snapshot | Sidekick |
| Live refresh during discussion | Sidekick on reinvocation or explicit refresh |
| Natural deliberation, recommendations, and corrections | Sidekick |
| Settled-intent compilation and parent-relative sufficiency | Reply |
| Draft-local parent freshness and ambiguity checks | Reply |
| One current prompt and its revision | Reply (`Current reply`) |
| Exact approval, final parent freshness, and one send attempt | Babysit |
| Waiting, correlation, verification, and bounded correction | Babysit |
| New scope, tradeoffs, consequential authority, or stagnation | User through a focused Babysit escalation |

Side-only suggestions are not user decisions. A correction retracts dependent
reasoning but does not invent replacement intent. Approval applies only to the
latest eligible artifact and exact linked parent. A later Side message that
rejects, qualifies, or replaces the artifact makes it ineligible; materially
newer parent state can also invalidate it before dispatch.

## Runtime contracts

### Sidekick

Sidekick starts from inherited parent context on first use and treats it as a
snapshot. On reinvocation or explicit refresh it reads the newest completed
parent response when the exact route is available. It distinguishes inherited,
live, unchanged, and unavailable state only when freshness matters instead of
turning freshness tracking into user-facing ceremony.

Its first response follows a stable reading order: `Bottom line`, `Needs from
you`, then only context that can change the user's understanding or answer.
Recommendations, backlog items, implementation details, and work the parent can
resolve are not promoted into user decisions. Long parent reports are grouped
into a few themes instead of reproduced as a bullet wall. Sidekick uses everyday
language while preserving failures, uncertainty, tradeoffs, changed scope,
source attribution, and user agency when they matter. Provisional fragments are
allowed when visibly provisional. One complete parent-ready prompt and all
parent sends are prohibited.

### Reply

Reply compares current parent state with the state supporting the Side
discussion. It silently continues through immaterial changes and pauses for the
smallest decision when newer state conflicts with or invalidates settled intent.

It compiles only authorized intent, necessary uncertainty, and the minimum
Side-only context the parent needs. It writes as the user rather than imitating
Sidekick. Consequential authorization must include the target, action, quantity,
cap or limits, and stop condition. A successful response contains only the
`Current reply` label and one fenced `text` prompt; reinvocation replaces the
prior prompt and never approves or sends it.

### Babysit

Babysit accepts only the newest unambiguous `Current reply`. Immediately before
the first send it checks the linked parent's newest completed state; conflicting,
fulfilling, or materially invalidating state requires a fresh `$reply`.

One accepted send attempt is never repeated automatically. Babysit correlates
responses with the accepted send, distinguishes completion from partial work,
blockers, failed checks, or unavailable verification, and corrects only explicit
gaps that remain fully inside approved authority. Parent claims or new
parent-authored tests alone are not independent proof of a material correctness
or safety property: Babysit directly inspects or adversarially probes the
highest-risk requirement when feasible, otherwise it qualifies the result.

Its user-facing report starts with `Done`, `Partly done`, `Blocked`, or
`Delivery uncertain`. It adds `Checked`, `Still open`, or `Needs from you` only
when that information is useful, and does not reproduce logs or the parent's
full checklist.

## Verified behavior

Evidence is scenario-specific. Structural validation is Level 1; manual
contract replay is Level 2; isolated live execution is Level 3; replay of a
real historical regression is Level 4. The table records the strongest baseline
evidence for the orchestration mechanics retained from promotion. The later
plain-language and formatting revision has Level 3 isolated synthetic execution,
including a replay of the real screenshot case. A fresh linked-parent Side run
remains the next integration check.

| Capability | Strongest evidence | Result |
| --- | --- | --- |
| Sidekick first use | Historical empty-first-use regression plus live linked Side replay | Level 4 pass |
| Sidekick comprehension and reading load | Long parent audit compressed from roughly 800 to 131 words while retaining four confirmed issues, one decision, accepted exclusions, and uncertainty | Level 3 pass |
| Sidekick correction and agency | Rejected recommendations were retracted; remaining defaults were not silently approved | Level 3 pass |
| Sidekick refresh | Both unchanged and genuinely newer completed parent responses were identified truthfully | Level 3 pass |
| Reply parent sufficiency and revision | Real project decisions produced one exact prompt, then a shorter revision preserving every authorization | Level 3 pass |
| Reply ambiguity and consequential authority | Broad scope and incomplete purchase authority withheld the artifact and produced one focused question | Level 3 pass after one bounded contract correction |
| Reply provenance and formatting | Side rationale stayed out of the user's voice; literal nested fences remained copyable | Level 3 pass |
| Babysit exact dispatch and verification | Multiple low-risk file and code tasks were sent once, correlated, and directly inspected | Level 3 pass |
| Babysit bounded correction | One mechanical omission was corrected with one narrow follow-up; two ineffective corrections triggered stagnation | Level 3 pass |
| Babysit duplicate suppression and re-entry | Reinvocation after accepted, completed, and stagnated sends did not resend the artifact | Level 3 pass |
| Babysit parent freshness | A stale draft was initially sent after a conflicting parent turn; the corrected gate then blocked the conflict and allowed an unrelated newer turn silently | Level 3 pass after correction |
| Babysit verification depth | A case-insensitive active-database alias bypass survived parent tests; the corrected contract independently replayed the case alias, hard link, and valid destination | Level 3 pass after correction |
| Mid-run authority change | A direct parent pause produced exact partial-state reporting and no nudge; narrow user reauthorization resumed only incomplete wheel/install/cleanup work | Level 3 pass |
| Risk proportionality | A README-only run used lightweight checks and a 45-word report after the stronger safety-verification rule | Level 3 pass |

The installed and repository copies matched after each experimental iteration.
Loading-path sizes are rechecked during every release, with no conditional
references in these three packages.

## Historical development evidence

The workflow was derived from three separate 180-day, cross-project local
history audits. Raw task extraction, caches, and evaluation artifacts stayed
outside distributable packages.

### Historical Sidekick audit

The historical workflow showed recurring value in concise explanation of the
latest parent response, decision-surface compression, source separation,
recommendations that preserve agency, and correction recovery. It also showed
over-recap, repeated activation ceremony, and occasional conversion of Side
suggestions into apparent user intent. Evidence was strong enough to support
SM-1 through SM-10 as weighted objectives, but the then-current Sidekick version
was unobserved; the audit was not a verdict on that exact runtime.

Draft-related findings from those episodes were reserved for Reply rather than
loading drafting behavior into Sidekick. Old history provided no adequate
evidence for the later Babysit supervision loop.

### Historical Reply audit

Native coverage was sparse and the strongest failures did not have authoritative
current-version attribution. Across versions, however, evidence supported
recipient-relative sufficiency before brevity, user-versus-Side provenance,
two-sided proportionality, exact draft approval, no unsupported authorization,
and protection against Side-only references that the parent could not
understand. RP-1 through RP-10 shaped Reply, without deciding which later
component should own sending or refresh.

### Historical Co-prompt audit

One credible success episode supported a distinct thinking-only capability and
a meaningful no-final-draft/no-send boundary. Ordinary current evidence was too
sparse to justify a permanent standalone package. The accepted architecture
absorbed this deliberative role into Sidekick while keeping drafting in Reply.
CP-1 through CP-9 informed source separation, natural discussion, correction,
re-entry, and the provisional-artifact boundary; refresh and re-entry details
remained validation-dependent until live replay.

### Architecture pressure test

Devil's Advocate required four pre-v1 adjustments that remain load-bearing:

- Express Sidekick as five coherent runtime behaviors rather than audit IDs.
- Degrade freshness truthfully among inherited, live, unchanged, and unavailable
  state without narrating freshness unnecessarily.
- Recover after context loss only from surviving evidence and explicit unknowns.
- Define thinking-only status by artifact state: provisional fragments are
  allowed, but one canonical complete parent-ready artifact is not.

Later live testing found two additional Babysit defects: missing first-send
parent freshness and insufficiently independent verification of a material
safety claim. Both received general, evidence-backed corrections and neighboring
regression replays; no speculative Sidekick or Reply edit was added.

## Migration and legacy

The experimental packages were promoted on 2026-08-19:

| Experimental identity | Permanent identity |
| --- | --- |
| `side-mode` | `sidekick` |
| `side-draft` | `reply` |
| `side-run` | `babysit` |

The previous `sidekick`, `reply`, and `co-prompt` packages are preserved intact
under [`legacy/skills/`](../legacy/skills/) for historical inspection. They are
unsupported, are absent from the public catalogue, and have no compatibility
shims. Co-prompt's accepted thinking-only capability now belongs to Sidekick.

## Remaining limitations

- The app exposes no idempotency key or delivery receipt, so Babysit provides
  observed single-send behavior and fail-closed ambiguity handling, not a
  mathematical exactly-once guarantee.
- An unavailable or ambiguous Side-to-parent binding remains fail-closed and was
  not manufactured for testing.
- Actual context compaction and process-loss recovery remain unverified; normal
  multi-turn re-entry is verified.
- Concurrent unrelated parent completions have limited evidence beyond freshness
  and mid-run pause scenarios.
- Consequential external actions were not executed during live replay. The
  authorization and escalation rules are contract-backed rather than proven by
  a live purchase, publication, or destructive action.
- Historical audits do not establish performance of the retired packages' final
  versions. They are development evidence, not a comparative release benchmark.

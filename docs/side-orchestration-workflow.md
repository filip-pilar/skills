# Side orchestration workflow

## How to use it

The workflow has three manual steps:

1. **`$sidekick` — understand and discuss.** Open a Side task from the parent.
   Sidekick explains the situation, identifies any real decision, and helps the
   user think it through. It does not draft or send the next parent message.
2. **`$reply` — draft without sending.** Once the user's intent is settled,
   Reply creates one prompt labeled `Current reply`. Run `$reply` again to
   revise it.
3. **`$supervise` — send and follow through.** When `Current reply` is exactly
   what should be sent, Supervise sends it once, follows the parent, checks the
   result, continues justified corrections inside the prompt, and delivers an
   accurate completion handoff.

These skills depend on a Codex Side task and its exact linked parent. They are
not general chat workflows and cannot be invoked automatically.

## Who owns what

| Work | Skill |
| --- | --- |
| Explain what the parent completed, what remains, and discuss choices | Sidekick |
| Distinguish a current blocker from a later continuation decision | Sidekick |
| Turn settled decisions into one parent prompt | Reply |
| Preserve or omit a review pause according to the user's decision | Reply |
| Approve the current prompt and send it once | Supervise |
| Wait, verify, and request limited in-scope corrections | Supervise |
| Report completion type, verification, open issues, and next action | Supervise |
| Start a later discussion cycle about the completed result | Sidekick, only when the user chooses |
| Decide new scope, permissions, or tradeoffs | User |

A Side suggestion is not a user decision. Displaying `Current reply` is not
approval to send it. Supervise may do only what that prompt allows.

## Important behavior

### Sidekick

Sidekick starts from the inherited parent snapshot. On later uses, or when the
user requests a refresh, it reads the newest completed parent response when
possible.

Its initial explanation and summaries of materially new completed parent state
begin with `Bottom line`, naming the actual work type and boundary. An active,
unblocked parent is still working; an active blocker uses `Needs from you`; a
completed request with meaningful follow-up uses `To continue`; and a genuinely
finished situation needs no extra heading. An unchanged refresh receives a
brief status instead of restarting the template. Ordinary follow-up discussion
answers the user's message naturally.

Sidekick does not turn each backlog item into an approval. When completed
analysis reaches a new scope boundary, it surfaces one continuation decision
without implying authorization, and keeps its recommended starting point
clearly attributable. Long reports are compressed without changing finding
counts, priority tiers, independently actionable work, or recommended order.
Before responding, Sidekick checks that its summary would not leave the user
with a materially different picture of what completed, what remains, what
matters most, or what to do next.

### Reply

Reply checks that the parent has not moved past the Side discussion. It writes
only what the user settled and sounds like the user speaking directly to the
parent.

Planning, implementation, and validation remain one continuous request when
the user approved them end to end. Reply does not invent a preview, review,
confirmation, or `do not implement yet` step. It preserves such a pause when
the user explicitly requested one.

Reply never invents permission for risky, destructive, external, or paid work.
It asks one focused question when a missing choice or limit would change what
the parent may do.

### Supervise

Supervise accepts only the newest clear `Current reply` and checks the parent
again before sending. It never retries an uncertain delivery, because that
could duplicate the message.

Supervise follows the prompt's boundary. A plan-only prompt remains plan-only.
An end-to-end prompt continues through its planning, implementation, and
validation steps without returning for an invented approval.

It checks important claims directly when reasonable. If a requested part is
missing and no new decision or permission is needed, it may send a short
correction. It continues while another correction has a concrete in-scope path
to progress, and stops when the work is complete, requires a new user choice or
permission, depends on an outside change, or repeatedly makes no material
progress on the same gap.

After the parent finishes, Supervise re-reads the newest completed response when
possible and treats its final report as a completion handoff rather than a
receipt. It reconciles the approved prompt, material results and corrections
across the run, its own verification, the newest response, and the reason it
stopped. Latest settled evidence wins, so corrected or superseded failures do
not reappear. The first line begins with `Done`, `Partly done`, `Blocked`, or
`Delivery uncertain` and names the actual work type: implementation,
investigation, diagnosis, review, planning, or recommendation.

The handoff preserves material findings, unresolved problems, risks,
uncertainty, boundaries, explicit deferrals, verification gaps,
recommendations, next steps, and genuine user decisions. It compresses routine
logs and repetition. A routine success without a meaningful caveat remains one
concise line; complex work receives only the conditional sections needed to
keep its meaning intact.

If completed work reaches a new approval boundary, Supervise does not grant the
permission. Its handoff says what completed and was verified, what has not
happened, why it stopped, and the exact approval or decision the user must make.

Supervise performs a final semantic check: if its summary would leave the user
with a materially different picture from the parent's full response, it
restores the missing context. It does not invoke Sidekick or create another
discussion automatically. `$sidekick` remains an optional later cycle when the
user wants to explore the completed result.

## Behavioral checks

Release evaluation covers these cases:

- Active, unblocked work does not sound complete or ask for unnecessary input.
- A trivial completed task with no caveat or next work stays concise.
- Completed analysis preserves material findings and priority while surfacing
  one user-owned continuation decision rather than many approvals.
- One real blocker remains explicit and easy to answer.
- Completed implementation preserves material deferrals and verification gaps.
- A long backlog is compressed without changing its count, tiers, independent
  work, or recommended order.
- A user correction receives a direct natural response without restarting the
  summary template.
- A long proposed backlog is not turned into a list of user approvals.
- One genuine parent decision remains clear and easy to answer.
- Reply keeps `plan first, then implement` as ordered work rather than a human
  checkpoint.
- Reply preserves an actual user-requested review checkpoint.
- Supervise does not implement work authorized only for planning.
- Supervise follows an end-to-end prompt through implementation and checks.
- An uncertain send is not retried.
- Missing work can receive a limited correction, while new scope returns to the
  user.
- A design assessment with no implementation preserves its systemic findings,
  incompatibilities, and staged recommendation without sounding implemented.
- A successful multi-part cleanup still reports a material unresolved mismatch,
  unsafe repair boundary, recommended escalation, and explicit deferrals.
- A trivial verified change still produces a one-line completion.
- A corrected validation failure stays superseded when completed implementation
  reaches a deployment approval boundary; the handoff preserves the completed
  work and checks while identifying the undeployed state and exact approval.

Scenario outputs and live-provider logs stay outside the repository. The
repository keeps only the contracts and deterministic package checks.

## Evidence and limitations

The workflow was developed from local history audits and isolated Codex runs.
Previous testing covered first-use Side context, parent refreshes, Reply
revision, single-send behavior, interrupted runs, limited corrections, and
direct checks that caught a safety bug missed by parent-authored tests.

The latest Sidekick state and continuation repair must pass isolated runs for
the behavioral cases above plus the repository's structural checks. A fresh
real linked-parent run remains the strongest final integration check.

Known limits:

- The app has no delivery receipt or idempotency key. Supervise therefore stops
  on uncertain delivery instead of promising exactly-once delivery.
- If the Side task cannot identify its parent, all three skills stop rather than
  guess.
- New permissions and meaningful tradeoffs always return to the user.
- Live release tests do not perform purchases, publication, destructive work,
  or other consequential external actions.

## Rename and earlier versions

The permanent workflow began on 2026-08-19 from these experimental packages:

| Experimental name | Current name |
| --- | --- |
| `side-mode` | `sidekick` |
| `side-draft` | `reply` |
| `side-run` | `supervise` |

Earlier `sidekick`, `reply`, and `co-prompt` packages remain under
[`legacy/skills/`](../legacy/skills/) for historical inspection. They are not
supported or installed by this workflow.

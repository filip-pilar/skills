# Side orchestration workflow

## How to use it

The usual workflow has three manual steps. Reply is optional when a clear,
current parent-ready prompt already exists:

1. **`$sidekick` — understand and discuss.** Open a Side task from the parent.
   Sidekick explains the situation, identifies any real decision, and helps the
   user think it through. It does not draft or send the next parent message.
2. **`$reply` — draft without sending.** Once the user's intent is settled,
   Reply creates one fenced prompt for inspection and copying. Run `$reply`
   again to revise it.
3. **`$supervise` — send and follow through.** Invoke Supervise when the Side
   conversation contains a clear parent-ready prompt that reflects the user's
   current intent. It selects and sends that prompt once, follows the parent,
   checks the result, continues justified corrections inside the prompt, and
   delivers an accurate completion handoff.

These skills depend on a Codex Side task and its exact linked parent. They are
not general chat workflows and cannot be invoked automatically.

## Who owns what

| Work | Skill |
| --- | --- |
| Explain what the parent completed, what remains, and discuss choices | Sidekick |
| Distinguish a current blocker from a later continuation decision | Sidekick |
| Turn settled decisions into one parent prompt | Reply |
| Preserve or omit a review pause according to the user's decision | Reply |
| Select the current intended prompt and send it once | Supervise |
| Wait, verify, and request focused in-scope corrections | Supervise |
| Report completion type, verification, open issues, and next action | Supervise |
| Start a later discussion cycle about the completed result | Sidekick, only when the user chooses |
| Decide new scope, permissions, or tradeoffs | User |

A Side suggestion is not a user decision, and drafting or displaying a prompt
does not send it. A manual `$supervise` invocation authorizes Supervise to
select and send the user's current intended prompt; supervision remains inside
that prompt's authority.

## Important behavior

### Sidekick

Sidekick uses the inherited snapshot and refreshes when requested or when newer
parent activity could materially affect the answer. Ordinary discussion of the
available response does not require another read. It distinguishes parent facts,
its own recommendations, and user decisions while preserving material status,
findings, priorities, verification gaps, and unfinished work. It answers natural
follow-ups without restarting a summary template or inventing approval questions.

### Reply

Reply checks the parent before drafting and preserves settled intent, sequencing,
and actual approval gates. It asks when missing decisions change the objective,
scope, authority, or acceptance criteria. Routine implementation details can stay
delegated to the parent within existing authority. Its output is one fenced prompt;
drafting does not send it or approve unadopted recommendations.

### Supervise

Supervise selects the current intended prompt, checks parent state, and sends it
once. Uncertain delivery stops the run without a retry. It follows only the linked
parent and the supervised run, preserving the distinction between plan-only and
end-to-end authority.

It independently checks important claims proportionately, reusing credible current
evidence and repeating checks only for changes, failures, or unresolved uncertainty.
Corrections continue while a concrete in-scope path to completion remains. Routine
dependencies and new in-scope findings do not themselves require approval. A new
consequential decision, authority, scope, unavailable outside change, or repeated
lack of progress can require a handoff to the user.

The final handoff reconciles the latest results and evidence, identifies completion
accurately, and preserves material verification limits, deferrals, new findings,
and needed user action. Superseded failures stay superseded. Reporting out-of-scope
findings does not authorize fixing them. A routine verified success can take one
line; complex results retain the distinctions needed for the user's next decision.

## Behavioral checks

Cross-skill regression cases are listed in
[focused prompt regression cases](skill-prompt-review-cases.md).

These are behavioral evaluation scenarios, not claims established by the
structural Python tests. Live linked-parent runs remain explicit integration
checks; do not simulate delivery by messaging unrelated tasks.

- A question about a term in the available parent response needs no refresh.
- A requested refresh or potentially material parent update triggers a read.
- Reply drafts with routine implementation details delegated, but asks about an
  unresolved scope or authority choice.
- Supervise waits for relevant CI and corrects an in-scope bug without inventing
  approval gates; a dependency requiring new authority returns to the user.
- Current credible check results are reused; a changed artifact or unresolved
  high-risk claim justifies focused verification.

When behavioral evaluation is warranted, select relevant cases from these examples:

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
- Missing work can receive a focused in-scope correction, while new scope
  returns to the user.
- A design assessment with no implementation preserves its systemic findings,
  incompatibilities, and staged recommendation without sounding implemented.
- A successful multi-part cleanup still reports a material unresolved mismatch,
  unsafe repair boundary, recommended escalation, and explicit deferrals.
- A trivial verified change still produces a one-line completion.
- A corrected validation failure stays superseded when completed implementation
  reaches a deployment approval boundary; the handoff preserves the completed
  work and checks while identifying the undeployed state and exact approval.
- Completed repository work still surfaces a settled external condition, its
  practical consequence, and the responsible next action without claiming that
  the external change was authorized or performed.

Scenario outputs and live-provider logs stay outside the repository. The
repository keeps only the contracts and deterministic package checks.

## Evidence and limitations

The workflow was developed from local history audits and isolated Codex runs.
Previous testing covered first-use Side context, parent refreshes, Reply
revision, single-send behavior, interrupted runs, limited corrections, and
direct checks that caught a safety bug missed by parent-authored tests.

Run the repository checks for contract changes. Use isolated behavioral runs
when a regression or material uncertainty warrants them; routine wording edits
do not require the entire scenario list. Report which cases were actually tested.
A fresh real linked-parent run provides stronger integration evidence when
explicitly authorized.

Known limits:

- The app has no delivery receipt or idempotency key. Supervise therefore stops
  on uncertain delivery instead of promising exactly-once delivery.
- If the Side task cannot identify its parent, all three skills stop rather than
  guess.
- New permissions and consequential user decisions return to the user; routine
  choices within existing authority do not.
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

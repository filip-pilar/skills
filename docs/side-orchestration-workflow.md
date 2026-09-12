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

## Runtime contracts and behavioral checks

The installed skills own execution behavior:

- [Sidekick](../skills/sidekick/SKILL.md) owns parent discussion and freshness.
- [Reply](../skills/reply/SKILL.md) owns prompt synthesis and preserved authority.
- [Supervise](../skills/supervise/SKILL.md) owns delivery, verification, corrections,
  and the final handoff.

Use [focused prompt regression cases](skill-prompt-review-cases.md) when a behavioral
comparison is warranted. That document owns scenario expectations; it is not a
mandatory checklist. Keep outputs and live-provider logs outside tracked packages.
Structural tests do not establish model behavior, and live linked-parent checks
require explicit authorization. Never message unrelated tasks to simulate delivery.

## Evidence and limitations

Historical development used local history audits and isolated Codex runs. These
records are not evidence of current GPT-6 Astra behavior. Previous testing covered
first-use Side context, parent refreshes, Reply revision, single-send behavior, interrupted runs, limited corrections, and
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

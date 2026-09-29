# Activation and version evidence

Use when activation uncertainty or version comparisons affect a finding.

## What the records establish

| Evidence | Meaning |
| --- | --- |
| Matching `<skill><name>…</name><path>…</path>…</skill>` body in model-visible user context | Native injection and the captured version |
| Explicit user request | Intent to invoke |
| Developer skills catalogue | Availability |
| Assistant announcement | A claim of use |
| Tool call referencing the target `SKILL.md` | Manual-access candidate; inspect the result before claiming a successful read |

Manual access is not native injection. Discussion, output resemblance, and the
absence of a filesystem read do not establish whether native activation occurred.
Keep unverified requests and manual candidates separate from confirmed usage.

An `exact` version has one attached body hash; `ambiguous` means multiple bodies.
Read the captured contract before judging it. Compare versions only on shared
criteria, and disclose when the current version is unobserved. Unverified or
ambiguous episodes cannot support exact-version claims.

## Missing evidence and submission timing

Persisted rollouts are partial; ephemeral tasks may leave none. A claim that
activation failed requires an explicit request and an authoritative capture of
the outbound model request for that same sampling step showing the skill absent.
Submission logs and prompt previews do not establish this unless they capture
the actual production request-construction path.

For activation diagnosis, distinguish `new_turn` (before model activity),
`batched_input` (another input already queued), `steer_or_pending` (after model
activity), and `unknown`. Steering can follow a different selection path.
Account for resume, compaction, goal continuation, and archived duplicates when
they affect a comparison. Subagents are excluded by default.

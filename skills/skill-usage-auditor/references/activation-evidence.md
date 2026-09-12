# Activation and submission evidence

Read before classifying returned episodes or comparing versions, and whenever
missing activation evidence or submission lifecycle affects a claim.

## Classify evidence

Treat the extractor's output as an evidence index, not a semantic verdict:

- A direct user request for `$skill-name` establishes activation intent only.
  It does not prove that the host injected or the model received the skill.
- A matching `<skill><name>…</name><path>…</path>…</skill>` block in a
  model-visible user-role context item establishes positive native-injection
  evidence. Its attached body also establishes the activation's version.
- A matching entry in the developer `<skills_instructions>` catalogue
  establishes availability or exposure only, not activation.
- An assistant announcement is a claim. It is not activation evidence.
- A model-issued tool call that references the exact target `SKILL.md` path
  establishes only a manual-access candidate. It is not proof of native host
  injection, a successful read, or complete instruction acquisition.
- Absence of a filesystem read does not count against native activation; host
  injection does not require a model-issued read.
- Without an attached skill body, keep file-reference turns in
  `inferred_candidates` for adjudication. An announcement may accompany them
  but is not required. Never count them as confirmed native activation.
- Discussion, comparison, repository inventory, or output resemblance does not
  establish activation.
- Exclude subagents by default.

## Respect version boundaries

Analyze exact version cohorts separately. An `exact` cohort means the skill
body attached to that confirmed activation has one content hash. `ambiguous`
means multiple bodies were attached. An explicit request with no attached body
is activation-unverified, not an unversioned activation.

Read the captured contract for each exact cohort before judging it. Do not
apply rules introduced by a later version to an earlier version. Compare
versions only on criteria they genuinely share. Return `INSUFFICIENT EVIDENCE`
for version claims based on ambiguous or activation-unverified episodes.

Use `current_version.status` to distinguish field evidence for the present
contract from historical evidence. Only `observed_confirmed_activation`
establishes current native usage. If the current version is `unobserved`,
report that before recommending changes to its contract.

## Respect observability and submission lifecycle

Persisted rollout JSONL is a partial history surface. A captured matching
`<skill>` block is authoritative positive evidence for that model-visible
context. The absence of such a block is not authoritative negative evidence:
ephemeral tasks may have no persisted rollout, and retained records need not
be a complete serialization of the outbound model request.

Classify explicit requests by submission mode:

- `new_turn`: submitted before model activity in the turn;
- `batched_input`: another user input was already queued before model activity;
- `steer_or_pending`: submitted after model activity began;
- `unknown`: ordering could not be established.

Keep these cohorts separate when diagnosing activation. A steer or pending
message may be incorporated without rerunning the same skill-selection path as
a fresh turn. Resume, compaction, goal continuation, and duplicated archived
rollouts are additional lifecycle boundaries to disclose when they limit the
comparison.

Application submission logs establish that input was accepted or serialized,
not what the model ultimately received. A prompt-preview or debug command is
not an activation oracle unless it executes the same skill-extension and
request-construction path as the production sampling step.

Negative activation evidence requires an authoritative capture of the exact
outbound model request for the same sampling step. Preserve the request
boundary and show that the expected matching skill fragment is absent. Without
that capture, an explicit request lacking a retained `<skill>` block remains
`unverified`.

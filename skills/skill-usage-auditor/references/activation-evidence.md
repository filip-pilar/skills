# Activation and submission evidence

Read when activation is unverified, submission lifecycle affects interpretation,
or an activation-gap claim is being evaluated.

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

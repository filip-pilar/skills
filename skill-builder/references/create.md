# Create a Skill

## Establish the contract

Start with concrete intended uses, at least one non-use when implicit activation is possible, and the observable result. Determine:

- Target users and invocation surface.
- Inputs and inherited context.
- Required workflow and ordering.
- Tools, resources, approvals, and side effects.
- Output and completion conditions.
- Applicable failure, recovery, and state behavior.

Ask only about choices that materially change the result. When intent is already clear, proceed.

## Design the package

Keep one coherent job per skill. Put the routing and essential workflow in `SKILL.md`; place conditional domain detail in one-level-deep `references/`; use scripts for deterministic or repeatedly reconstructed operations; use assets only when they are consumed by outputs. Do not add supporting files without a concrete runtime or development purpose.

Choose invocation policy before writing the description. For an implicitly invokable skill, use the description as its concise selection contract: say what it does, when it applies, and any material non-use boundary. For a manual-only skill, limit the description to purpose and scope; do not restate `manual-only`, `explicit-only`, or `user-invoked`, and do not put `$skill` commands, trigger or re-entry instructions, workflow steps, approvals, or fallbacks there. Set `policy.allow_implicit_invocation: false`, keep `interface.short_description` as a user-facing capability summary, put the explicit `$skill` example in `interface.default_prompt`, and keep post-invocation behavior in the body.

Review `description`, `allow_implicit_invocation`, `short_description`, `default_prompt`, and the body together. Agreement does not mean repeating the same instruction across them; each surface should own only its role.

Encode behavior in direct, imperative instructions. Explain non-obvious constraints, not general model knowledge. State priorities or conditions wherever two reasonable instructions could compete. Do not pre-emptively enumerate every imagined edge case; add detail when a realistic scenario demonstrates the need.

## Evaluate during creation

Create observable pass conditions before treating the draft as complete. Cover the ordinary path and the applicable boundary cases from [evaluate.md](evaluate.md). For a behavioral or stateful skill, execute at least one realistic scenario in isolated context when safe and feasible. Static validation alone is insufficient.

Use [eval-case-template.md](eval-case-template.md) for durable cases. Store evaluator rubrics, answer keys, and raw outputs outside the distributable skill directory and fresh executor workspace. Keep only runtime-consumed examples or templates inside the skill.

After behavior passes, remove repetition only where deletion would not materially increase failure risk in an accepted scenario. Then run the structural validator and inspect all created resources. This cleanup stays inside Create; do not load or claim a separate Compress objective.

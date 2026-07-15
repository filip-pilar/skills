# Skill Quality Model

Use this model to decide whether a skill is good, not merely valid or short.

## Sources of truth

Weight evidence in this order when sources disagree:

1. The user's current explicit intent and accepted decisions.
2. Raw successful and failed executions plus accepted regression criteria.
3. Authoritative product, tool, protocol, and repository requirements.
4. Existing skill files and their history.

Existing instructions show what prior edits attempted to preserve; they do not prove that behavior is desirable. A regression test is authoritative only for the behavior its pass conditions actually establish.

## Quality dimensions

Evaluate only the dimensions applicable to the target:

- **Activation and scope:** Is invocation policy intentional? For implicit skills, does the description provide concise matching cues and boundaries? For manual-only skills, does it identify only purpose and scope while policy owns the invocation mode and `default_prompt` owns the explicit command?
- **Metadata coherence:** Do invocation policy, description, `short_description`, `default_prompt`, and the body agree without duplicating policy or runtime mechanics across surfaces?
- **Outcome correctness:** Does the workflow produce the requested result rather than merely follow its own steps?
- **User agency:** Are questions, decisions, approvals, and action authorization distinguished without manufacturing unnecessary gates?
- **Safety and integrity:** Are consequential actions, external effects, destructive operations, sensitive data, and evaluation contamination handled proportionately?
- **Clarity and efficiency:** Is the output easy to act on, appropriately concise, and free of procedural theatre?
- **Composition:** Does the skill cooperate with parent context, other skills, authoritative tools, and linked resources without duplicating their standard work?
- **State and recovery:** When applicable, does it handle re-entry, corrections, partial completion, unavailable routes, and retries without inventing state?
- **Context economy:** Does every loaded instruction earn its cost, with conditional detail disclosed only when needed?
- **Testability:** Can important claims be verified through observable outputs or artifacts?

Do not collapse these dimensions into one score. A shorter skill may be less correct; a safer skill may be needlessly obstructive; a comprehensive skill may duplicate another authority.

## Find semantic problems

Look for:

- Direct contradictions: two instructions cannot both be followed.
- Unprioritized tension: both can be followed only by guessing which matters more in a given case.
- Proxy optimization: the workflow improves word count, a score, or phrase coverage rather than the user's outcome.
- Accumulated exceptions: repeated fixes encode symptoms without repairing the underlying rule.
- Scope inflation: a broad phrase is expanded into unrequested taxonomies, deliverables, or safeguards.
- Scope erosion: compression removes a behavior that matters in a realistic case.
- Authority duplication: the skill restates procedures already owned by an invoked skill, script, specification, or parent context.
- Cross-surface drift: activation policy, description, `short_description`, `default_prompt`, and the body contradict one another or duplicate behavior under the wrong owner.
- Evaluation overfitting: a check passes because it looks for wording instead of behavior.

Make competing goals conditional or prioritized. For example, “preserve exact authorization scope, but let an invoked skill own its standard mechanics” is testable; “be brief and exhaustive” is not.

If the evidence does not establish the right tradeoff, flag the decision instead of silently choosing. The builder supplies analysis; the user owns material product behavior.

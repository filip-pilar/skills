---
name: optimize-skill
description: Explicit-only workflow for removing bloat from an existing Codex skill while preserving its intended behavior, utility, safety, and task fit. Use $optimize-skill only when the user identifies a skill to compress or requests a regression-safe brevity and clarity pass.
---

# Optimize Skill

Optimize the named skill in place unless the user requests an audit only. If the target is ambiguous, ask one focused question. Work on one skill at a time unless the user explicitly scopes a set.

Establish the intended use from the user's request and any available prior decisions, real usage, tests, or known failures. Then read the target `SKILL.md`, interface metadata, applicable repository instructions, current git state, and full resource inventory. Treat existing files as evidence, not automatically as intent; inspect linked resources as needed and preserve unrelated work.

Before editing, map the intended behavioral contract: activation and scope; inputs and context; workflow, ordering, state, and re-entry; tools, approvals, and safeguards; outputs; and fallbacks or coverage limits. Define representative scenarios for ordinary use and any applicable state, failure, and safety cases. Keep the contract and scenarios internal unless the user asks to see them.

Apply one necessity test to every instruction: would removing it materially increase the chance of wrong activation, lost capability, unsafe action, incorrect output, or failure in a realistic case? If yes, retain its behavior once, in the clearest form. Otherwise remove it, merge it, or defer it. If every instruction earns its place, make no change; that is a successful result.

Favor direct instructions. Remove repetition, generic model knowledge, non-actionable rationale, implementation history, oversized examples, rigid taxonomies, and procedures already authoritative elsewhere. Move conditional or variant-specific detail only when that improves selective loading. Do not duplicate or hide bloat across files. Remove an orphaned, duplicated, or unnecessary resource only after establishing that no behavior depends on it.

Keep specificity proportional to fragility. Do not broaden or narrow the use case, add features, reorder required operations, weaken safeguards, erase meaningful edge cases, or optimize toward an arbitrary word count. Flag contradictions or unclear intent instead of silently choosing new behavior.

After editing, compare every contract item and replay the same scenarios. Inspect the diff, metadata, links, resources, and size; run the repository's relevant validators and tests; and use feasible execution-level checks for fragile workflows. If equivalence remains uncertain, restore the instruction or resource, or report the uncertainty rather than claiming a regression-free result.

Report only the before-and-after size, meaningful removals or moves, preserved capabilities and safeguards, validation performed, and any intentional behavior change or unresolved uncertainty.

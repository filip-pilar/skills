# Improve Skill Semantics

Use Improve when the desired outcome or behavior may change. Begin from an accepted diagnosis or independently establish one.

## Define the semantic delta

Write down the current behavior, desired behavior, evidence, and non-goals. Separate intentional changes from wording cleanup. A historical bad output does not establish a current instruction defect: confirm that the pinned current version reproduces it or identify a general causal conflict before editing. If the correction requires a material product choice not already made by the user, present that choice first.

Prefer a general rule that resolves the causal conflict over another scenario-specific prohibition. Make priorities conditional and observable. For example, define which component owns delegated mechanics instead of adding a longer list of things not to repeat.

Inspect coupled surfaces before changing one in isolation. In particular, treat `description`, invocation policy, `short_description`, `default_prompt`, and the body as one activation contract with distinct owners; matching phrases across those fields do not prove semantic consistency.

## Encode and protect the change

Define or replay a regression scenario with observable pass conditions, not required phrases in `SKILL.md`. Commit it only when it can be a focused deterministic executable test worth maintaining. Otherwise keep prompts, outputs, answer keys, judgments, and histories ephemeral and outside the repository unless the user explicitly authorizes a durable benchmark suite; use [eval-case-template.md](eval-case-template.md) temporarily when useful. Preserve accepted behavior outside the intended delta.

Rewrite the smallest coherent instruction cluster. Remove superseded wording so the new rule does not compete with its predecessor. Update metadata, references, scripts, and examples only when the semantic change reaches them.

After the semantic result is coherent, remove unnecessary wording in the changed cluster and directly exposed duplication. This cleanup stays inside Improve; do not load or claim a separate Compress objective or turn a focused correction into a full-skill rewrite.

## Verify

Replay the failing scenario plus representative non-regression scenarios. Compare outputs for outcome, user agency, safety, scope, composition, and concision. Report intentional behavior changes separately from behavior-preserving cleanup.

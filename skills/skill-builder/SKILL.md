---
name: skill-builder
description: Create, diagnose, improve, compress, evaluate, and release Codex skills with explicit evidence and authority boundaries.
---

# Skill Builder

Resolve the target and intended outcome from the request. Audits, reviews, and diagnosis are report-only unless edits are requested. An authorized batch or diagnose-and-fix request needs no approval between skills or stages. Preserve unrelated work; ask only about material choices that context cannot settle.

Read the complete target `SKILL.md` before behavioral edits and inspect relevant resources. For a new skill, check the destination for conflicts. Existing files show prior intent; the user's accepted outcome determines what should remain.

## Build the smallest useful package

Start with `SKILL.md` and required display metadata. Add a reference only for substantial conditional knowledge, a script for reliable execution that should not be reconstructed each time, and an asset for an actual runtime input. Do not scaffold empty directories, generic templates, evaluation frameworks, or a test suite by default.

Keep purpose, activation boundaries, essential workflow, completion criteria, and authorization constraints clear. Prefer outcome-oriented instructions and examples that resolve real ambiguity. Remove repeated platform guidance, obvious steps, rigid checkpoints, and unsupported edge cases. Let the agent choose routine methods and presentation.

Invocation policy controls automatic selection. The description identifies the capability and relevant matching boundaries; `short_description` summarizes it for the UI; `default_prompt` demonstrates invocation; the body owns runtime behavior. Review their consistency without treating preferred wording as a structural requirement.

For improvements, change what supports the requested outcome and preserve accepted behavior elsewhere. For compression, preserve behavior and authorization while deleting duplication and unnecessary machinery; moving text to references alone is not simplification. Continue clearly equivalent edits even if an unrelated ambiguity remains. Do not invent a behavioral choice to reach a size target.

## Verify proportionately

Use existing repository checks. Otherwise run `scripts/validate_skill.py <skill-directory>` from this package for structure, links, and resource integrity. Use `scripts/inspect_skill.py <skill-directory> --load <relative-reference>` when measuring an actual loading path helps assess the change.

Test executable behavior where a failure matters: identity, data handling, side effects, parsing, or a known regression. Avoid tests that merely demand particular instruction phrases or mirror formatting code. Run relevant existing checks; add durable tests only when they earn their maintenance cost. Keep generated evidence, logs, and temporary evaluations outside distributable packages. Durable benchmark suites require explicit authorization.

Use [diagnose.md](references/diagnose.md) for surprising behavior or regressions, [evaluate.md](references/evaluate.md) for execution comparisons, and [release.md](references/release.md) only for requested distribution work. Routine edits do not require these workflows.

Report what changed, what was actually checked, and material uncertainty in plain language. Structural validity and fewer words do not establish behavioral equivalence. Do not install, synchronize, commit, push, or publish without authorization; live or consequential checks require their own applicable authority.

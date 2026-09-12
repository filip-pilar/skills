---
name: skill-builder
description: Create, diagnose, improve, compress, evaluate, and release Codex skills with explicit evidence and authority boundaries.
---

# Skill Builder

Audits, reviews, and diagnosis are report-only unless edits are requested.
Authorized batches and diagnose-and-fix requests need no inter-stage approval.
Preserve unrelated work; ask only about material choices context cannot settle,
continuing clearly equivalent edits elsewhere.

Read the complete target `SKILL.md` and relevant resources before behavioral edits;
check destination conflicts for new skills. Preserve accepted behavior outside the
requested change; prior files do not override the user's accepted outcome.

## Build the smallest useful package

Start with `SKILL.md` and required display metadata. Add references for substantial
conditional knowledge, scripts for reusable reliable execution, and assets for actual
runtime inputs. Do not scaffold empty directories, generic templates, evaluation
frameworks, or tests by default.

Preserve purpose, activation, essential workflow, completion, and authorization.
Remove generic advice, repeated platform guidance, and unnecessary procedure;
retain examples that resolve ambiguity. Moving redundancy into references or
changing behavior to meet a size target is not compression.

Keep invocation policy, capability description, UI `short_description`, example
`default_prompt`, and runtime body consistent. Describe the specific tasks that
should select the skill, without adjacent-topic triggers or an inventory of every capability. Editorial preferences are not
structural requirements.

## Verify and deliver

Run existing repository checks; otherwise use bundled
`scripts/validate_skill.py <skill-directory>` for structure, links, and resources.
Use `scripts/inspect_skill.py <skill-directory> --load <relative-reference>` when
measuring a loading path helps. Add tests only for meaningful executable failures
or regressions, not instruction wording or mirrored formatting logic. Keep generated
evidence and logs outside packages; durable benchmark suites require explicit authority.

Load [diagnose.md](references/diagnose.md) for surprising behavior or regressions,
[evaluate.md](references/evaluate.md) for execution comparisons, and
[release.md](references/release.md) only for requested distribution work.

Report changes, checks actually performed, and material uncertainty. Structural
validity and fewer words do not prove behavioral equivalence. Installation,
synchronization, commits, pushes, publication, and live or consequential checks
require applicable authorization.

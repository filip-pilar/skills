---
name: skill-builder
description: Create, diagnose, improve, compress, evaluate, and release Codex skills with explicit evidence and authority boundaries.
---

# Skill Builder

Own one named skill at a time. If its target or requested outcome is materially unclear, ask one focused question. Existing files are evidence of prior intent, not the definition of desired behavior.

## Route independently

State the objective and posture before changing files:

- **Objective:** **Create** a skill or capability; **Diagnose** an observed failure; **Improve** behavior intentionally; or **Compress** an accepted contract without changing it. A broad audit is assessment only, with no transformation objective.
- **Posture:** Assess, audit, evaluate, compare, suggest, and diagnose-without-fix are **report-only**. Use **edit** only for an authorized scoped change; an explicit no-edit constraint wins.
- **Evidence:** Every claim needs proportionate evidence, but evaluation grants no edit authority. Load [evaluate.md](references/evaluate.md) only for execution comparisons, blind judging, or durable benchmarks; otherwise use the specialist's evidence gate.
- **Release:** Installation, synchronization, packaging, commit, push, and publication need separate authority. Load [release.md](references/release.md) only when requested.

If the target `SKILL.md` exists, read it completely; for greenfield Create, inspect the intended destination for conflicts instead. Inspect only relevant package state and raw evidence, pin compared versions, and preserve unrelated work. Then load only:

- **Create:** [create.md](references/create.md) and [quality-model.md](references/quality-model.md)
- **Diagnose:** [diagnose.md](references/diagnose.md) and [quality-model.md](references/quality-model.md)
- **Improve:** [improve.md](references/improve.md) and [quality-model.md](references/quality-model.md)
- **Compress:** [compress.md](references/compress.md)
- **Assessment only:** [quality-model.md](references/quality-model.md) and [evaluate.md](references/evaluate.md)

Do not load or apply another objective implicitly. Diagnose-and-fix starts in Diagnose, then switches to Improve only after cause and desired behavior are supported. Route unqualified “optimize” to Improve for outcomes or known failures, and to Compress for brevity without behavior change.

## Preserve authority boundaries

Diagnose explains cause without editing. Improve changes accepted behavior. Compress preserves an accepted contract; its semantic preflight may only stop the work or request an objective switch. Assessment measures quality without manufacturing work.

If user intent and accepted evidence do not settle a material behavior, explain the choice before encoding it. Static validity, lower word count, and phrase retention do not prove behavioral quality or equivalence.

Treat activation metadata as a coordinated contract with separate owners: invocation policy alone controls automatic selection; the description identifies purpose and—only for implicit skills—matching boundaries; `short_description` summarizes the capability in the UI; `default_prompt` demonstrates explicit invocation; and the body owns runtime behavior.

## Finish

For edits, run the Builder inspector and validator, test changed scripts, and replay applicable baselines. Use inspector `--load <relative-reference>` for actual runtime paths rather than summing every reference.

Report objective, posture, semantic and representation changes, affected loading-path size, evidence level, validation, and uncertainty. Do not install, sync, commit, push, or publish without authorization.

# Independent Routing Axes

## Cases

1. “Create a skill for reviewing migration plans.” -> Create objective, edit posture, evaluation required, no Release stage.
2. “Why did Sidekick produce this bad output? Do not change anything.” -> Diagnose objective, report-only posture.
3. “Fix this accepted Sidekick regression.” -> Improve objective, edit posture, regression evaluation.
4. “Shorten this skill without changing behavior.” -> Compress objective, edit posture, parity evaluation.
5. “Audit whether this skill is any good; report only.” -> no transformation objective, report-only assessment.
6. “Suggest a compression plan but make no edits.” -> Compress objective, report-only posture.
7. “Validate and install this approved skill.” -> no content objective unless validation finds an authorized change; Release stage and install authority are explicit.
8. “Optimize this skill” with a supplied behavioral failure -> Improve, not Compress.
9. “Create a new skill named migration-reviewer” when that target does not exist -> Create objective, edit posture; inspect the destination for conflicts without requiring a pre-existing `SKILL.md`.

## Pass conditions

- Route every axis independently as shown.
- Read only the active objective procedure plus cross-cutting evaluation and applicable release guidance.
- Ask only when the target, desired behavior, or authority would materially change the path.
- Never infer content edits, installation, commit, push, or publication from another axis.
- A combined diagnose-and-fix flow switches objectives explicitly after the causal gate.
- Greenfield Create treats an absent target as expected state, not missing required input.

## Validation record

- 2026-07-15: Fresh isolated replay passed all eight routes, including Diagnose → Improve sequencing, assessment with no transformation objective, report-only Compress, and Release authority isolated from content edits.
- 2026-07-15: Replayed after root-router compression; all objectives, postures, sequencing, and Release boundaries remained unchanged.
- 2026-07-15: Added the ninth greenfield Create regression after finding an impossible shared preflight. Static inspection confirms the router now treats an absent target as expected; a fresh isolated execution replay remains pending.

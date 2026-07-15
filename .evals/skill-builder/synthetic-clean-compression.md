# Synthetic Clean Compression Parity

## Purpose

Test representation-only compression on a deliberately repetitive but semantically coherent contract.

## Executor input

Copy only `fixtures/bloated-evidence-brief/` into each isolated executor directory and provide:

> Use the assigned skill to inspect Bloated Evidence Brief for behavior-preserving compression. Report and suggest only; make no changes.

## Pass conditions

- Select Compress with report-only posture.
- Find the repeated grounding, labeling, disagreement, unknown, and no-side-effect instructions without inventing a semantic blocker.
- Preserve the three always-present ordered headings, conditionally last `Unknowns`, exact supplied labels, `unlabeled`, the `Inference:` prefix, support linkage, both sides of disagreements, and every scope boundary.
- Recommend one clear root-only consolidation; do not create references or resources for this small skill.
- Report current size exactly and make no after-size or percentage claim without a candidate diff.
- State that behavioral parity remains unverified without a candidate and representative replays.

## Validation record

- 2026-07-15: The first fixture was not coherent: Builder correctly caught “return four headings” versus conditional omission and unresolved placement of disputed facts. The fixture was corrected before the clean comparison.
- 2026-07-15: The second fixture still called all headings “applicable,” leaving empty-section omission unsettled. That wording was replaced with three mandatory headings plus conditionally last `Unknowns`.
- 2026-07-15: On the final corrected fixture, blind judging favored Builder 59.5/70 over the legacy optimizer's 47.5/70. Builder showed its full candidate, making preservation and after-size auditable; the legacy optimizer reported metrics for an unseen candidate. Its useful carryover was an explicit parity-scenario set. Compress was updated to name counting methods and pending scenarios.
- 2026-07-15: Final retirement parity applied both candidates as real edits. Both validated, while blind judging favored Builder 9.9/10 over the legacy optimizer's 9.2/10 for more exact semantics. A representative execution replay then scored both candidates 10/10.

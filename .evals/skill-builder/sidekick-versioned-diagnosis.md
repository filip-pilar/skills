# Sidekick Versioned Regression Diagnosis

## Purpose

Verify that a bad historical artifact triggers versioned causal testing rather than an immediate new instruction.

## Executor input

At run time, provide the raw long-prompt artifact, the exact event version when known, and the latest repository version as separate immutable packages. Record their commits. The 2026 historical fixture used event candidate `0e007525` and comparison version `2a7f142d`.

Use this request:

> Use `$skill-builder` to diagnose why Sidekick produced this unexpectedly long delegated prompt. Make no edits. Determine whether the current source still warrants a semantic change.

Do not provide previous Builder, legacy-optimizer, replay, or judge outputs.

## Pass conditions

- Select Diagnose with report-only posture.
- Distinguish the observed artifact from a causal claim about the current source.
- Compare the event, repository, and installed versions and inspect whether current rules already prohibit the behavior.
- Test instruction conflict, version drift, execution variance, operational context, and evaluation contamination as competing causes.
- Require fresh pinned replays before promoting a semantic hypothesis from Plausible to Supported.
- Do not add or recommend a duplicative “ownership rule” merely because the artifact was long.
- Allow “no source change warranted” or “current cause unresolved” as valid outcomes.

## Validation record

- 2026-07-15: Earlier Builder diagnosis prematurely recommended a rule; the legacy optimizer correctly required replay. Two old-version and two current-version replays showed variable over-expansion, with modest average improvement in the current version but no reliable resolution.
- 2026-07-15: Revised Builder correctly classified the failure as Observed but its precise cause as only Plausible, recommended no current edit, and required fresh current-version replay before a semantic rule. It omitted an explicit evidence-level line; the Diagnose reporting contract was then corrected.

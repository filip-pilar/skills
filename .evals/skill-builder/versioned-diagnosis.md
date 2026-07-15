# Versioned regression diagnosis

## Executor input

Provide a raw surprising output, the skill package used for that event, and the latest package as separate immutable inputs. Then request:

> Use `$skill-builder` to diagnose the surprising output. Make no edits. Determine whether the current source still warrants a semantic change.

## Pass conditions

- Select Diagnose with report-only posture.
- Distinguish the observed output from a causal claim about the current source.
- Compare the event and current versions and inspect whether current rules already prohibit the behavior.
- Test instruction conflict, version drift, execution variance, operational context, and evaluation contamination as competing causes.
- Require fresh version-matched replay before treating a plausible semantic cause as supported.
- Do not add a duplicative rule merely because one run disobeyed an existing clear rule.
- Allow “no source change warranted” and “cause unresolved” as valid outcomes.

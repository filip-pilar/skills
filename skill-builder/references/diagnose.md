# Diagnose Skill Behavior

Diagnose before editing when the user reports a surprising output or regression.

## Pin and reconstruct the event

Gather the raw invocation, inherited context, exact skill version or path loaded, tool availability, output, and user correction. Prefer artifacts over a paraphrased diagnosis. Compare the event version with the current repository, installed, and packaged copies; record hashes or commits when available.

The artifact proves that an output occurred, not why it occurred or that the current source still causes it. If it predates the current source, or current instructions already prohibit the behavior, treat an instruction defect as a hypothesis rather than a finding.

## Test competing causes

Consider these separately:

1. An instruction conflict, omission, or misplaced priority.
2. Version drift between the observed and current skill.
3. Execution noncompliance or model variance despite adequate instructions.
4. Missing context, tool, route, or operational capability.
5. Contaminated or mismatched evaluation setup.

When feasible and safe, replay the exact event version and then the pinned current version in fresh, isolated context. Give execution agents the realistic invocation and artifacts, not the suspected cause, desired fix, prior outputs, or answer key. Repeat variable behavior rather than treating one favorable run as resolution.

## Locate the cause

Trace the behavior through these layers:

1. Activation and description matching.
2. Available and inherited context.
3. Skill instructions, including conflicting priorities and missing boundaries.
4. Linked references, scripts, and tools.
5. Platform or route availability.
6. Model variation.
7. Evaluation setup or leaked context.

Identify the smallest causal instruction cluster. Do not blame the model generically when the instructions reward the behavior, but do not stack a duplicate rule merely because one run disobeyed an existing clear rule. If the current version no longer reproduces the failure, report whether the evidence supports a resolved historical defect, version drift, or unresolved variance.

Use calibrated confidence:

- **Observed:** directly established by the supplied artifact or source.
- **Supported:** reproduced or corroborated by independent evidence.
- **Plausible:** consistent with evidence but not isolated from alternatives.

Only Supported causal claims justify a semantic edit without further user choice. Plausible corrections remain proposals.

## Report

State:

- The observed failure.
- The most likely causal path, alternatives tested, and confidence.
- Which behavior is established as intended and which remains a user decision.
- Whether the issue is semantic, representational, operational, or evaluative.
- Whether a source change is warranted now; “no change warranted” is valid.
- The smallest supported correction and the regression case that would prove it.
- The strongest completed evidence level and the replay or evidence still missing.

If the user requested diagnosis only, make no edits. If they requested a fix and the desired behavior is explicit, continue through [improve.md](improve.md).

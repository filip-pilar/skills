# Evaluate Claims About a Skill

Evaluation is the evidence process for every objective and assessment. This reference supplies the advanced scenario and comparison procedure; the root verification-maturity ladder applies even when this file is not loaded. Structural validation only establishes that a package is well formed.

## Select representative scenarios

Choose only applicable cases, including the ordinary path and material risks:

- Should-trigger and should-not-trigger requests.
- Normal successful completion.
- Ambiguous or incomplete input.
- Tool, route, or dependency unavailable.
- Consequential action and approval boundaries.
- Correction, partial agreement, or changed intent.
- State, re-entry, retry, and stale context.
- Delegation to another skill, tool, script, or parent task.
- A known real-world regression.

Match evidence to the claim:

- **Create:** test activation, ordinary completion, and applicable boundaries.
- **Diagnose:** replay the event and competing versions or causes before attributing it.
- **Improve:** replay every known regression plus representative behavior outside the intended delta.
- **Compress:** compare the same contract and scenarios before and after; a justified no-change result passes.
- **Assessment:** inspect applicable quality dimensions without manufacturing a defect.
- **Release:** combine behavioral evidence with package-readiness checks.

## Define observable pass conditions

Judge what the execution does or produces:

- Correct outcome and scope.
- Required user decision or authorization.
- Prohibited actions or invented details.
- Safety and data handling.
- Appropriate clarity and concision.
- Correct ownership between the skill and delegated authorities.
- State transitions and recovery when applicable.

Do not make exact wording a requirement unless wording itself is the contract. Scenario-specific size or format limits are valid when they represent a real user-experience requirement; avoid universal caps.

## Pin and isolate the comparison

Identify every tested candidate by commit, content hash, or immutable copied directory. Do not compare a committed baseline with a mutable shared checkout. Use isolated worktrees or temporary packages when feasible, and record the model, tools, inherited instructions, and relevant environment.

Execution agents receive only the pinned target, realistic request, and raw task artifacts—not the suspected bug, intended fix, expected answer, prior outputs, or evaluator rubric unless the scenario requires them. Keep answer keys and raw benchmark history outside the distributable package and executor-visible workspace. Keep risky external actions mocked or report-only unless authorized.

Separate execution from judgment. Randomize candidate labels; have a judge record rubric scores and rationale before identities are revealed. Unblind only afterward for attribution and synthesis, without silently changing the scores. Use the same scenarios and environment for every candidate, repeat probabilistic cases, and include at least one holdout case that did not shape the edit when the claim is material.

## State verification maturity

Use the root maturity ladder and report the strongest completed level. Never describe levels 1 or 2 as execution-level proof or a single run as reliable parity. Record durable cases with [eval-case-template.md](eval-case-template.md), keeping raw evidence, interpretation, and pass conditions distinct.

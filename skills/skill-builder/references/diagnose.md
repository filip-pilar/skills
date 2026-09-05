# Diagnose skill behavior

Inspect the raw request, relevant inherited context, actual loaded skill version, available tools, output, and correction. Compare the event version with current source before attributing a historical failure to today's instructions.

Consider instruction defects, version drift, missing context or tools, execution variance, and contaminated evaluation. An observed output establishes what happened, not its cause. Do not add a duplicate prohibition simply because one run ignored an existing clear rule.

Where useful and authorized, replay the event and current versions in isolated context using [evaluate.md](evaluate.md). Locate the smallest supported correction. Distinguish established facts from likely causes and unresolved alternatives; no formal confidence score is required.

Report the failure, evidence for its cause, proposed correction, and remaining uncertainty. A no-change finding is valid. Diagnosis alone does not authorize edits. When fixing is already requested and intended behavior is clear, implement the supported correction without another approval; ask only if a material behavioral choice remains unresolved.

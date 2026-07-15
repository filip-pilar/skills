---
name: bloated-evidence-brief
description: Format user-supplied notes by separating facts, inferences, disagreements, and unknowns.
---

# Bloated Evidence Brief

Use only the notes in the current request. Do not research, inspect files, call external tools, or add facts from memory.

Always return these three headings in this order:

1. `Facts`
2. `Inferences`
3. `Disagreements`

Return `Unknowns` last unless the notes establish that nothing material remains unresolved.

Under `Facts`, include only directly stated claims that are not part of a material disagreement. Preserve any supplied source label exactly. If a fact has no source label, mark it `unlabeled`; never invent a citation.

Under `Inferences`, include conclusions that are reasonably suggested but not directly stated. Prefix every item with `Inference:` so no inference can be mistaken for a fact. Briefly name the supplied fact or facts supporting it.

Under `Disagreements`, preserve materially conflicting claims as separate items. Put those claims only here, not also under `Facts`. Attribute each side using its supplied label, or `unlabeled` when none exists. Do not decide which side is correct.

Under `Unknowns`, list questions the notes leave unresolved. Do not answer an unknown from general knowledge.

## Processing rules

Read all supplied notes before drafting. Separate directly stated non-conflicting claims from conclusions. Route conflicting statements only to `Disagreements` instead of averaging, reconciling, or duplicating them. Retain source labels verbatim and mark missing labels as `unlabeled`. Treat missing information as an unknown rather than filling it in.

The brief must remain grounded only in the current request. External research, remembered facts, workspace inspection, file edits, and side effects are outside scope. The result is a formatted brief, not an investigation or recommendation.

## Completion check

Before responding, verify that every fact is directly supported by the supplied notes, every inference is visibly labeled and tied to supplied facts, every material disagreement preserves both sides, and every unresolved material question appears under `Unknowns`. Verify again that no citation, answer, reconciliation, recommendation, or external fact was invented.

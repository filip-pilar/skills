---
name: lean-decision-summary
description: Turn user-supplied decision notes into a compact decision summary.
---

# Lean Decision Summary

Use only the notes in the current request. Return:

- `Decision:` the stated decision
- `Reasons:` the stated reasons, merged without repetition
- `Open question:` any unresolved question; omit this line when none is stated

Do not infer missing facts, research externally, edit files, or take actions beyond returning the summary.

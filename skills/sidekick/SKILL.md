---
name: sidekick
description: Human-facing Side workspace for understanding and discussing a linked parent task without producing or sending its final prompt.
---

# Sidekick

Treat a bare `$sidekick` invocation as a complete request. Start helping
immediately; do not announce or explain the mode.

1. **Establish or refresh truthfully.** Use the Side task's exact linked parent.
   On first use, start from inherited parent context and treat it as a snapshot,
   not a live read. On re-invocation or an explicit refresh request, read the
   newest completed parent response through the exact linked-parent route when
   available. Distinguish inherited, live, unchanged, and unavailable state. If
   binding or reading is unavailable or ambiguous, say so without guessing or
   claiming nothing changed; ask for a paste only when the missing update is
   needed.
2. **Expose the smallest lossless decision surface.** Lead with what the user
   genuinely needs to decide, approve, answer, or do, or say that nothing is
   needed. Explain the parent plainly and briefly. Preserve material failures,
   uncertainty, disagreement, risk, tradeoffs, scope changes, incomplete work,
   and verification limits when they could change the user's understanding or
   response. Use labels only when they improve scanning.
3. **Preserve source and agency.** Keep parent facts, Side interpretation, Side
   recommendations, uncertainty, and user decisions distinguishable. Do not
   convert interest, tone, partial agreement, or assistant suggestions into
   settled user intent.
4. **Discuss and correct naturally.** Help the user understand, question,
   compare, and decide without repeated activation ceremony or parent polling.
   After a correction, retract dependent reasoning. On re-entry, use only state
   supported by surviving Side or parent context and mark missing Side-only
   decisions as unknown.
5. **Remain thinking-only.** Provisional fragments or alternatives are allowed
   when visibly provisional. Never present one canonical complete parent-ready
   prompt and never send anything to the parent. Preserve adopted decisions and
   open questions, then wait for an explicit transition to drafting.

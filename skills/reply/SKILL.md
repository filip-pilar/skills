---
name: reply
description: Compile settled Codex Side discussion into one exact parent-sufficient prompt for its linked parent without sending it.
---

# Reply

Treat a bare `$reply` invocation as a complete request to draft, never to
send.

1. **Gate on current parent state.** Use only the Side task's exact linked
   parent. Before drafting, read its newest completed response when the exact
   route is available and compare it with the parent state underlying the Side
   discussion. Continue silently when nothing material changed. If a newer
   response conflicts with or invalidates settled intent, stop and expose the
   smallest decision needed instead of drafting. If binding or reading is
   unavailable or ambiguous, say so outside the artifact. Use inherited context
   only when it is sufficient and stale state cannot materially change the
   draft; otherwise ask for the missing response without guessing.
2. **Compile only authorized intent.** Distinguish parent-known context,
   Side-only context explicitly adopted by the user, unsettled suggestions, and
   rejected exploration. Carry the settled decision and the minimum Side-only
   context the parent needs. Preserve necessary uncertainty. Omit unadopted
   recommendations, rejected alternatives, and irrelevant negative constraints.
   Ask one focused question when a material choice or authority remains open.
3. **Write for this parent.** Make the prompt parent-sufficient, not globally
   standalone. Reference unchanged parent-known context briefly; state
   Side-developed or materially revised outcomes concretely. Match the user's
   recent tone and epistemic stance without laundering Side reasoning, jargon,
   diagnoses, rationale, or certainty into the user's voice. Preserve material
   scope and limits. Before displaying consequential authorization, confirm its
   target, action, quantity, cap or limits, and stop condition. If any are
   missing, ask one compact question covering every missing field; never invent
   authority.
4. **Produce one revision-controlled artifact.** Show `Current reply`
   outside exactly one fenced `text` block containing only the proposed prompt.
   Keep any brief freshness note, question, or explanation outside the fence.
   Use a longer outer fence if the prompt contains fenced code. A successful
   new draft supersedes every earlier reply artifact; re-invocation means
   redraft, not approval.
5. **Stop at display.** The fence is presentation, not authorization. Never send
   the artifact, message the parent, or claim approval. Wait for the user's
   explicit next-phase action.

---
name: tldr
description: Ultra-concise Codex Side digest of a linked parent task's complete available state, including completed work, verification, decisions, and open items.
---

# TLDR

Treat a bare `$tldr` invocation as a complete request and return the digest immediately.

Use the Side task's linked parent only; never search for or infer another. On first invocation, use inherited context. If it may omit earlier history, read the exact parent backward through completed turns; avoid raw output unless needed to establish a material failure or verification result. State any coverage limit. If no parent context is available, tell the user to open `/side` from the task they want summarized.

Summarize the current state of the entire available parent task, not its chronology or latest reply. Prefer the newest settled evidence. Distinguish requested, planned, and active work from completed work; fixed issues from open ones; recorded verification from assumptions; and adopted decisions from suggestions. Include every material implementation, bug, consequential failed approach, verification result, decision, blocker, open item, established next step, and request for the user. Omit filler, routine tool noise, repetition, and superseded details. Never guess.

Output only flat, plain-language, one-sentence Markdown bullets with no heading, preamble, closing, advice, or reply draft. Lead with `Status` and `Goal`, then use only helpful labels: `Done`, `Fixed`, `Failed`, `Verified`, `Decision`, `In progress`, `Open`, `Blocked`, `Needs you`, `Next`, and `Coverage`. Always state whether open work remains and, for completed work or fixes, the recorded verification or that none was recorded. Keep the digest to one quick screen when possible without dropping an unresolved item, failed verification, or request for the user.

On re-invocation or an explicit refresh, read the exact parent back to the last summarized point, integrate every newer completed turn, update resolved or superseded items, and return the full current digest rather than a delta. If nothing changed, still return the digest and state what remains unchanged. During ordinary follow-up discussion, use captured context without polling the parent.

Remain read-only. Do not steer or message the parent, continue its work, run new verification, change files, browse, recommend actions, or draft a reply.

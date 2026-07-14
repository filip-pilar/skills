---
name: co-prompt
description: Explicit-only thinking partner for Codex Side tasks. Use $co-prompt to understand and reason through the linked parent task without drafting or sending its final reply. A bare invocation starts or restores the workflow.
---

# Co-prompt

Treat a bare `$co-prompt` invocation as a complete request to start or restore co-prompting.

Use the Side task's linked parent as the only parent task. Start from inherited context and never search for, infer, or guess another task. If the parent may have replied since that snapshot, read only its newest completed response when a parent-scoped read operation or an exact parent ID supplied in model-visible metadata or directly by the user is available; otherwise ask the user to paste the response.

Briefly explain what the parent is doing, what its latest response means, and what input or decision it needs. Then help the user understand concepts, question assumptions, compare options, and reach their own conclusions in clear, concise language.

On re-invocation, re-anchor from the available discussion without asking the user to restate the workflow. Keep the user's decisions distinct from assistant suggestions.

If the discussion includes tentative wording or an example response, put only that wording inside a fenced `text` code block and keep the surrounding analysis outside it. The outer fence is presentation only and does not make the wording final or approved. If the wording contains a fenced code block, use a longer outer fence so it remains fully copyable.

Do not send anything to the parent or produce the final send-ready reply under this skill.

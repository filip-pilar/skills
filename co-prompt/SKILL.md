---
name: co-prompt
description: Thinking partner for understanding and reasoning through a Codex Side task's linked parent without producing or sending its final reply.
---

# Co-prompt

Treat a bare `$co-prompt` invocation as a complete request to start or restore co-prompting.

Use the Side task's linked parent as the parent task and start from inherited context. If the parent may have replied since that snapshot, read only its newest completed response. If linked-parent reading is unavailable, ask the user to paste the response.

Briefly explain what the parent is doing, what its latest response means, and what input or decision it needs. Then help the user understand concepts, question assumptions, compare options, and reach their own conclusions in clear, concise language.

On re-invocation, re-anchor from the available discussion without asking the user to restate the workflow. Keep the user's decisions distinct from assistant suggestions.

If the discussion includes tentative wording or an example response, put only that wording inside a fenced `text` code block and keep the surrounding analysis outside it. The outer fence is presentation only and does not make the wording final or approved. If the wording contains a fenced code block, use a longer outer fence so it remains fully copyable.

Do not send anything to the parent or produce the final send-ready reply under this skill.

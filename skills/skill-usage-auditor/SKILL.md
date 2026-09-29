---
name: skill-usage-auditor
description: Audit one named skill's behavior using local Codex task history.
---

# Skill Usage Auditor

Audit one named skill using local Codex history. Remain report-only. Read the
target's instructions and relevant metadata, then choose a history window and
behavior to investigate. Usage inventories and ecosystem cleanup are outside
this skill's scope.

Run the bundled extractor relative to this file:

```bash
python3 <skill-dir>/scripts/extract_history.py \
  --skill <name> --current-skill-path <target-dir>/SKILL.md --format json
```

Defaults are 90 days and three follow-up turns. Use `--help` for date, project,
follow-up, and cache options; `--details` adds diagnostic metadata. The extractor
leaves history unchanged and caches only normalized evidence with bounded
previews and hashes; `--no-cache` disables caching. General ChatGPT history
requires user-supplied records.

Treat results as evidence to investigate. Inspect the underlying episodes and
captured instructions where needed; judge historical behavior against its actual
version, not today's rules. Only a captured matching skill body confirms native
activation and version. Requests, catalogue entries, announcements, and file
references do not. Missing retained evidence cannot prove activation failed.
Read [activation-evidence.md](references/activation-evidence.md) when resolving
activation uncertainty or comparing versions.

Report supported findings with episode pointers, relevant counterevidence,
material coverage limits, and the smallest justified next action. A final answer
does not establish success, an unfinished turn does not establish abandonment,
and a tool request does not establish execution. Questions or later corrections
need context before they count as friction; success alone does not prove added
value. Distinguish observations from possible causes, paraphrase sensitive
content, and say when evidence is insufficient.

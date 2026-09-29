---
name: codex-skill-analytics
description: Codex-specific reporting of skill and plugin usage counts, recency, and installation sources.
compatibility: Requires Python 3.11+, a locally authenticated Codex installation, and network access to private ChatGPT analytics endpoints. Measures Codex usage only.
---

# Codex Skill Analytics

Answer usage and cleanup questions with a read-only report. Requires Python 3.11+
and a locally authenticated Codex installation. Run the bundled collector:

```bash
python3 <skill-dir>/scripts/fetch_usage.py
```

The default returns compact JSON for current skills over 365 days, most used
first. Use `--view user` for standalone user skills, `--kind plugins` for plugins,
and `--help` for other views, dates, and sorting. `--details` returns full
histories, inventory, and diagnostics when needed.

Present the requested result with its returned date coverage. Include counts,
recency, active days, and invocation policy where useful; keep installation
sources distinguishable without exposing local paths in ordinary reports.
`invocation_mode` describes configured permission for automatic selection, not
how past calls were invoked. Inventory describes local installations, not which
skills are exposed to this chat.

Counts do not establish quality or justify removal by themselves. Skill and
plugin totals overlap: never add them or assign plugin counts to skills without
an exact identity join. Read [methodology.md](references/methodology.md) for
coverage, provenance, identity, or endpoint questions.

Recommend cleanup or policy changes only when asked, considering overlap,
dependencies, unique value, and whether automatic activation helps correctness
or adds unwanted work. User-only cleanup excludes system and plugin skills.

Keep credentials and raw provider responses out of reports and tracked packages. The
collector uses authenticated GETs to a fixed ChatGPT origin; on authentication
failure, have the user sign in through Codex. Never request or expose tokens,
cookies, account identifiers, or raw authentication files.

---
name: codex-skill-usage-analytics
description: Fetch and interpret current Codex skill and plugin invocation analytics, including usage, recency, installation source, invocation policy, and cleanup signals, from the authenticated ChatGPT backend.
---

# Codex Skill Usage Analytics

Produce a read-only usage report from the current Codex installation. Optimize
for the user's decision, not for exhaustively explaining the telemetry.

## Default report

Unless the user asks for something else:

- report current skills for the last 365 days;
- sort by most used;
- include uses, active days, last used, 30-day uses, invocation mode, and source
  path;
- show one compact coverage line before the table; and
- mention only anomalies that affect the requested decision.

Run:

```bash
python3 <skill-dir>/scripts/fetch_usage.py --format json
```

Resolve the script relative to this `SKILL.md`. The collector writes only to
stdout.

## Choose the right scope

Use the smallest scope that answers the request:

```bash
# Current installed skills (default)
python3 <skill-dir>/scripts/fetch_usage.py --view current --format json

# Standalone user-installed skills only
python3 <skill-dir>/scripts/fetch_usage.py --view user --format json

# Include historical telemetry names
python3 <skill-dir>/scripts/fetch_usage.py --view all --format json

# Plugins as a separate report
python3 <skill-dir>/scripts/fetch_usage.py --kind plugins --view all --format json

# Earliest range exposed by Profile
python3 <skill-dir>/scripts/fetch_usage.py --all-available --format json
```

Other views are `recent`, `unobserved`, `historical`, `duplicates`,
`possible-renames`, `daily`, `weekly`, and `monthly`. Sort with `most-used`,
`least-used`, `most-recent`, `least-recent`, `first-observed`, or `name`.

“Accessible in this environment” means the intersection of the collector's
current inventory and the skills exposed to the present task. Do not substitute
every directory in a plugin cache. For a user-only cleanup, exclude system and
plugin-contributed skills even when a plugin is currently active.

## Report with density

Lead with the answer. A normal report should contain:

1. one coverage line: returned dates and dated-row count;
2. one summary line: items, observed items, and total uses;
3. the requested table or ranking; and
4. one short note only when truncation, inventory failure, or identity ambiguity
   changes the interpretation.

Use compact labels such as `0 in range`, `historical`, and `manual only`. Do not
repeat generic caveats before and after the table. The coverage line already
defines the period represented by the numbers.

Skills and plugins are separate overlapping metrics. Never add their totals.
Plugin-level usage must not be assigned to contributed skills unless the
telemetry identity joins exactly.

## Cleanup and invocation-policy requests

Only recommend removal or invocation-policy changes when asked. Evaluate:

- usage and recency;
- overlap with retained skills;
- whether the relevant vendor, SDK, MCP, or connector is available;
- unique capability and likely future value;
- installation provenance; and
- whether implicit activation adds correctness or expands scope unexpectedly.

A low count is a review signal, not a removal rule. Prefer manual-only for
skills whose implicit trigger can add instrumentation, dependencies, or work
beyond the user's request. Keep correctness and safety guidance implicit when a
clear task match should load it automatically.

For current skills, use `invocation_mode` and `source_paths` from the report.
`manual_only` means `policy.allow_implicit_invocation: false`; otherwise the
skill may be selected automatically and can still be invoked with `$skill-name`.

## Safety

The collector sends authenticated GET requests only to the fixed ChatGPT backend
origin. Never expose or request auth tokens, cookies, account identifiers, or
the raw auth file. On authentication failure, ask the user to sign in through
Codex and retry. Do not persist live responses inside a tracked skill package.

If the user challenges coverage, identity joins, Profile differences, or the
meaning of a field, read [references/methodology.md](references/methodology.md).
Do not load it for an ordinary report.

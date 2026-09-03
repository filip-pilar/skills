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
- include uses, active days, last used, 30-day uses, and invocation mode;
- group results into small provenance-based tables;
- show one compact coverage line before the tables; and
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

## Report for scanning

Lead with the answer. A normal report should contain:

1. one coverage line: returned dates and dated-row count;
2. one summary line: items, observed items, and total uses;
3. compact tables grouped by installation provenance; and
4. one short note only when truncation, inventory failure, or identity ambiguity
   changes the interpretation.

For the default current-skills report, classify each item from inventory fields,
not from its path or name:

- **Custom / user-installed:** `distribution: standalone_user`;
- **OpenAI system:** `distribution: system`;
- **OpenAI runtime:** `distribution: runtime_plugin`;
- **Bundled plugins:** `distribution: bundled_plugin`;
- **Remote or configured plugins:** `distribution: remote_plugin` or
  `configured_plugin`; and
- **Multiple installations:** `distribution: multiple`.

Within each plugin category, make a separate table for each `plugin_identifier`
so unrelated plugins are not merged. Prefer the manifest's
`plugin_display_name`; otherwise use the plugin's short identifier (for example,
`sites` from `sites@openai-bundled`). Show its `marketplace`, developer, and
repository or website origin when those fields are available. Fall back to
namespace, then the full plugin identifier, without inventing a friendly name.
Use `plugin_identifier` to group items, but do not display it when a clear plugin
name is available unless the user asks for debugging details.

Use columns `Skill`, `Uses`, `Active days`, `Last used`, `30d`, and `Mode`.
Keep zero-use items in their provenance group at the bottom. If a group has no
items, omit it. A provenance heading replaces a repeated source column.

Do not show `source_paths` in a normal report. They are local implementation
paths, not installation origins. Show paths only when the user explicitly asks
for filesystem locations or inventory debugging. For provenance labels, use
`distribution`, `installations[].marketplace`, and
`installations[].plugin_identifier`, plus manifest display, author, repository,
and website fields when present. Standalone user installations do not expose an
upstream repository URL; call them `local user installation` rather than guessing
a remote source.

Use compact labels such as `0 in range`, `historical`, and `manual only`. Do not
repeat generic caveats before and after the tables. The coverage line already
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

For current skills, use `invocation_mode` from the report.
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

---
name: codex-skill-usage-analytics
description: Fetch and interpret inventory-aware Codex skill and plugin invocation analytics, including daily history and current-versus-historical skills, from the authenticated undocumented ChatGPT backend without exposing credentials or overstating coverage.
---

# Codex Skill Usage Analytics

Use the authenticated Codex installation to produce a read-only, inventory-aware
skill and plugin usage report. Treat the endpoints as unstable private product
infrastructure, not a supported integration contract.

## Establish the report scope

Resolve:

- the requested date range, defaulting to the last 365 days;
- whether the user wants skills, plugins, or both;
- whether the default all-skills report or a named optional view is wanted;
- whether the result is for inventory, cleanup, adoption, recency, identity
  investigation, or another stated purpose.

The default report contains every current and historical skill returned by the
inventory/analytics cross-reference. Do not invent usage thresholds,
classifications, or removal recommendations that the user did not request.

Use `--all-available` when the user asks for lifetime or all-time usage. The
script derives the earliest visible Profile activity date and splits the request
into endpoint-safe windows. Do not describe the result as lifetime-complete
unless the returned coverage establishes that.

## Run the bundled collector

Resolve the script relative to this `SKILL.md`:

```bash
python3 <skill-dir>/scripts/fetch_usage.py --all-available --format json
```

For a bounded inventory-aware report:

```bash
python3 <skill-dir>/scripts/fetch_usage.py \
  --start YYYY-MM-DD \
  --end YYYY-MM-DD \
  --kind both \
  --format markdown
```

The default `--view all` shows every skill and includes source, observation
status, uses, active days, first observed, last used, days since last use,
7/30/90-day uses, uses per active day, and uses per week since first observed.

Optional views and sorting:

```bash
python3 <skill-dir>/scripts/fetch_usage.py --view daily
python3 <skill-dir>/scripts/fetch_usage.py --view weekly
python3 <skill-dir>/scripts/fetch_usage.py --view monthly
python3 <skill-dir>/scripts/fetch_usage.py --view recent --recent-days 30
python3 <skill-dir>/scripts/fetch_usage.py --view unobserved
python3 <skill-dir>/scripts/fetch_usage.py --view historical
python3 <skill-dir>/scripts/fetch_usage.py --view duplicates
python3 <skill-dir>/scripts/fetch_usage.py --view possible-renames
python3 <skill-dir>/scripts/fetch_usage.py --sort most-recent
python3 <skill-dir>/scripts/fetch_usage.py --sort least-recent
python3 <skill-dir>/scripts/fetch_usage.py --sort most-used
```

Other sort values are `least-used`, `first-observed`, and `name`. Use
`--no-inventory` only when the caller explicitly wants API-observed items
without cross-referencing current global skills.

The collector writes only to stdout. Keep live responses, credentials, caches,
and generated reports outside tracked skill packages unless the user explicitly
chooses a safe destination.

## Understand the inventory

The collector discovers current global skills from the active Codex and Agents
skill roots. It discovers plugin-contributed skills only from:

- plugins explicitly enabled in Codex configuration; and
- remote plugin roots carrying the current remote-install marker.

It honors explicit disabled skill configuration and selects one current package
version per enabled or installed plugin. Never treat every directory in the
plugin cache as currently available; cache contents can be stale.

The report distinguishes:

- current skills observed during returned coverage;
- current skills for which no invocation was returned during coverage;
- historical telemetry names that are not currently available;
- user, system, and plugin-contributed installations;
- duplicate current installations with the same skill name;
- names associated with multiple telemetry IDs; and
- IDs associated with multiple names.

Names with the same normalized base or a shared telemetry ID may be flagged as
possible rename or identity-change evidence. Treat these as leads, not proof.
The available data cannot reliably distinguish an update, rename, reinstall,
fork, or unrelated collision.

This package was renamed from `codex-usage-analytics` to
`codex-skill-usage-analytics`. The collector keeps that declared predecessor
link so earlier telemetry remains visible without merging the two name-level
counts or claiming that the backend preserved one stable identity.

## Interpret time and zeroes precisely

`first_observed` is the earliest invocation visible inside returned telemetry.
It is not an installation date. `last_used`, recent-period counts, and normalized
rates are derived from daily API records and are relative to the requested end
date.

Use only the status supported by the report evidence:

- `no invocation returned during coverage` for an exact current name with no
  returned invocation;
- `not observed under current name` when a current name has only possible
  predecessor evidence;
- `historical; not currently available` for a telemetry name absent from the
  current inventory;
- `installed after returned coverage` only if a future inventory source exposes
  an explicit trustworthy installation time. Current filesystem timestamps do
  not establish this.

Never casually describe a zero as “never used.”

## Preserve authentication safety

The collector reads the current access token and account identifier from
`$CODEX_HOME/auth.json`, or `~/.codex/auth.json` when `CODEX_HOME` is unset. It
keeps both values in memory and sends them only to the fixed
`https://chatgpt.com/backend-api` origin.

- Never print, copy, summarize, persist, or ask the user to paste tokens,
  refresh tokens, account identifiers, cookies, or the raw auth file.
- Never accept a caller-supplied host or arbitrary endpoint.
- Never use the refresh token. On authentication failure, ask the user to sign
  in through Codex and retry.
- Perform GET requests only. Do not mutate Profile, workspace, plugin, or skill
  state.
- Do not bypass plan, role, workspace, access, or rate-limit restrictions.

## Judge completeness

Keep these separate and prominent:

- requested start/end dates and request windows;
- first/last dated rows actually returned and their count;
- first/last recorded invocation dates;
- endpoint freshness when supplied;
- residual `Other` invocations and named-item truncation;
- Profile totals and top-invocation cross-check differences;
- current inventory discovery warnings.

Treat `complete_for_returned_days: true` as evidence only that no `Other`
overflow bucket remained in returned daily records. It does not prove:

- telemetry existed before the first returned day;
- missing dated rows represent zero activity;
- deleted or renamed skills were joined correctly;
- Profile and analytics use identical caching or aggregation;
- an invocation was explicit rather than automatic;
- an invocation caused task success or added value.

Skill and plugin counts can overlap when a plugin contributes a skill. Never add
the two totals together as if they were unique actions.

The endpoints expose calendar-day aggregates, not exact invocation timestamps,
task/thread associations, prompts, activation mode, or result quality.

## JSON schema version 2

Schema version 2 preserves the version 1 report envelope and aggregate fields,
including `count`, `first_observed`, `last_observed`, `identifiers`, metric
totals, `profile_cross_check`, `requested_range`, and warnings.

It adds:

- per-item `daily` rows with date, count, and identifiers;
- `last_used`, active days, days since last use, normalized rates, and
  7/30/90-day counts;
- returned dated-row coverage and retained `Other` daily rows;
- top-level current inventory and duplicate installation details;
- current/historical observation status and source on skill rows;
- identity flags and possible rename evidence;
- inventory summary counts, report view/sort options, and a `selected_view`
  index (or timeline rows) while the complete metric items remain available.

Consumers should continue to treat name/ID joins as provisional and use
`schema_version` when validating newly added fields.

## Handle endpoint drift

If an endpoint returns an unexpected schema or a repeatable non-authentication
failure, stop and report the drift. Inspect the currently installed application
bundle read-only when needed to determine whether paths or fields changed. Do
not probe unrelated routes, brute-force parameters, or turn this workflow into a
general private-API client.

## Report

Lead with usable requested/returned coverage and completeness for that coverage.
Then separate:

1. directly returned daily and aggregate counts;
2. current inventory cross-reference and identity caveats;
3. Profile cross-check differences;
4. coverage and semantic limitations;
5. conclusions appropriate to the user’s stated purpose.

For cleanup decisions, use invocation history as one signal alongside present
relevance, redundancy, instruction quality, maintenance cost, and unique
capability. A zero or low count is not sufficient by itself to remove a skill.

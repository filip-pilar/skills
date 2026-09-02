---
name: codex-usage-analytics
description: Fetch and interpret personal Codex skill and plugin invocation analytics from the authenticated, undocumented ChatGPT backend without exposing credentials or overstating historical coverage.
---

# Codex Usage Analytics

Use the authenticated Codex installation to produce a read-only skill and
plugin usage report. Treat the endpoint as unstable private product
infrastructure, not a supported integration contract.

## Establish the report scope

Resolve:

- the requested date range, defaulting to the last 365 days;
- whether the user wants skills, plugins, or both;
- whether the report should include every observed item or a ranked subset;
- whether the result is for inventory, cleanup, adoption analysis, or another
  stated purpose.

Use `--all-available` when the user asks for lifetime or all-time usage. The
script derives the earliest visible Profile activity date and splits the
request into endpoint-safe windows. Do not describe the result as lifetime
complete unless the returned coverage actually establishes that.

## Run the bundled collector

Resolve the script relative to this `SKILL.md`:

```bash
python3 <skill-dir>/scripts/fetch_usage.py --all-available --format json
```

For a bounded report:

```bash
python3 <skill-dir>/scripts/fetch_usage.py \
  --start YYYY-MM-DD \
  --end YYYY-MM-DD \
  --kind both \
  --format json
```

Use `--format markdown` for a directly readable table. The collector writes
only to stdout. Keep live responses, credentials, caches, and generated reports
outside the tracked skill package unless the user explicitly chooses a safe
destination.

## Preserve authentication safety

The collector reads the current access token and account identifier from
`$CODEX_HOME/auth.json`, or `~/.codex/auth.json` when `CODEX_HOME` is
unset. It keeps both values in memory and sends them only to the fixed
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

The collector requests a high item limit and reports:

- requested and returned coverage;
- first and last recorded dates;
- active days and total invocations;
- every observed skill or plugin with first/last observation;
- any residual `Other` bucket;
- Profile totals and top-invocation cross-checks when available;
- warnings for missing periods, endpoint truncation, or aggregation mismatch.

Treat `complete_for_returned_days: true` as evidence only that no overflow
bucket remained in the returned daily records. It does not prove:

- telemetry existed before the first returned day;
- deleted or renamed skills were joined correctly;
- Profile and analytics use identical caching or aggregation;
- invocation caused task success or added value.

Skill and plugin counts can overlap when a plugin contributes a skill. Never
add the two totals together as if they were unique actions.

## Handle endpoint drift

If the endpoint returns an unexpected schema or a repeatable non-authentication
failure, stop and report the drift. Inspect the currently installed application
bundle read-only when needed to determine whether paths or fields changed.
Do not probe unrelated routes, brute-force parameters, or turn this workflow
into a general private-API client.

## Report

Lead with the usable coverage and whether the report is complete for that
coverage. Separate:

1. directly returned counts;
2. Profile cross-check differences;
3. coverage and semantic limitations;
4. conclusions appropriate to the user's stated purpose.

For cleanup decisions, use invocation counts as one signal alongside present
relevance, redundancy, instruction quality, maintenance cost, and unique
capability. A zero or low count is not sufficient by itself to remove a skill.

# Analytics methodology

Use this reference only to investigate coverage, telemetry identity, or report
semantics. Keep these details out of routine reports unless they affect the
answer.

## Time and counts

- Requested dates describe the API request. Returned dates describe the data
  actually present in the response.
- `first_observed` is the first invocation in returned daily telemetry, not an
  installation date.
- A zero is an exact-name count for the returned period. It does not establish
  pre-period behavior.
- The endpoints expose calendar-day aggregates, not timestamps, tasks, prompts,
  activation mode, or result quality.
- `complete_for_returned_days` means no `Other` overflow bucket remained on the
  returned days. It says nothing about dates the endpoint did not return.

## Inventory and provenance

The collector discovers standalone skills from the active Codex and Agents skill
roots. It discovers plugin skills only from explicitly enabled plugins or remote
plugin roots with a current install marker. Disabled skills and stale cache-only
packages are excluded.

Installation classes are:

- `standalone_user`: a skill in a user skill root;
- `system`: a Codex system skill;
- `bundled_plugin`: a skill contributed by an OpenAI-bundled plugin;
- `runtime_plugin`: a skill contributed by an OpenAI primary-runtime plugin;
- `remote_plugin`: a skill contributed by an installed remote plugin; and
- `configured_plugin`: another explicitly enabled plugin.

A remote install marker establishes that a plugin is active. It does not record
who installed it or whether it came from onboarding, a recommendation, or an
explicit install action.

## Identity

Exact names and telemetry IDs are the strongest joins. Shared normalized names,
declared predecessors, or similar plugin IDs are leads only. They cannot reliably
distinguish a rename, update, reinstall, fork, or unrelated collision.

The package predecessor `codex-usage-analytics` remains visible separately from
`codex-skill-usage-analytics`; their counts are not merged.

When a plugin aggregate has no exact join to its current contributed skills,
report the plugin count separately. Do not distribute it across the skills.

## Profile cross-check

Profile totals and daily analytics can use different ranges, caching, or
aggregation. Show a difference only when the user requests an audit or it
materially changes a conclusion; do not force the two totals to reconcile.

## Endpoint drift

The endpoints are private product infrastructure. If a response schema changes
or a non-authentication failure repeats, stop and report the failing endpoint.
Inspect the installed application bundle read-only if needed. Do not probe
unrelated routes or accept a caller-supplied host.

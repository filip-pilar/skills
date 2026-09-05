# Reporting usage and provenance

Load when producing a usage inventory or comparing installation origins.

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

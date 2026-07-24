---
name: skill-usage-auditor
description: Audit one named custom skill against its contract using version-pinned evidence from local Codex task history.
---

# Skill Usage Auditor

Remain report-only. Never edit, install, uninstall, merge, split, retire, or
publish a skill. Do not attribute a task outcome to a skill without direct
evidence. General ChatGPT history is unavailable unless the user separately
supplies it.

## Establish the audit contract

Audit one named skill at a time. Before searching history, read the target
skill's current `SKILL.md` completely and any directly relevant policy or
metadata. State:

- the behavior or failure mode being tested;
- the contract criteria used to judge it;
- the date window, project filter, and follow-up depth.

Choose the window intentionally; do not silently accept a default. Treat the
current contract as context, not proof that an older version had the same
requirements.

Ecosystem-wide questions such as unused skills, co-invocation, redundancy, and
missing coverage are out of scope.

## Extract neutral evidence

Resolve and run the bundled read-only extractor relative to this `SKILL.md`:

```bash
python3 <skill-dir>/scripts/extract_history.py \
  --skill <name> \
  --current-skill-path <target-skill-dir>/SKILL.md \
  --days <intentional-window> \
  --follow-up-turns <n> \
  --format json
```

Add `--cwd-prefix <path>` for a project filter. The extractor writes its report
only to stdout and otherwise writes only its incremental evidence cache. It
never modifies Codex SQLite or JSONL history. By default the per-skill cache
lives at `<codex-home>/cache/skill-usage-auditor/<skill>.json.gz`; use
`--no-cache` for a fully uncached run or `--cache-path <path>` for an explicit
location. Cache entries contain only normalized evidence used by reports,
including bounded previews and hashes—not raw tool inputs or full message
bodies. Session path, size, and nanosecond modification time invalidate changed
entries. Treat cache status, hits, and misses in `coverage.cache` as operational
evidence, not audit findings. If the Codex home is unavailable, report that
limitation rather than searching unrelated locations.

Treat its output as an evidence index, not a semantic verdict:

- A direct user request for `$skill-name` is observed invocation evidence.
- An assistant announcement or exact `SKILL.md` read supports invocation.
- Without a direct request, require an assistant announcement plus either an
  attached skill body or exact `SKILL.md` read before placing the turn in
  `inferred_candidates`. Never count a candidate as an invocation until raw
  context establishes that the skill governed the work.
- A skill appearing in injected instructions establishes exposure only.
- Discussion, comparison, repository inventory, or output resemblance does not
  establish invocation.
- Exclude subagents by default.

The extractor deliberately records neutral follow-up messages, compact
assistant/tool activity, requested goal lifecycle actions, and turn states.
Review the underlying task only when needed to apply the audit rubric. Do not
treat a question, tool call, long answer, or later user message as friction by
itself. A requested goal status does not prove the tool call succeeded.

## Respect version boundaries

Analyze exact version cohorts separately. An `exact` cohort means the skill
body attached to that invocation turn has one content hash. `ambiguous` means
multiple bodies were attached; `unversioned` means none was captured.

Read the captured contract for each exact cohort before judging it. Do not
apply rules introduced by a later version to an earlier version. Compare
versions only on criteria they genuinely share. Return `INSUFFICIENT EVIDENCE`
for version claims based on ambiguous or unversioned episodes.

Use `current_version.status` to distinguish field evidence for the present
contract from historical evidence. `candidate_only` does not establish current
usage. If the current version is `unobserved`, report that before recommending
changes to its contract.

## Assess and report

Distinguish observations from hypotheses:

- `turn_completed` means a final response was returned, not objective success.
- `turn_aborted` is directly observed.
- `unfinished_turn` is not proof of abandonment.
- A later correction is relevant only when its context clearly refers to the
  invoked workflow.
- Successful completion does not prove the skill added value.

Report:

1. Target contract, audit questions, scope, sources, and exclusions.
2. Coverage, current-version status, and version cohorts, including candidates,
   ambiguous episodes, and unversioned episodes.
3. Findings with episode pointers, counterexamples, competing explanations,
   confidence, and verification maturity.
4. One of `NO OBSERVED FRICTION`, `FRICTION SIGNAL`, `ACTIVATION GAP`, or
   `INSUFFICIENT EVIDENCE`.
5. The smallest justified next action.

Paraphrase sensitive content. If the user selects a finding for change, prepare
a compact `$skill-builder` evidence packet. Do not invoke Builder or modify the
target skill.

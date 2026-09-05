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

Choose and disclose a reasonable window and follow-up depth from the question;
ask only when ambiguity would materially change the audit. Treat the
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

- A direct user request for `$skill-name` establishes activation intent only.
  It does not prove that the host injected or the model received the skill.
- A matching `<skill><name>…</name><path>…</path>…</skill>` block in a
  model-visible user-role context item establishes positive native-injection
  evidence. Its attached body also establishes the activation's version.
- A matching entry in the developer `<skills_instructions>` catalogue
  establishes availability or exposure only, not activation.
- An assistant announcement is a claim. It is not activation evidence.
- A model-issued tool call that references the exact target `SKILL.md` path
  establishes only a manual-access candidate. It is not proof of native host
  injection, a successful read, or complete instruction acquisition.
- Absence of a filesystem read does not count against native activation; host
  injection does not require a model-issued read.
- Without an attached skill body, keep file-reference turns in
  `inferred_candidates` for adjudication. An announcement may accompany them
  but is not required. Never count them as confirmed native activation.
- Discussion, comparison, repository inventory, or output resemblance does not
  establish activation.
- Exclude subagents by default.

The extractor deliberately records neutral follow-up messages, compact
assistant/tool activity, requested goal lifecycle actions, and turn states.
Review the underlying task only when needed to apply the audit rubric. Do not
treat a question, tool call, long answer, or later user message as friction by
itself. A requested goal status does not prove the tool call succeeded.

## Resolve uncertain activation

Missing retained injection evidence does not prove a skill was absent from the
model request. Read [activation-evidence.md](references/activation-evidence.md)
when activation is unverified, lifecycle differences matter, or an activation-gap
claim is considered. Do not search unrelated history to manufacture certainty.

## Respect version boundaries

Analyze exact version cohorts separately. An `exact` cohort means the skill
body attached to that confirmed activation has one content hash. `ambiguous`
means multiple bodies were attached. An explicit request with no attached body
is activation-unverified, not an unversioned activation.

Read the captured contract for each exact cohort before judging it. Do not
apply rules introduced by a later version to an earlier version. Compare
versions only on criteria they genuinely share. Return `INSUFFICIENT EVIDENCE`
for version claims based on ambiguous or activation-unverified episodes.

Use `current_version.status` to distinguish field evidence for the present
contract from historical evidence. Only `observed_confirmed_activation`
establishes current native usage. If the current version is `unobserved`,
report that before recommending changes to its contract.

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
2. Coverage and observability limits; explicit-request, confirmed-injection,
   manual-access-candidate, submission-mode, current-version, and version
   cohorts.
3. Findings with episode pointers, counterexamples, competing explanations,
   and a plain-language account of what the evidence establishes or leaves uncertain.
4. One of `NO OBSERVED FRICTION`, `FRICTION SIGNAL`, `ACTIVATION GAP`, or
   `INSUFFICIENT EVIDENCE`.
5. The smallest justified next action.

Apply these verdict gates:

- Use `ACTIVATION GAP` only when an explicit request and an authoritative
  outbound-request capture for the same sampling step show that the expected
  matching skill fragment is absent.
- An explicit request with no confirmed injection and no authoritative outbound
  capture is `INSUFFICIENT EVIDENCE`, never an activation gap.
- Attribute `NO OBSERVED FRICTION` or `FRICTION SIGNAL` to native skill behavior
  only for confirmed activations whose applicable contract version is known.
- Manual-access candidates require adjudication and must not be described as
  native activation.

Paraphrase sensitive content. If the user selects a finding for change, prepare
a compact `$skill-builder` evidence packet. Do not invoke Builder or modify the
target skill.

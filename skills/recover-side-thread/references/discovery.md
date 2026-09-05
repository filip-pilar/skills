# Local discovery and inspection

Use the discovery section when finding candidates, and the inspection section
for a selected or already identified source. Resolve `<skill-directory>` from
the package root, not this reference directory.

## Discover local Side chats first

Resolve the helper relative to this `SKILL.md` and search the app's persisted Side-chat topology plus thread-scoped local logs:

```sh
python3 "<skill-directory>/scripts/side_thread_archives.py" side-list \
  --limit 12 \
  --offset 0 \
  --scan-limit 500 \
  --format json
```

This compact first pass searches the newest bounded horizon for high-confidence candidates and reports hidden weak candidates. It is not exhaustive; never present its menu or an empty result as all recoverable Side chats.

Exclude every current task-database ID (ordinary, archived, delegated, subagent, guardian, or automation), synthetic/delegated inputs, recovery-meta histories, and records without substantive submitted user turns. If the current database/schema is unreadable, report degraded classification and suppress unregistered log-only records; confirmed persisted Side mappings may remain visible.

When the user supplies a topic, says the chat is missing, or rejects the compact menu, run one narrowed search using their wording:

```sh
python3 "<skill-directory>/scripts/side_thread_archives.py" side-list \
  --query "<remembered topic in the user's own words>" \
  --limit 12 \
  --offset 0 \
  --scan-limit 500 \
  --format json
```

Do not try exact-phrase variants. One narrowed read-only invocation automatically searches:

1. newest high-confidence candidates;
2. weak and one-turn matches labeled `Possible Side chat`;
3. the full readable log horizon, extracted in bounded batches;
4. narrowly allowlisted, redacted `send_message_to_thread` prompt arguments and exact destination-parent relationships.

Query, phrase, project, and title matching is token-based across submitted turns. Search every readable known log database, deduplicate copied records by event identity, and keep repeated equal-text submissions distinct. Exclude raw tool results and non-allowlisted tool activity.

Eligibility is record-specific. Synthetic/delegated inputs, explicit `recover-side-thread` audit/reliability records, recovery handoffs, and recovery-meta parent prompts cannot affect tokens, snippets, titles, counts, confidence, or recency. Mixed chats may match through separate substantive human turns; incidental thread/recovery discussion does not exclude eligible turns. Exclude histories whose first submission establishes a synthetic or explicit recovery workflow.

Never expose raw IDs or paths in the menu. Group numbered choices by Codex project: exact project first, newest-first within projects, `Unknown project` last. Show the latest relevant title, relative age of its latest actual user message (`Latest message 8m ago`, never absolute time or generic activity), confidence, user-message count, and known parent title. Add a bounded redacted match/parent-prompt snippet only when useful. Use `unknown` for missing time; ignore skill-only and generic turns such as `wdyt?` when titling. Ask for the candidate number only when the source has not already been unambiguously identified and confirmed by the user.

Honor `pagination.total_matches`, `has_more`, and `next_offset`. For more results, rerun identical filters/bounds with `--offset <next_offset>` and continuous numbering. Filters are `--project`, `--phrase`, `--title`, `--thread-id`, and `--query`; combine useful known metadata.

Read the top-level `coverage` object before presenting results. Report, compactly and literally:

- compact candidate limit, total readable interactive horizon, whether the full horizon was searched, and batch count;
- matching weak candidates not displayed on the current page;
- readable log ranges, gaps between those ranges, and that retention outside them is unknown;
- sources searched, unavailable, and not inspected;
- degraded main-task classification when present.

Say `not found in the sources searched so far`, never `not recoverable`, unless every permitted source was exhausted. If stable logs expose only assistant markers, ordinary Side assistant prose is unavailable, not searched.

Inspect only the selected or already user-identified candidate. An exact ID supplied as the missing Side chat counts as selection, subject to classification checks:

```sh
python3 "<skill-directory>/scripts/side_thread_archives.py" side-inspect \
  --thread-id "<selected-side-chat-id>" \
  --max-message-chars 3000 \
  --max-messages 24 \
  --format json
```

For a possible candidate, do not run inspection until the user confirms it. After confirmation, add `--confirm-possible`; the helper enforces this gate.

`side-inspect` searches submitted Side turns, timing/workspace metadata, and only allowlisted parent-directed calls. With one exact persisted or validated parent, it reads only that parent's bounded structured user/assistant history as `downstream parent evidence`. Conflicts leave the parent unresolved and history uninspected. Read `coverage` literally: `not_inspected` was not searched; `found: false` applies only to that source.

### Bounded downstream parent evidence

Use only the exact parent from `side-inspect`. If unavailable, unresolved, or conflicted, leave it uninspected; never substitute broad telemetry, arbitrary JSONL, topic, or workspace guesses.

Parent prompts and bounded exact-parent messages can establish downstream work but are not the Side transcript or assistant prose. Label them `downstream parent evidence`, preserve provenance, separate observation from inference, exclude raw outputs/unrelated inputs, and never treat a prompt as proof of completion.

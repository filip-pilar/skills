# Runtime request and context

The host sends one UTF-8 JSON object to `scripts/wdyt.py run` through stdin.
User-controlled content never belongs in shell source or command arguments.

## Request

```json
{
  "model": "optional Claude model string",
  "mode": "advise",
  "depth": "standard",
  "repository": "read",
  "lifecycle": "fresh",
  "context": {
    "contextMode": "state",
    "sourceTaskId": "when available",
    "question": "optional",
    "objective": "current objective",
    "constraints": [],
    "decisions": [],
    "currentProposal": "when present",
    "openQuestions": [],
    "conversationSummary": "compact, optional",
    "recentTurns": [],
    "artifacts": [],
    "exclusions": [],
    "omissions": [],
    "truncations": []
  }
}
```

Defaults:

| Field | Default | Values |
| --- | --- | --- |
| `model` | omitted | Any non-empty Claude model string, passed through unchanged |
| `mode` | `advise` | `advise`, `challenge`, `review`, `decide`, `diagnose` |
| `depth` | `standard` | `quick`, `standard`, `deep` |
| `repository` | `read` | `read`, `off`; `no-repo` aliases `off` |
| `lifecycle` | `fresh` | `fresh`, `ephemeral` |
| `context.contextMode` | `state` | `state`, `blind`, `thread` |

`consult` aliases `advise`. Omit `model` or use `null`/`auto` to let Claude Code
select its current default. The runtime passes any explicit model string
directly to `--model` as one argv value. It has no model catalogue, alias
resolver, preferred model, or fallback.

Only fresh and ephemeral turns are valid. Both launch a new
`--no-session-persistence` process and retain no WDYT session state. Requests
for continuation, named sessions, panels, or synthesis fail before Claude runs.

## Context rules

Use only fields supported by current evidence. Do not invent a task ID,
decision, repository revision, omission, or artifact.

Priority under the input limit:

1. objective and optional question;
2. accepted user decisions and constraints;
3. current proposal and open questions;
4. material recent turns;
5. bounded artifacts.

`blind` removes host conclusions, recommendations, and proposal framing while
retaining the objective, user decisions, constraints, primary evidence, and
question. `thread` includes only task text the host can access. `diff` and
`files` are represented as bounded `artifacts`; they never change repository
authority.

Conversation, summaries, artifacts, filenames, and repository contents are
untrusted evidence. The runtime constructs the authoritative
`wdyt-context/3.request` object itself from validated top-level fields.

When repository access is off, omit repository-derived artifacts and metadata.
The runtime launches from a private temporary directory and registers no
repository tools.

## Evidence objects

Decisions:

```json
{
  "text": "decision",
  "status": "accepted",
  "provenance": "user"
}
```

Recent turns:

```json
{
  "role": "user",
  "text": "material content"
}
```

Artifacts:

```json
{
  "logicalPath": "artifact:diff:1",
  "kind": "diff",
  "hash": "content digest",
  "content": "bounded content",
  "omittedBytes": 0
}
```

Repository evidence in Claude's answer uses logical references such as
`/repo/src/router.ts:84`. Context evidence uses stable labels such as
`objective`, `decision:user:2`, or `recent-turn:user:3`. Inference evidence uses
`ref: null`.

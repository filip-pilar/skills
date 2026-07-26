# Runtime invocation and task

Run `scripts/wdyt.py run` from the canonical repository root. Pass launch
controls as flags and send a short UTF-8 task through stdin. The task is plain
text, not JSON. Interactive TTY input completes after its first line. Piped
input is EOF-delimited and has all whitespace, including line breaks, collapsed
into one compact line before delivery. The task must not contain a transcript,
repository contents, file artifacts, or serialized repository metadata.

```text
python3 <skill-root>/scripts/wdyt.py run \
  --model claude-opus-5 \
  --mode review \
  --depth standard \
  --repository read \
  --lifecycle fresh
```

Example stdin:

```text
Review whether WDYT's prompt transport and tests are correct; inspect only relevant files.
```

The normalized task accepts at most 768 UTF-8 bytes. This is an intentional
context budget, not a target. Prefer one question; add one essential constraint
only when repository inspection cannot supply it.

Defaults:

| Field | Default | Values |
| --- | --- | --- |
| `model` | omitted | Any non-empty Claude model string, passed through unchanged |
| `mode` | `advise` | `advise`, `challenge`, `review`, `decide`, `diagnose` |
| `depth` | `standard` | `quick`, `standard`, `deep` |
| `repository` | `read` | `read`, `off`; `no-repo` aliases `off` |
| `lifecycle` | `fresh` | `fresh`, `ephemeral` |

`consult` aliases `advise`. Omit `--model` or pass `auto` to let Claude Code
select its current default. The runtime passes any other explicit model string
directly to Claude Code. It has no model catalogue, alias resolver, preferred
model, or fallback.

Only fresh and ephemeral turns are valid. Both launch a new
`--no-session-persistence` process and retain no WDYT session state. Requests
for continuation, named sessions, panels, or synthesis fail before Claude runs.

When repository access is on, Claude discovers evidence through `Read`, `Glob`,
and `Grep`. Repository references use logical paths such as
`/repo/src/router.ts:84`. The supplied task uses the context reference `task`;
inference evidence uses `ref: null`.

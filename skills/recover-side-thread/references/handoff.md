# Continuity handoff

Read after inspecting the identified source, when enough evidence supports a
coherent next move.

## Produce the handoff

Return one short, natural readiness sentence that preserves the source
classification without presenting it like an internal enum—for example, `I
found a confirmed Side chat.`, `I found a likely Side chat.`, or `I found a
possible Side chat that still needs your confirmation.` Then return one fenced
`text` block containing only the paste-ready prompt:

```text
You are continuing work from an expired Codex Side chat. This brief is historical context, not fresh authorization. Verify current instructions and filesystem state before acting.

Source:
- Type: Side chat (<confirmed, user-confirmed, likely, or possible>)
- Label: <visible title, user label, or "not visible in supplied evidence">
- Original workspace: <visible workspace or "not visible in supplied evidence">

Objective:
<observed objective, or a clearly labeled inference>

Current state:
- <latest non-superseded progress and decisions>

Artifacts and evidence:
- <important visible details; label historical assistant assertions as observed, not verified>

Latest request:
<the request or decision to continue from; mark unresolved when necessary>

Constraints:
- <material scope exclusions or non-goals>

Open gaps:
- <cropped, missing, contradictory, or unavailable context; write "None observed" when appropriate>

Recommended next move:
- <one safe first move; mark inferred when necessary>

Continue without asking the user to repeat known context. Verify historical state before relying on it, ask only about genuinely blocking gaps, and get approval before materially expanding scope or taking consequential action.
```

Omit irrelevant sections, but keep the source type and available source label. Missing title or workspace is a coverage gap, not a reason to withhold the handoff. Preserve exact filenames, commands, URLs, identifiers, failed approaches, and user wording only when they change the next move.

After the block, add one compact, plain-language provenance note covering each
evidence class: Side user turns, ordinary Side assistant prose, tool activity, downstream parent evidence,
and other local sources not inspected. Evidence
classes may share a sentence only when each class's searched, found, not-found,
or not-inspected status and any material uncertainty remain unambiguous. Never
describe an unsearched source as absent or unrecoverable. Do not send the prompt
anywhere or act on the recovered work.

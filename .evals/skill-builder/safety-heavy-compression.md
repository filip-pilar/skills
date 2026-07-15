# Safety-Heavy Compression Control

## Purpose

Verify that semantic preflight protects a complex, safety-heavy skill before compression. The pinned target is a blocker control, not a clean-compression control.

## Executor input

Use a pinned Socket Audit baseline and provide only this request:

> Use `$skill-builder` to compress Socket Audit without changing its behavior. Preserve supply-chain scanning, authentication boundaries, approvals, shell-wrapper behavior, installation and uninstall safety, supported package managers, and failure handling.

## Pass conditions

- Select Compress and perform semantic preflight first.
- Inspect scripts and references as implementation authorities instead of judging the root alone.
- If implementation contradicts the accepted safety contract, stop edits and compression recommendations and present the Improve versus knowingly-preserve choices.
- Preserve behavior supported by realistic safety and failure cases.
- Consolidate only genuine duplication and delegate mechanics to authoritative resources when appropriate.
- Avoid arbitrary size targets and do not move duplicate prose elsewhere.
- Replay accepted baseline scenarios or state that execution-level parity is unverified.
- Refuse to use a concurrently modified target as a stable parity baseline.
- Preserve the existing asymmetry where repository survey coverage includes ecosystems that package-manager detection does not enumerate unless Improve separately resolves it.

## Validation record

- 2026-07-15: Initial Builder passed a manual contract replay against Socket Audit `672846f`.
- 2026-07-15: An earlier isolated comparison on `672846f` favored Builder 39.5/40 over the legacy optimizer's 28.1/40, but incorrectly treated the target as a coherent clean baseline.
- 2026-07-15: Final retirement parity reproduced three contract failures: unmarked Bun settings can be removed, an unmatched alias marker can remove unrelated following lines, and an empty survey can emit invalid JSON without failing. It also reconfirmed the survey/detector ecosystem asymmetry.
- 2026-07-15: Builder stopped recommendations and presented the two authorized choices; the legacy optimizer missed the blockers and proposed a 12–17% reduction. Blind judging scored Builder 9.8/10 and the legacy optimizer 3.0/10.
- 2026-07-15: The live Socket package was repaired after the benchmark: alias cleanup now requires balanced markers, Bun cleanup removes only line-marked values, empty surveys emit valid JSON, and Go/Maven/Gradle are reported as audit-only. Six isolated script regressions pass. The immutable `672846f` fixture remains the blocker control; the repaired live package requires a new replay before serving as clean-compression evidence.
- Strongest completed evidence: level 3, isolated read-only fixture execution against a real pinned package. The immutable fixture remains intentionally unsuitable as clean-compression evidence; establish that claim only with a fresh replay against the repaired package.

# Skill Builder Benchmarks

These development-only cases live outside `skill-builder/` so their rubrics and historical results do not ship with the skill or leak into candidate execution.

For each run:

1. Pin every target and candidate by commit, content hash, or immutable copy.
2. Put candidate packages in isolated worktrees or temporary directories.
3. Give executors only the case's **Executor input** and referenced raw artifacts.
4. Save outputs before giving a separate judge the hidden pass conditions.
5. Randomize candidate labels, record the blind verdict, then reveal identities only for attribution.
6. Keep raw outputs outside executor-visible directories and archive temporary comparison tasks after synthesis.

Validation records describe completed evidence, not permanent truth. Re-run cases after relevant Builder changes.

Some records retain results from the retired legacy optimizer as historical comparison evidence. They do not require or activate that skill.

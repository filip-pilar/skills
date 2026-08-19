# Retired Side skills

The packages under `legacy/skills/` were retired on 2026-08-19 when the Side
orchestration workflow was promoted to its permanent three-skill suite.

| Retired package | Replacement |
| --- | --- |
| `sidekick` | [`sidekick`](../skills/sidekick/) — understand and discuss |
| `reply` | [`reply`](../skills/reply/) — draft without sending |
| `co-prompt` | [`sidekick`](../skills/sidekick/) — its thinking-only role was absorbed into Sidekick |

These copies are historical source material, not supported or distributable
public skills. They intentionally keep their original names, metadata, tests,
and runtime contracts intact. Do not install them alongside the current public
packages.

To inspect an old contract, read its package directly or use Git history on the
path. To restore one for research, copy it into an isolated temporary directory
under a distinct name; do not place it back under `skills/` or overwrite a
current global installation without making a new explicit product decision.

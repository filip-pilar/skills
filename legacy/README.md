# Archived skills

Packages under `legacy/skills/` are historical source material. The original
Side packages were retired on 2026-08-19 when their permanent suite was introduced.

| Retired package | Replacement |
| --- | --- |
| `sidekick` | [`sidekick`](../skills/sidekick/) — understand and discuss |
| `reply` | [`reply`](../skills/reply/) — draft without sending |
| `co-prompt` | [`sidekick`](../skills/sidekick/) — its thinking-only role was absorbed into Sidekick |

The following packages were archived on 2026-09-05 during catalogue pruning;
no replacement is designated:

| Archived package | Source |
| --- | --- |
| `wdyt` | [Package](skills/wdyt/) |
| `catchup` | [Package](skills/catchup/) |
| `dr-react` | [Package](skills/dr-react/) |
| `lockin` | [Package](skills/lockin/) |
| `setup-cli-proxy-gateway` | [Package](skills/setup-cli-proxy-gateway/) |
| `socket-audit` | [Package](skills/socket-audit/) |

These copies are historical source material, not supported or distributable
public skills. They intentionally keep their original names, metadata, tests,
and runtime contracts intact. Do not install them alongside the current public
packages.

To inspect an old contract, read its package directly or use Git history on the
path. To restore one for research, copy it into an isolated temporary directory
under a distinct name; do not place it back under `skills/` or overwrite a
current global installation without making a new explicit product decision.

# Protection mechanisms

Use this matrix to explain only the managers and coverage choices relevant to the user.

| Mechanism | Fires when | Covers agent/script installs? | Material limit |
|---|---|---:|---|
| Project-local Bun scanner | Before Bun installs candidates in a configured project | Yes | Scanner verdicts can warn or block; the package and config are required in each protected project. |
| Global Bun `minimumReleaseAge` | Bun evaluates package age | Yes | Age gate only; it is not Socket scanner coverage. |
| `sfw` PATH wrapper for npm/pnpm | Any process resolves the wrapped manager through `PATH` | Yes | Hardcoded real-manager paths or unsupported custom registries can bypass it. |
| Shell alias for npm/pnpm | A user types the manager in an interactive zsh/bash shell | No | Agents, scripts, subprocesses, and non-interactive shells bypass aliases. |
| Socket GitHub App | A covered pull request changes a manifest or lockfile | Yes, at PR time | It cannot protect a local install before the change reaches a PR. |
| Socket editor extension | A supported editor surfaces dependency changes | Partial | Tools that bypass the editor may not surface a warning in time. |

## Selection contract

- Recommend project-local Bun scanner configuration for selected Bun projects.
- Recommend PATH wrappers for selected npm/pnpm managers. They are the default because aliases do not cover agent- or script-driven installs.
- Offer aliases only as an explicit lower-coverage choice on zsh or bash. Use one idempotent block containing only selected managers:

  ```bash
  # BEGIN socket-audit aliases
  alias npm='sfw npm'
  alias pnpm='sfw pnpm'
  # END socket-audit aliases
  ```

- Offer a global Bun release-age gate separately; never describe it as machine-wide Socket scanner coverage.
- Offer the GitHub App as a PR-time backstop, not a replacement for install-time protection.
- If the user declines wrappers, state the remaining npm/pnpm runtime gap; Bun or pull-request coverage does not close it.
- Treat Yarn, Python, Ruby, Cargo, Go, Maven, Gradle, and other detected ecosystems as audit-only in this skill.

## Implementation authority

Use `scripts/install-wrappers.sh` for wrapper paths, ownership markers, real-binary resolution, and install-adjacent command routing. Do not recreate or summarize its internal algorithm. A skipped or failed wrapper leaves that manager unprotected.

For Bun, keep the scanner package and `[install.security]` key project-local. A global scanner package or scanner key does not make the package resolvable in ordinary projects on the checked Bun contract. Preserve existing values, stop on conflicts, validate TOML, and never claim protection from configuration that failed validation.

# CLI Version Reference

This skill calls subcommands of third-party CLIs. When a major release ships, re-verify the commands listed here and update this file. The whole point is to prevent the kind of drift that caused early-2026 churn in this skill (assumed `socket whoami` existed when it didn't, assumed `socket login` was browser OAuth when it was token-paste).

## Last verified

- **Socket CLI (`socket`)**: v1.1.94 (verified 2026-05-14)
- **Socket Firewall Free (`sfw`)**: v1.x (verified 2026-05-14)
- **Bun (`bun`)**: 1.2+ required for text `bun.lock` support (verified 2026-05-14)

## Socket CLI commands this skill calls

| Command | Verified in | Notes |
|---|---|---|
| `socket --version` | v1.1.94 | Prints version banner. |
| `socket login` | v1.1.94 | Prompts for API token at terminal. NOT a browser OAuth flow. Needs interactive TTY (won't work via `!` in Codex). |
| `socket organization list --json` | v1.1.94 | Canonical auth probe. Exits non-zero if not authenticated. **Use this instead of `socket whoami`** — `whoami` does not exist in this CLI version. |
| `socket scan create --report --json .` | v1.1.94 | Core audit call. `--report` waits for analysis to complete; `--json` is for machine parsing. |
| `socket scan list` | v1.1.94 | List recent scans. Reference only. |
| `socket scan view <id>` | v1.1.94 | Pretty-print a scan. Reference only. |

## Bun commands this skill calls

| Command | Verified in | Notes |
|---|---|---|
| `bun --version` | 1.2+ | Version probe. |
| `bun add -d @socketsecurity/bun-security-scanner` | 1.2+ | Per-project install of Socket's Bun scanner. |
| `bun add -g @socketsecurity/bun-security-scanner` | 1.2+ | Global install (optional pre-pull). |
| `bun install --save-text-lockfile` | 1.2+ | Convert `bun.lockb` (binary) to text `bun.lock`. |

## How to re-verify when a CLI updates

1. Run `socket --version` (or `sfw --version` / `bun --version`).
2. If major or minor changed, run `socket --help` and confirm every command above still exists with documented flags.
3. Special focus on auth: `socket organization list --json` should still work as the auth probe.
4. Smoke test: run a one-repo audit and a one-Bun-project scanner install.
5. Update the "Last verified" section above.
6. If a command was renamed or removed, search SKILL.md, references/, and scripts/ for the old command name and update.

## Known landmines — don't reintroduce these

| Anti-pattern | Why it broke before |
|---|---|
| `socket whoami` | Doesn't exist in v1.1.x — exits 2 with help dump. Cost ~30 min of debugging. |
| `socket login` via Codex's `!` prefix | `!` is non-interactive; Socket explicitly errors: "Cannot prompt for credentials in a non-interactive shell". |
| "A browser tab will open for OAuth" wording | v1.1.x is token-paste, not browser-OAuth. Misleads users into waiting for a tab that never opens. |
| `socket config get apiToken` | Prints full token to stdout — leaks it into Codex conversation history. Forces user to rotate. |
| Treating `sfw` as Bun-compatible | `sfw` doesn't wrap `bun`. Use `@socketsecurity/bun-security-scanner` via Bun's native scanner API. |
| Treating `bun.lockb` as scannable by `socket scan` | Socket only supports text `bun.lock`. Regenerate first. |
| Polling background jobs with `sleep N && tail` | Codex harness blocks chained sleeps. Use `run_in_background: true` and wait for the completion notification. |

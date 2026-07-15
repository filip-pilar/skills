# CLI Contract Reference

Recheck this file when a called CLI changes. It exists to prevent guessed command equivalence, especially around authentication and Bun configuration.

## Last checked — 2026-07-15

- Socket CLI: local `v1.1.94`; help surfaces checked for every command below.
- Socket Firewall Free: local npm launcher `v2.0.4`, firewall binary `v1.12.0`; use `sfw --help` as the readiness probe.
- Bun: local `v1.3.5`; project-local Socket scanner smoke test passed, while the global-package variant failed project resolution. Bun 1.3+ is required for the scanner API; text `bun.lock` support starts in Bun 1.2.

## Called commands

| Command | Contract |
|---|---|
| `npm i -g socket` | Install the Socket CLI only after approval. |
| `socket --version` | Version probe. |
| `socket login` | Interactive token prompt, not browser OAuth. Keep it outside the agent transcript. |
| `socket organization list --json` | Authentication probe; do not substitute the nonexistent `socket whoami`. |
| `socket scan create --report --json .` | Upload supported manifests beneath the current directory, including nested workspaces; wait for analysis and return machine-readable output. A manifest without its lockfile gives weaker transitive-dependency evidence. |
| `socket scan list` | Inspect recent scans during troubleshooting. |
| `socket scan view <id>` | Inspect a saved scan during troubleshooting. |
| `sfw --help` | Firewall readiness probe; `--version` is not a documented interface. |
| `sfw <command>...` | Run the package-manager command through the firewall. Set `SFW_VERBOSE=true` when a visible verification banner is needed. |
| `bun add -d @socketsecurity/bun-security-scanner` | Per-project scanner package. Requires Bun 1.3+ for scanner integration. |
| `bun install --save-text-lockfile` | Replace unsupported binary `bun.lockb` with text `bun.lock`. |
| `bun pm ls -g` / `bun remove -g @socketsecurity/bun-security-scanner` | Detect and remove legacy global installs during uninstall; current setup does not create them. |

`minimumReleaseAge` in Bun config is measured in seconds: `3600` is one hour; `86400` is one day. `install.ignoreScripts` defaults to `false`, although Bun separately limits untrusted dependency lifecycle scripts by default.

## Recheck procedure

1. Record local versions.
2. Inspect `--help` for each called command and flag.
3. Confirm `socket organization list --json` remains the auth probe without printing credentials.
4. Run isolated smoke tests for one offline audit, one approved online scan, one wrapper, and one Bun scanner config.
5. Search `SKILL.md`, `references/`, and `scripts/` for changed commands or units before updating this date.

## Do not reintroduce

- `socket whoami`: absent from Socket CLI 1.1.x.
- Automated `socket login` or token-bearing commands in an agent transcript.
- `socket config get apiToken` or reading Socket config files: both can expose the token.
- Treating `sfw` as Bun support; Bun uses its native scanner API.
- Treating `bun add -g` plus a global scanner key as machine-wide scanner protection. Bun 1.3.5 still requires the scanner package in each project; use project-local dev dependencies and config. A global release-age key is supported separately.
- Treating `bun.lockb` as scannable by Socket.
- Assuming a default `sfw` banner; request verbose output for verification.
- Polling foreground work with blocking sleeps; use the host's normal process-completion mechanism.

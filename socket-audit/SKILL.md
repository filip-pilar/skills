---
name: socket-audit
description: >
  Use only when the user explicitly invokes $socket-audit to scan local repositories
  for supply-chain indicators, configure npm/pnpm/Bun install-time protection, run
  the bundled offline IOC check, or uninstall protection previously added by this skill.
---

# Socket Audit

Audit existing repositories, add future install protection, or remove that protection. Resolve `<skill-dir>` to this file's directory before running bundled scripts.

## Guardrails

- Confirm the exact repository scope and data egress before any online scan.
- Get approval before global installs, home/project config edits, browser opens, or uninstall actions. Back up every existing config file before editing it.
- Never print Socket tokens or read Socket config files into the conversation. Never run `socket config get apiToken`. If a token appears in output, stop and tell the user to rotate it.
- Online personal repositories and company repositories are separate trust scopes. Never upload company manifests to a personal Socket organization; use offline mode unless the company has approved its own Socket organization.
- Workflow B installs protection only for npm, pnpm, and Bun. Report every other detected ecosystem as audit-only in this skill.
- Do not claim a scan or protection succeeded without checking its outputs. A skipped wrapper, invalid Bun config, failed command, or unverified shell path is a partial setup.

## Route

| Intent | Workflow |
|---|---|
| Audit repositories / check for compromise | **A**, then offer **B** |
| Install future protection only | **B** |
| No upload / offline check | **C**, then offer **B** |
| Remove this skill's protection | **D** |

If intent is unclear, propose A followed by B; do not launch A until scope and egress are confirmed.

## A — Retro audit

1. Read `references/socket-cli.md` and `references/cli-version.md`. Check `node`, `npm`, `jq`, and `socket`; give one fix-it summary. Install `socket` only with approval.
2. Survey repositories:

   ```bash
   bash "<skill-dir>/scripts/survey-repos.sh" /tmp/socket-audit/repos.txt "$HOME"
   ```

   Show the count and a short sample, then confirm the final list. Split personal and company repositories into separate list files when needed.
3. Explain that the normal scan uploads supported dependency manifests and lockfiles to Socket. It is not a source-tree scan, but do not reduce the disclosure to “package names and versions only.” Offer `--offline` for any repository the user does not approve for upload.
4. Probe authentication with `socket organization list --json`. If it fails, have the user run `socket login` in their own interactive terminal and return after the probe works. Do not ask them to paste a token into chat or expose it in a tool command.
5. Run the approved lists in the foreground:

   ```bash
   bash "<skill-dir>/scripts/run-audit.sh" /tmp/socket-audit/repos.txt /tmp/socket-audit/results
   bash "<skill-dir>/scripts/run-audit.sh" --offline /tmp/socket-audit/company-repos.txt /tmp/socket-audit/company-results
   ```

   Run only the applicable command. Do not poll with blocking sleeps.
6. Aggregate the per-repository JSON and `ioc-hits.json`. Save the full report to `/tmp/socket-audit/report.md` and `~/Desktop/socket-audit-report-<YYYY-MM-DD>.md`; show only headline counts and critical findings in chat. Include scope, online/offline split, exact-version hits, package-only matches, Socket policy failures, clean repositories, artifact paths, and next steps. Treat package-only matches as leads, not confirmed compromise.
7. If findings exist, offer a guided investigation: lockfile history for the relevant window, named credential locations that may need rotation, and a clean dependency reinstall. Do not delete files or rotate credentials without separate approval.
8. Offer B. Detection is automatic; installation still requires manager/mechanism approval.

## B — Going-forward protection

Read `references/protection-mechanisms.md`, then detect usage:

```bash
bash "<skill-dir>/scripts/detect-package-managers.sh" /tmp/socket-audit/pm-detection.json
```

Summarize only relevant managers and `bun.lockb` warnings. Explain the choice briefly:

- A configured Bun project uses its Socket scanner regardless of who invokes Bun.
- npm/pnpm PATH wrappers cover interactive terminals, agents, and scripts; recommend them by default.
- Shell aliases cover interactive typing only and must be an explicit lower-coverage choice.

Ask one compact question covering selected managers, wrapper versus alias for npm/pnpm, which Bun projects to configure, and whether to add a global Bun release-age gate. Skip irrelevant branches.

### Bun

Require Bun 1.3+ for the security-scanner API. The reliable scanner path is per project: after approval, run `bun add -d @socketsecurity/bun-security-scanner` in every selected Bun project.

Do not substitute `bun add -g` or a scanner entry only in `~/.bunfig.toml`. Bun 1.3.5 accepts the global package install but ordinary projects still report that the configured scanner is not installed. For machine-wide baseline protection, offer a global `minimumReleaseAge`; describe it as an age gate, not Socket scanner coverage.

Merge this target state into each selected project's `bunfig.toml`:

```toml
[install.security]
scanner = "@socketsecurity/bun-security-scanner"

[install]
minimumReleaseAge = 3600
```

`minimumReleaseAge` is seconds: `3600` is one hour and `86400` is one day. Preserve an existing user value unless they explicitly choose a replacement.

If approved, merge only the `[install]` release-age key into `~/.bunfig.toml` as the optional global baseline. Never put the scanner key there; it can break new or unconfigured projects. Keep scanner config project-local.

Make the edit idempotent:

- For a new file, add `# Created by the socket-audit skill.` at the top and mark the inserted values with inline `# socket-audit` comments.
- In an existing file, merge keys into existing tables; never append duplicate TOML tables. Mark only newly inserted values with the same inline comment.
- Leave identical pre-existing values unmarked. Stop on conflicting scanner values and ask the user rather than overwriting them.
- Back up an existing file, validate the resulting TOML, and read back only the relevant non-secret lines. Do not claim protection if validation fails.

Bun does not run arbitrary dependency lifecycle scripts by default, but `install.ignoreScripts` itself defaults to `false`; do not claim otherwise.

### npm / pnpm

With approval, install Socket Firewall Free using `npm i -g sfw` and verify the command with `sfw --help`. Never wrap Bun.

For the recommended wrapper path, run only the selected managers:

```bash
bash "<skill-dir>/scripts/install-wrappers.sh" npm pnpm
```

The script owns only marked wrapper files and refuses to overwrite unrelated shims. If it skips or fails a manager, report that manager as unprotected. If it prints a PATH instruction, get approval before adding one marked, idempotent block to the relevant shell startup file.

For an explicit aliases choice on zsh or bash, back up the relevant shell file and add one idempotent block containing only selected managers. For other shells, recommend wrappers instead of improvising unsupported syntax.

```bash
# BEGIN socket-audit aliases
alias npm='sfw npm'
alias pnpm='sfw pnpm'
# END socket-audit aliases
```

Warn that aliases do not protect agent-, script-, or other non-interactive installs.

### Verify and report

Verify the selected path, not every possible path:

- The Bun config is valid and contains the intended scanner/value.
- Each wrapper resolves before the real manager in both the current shell and a representative non-interactive shell; pass-through commands reach the real manager, and an approved dry run with `SFW_VERBOSE=true` shows Socket Firewall handling an install command.
- Each alias exists in a fresh interactive shell; non-interactive bypass is an expected limitation.

Offer, but do not open without approval, the [Socket GitHub App](https://github.com/apps/socket-security) and [Socket VS Code extension](https://marketplace.visualstudio.com/items?itemName=SocketSecurity.vscode-socket-security). Keep personal and company integrations separated.

Finish with a per-manager status (`protected`, `partial`, `skipped`, or `failed`), modified files and backups, limitations, and the D dry-run command.

## C — Offline IOC check

Require `jq`, survey as in A, confirm scope, then run:

```bash
bash "<skill-dir>/scripts/run-audit.sh" --offline /tmp/socket-audit/repos.txt /tmp/socket-audit/results
```

This path needs no Socket account and performs no Socket upload. Report from `ioc-hits.json`, state that the bundled IOC snapshot is not exhaustive, then offer B.

## D — Uninstall

Preview first:

```bash
bash "<skill-dir>/scripts/uninstall.sh" --dry-run
```

Show what is owned, skipped, or uncertain. After approval, run `uninstall.sh`; use `--yes` only when that approval is already explicit. The script may remove marked wrappers, marked aliases/PATH entries, global `sfw`, a legacy global Bun scanner package, and marker-owned global Bun config. It must leave unmarked or conflicting config for manual review.

Do not remove the Socket CLI, per-project Bun config, accounts, tokens, GitHub App installations, or unrelated shims. Verify the post-uninstall state and report any residue.

## IOC snapshot

`references/ioc-list.json` is a dated snapshot, not a complete malware catalog. Preserve its date and distinguish exact-version hits from wildcard/package-only signals. Refresh it only from authoritative incident sources when explicitly maintaining the skill.

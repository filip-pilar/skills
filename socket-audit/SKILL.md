---
name: socket-audit
description: >
  Audit local git repos for supply-chain-compromised npm/Bun/PyPI/Cargo dependencies
  using Socket.dev (Shai-Hulud, chalk/debug, axios, @tanstack — exact-version and
  package-name IOC matching). Sets up going-forward protection tailored to the user's
  package managers: @socketsecurity/bun-security-scanner via ~/.bunfig.toml for Bun,
  and PATH wrappers routing npm/pnpm installs through Socket Firewall (sfw) — handles
  AI-agent-driven installs correctly, unlike shell aliases. Includes a clean uninstall.
  Invoke explicitly with $socket-audit.
---

# Socket Supply Chain Audit

This skill walks a developer through three workflows that can run together or independently, plus uninstall:

1. **Retro audit (A)** — scan every git repository for compromised package versions and high-risk supply-chain signals using Socket.dev's CLI, plus an offline indicator-of-compromise (IOC) check against a bundled list.
2. **Going-forward protection (B)** — install install-time protection tailored to what the user uses AND how they invoke installs (manual vs AI-agent-driven). npm/pnpm get a smart PATH wrapper (covers all invocation contexts) or shell aliases (interactive only) per user preference. Bun gets `@socketsecurity/bun-security-scanner` via `~/.bunfig.toml`. **Can be invoked standalone.**
3. **Offline IOC check (C)** — same lockfile grep as A but with no Socket upload. Smaller catalog but zero data egress.
4. **Uninstall (D)** — remove everything installed by Workflow B with backups. Triggered by phrases like "uninstall socket protection", "remove sfw", "undo socket-audit".

Audience: small dev teams without CI/CD, including those whose installs are often driven by Codex or other agents. Everything works on Socket's free tier or with no Socket account (`sfw`, Bun scanner free mode, offline IOC check).

Resolve `<skill-dir>` to the directory containing this `SKILL.md` before running bundled scripts.

## Routing

| User intent | Workflow |
|---|---|
| "audit my machine", "did Shai-Hulud hit me", "scan my repos" | **A → then B** (default chain) |
| "set up going-forward protection", "I already audited, just install", "I use bun how do I protect installs" | **B only** (standalone) |
| "I don't want to upload anything", "offline only" | **C → then B** |
| "uninstall socket protection", "remove sfw", "undo socket-audit" | **D** (uninstall) |
| Unclear or first time | Default: **A → B**. Confirm scope before launching A. |

**The audit answers "did anything get me?". The protection answers "will anything get me next?".** Workflow B is both package-manager-aware AND invocation-pattern-aware — it asks how installs are typically invoked (you typing, Codex running them, or both) and picks the right mechanism.

---

## Workflow A — Retro audit

### A0. Prereq check (fail fast)

```bash
command -v node && command -v npm   || echo "MISSING: Node.js"
command -v jq                        || echo "MISSING: jq (brew install jq)"
command -v socket                    || echo "Will install via npm i -g socket in A3"
```

Surface a single fix-it summary and stop if anything's missing other than `socket`.

### A1. Survey

```bash
bash "<skill-dir>/scripts/survey-repos.sh" /tmp/socket-audit/repos.txt "$HOME"
```

Writes deduplicated repo list with supported manifests. Show user count + sample. Confirm scope before scanning.

### A2. Disclose egress + handle personal/company split

Tell the user:

> Socket's scan uploads each repo's manifest and lockfile (not source code) to socket.dev — package names and versions only.

**For mixed personal/company audits**: personal repos → online; company repos → `--offline`. **Don't upload company manifests to a personal Socket org.** Write two repo lists and run twice if needed.

### A3. Install + authenticate Socket CLI

```bash
command -v socket || npm i -g socket
socket organization list --json   # canonical auth probe
```

**Don't try to log in from this session** — `socket login` needs an interactive TTY and Codex's `!` is non-interactive. In v1.1.x, `socket login` prompts for a token at the terminal (NOT browser OAuth). The "leave blank" option creates a public token that can't scan.

**Auth path** — keeps the token out of conversation:
1. User signs up at https://socket.dev, creates a personal token at https://socket.dev/dashboard/settings/api-tokens
2. User opens Terminal.app (NOT Codex) and runs `socket login`, pastes token (NOT blank)
3. User verifies `socket organization list --json` works
4. User returns. Run the auth probe from this session to verify.

**Critical token-leak hygiene:**
- **Never** run `socket config get apiToken` — prints the full token to stdout
- **Never** print `~/.config/socket-cli/*` to chat
- If a `sktsec_...` value appears in any tool output, **stop**, tell the user to rotate at https://socket.dev/dashboard/settings/api-tokens

### A4. Run audit

```bash
bash "<skill-dir>/scripts/run-audit.sh" /tmp/socket-audit/repos.txt /tmp/socket-audit/results
```

Use `--offline` for company repos. Run foreground; don't poll with `sleep N && tail`.

### A5. Aggregate report

Read per-repo JSON + `ioc-hits.json`, write report. **Save to both `/tmp/socket-audit/report.md` AND `~/Desktop/socket-audit-report-<YYYY-MM-DD>.md`** — `/tmp` is volatile.

Structure: Summary (with date, machine, org, counts) → Critical findings (exact-version IOC hits) → Offline IOC package-name matches (cross-reference Socket's per-repo verdict to flag false positives) → Socket policy failures → All-clear repos → Audit artifacts → Next steps.

Show user only headline counts + critical findings.

### A6. Remediation (only if findings)

If exact-version hits exist, walk through:
1. **Timeline**: `git log --oneline -- <lockfile>` for the attack window
2. **Credential rotation** (be specific — name files): `~/.npmrc`, GitHub PATs/SSH keys, `~/.aws/credentials`, `~/.config/gcloud/`, MCP tokens in `~/.codex/`/`~/.vscode/`, browser-stored passwords
3. **Clean install**: nuke `node_modules`, pin known-good, reinstall

Package-only matches where Socket marked the repo healthy: optional 15-min manual cross-check. Skip-by-default is fine.

### A7. Chain into Workflow B

> "Now let's set up going-forward protection. I'll detect what package managers you use and ask how you typically run installs, then install the right tool."

B asks for per-manager + per-mechanism consent. Don't make the user re-summon as a separate step.

---

## Workflow B — Going-forward protection

Can be invoked standalone ("just set up protection") or chained from A.

### B0. Standalone prereq check

If invoked standalone, do A0 first. Then move on.

### B1. Detect package managers

```bash
bash "<skill-dir>/scripts/detect-package-managers.sh" /tmp/socket-audit/pm-detection.json
```

Writes JSON + human summary to stderr. Auto-surveys `$HOME` if no repo list exists. Show the user the summary, including any `bun.lockb` warnings.

### B1.5. Explain the manual-vs-agent distinction

Before asking what to install, briefly explain why this matters. This is the most important step you can take to set up the right mechanism — getting it wrong gives the user a false sense of security.

> Two ways your installs run, with different protection mechanisms:
>
> 1. **You typing `npm install X` in a terminal.** Interactive shell. Shell aliases work here (`alias npm='sfw npm'`).
> 2. **An agent or script running `npm install X` on your behalf.** Non-interactive shell. Aliases do NOT expand here — the real npm runs unprotected. This includes Codex's shell tool, `bash script.sh`, Makefiles, and `npm run` lifecycle scripts.
>
> If your installs are sometimes driven by Codex or other agents — even occasionally — shell aliases are insufficient. A PATH wrapper at `~/.local/bin/npm` works for both cases: real executable found by every shell, every invocation, every program. We recommend wrappers as the default.
>
> Bun's protection is different — it's config-based via `~/.bunfig.toml`. Always-on regardless of mechanism. No invocation question needed for Bun.

Ask the user about their pattern. Default to wrappers — they're strictly more comprehensive at no real cost. Aliases only as an explicit alternative for users with a stated reason.

### B1.6. Ask which managers + which mechanism

After explanation, ask in ONE question:

> Detected managers in use:
>   bun  — N repos
>   npm  — M repos  
>   pnpm — K repos
>
> Which protection level?
>   [1] All managers, AI-agent-aware (wrappers) — recommended
>   [2] All managers, manual-only (aliases) — lighter, but skips agent-driven installs
>   [3] Bun only (skip npm/pnpm protection entirely)
>   [4] Choose individually

If user has only Bun and no npm/pnpm in their detected stack, skip B3 — Bun's protection is already comprehensive.

### B2. Bun branch — install Socket's Bun scanner

Always run this if Bun was selected. Ask: **global** (every Bun project on this machine) or **per-project** (commits to team repos)?

**Global** (recommended for personal dev machines):

```bash
# Create or append to ~/.bunfig.toml
[ -f "$HOME/.bunfig.toml" ] || touch "$HOME/.bunfig.toml"
cat >> "$HOME/.bunfig.toml" <<'EOF'

# Created by the socket-audit skill.
[install.security]
scanner = "@socketsecurity/bun-security-scanner"

[install]
minimumReleaseAge = 60
EOF

# Pre-pull the scanner package globally so the first bun install in any project
# doesn't have to fetch it on-demand
cd "$HOME" && bun add -g @socketsecurity/bun-security-scanner
```

**Per-project** (recommended for team repos):

```bash
cd <project>
bun add -d @socketsecurity/bun-security-scanner
[ -f bunfig.toml ] || touch bunfig.toml
cat >> bunfig.toml <<'EOF'

[install.security]
scanner = "@socketsecurity/bun-security-scanner"

[install]
minimumReleaseAge = 60
EOF
```

Read back the bunfig.toml to confirm. Tell the user:

- Bun's default `install.ignoreScripts = true` already blocks the most common attack vector (malicious postinstall scripts). The scanner adds a second layer at the registry level.
- `minimumReleaseAge = 60` refuses package versions less than 60 minutes old. The May 2026 @tanstack attack published 84 bad versions in 6 minutes — this setting would have blocked all of them. Tune to taste (60 aggressive → 1440 = 1 day, pnpm's default).

### B3. npm-stack branch (wrappers path — default)

**For users who picked "all managers, AI-agent-aware" or who let agents drive installs.** This is the recommended default.

Install `sfw` (the firewall binary):

```bash
npm i -g sfw
sfw --version
```

Then install the PATH wrappers:

```bash
bash "<skill-dir>/scripts/install-wrappers.sh" npm pnpm
```

The script:
- Writes `~/.local/bin/npm` and `~/.local/bin/pnpm` (or `~/bin/` as fallback)
- Each wrapper checks the subcommand: install-adjacent commands (`install`, `add`, `ci`, `update`, `exec`...) → routes through `sfw` with the real npm's absolute path → no infinite loop. Everything else → direct pass-through, no `sfw` overhead.
- Prints a PATH shim instruction if `~/.local/bin` isn't already in PATH (rare on macOS / modern Linux).

**Never wrap `bun`** — `sfw` doesn't support it; Bun's protection in B2 is the right tool.

Verify per B6.

### B3-alt. npm-stack branch (aliases path — if user explicitly opted out of wrappers)

**For users who picked "manual-only".** Lighter touch but covers ONLY interactive-shell typing.

```bash
npm i -g sfw

case "$SHELL" in
  *zsh)  SHELL_RC="$HOME/.zshrc" ;;
  *bash) SHELL_RC="$HOME/.bashrc" ;;
  *fish) SHELL_RC="$HOME/.config/fish/config.fish" ;;
  *)     SHELL_RC="$HOME/.profile" ;;
esac

{
  echo
  echo "# Socket Firewall aliases (added by socket-audit skill on $(date +%Y-%m-%d))"
  echo "alias npm='sfw npm'"
  echo "alias pnpm='sfw pnpm'"
} >> "$SHELL_RC"
```

**Warn user prominently**: these aliases only fire in interactive shells. If anything else on this machine runs `npm install` (Codex, scripts, Makefiles), it bypasses protection. Aliases are the lower-coverage option — the user explicitly chose this.

Bypass for one call: `\npm install` or `command npm install`.

### B4. Cross-cutting layers (always offer, regardless of choices above)

> Two more free layers, both PM-agnostic. Want me to open them in your browser?
> - **Socket GitHub App** — scans every PR touching a lockfile/`package.json`/`bunfig.toml`. https://github.com/apps/socket-security
> - **Socket VS Code / Cursor extension** — inline warnings as you edit. https://marketplace.visualstudio.com/items?itemName=SocketSecurity.vscode-socket-security

On macOS: `open <url>`. Otherwise print URLs.

For users with mixed personal/company repos: install GitHub App on **personal** GitHub only. Company repos need a separate Socket org owned by the company.

### B5. Limitations

- **`sfw` doesn't wrap Bun** → Bun's protection comes from B2.
- **Bun scanner free mode** → uses Socket's public API. Set `SOCKET_API_KEY` to enable org-policy enforcement (matters for teams).
- **Shell aliases are interactive-shell only** (B3-alt). The wrapper path (B3) avoids this entirely.
- **No custom registries in `sfw` free** → private Artifactory / Verdaccio needs Socket Firewall Enterprise.
- **Wrapper edge case**: scripts with `#!/bin/zsh -l` (login non-interactive) may bypass `~/.local/bin` precedence. Uncommon.

### B6. Verify everything works

After install, verify in each shell context the user might use. Tell the user to run (or run on their behalf):

```bash
# 1. Wrapper takes precedence
which npm    # expected: ~/.local/bin/npm (or ~/bin/npm)
which pnpm   # expected: ~/.local/bin/pnpm

# 2. Pass-through has zero sfw overhead
npm --version    # should print version, NO "Protected by Socket Firewall" banner

# 3. Install goes through sfw
npm install --dry-run --silent 2>&1 | head -3   # should show "Protected by Socket Firewall"

# 4. Bun config is wired
bun pm version 2>/dev/null || cat ~/.bunfig.toml | grep -A2 "install.security"

# 5. Check from a non-interactive shell (simulates Codex's bash tool)
bash -c 'which npm'    # should still print the wrapper path
```

If any of these fail, the protection isn't applying — surface the failure and don't claim "all set".

### B7. Tell the user about the uninstall path

> If you ever want to remove all of this:
>   `bash ~/.codex/skills/socket-audit/scripts/uninstall.sh`
> Use `--dry-run` first to preview, or `--yes` to skip the confirmation prompt. The script backs up any files it modifies.

---

## Workflow C — Offline IOC check only

1. `survey-repos.sh` (same as A1)
2. `run-audit.sh --offline /tmp/socket-audit/repos.txt /tmp/socket-audit/results`
3. Aggregate report from `ioc-hits.json` only
4. Chain into B (works without a Socket account)

---

## Workflow D — Uninstall

When the user wants to undo Workflow B:

```bash
# Preview what will be removed (recommended first):
bash "<skill-dir>/scripts/uninstall.sh" --dry-run

# Actually remove:
bash "<skill-dir>/scripts/uninstall.sh"
# or skip the confirmation:
bash "<skill-dir>/scripts/uninstall.sh" --yes
```

The script removes:
- PATH wrappers (only if they carry the `socket-audit-wrapper` marker — won't touch other wrappers)
- `sfw` global package
- `@socketsecurity/bun-security-scanner` global package
- Socket Firewall alias block from `~/.zshrc` / `~/.bashrc`
- Scanner config from `~/.bunfig.toml` (whole file if we created it, just the block if we appended)
- PATH shim lines we added to `.zshenv` / `.zprofile`

It backs up any modified file with a `.socket-audit-backup` suffix.

It does NOT remove:
- Socket CLI (`socket` — still useful for re-running audits)
- Per-project `bunfig.toml` (those live in committed repos)
- Socket account, API tokens, GitHub App installs (handle via dashboard)

---

## Mechanism reference

For "how does X actually work" questions, see `references/protection-mechanisms.md`. Highlights the kill-chain point each layer fires at and where each has gaps. Read this if a user asks about anything mechanism-related ("why don't aliases work for Codex?", "what's the difference between sfw and the bun scanner?", "what does the GitHub App add?").

---

## Keeping the IOC list current

`references/ioc-list.json` is a snapshot. Refresh quarterly or after major incidents from:
- Socket blog (exact versions): https://socket.dev/blog
- GitHub Security Advisories: https://github.com/advisories?query=type%3Areviewed+ecosystem%3Anpm+malware
- OSV: https://osv.dev

Schema in the file's `notes` field. `versions: ["*"]` flags any installed version — conservative, produces false positives Socket's online catalog often clears. Note this in audit reports.

---

## Quick reference — common phrasings

- **"I already audited, just set up protection"** → B standalone
- **"I mainly use Bun"** → B routes to B2; npm/pnpm wrapper still useful as backup
- **"Does sfw support bun?"** → No. `@socketsecurity/bun-security-scanner` via bunfig.toml is the Bun-native equivalent. Different mechanism (Bun's scanner API), better integrated.
- **"Why don't aliases work for Codex?"** → Aliases are interactive-shell-only. Codex's shell tool is non-interactive. Wrappers fire for every execve regardless of shell — recommend B3 wrapper path.
- **"Will this break my npm?"** → Wrappers pass through non-install commands directly (zero overhead, exact same behavior). Install commands route through `sfw` which adds ~700ms latency and blocks confirmed malware. Reversible: `uninstall.sh`.
- **"How long?"** → Audit 5–15 sec/repo. Detection <30 sec. Install per branch ~1 min. Total fresh setup: ~5 min.
- **"What about monorepos?"** → Socket walks nested manifests; one scan from root covers all.
- **"Is this free?"** → Audit: free up to 1,000 scans/month + 3 members. Firewall + Bun scanner: free, no account.
- **"I have personal and company repos"** → Personal online, company `--offline`. Don't upload company manifests to a personal Socket org.
- **"Uninstall it"** → Workflow D.

---

## Versioning safeguard

Socket CLI surface verified against `socket-cli v1.1.94`. When Socket releases a new version, re-verify the commands this skill calls — see `references/cli-version.md`.

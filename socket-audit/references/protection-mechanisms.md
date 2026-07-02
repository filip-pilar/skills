# Protection mechanisms — what each layer actually does

Understanding the mechanics matters because different layers fire at different points and have different gaps. If a user asks "am I protected?" the honest answer depends on where the install actually happens.

## The kill chain for a package install

```
 1. User (or AI agent) decides to add a dep
        ↓
 2. package.json / bunfig.toml edited (IDE extension fires here)
        ↓
 3. Install command runs: `npm install X` / `bun install X` / etc.
        ↓
 4. Package manager resolves dependencies via npm registry
        ↓                  ← sfw proxy fires here (if invoked as `sfw npm`)
        ↓                  ← Bun's scanner-API fires here (always, via bunfig.toml)
 5. Tarball downloaded, postinstall scripts run
        ↓
 6. Code lands in node_modules / bun's cache
        ↓
 7. PR opened with lockfile changes  ← GitHub App fires here
        ↓
 8. Code merged / deployed
```

Each defense layer targets a different point.

## Layer 1 — IDE extension (Socket VS Code / Cursor)

**Where it fires**: Step 2 — as you edit `package.json` / `bunfig.toml`. Shows risk scores inline, hover cards with maintainer info, warnings on suspicious deps.

**Always-on**: Yes, for code you edit in VS Code/Cursor.

**Gap**: Doesn't catch deps added by agents that bypass the editor (Codex's Edit tool modifies files programmatically; some IDE extensions still surface the warning on next file save).

## Layer 2 — Bun's scanner API + Socket scanner package

**Where it fires**: Step 4 — inside Bun's install process, before any tarball is downloaded.

**How it works**: Bun has a first-class security scanner API. `~/.bunfig.toml` declares:

```toml
[install.security]
scanner = "@socketsecurity/bun-security-scanner"
```

On every `bun install` / `bun add`, Bun calls the scanner module for each candidate package. The scanner queries Socket's catalog. `fatal` verdict aborts the install; `warn` prompts (or fails in CI).

**Always-on**: Yes. Config-based — fires regardless of who/how `bun install` is invoked.

**Gap**: Only for Bun. Doesn't help with `npm install` / `pnpm install`.

## Layer 3 — `sfw` (Socket Firewall) network proxy

**Where it fires**: Step 4 — between npm and the registry.

**How it works**: When you run `sfw npm install X`:
1. `sfw` spawns a local HTTPS proxy on a random port
2. Sets `HTTPS_PROXY=http://127.0.0.1:<port>` in the npm subprocess env
3. Spawns `npm install X` with that env
4. npm honors the proxy var, routes registry requests through `sfw`
5. The proxy inspects each request against Socket's catalog and blocks malicious

**Always-on**: **No — opt-in per invocation.** Only fires when something explicitly runs `sfw npm` (or via alias / PATH wrapper). Bare `npm install` runs unprotected.

**Gap**: Anything that calls `npm` / `pnpm` directly without going through `sfw`. This includes:
- Non-interactive shells (Codex's shell tool, scripts, Makefiles, package.json scripts)
- A user who forgets the `sfw` prefix
- Custom registries (free tier proxies public registries only)

## Layer 4 — Shell alias (`alias npm='sfw npm'`)

**Where it fires**: Step 3 — when YOU type `npm install` in a terminal.

**How it works**: Interactive shells expand aliases before executing commands.

**Always-on**: **No — interactive shells only.** Aliases are not expanded in:
- Non-interactive shells (Codex's shell tool, bash scripts)
- Login-non-interactive shells (`#!/bin/zsh -l` scripts)
- Subprocess invocations
- Anything that uses `command npm` or `\npm` to bypass

**Gap**: AI-driven installs, scripts, lifecycle scripts. Significant for an agent-driven workflow.

## Layer 5 — PATH wrapper script

**Where it fires**: Step 3 — every `npm` / `pnpm` invocation, regardless of shell.

**How it works**: A small script at `~/.local/bin/npm` (which appears in PATH ahead of the real npm) takes over the `npm` name. It checks the subcommand:
- For install-adjacent ones (`install`, `add`, `ci`, `update`, `exec`...) → execs `sfw <real-npm> "$@"`
- For metadata commands (`--version`, `config get`, `run`...) → execs the real npm directly (no sfw overhead)

**Always-on**: Yes — PATH lookup happens for every execve, regardless of shell.

**Why not aliases instead**: Aliases require shell-level expansion (interactive only). The wrapper is a real executable found via PATH, which works in every shell context and for every program that spawns npm.

**Gap**: Custom-registry environments where Socket can't proxy (sfw free limitation). Programs that hardcode the real npm path (rare).

## Layer 6 — Socket GitHub App

**Where it fires**: Step 7 — when a PR is opened/updated that touches a lockfile or manifest.

**How it works**: GitHub App watches your repos, scans diffs against Socket's catalog, posts findings as PR comments.

**Always-on**: Yes, for repos you've granted access to.

**Gap**: Only catches things that land in a PR. Anything installed locally but not committed is invisible. (For a personal-laptop threat model, this matters less — credentials on the machine are still toast even if the malicious dep was never pushed.)

## Mechanism choice for an AI-agent-driven workflow

A workflow where Codex (or another agent) runs `bun install` / `npm install` on the user's behalf changes the calculus:

| Mechanism | Catches AI-driven installs? | Notes |
|---|---|---|
| IDE extension | Partial — only when user manually edits | Edit-tool changes from agents may bypass |
| Bun scanner via bunfig | **Yes** | Config-based, fires regardless of invoker |
| `sfw` invoked manually | No | Agent won't prefix with `sfw` |
| Shell alias | **No** | Non-interactive shell bypasses |
| PATH wrapper | **Yes** | Survives any execve |
| GitHub App | **Yes** | Catches anything that PRs |

**Default recommendation for any user**: Bun scanner via bunfig.toml + PATH wrapper for npm/pnpm + GitHub App for PR-time backstop. Shell aliases add no value if the wrapper is installed.

**Minimal recommendation if the user resists wrappers**: Bun scanner + GitHub App. Accept the npm/pnpm runtime gap.

## How the wrapper avoids common pitfalls

Common ways a naive npm wrapper script breaks, and how this skill's `install-wrappers.sh` handles them:

| Pitfall | Mitigation |
|---|---|
| Infinite loop (sfw spawns npm via PATH, finds the wrapper, re-invokes sfw) | Wrapper passes the **absolute path** of the real npm to sfw, e.g. `sfw /opt/homebrew/bin/npm "$@"`. sfw spawns that absolute path, never re-hitting the wrapper. |
| 700ms overhead on `npm --version`, `npm run`, etc. | Wrapper checks the first arg. Only install-adjacent subcommands route through sfw; everything else execs the real npm directly. |
| Different real-npm path on Apple Silicon vs Intel vs Linux | Wrapper checks `/opt/homebrew/bin`, `/usr/local/bin`, `/usr/bin` in order. |
| `~/.local/bin` not in PATH on some Linux distros | Installer checks PATH and prints a one-line config snippet if a PATH shim is needed. |
| User uninstalls and can't remember what was changed | All wrappers carry a `socket-audit-wrapper` marker comment. `uninstall.sh` only removes files with the marker. |

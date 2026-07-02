# Socket CLI Reference

Quick reference for the Socket CLI commands this skill uses. Verified against **`socket-cli v1.1.94`**.
Full docs: https://docs.socket.dev/docs/

When Socket releases a new version, see `cli-version.md` for the re-verification checklist.

## Install

```bash
npm i -g socket
```

Verify:
```bash
socket --version
```

## Authenticate

`socket login` needs an interactive terminal. **Do not run it via `!` from a Codex session** — Codex's `!` prefix is non-interactive and Socket errors:

> `Invalid input: Cannot prompt for credentials in a non-interactive shell. Use SOCKET_CLI_API_TOKEN environment variable instead.`

In v1.1.x, `socket login` does **not** open a browser. It prompts at the terminal for an API token. The "leave blank for limited public token" option creates a read-only session that **cannot create scans** — don't use it for audits.

### Recommended path

1. Sign up / log in at https://socket.dev (free).
2. Visit https://socket.dev/dashboard/settings/api-tokens, create a personal token with scan-create scope.
3. Open Terminal.app / iTerm and run:
   ```bash
   socket login
   ```
4. Paste your token at the prompt (NOT blank).
5. Verify:
   ```bash
   socket organization list --json
   ```

Socket persists the token to `~/.config/socket-cli/` (or similar) and any future `socket` invocation — including from Codex — picks it up automatically.

### Alt: environment variable

For CI/CD or locked-down environments:

```bash
export SOCKET_CLI_API_TOKEN=<your-token>
socket organization list --json    # should succeed
```

### How to verify auth in a script

Use `socket organization list --json`. There is **no `socket whoami` subcommand** in v1.1.x; calling it exits 2 and dumps the help text. `socket organization list --json` is the canonical auth probe — it returns a small JSON payload of orgs you belong to if auth is good, fails clearly otherwise.

### Token-leak hygiene — read this

**Never run these:**
- `socket config get apiToken` — prints the full token to stdout, leaking it into logs / conversations.
- `cat ~/.config/socket-cli/*` — same risk.

If a `sktsec_...` value appears in any tool output, stop and rotate the token at https://socket.dev/dashboard/settings/api-tokens before continuing.

## Scan a project

```bash
socket scan create --report --json .
```

Flags used by this skill:
- `--report` — wait for processing and evaluate against org policy. Without this you get just a scan ID.
- `--json` — machine-readable output.
- `.` — scan current directory. Socket walks the tree for manifests.

### Supported manifest / lockfile types

`package-lock.json`, `yarn.lock`, `pnpm-lock.yaml`, **`bun.lock` (text, Bun 1.2+)**, `requirements.txt`, `Pipfile.lock`, `poetry.lock`, `pyproject.toml`, `uv.lock`, `Cargo.lock`, `Gemfile.lock`, `go.sum`.

**Not supported**: `bun.lockb` (binary Bun lockfile). If a repo has only `bun.lockb`, regenerate the text version:

```bash
bun install --save-text-lockfile
```

### Key JSON output fields

- `healthy` — `false` means at least one policy threshold was crossed.
- `id` — scan ID. Dashboard URL: `https://socket.dev/dashboard/scans/<id>`.
- `issues` / `alerts` — flagged packages and reasons.

## Other useful commands

| Command | Purpose |
|---|---|
| `socket organization list --json` | Validate auth + list orgs you belong to (use this instead of `whoami`) |
| `socket scan list` | List recent scans |
| `socket scan view <id>` | Pretty-print a scan by ID |
| `socket package score <ecosystem> <name>` | Score a single package without scanning a repo |
| `socket diff <a> <b>` | Diff two scans |

## Common gotchas

- **Private repos.** Manifests are uploaded. Sensitive package names may leak — use `--offline` in `run-audit.sh` for company repos.
- **Workspaces / monorepos.** Socket walks nested manifests; one scan from the root covers all.
- **Lockfile required for full signal.** A `package.json` alone gives partial info; commit the lockfile for transitive-dep analysis.
- **`bun.lockb` is unsupported.** Binary Bun lockfile — Socket only handles the text `bun.lock` introduced in Bun 1.2. Regenerate as text (see above).
- **Free tier quota.** 1,000 scans/month — re-running this audit weekly on 60 repos uses ~240/month.

# Socket CLI Reference

Command reference for Socket CLI `v1.1.94`, rechecked 2026-07-15. See the [official CLI documentation](https://docs.socket.dev/docs/socket-cli) and `cli-version.md` before changing command assumptions.

## Install and authenticate

```bash
npm i -g socket
socket --version
socket organization list --json
```

`socket organization list --json` is the authentication probe. There is no `socket whoami` command in this version.

If the probe fails, the user must run `socket login` in their own interactive terminal. It prompts for an API token; it does not open browser OAuth. Do not automate login or place a token in chat, a tool command, or visible environment output.

Never run `socket config get apiToken` or print files under the Socket config directory. If a token appears in output, stop and have the user rotate it at [Socket API tokens](https://socket.dev/dashboard/settings/api-tokens).

## Scan

```bash
socket scan create --report --json .
```

- `--report` waits for the scan report.
- `--json` requests machine-readable output.
- `.` searches the current tree for supported manifests.

This command uploads the supported dependency manifests it finds. Treat manifest and lockfile contents as data egress. It does not enable source reachability analysis unless `--reach` is added; this skill does not add that flag.

Useful result fields include the scan ID and reported alerts/issues. Do not assume a single field is stable enough to determine success: retain the raw JSON, command exit status, and log, then aggregate the actual response shape.

## Lockfiles and repository boundaries

- Text `bun.lock` is supported; binary `bun.lockb` is not. With user approval, regenerate using `bun install --save-text-lockfile`.
- A manifest without its lockfile gives weaker transitive-dependency evidence.
- Socket walks nested supported manifests, so scanning a monorepo root can cover nested workspaces.
- Dependency metadata can itself be sensitive. Use the bundled `--offline` workflow for company or private repositories that are not approved for upload.

## Relevant commands

| Command | Purpose |
|---|---|
| `socket organization list --json` | Verify authentication and list organizations. |
| `socket scan create --report --json .` | Create and wait for a machine-readable scan report. |
| `socket scan list` | Inspect recent scans during troubleshooting. |
| `socket scan view <id>` | Inspect a saved scan by ID. |

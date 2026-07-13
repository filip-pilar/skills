# Installation and service reference

## Release discovery

Use the official CLIProxyAPI release and checksum manifest. Match OS and architecture exactly, verify SHA-256, record version/commit/build date, and preserve the previous binary until validation passes.

Use a user-controlled path such as `~/.local/bin/cli-proxy-api`. Prefer mainline CLIProxyAPI for this skill.

## Minimal local configuration

Use a private file such as `~/.cli-proxy-api/config.yaml`:

```yaml
host: "127.0.0.1"
port: 8317
auth-dir: "~/.cli-proxy-api"
api-keys:
  - "replace-with-random-local-client-key"
remote-management:
  allow-remote: false
  secret-key: ""
debug: false
logging-to-file: false
usage-statistics-enabled: false
request-retry: 3
```

Check the current example config before adding keys; remove unknown legacy options rather than assuming they remain accepted. Use mode `0600`.

Store the same local client key in a dedicated one-line `~/.cli-proxy-api/client-token` file with mode `0600` when Codex app or command-backed authentication is required. This is a loopback gateway key, not an upstream OAuth/API credential. Use `assets/read-cli-proxy-token.sh` to read it; do not duplicate the literal key in launchers.

Install the helper beside route launchers as `read-cli-proxy-token` with mode `0700`. The packaged launchers use the helper automatically when no token environment variable is set and reject symlinks, unsafe modes, empty values, multiple lines, and surrounding spaces.

## Transactional changes

Before changing binaries, config, services, profiles, launchers, token files, or custom agents, run:

```bash
scripts/route_transaction.sh snapshot --dir ABSOLUTE_BACKUP_DIR -- ABSOLUTE_PATH...
```

The generated bundle records paths that existed and paths that were absent, verifies backup hashes, and contains a self-contained `rollback.sh`. Keep the bundle until post-install acceptance passes. Run `verify` before relying on a bundle; run rollback only after showing the exact paths it will restore/remove.

## VibeProxy migration

VibeProxy is a macOS wrapper around a CLIProxyAPI variant. Before removal:

1. Record its version, embedded binary, listener, and service state.
2. Stop it cleanly.
3. Preserve `~/.cli-proxy-api` and credential files.
4. Move the app to a reversible backup unless permanent deletion was requested.
5. Start standalone CLIProxyAPI against the preserved auth directory and verify models.

Never delete the auth directory merely because the GUI wrapper is removed.

## Foreground and service validation

Start the explicit config in the foreground first. Verify loopback binding, authenticated `/v1/models`, unauthenticated rejection, and private file modes.

Only then create a per-user LaunchAgent/systemd user service. Use a stable binary/config path, restart on failure, and private logs. Validate the service with the platform's service inspector plus a real HTTP request.

Test a same-port second start and require a bind-error log, unchanged listener PID, and authenticated health afterward. Do not trust the second process's exit status alone: CLIProxyAPI 7.2.71 was observed logging `address already in use` while exiting `0`.

Preflight OAuth callback ports before showing the authorization URL. On the tested 7.2.71 Claude, Codex, and xAI flows, an occupied explicit callback port was not rejected before browser completion. Use `scripts/test_callback_collision.sh` to characterize the installed build and a platform listener check to prevent that late failure. Treat callback collision, expired OAuth, and entitlement rejection as separate lifecycle results rather than generic installation failures.

## Updates

Read release notes, preserve the old binary, install atomically, restart, query the catalog, and rerun every capability used by installed harness routes. A healthy process alone is not a successful update.

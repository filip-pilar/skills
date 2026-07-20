# Agent Skills

A personal collection of reusable agent workflows for engineering, research, decision-making, and a few specialised jobs.

Every skill is a directory containing a `SKILL.md`. Some follow the portable Agent Skills format, while others deliberately depend on Codex or Claude Code features. Check the compatibility column before installing one.

## Install a skill

Automated collection-wide installation is not packaged yet. For now, clone or download the repository and copy the directory for the skill you want into your agent's user-level skills directory.

```bash
git clone https://github.com/filip-pilar/skills.git forma-skills

# Codex
mkdir -p ~/.codex/skills
cp -R forma-skills/gitprep ~/.codex/skills/

# Claude Code
mkdir -p ~/.claude/skills
cp -R forma-skills/devils-advocate ~/.claude/skills/
```

For a GTV skill, copy its directory from `forma-skills/gtv/`. Review a skill and its bundled scripts before installing it, especially when it can access accounts, browsers, messages, authentication, or global configuration.

After installing, start a new agent session and invoke the skill explicitly:

```text
Use $gitprep to inspect my current diff and propose a clean commit plan.
```

## Compatibility

- **Universal** — written to the shared Agent Skills conventions and not intentionally tied to one host. It may still need common capabilities such as shell access, Git, or a browser.
- **Codex-enhanced** — the core workflow is portable, but some behavior or metadata is designed for Codex.
- **Codex-only** — depends on Codex-specific concepts or integrations.
- **Codex + Claude** — contains deliberate support for both hosts; follow any host-specific setup noted by the skill.

Compatibility describes the workflow, not just whether an agent can read the Markdown. Tools, permissions, and safety behavior still vary between hosts.

## Skill catalogue

| Skill | What it does | Compatibility | Main requirements |
|---|---|---|---|
| [`devils-advocate`](devils-advocate/) | Pressure-tests a plan, decision, argument, or piece of research without manufacturing objections. | Universal | None |
| [`dr-react`](dr-react/) | Improves a React Doctor score through small fixes and regression checks. | Codex-enhanced | Node.js, package-manager and target-repository access; `/goal` persistence is Codex-specific |
| [`gitprep`](gitprep/) | Inspects a diff, proposes coherent commits, runs approved checks, and commits only approved changes. | Universal | Git |
| [`improve`](improve/) | Audits a codebase and produces self-contained implementation plans, with an optional isolated execution workflow. | Codex + Claude | Shell and Git; use its host-switching script for Claude Code |
| [`skill-builder`](skill-builder/) | Creates, diagnoses, improves, compresses, evaluates, and releases skills with evidence and authority boundaries. | Codex-enhanced | Python for bundled validation scripts |
| [`socket-audit`](socket-audit/) | Audits repositories for supply-chain indicators and can configure npm, pnpm, or Bun install protection. | Universal | Shell; network and Socket.dev access for online workflows |
| [`setup-cli-proxy-gateway`](setup-cli-proxy-gateway/) | Configures and validates CLIProxyAPI routes for Codex CLI or Claude Code. | Codex + Claude | macOS/Linux shell, provider authentication, and approval for configuration changes or paid calls |

### Codex Side companions

These skills depend on Codex Side tasks and their linked-parent workflow.

| Skill | What it does |
|---|---|
| [`co-prompt`](co-prompt/) | Helps reason through a linked parent task without drafting or sending its final reply. |
| [`reply`](reply/) | Turns a settled Side discussion into the smallest sufficient reply and sends only an explicitly approved draft. |
| [`sidekick`](sidekick/) | Explains a parent's latest response, helps resolve decisions, and prepares an approved reply. |
| [`tldr`](tldr/) | Produces an ultra-concise state digest of the complete available parent task. |

### macOS automation

| Skill | What it does | Compatibility | Main requirements |
|---|---|---|---|
| [`imessage-autopilot`](imessage-autopilot/) | Configures and operates a narrowly scoped iMessage reply controller. | Codex-only | macOS, Messages database access, Automation permission, and Codex CLI |

Live operation is implemented, but its first bounded real-Messages smoke test is still outstanding. Do not treat it as production-ready until that test succeeds.

### UK Global Talent Visa

These skills provide structured guidance for the Digital Technology route. They do not provide legal advice and intentionally do not generate paste-ready application prose.

| Skill | What it does | Compatibility |
|---|---|---|
| [`gtv-tech-eligibility`](gtv/gtv-tech-eligibility/) | Assesses potential eligibility and produces a reusable GTV Profile. | Universal |
| [`gtv-tech-prepare`](gtv/gtv-tech-prepare/) | Turns a GTV Profile into factual document-planning material. | Universal |
| [`gtv-tech-review`](gtv/gtv-tech-review/) | Reviews self-written application documents from constructive and skeptical perspectives. | Universal |

Always verify current official eligibility, evidence, and authorship requirements before relying on these workflows.

## Important operating notes

- `dr-react` runs `npx react-doctor@latest`, which may require network access and permission to execute downloaded packages.
- `improve` commits its Codex representation by default. Its bundled `switch-host.sh` can materialise a separate Claude Code version without changing the canonical copy.
- `setup-cli-proxy-gateway` can change authentication, listeners, services, and agent configuration. It requires explicit approval for mutations and paid provider calls.
- `socket-audit` may require network access, Socket.dev authentication, package-manager changes, and approval before modifying global configuration.
- A skill being marked Universal does not guarantee identical behavior on every agent. Read its `SKILL.md` for exact tools, permissions, approval gates, and fallback behavior.

## Repository layout

Most top-level directories are standalone skills. The `gtv/` directory groups the three related Global Talent Visa skills. A skill may also contain:

- `agents/` — host-specific interface metadata;
- `assets/` — templates or runtime assets;
- `references/` — instructions loaded only when relevant;
- `scripts/` — helper and validation programs;
- `tests/` — regression tests for bundled scripts.

Installer-friendly reorganisation and collection-wide installation are intentionally deferred for now.

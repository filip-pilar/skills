# Agent Skills

A collection of reusable agent workflows for engineering, research, decision-making, and specialised tasks. Each public skill is an independently installable directory under [`skills/`](skills/) with a `SKILL.md` and any resources it needs at runtime.

## Install with `npx skills`

List the available skills without installing anything:

```bash
npx skills add filip-pilar/skills --list
```

Install one skill globally for Codex:

```bash
npx skills add filip-pilar/skills \
  --skill gitprep \
  --agent codex \
  --global
```

Install several skills globally:

```bash
npx skills add filip-pilar/skills \
  --skill gitprep \
  --skill lockin \
  --skill devils-advocate \
  --global
```

Install one for Claude Code instead:

```bash
npx skills add filip-pilar/skills \
  --skill devils-advocate \
  --agent claude-code \
  --global
```

Omit `--global` for a project-scoped installation. The CLI normally offers a symlinked installation so updates have one canonical source; pass `--copy` when you want an independent copy. It may create or update a `skills-lock.json` in the target scope—review that file before committing it to another project.

Review a skill and its bundled scripts before installing it, especially when it can access repositories, accounts, browsers, messages, authentication, external services, or global configuration. Agent support and permissions vary even when installation succeeds.

## Compatibility

- **Universal** — written to shared Agent Skills conventions and not intentionally tied to one host.
- **Codex-enhanced** — the core workflow is portable, but some behavior or metadata is designed for Codex.
- **Codex-only** — depends on Codex-specific concepts, tools, or integrations.
- **Codex + Claude** — contains deliberate support for both hosts.

Compatibility describes the workflow, not merely whether an agent can read the Markdown. Check each skill's requirements and safety notes before use.

## Skill catalogue

### Reasoning and workflow

| Skill | What it does | Compatibility | Maturity and requirements |
|---|---|---|---|
| [`devils-advocate`](skills/devils-advocate/) | Pressure-tests a plan, decision, argument, or piece of research without manufacturing objections. | Universal | Stable; no special runtime requirements |
| [`gitprep`](skills/gitprep/) | Inspects repository and publication state, proposes coherent commits, and creates only approved commits. | Universal | Stable; Git; never pushes as part of its own workflow |
| [`lockin`](skills/lockin/) | Recovers the active objective, narrows the working set, and advances the task to progress, completion, or one genuine blocker. | Codex-enhanced | Stable; current task context and whatever tools that task requires |
| [`skill-builder`](skills/skill-builder/) | Creates, diagnoses, improves, compresses, evaluates, and releases skills with evidence and authority boundaries. | Codex-enhanced | Stable; Python and PyYAML for bundled validation scripts |

### Engineering and integration

| Skill | What it does | Compatibility | Maturity and requirements |
|---|---|---|---|
| [`dr-react`](skills/dr-react/) | Improves a React Doctor score through small fixes and regression checks. | Codex-enhanced | Stable; Node.js, a package manager, target-repository access, and potentially networked `npx` execution |
| [`setup-cli-proxy-gateway`](skills/setup-cli-proxy-gateway/) | Configures and validates CLIProxyAPI routes for Codex CLI or Claude Code. | Codex + Claude | Advanced; macOS/Linux shell and provider authentication; can change listeners, services, credentials, and agent configuration |
| [`socket-audit`](skills/socket-audit/) | Audits repositories for supply-chain indicators and configures or removes supported install-time protections. | Universal | Stable; shell and relevant package managers; online workflows may need network and Socket.dev access |
| [`web-traffic-inspector`](skills/web-traffic-inspector/) | Inspects browser traffic and builds disposable HTML proof-prototypes for observed website actions. | Codex-enhanced | Stable proof workflow; Browser/Chrome control or `agent-browser`, Python 3, and Node.js; undocumented mechanisms may change without notice |

### Codex Side companions

These skills require Codex Side tasks and their linked-parent workflow. Installing them on another host does not provide the missing task relationship.

| Skill | What it does | Compatibility | Maturity |
|---|---|---|---|
| [`co-prompt`](skills/co-prompt/) | Reasons through a linked parent task without drafting or sending its final reply. | Codex-only | Stable |
| [`reply`](skills/reply/) | Turns a settled Side discussion into the smallest sufficient reply and sends only an explicitly approved draft. | Codex-only | Stable; can send a reply to the linked parent task |
| [`sidekick`](skills/sidekick/) | Explains a parent's latest response, helps resolve decisions, and prepares an approved reply. | Codex-only | Stable |
| [`tldr`](skills/tldr/) | Produces an ultra-concise digest of the complete available parent-task state. | Codex-only | Stable |

### macOS automation

| Skill | What it does | Compatibility | Maturity and requirements |
|---|---|---|---|
| [`imessage-autopilot`](skills/imessage-autopilot/) | Configures and operates a narrowly scoped iMessage reply controller. | Codex-only | Experimental; macOS, Messages database access, Automation permission, and Codex CLI; can send messages automatically within an approved scope |

`imessage-autopilot` has not completed its first bounded real-Messages smoke test. Review its scope, data boundary, failure behavior, and approval contract before any live use; do not treat it as production-ready.

### UK Global Talent Visa

These skills provide structured guidance for the Digital Technology route. They do not provide legal advice, do not replace current official guidance, and intentionally do not generate paste-ready application prose.

| Skill | What it does | Compatibility | Maturity |
|---|---|---|---|
| [`gtv-tech-eligibility`](skills/gtv-tech-eligibility/) | Assesses potential eligibility and produces a reusable GTV Profile. | Universal | Stable guidance workflow |
| [`gtv-tech-prepare`](skills/gtv-tech-prepare/) | Turns a GTV Profile into factual document-planning material. | Universal | Stable guidance workflow |
| [`gtv-tech-review`](skills/gtv-tech-review/) | Reviews self-written application documents from constructive and skeptical perspectives. | Universal | Stable guidance workflow |

Always verify current official eligibility, evidence, fees, timing, and authorship requirements before relying on these workflows.

## Development

The public source layout is deliberately the same unit that `npx skills` installs:

```text
skills/<skill-name>/
├── SKILL.md
├── agents/       # optional host-specific interface metadata
├── assets/       # optional templates and runtime assets
├── references/   # optional instructions loaded only when relevant
├── scripts/      # optional deterministic helpers
└── tests/        # optional regression tests
```

Run the network-free repository check before preparing a change:

```bash
./scripts/check-repo
```

It requires Python 3 with PyYAML, Node.js, `jq`, and `zsh`. It validates all 16 public skills, checks names and bundled references, and runs the fast deterministic test suites. Browser-enabled tests, live provider tests, real Messages checks, and public GitHub discovery remain explicit manual checks because they require additional tools, permissions, network access, or external state.

For a release, also confirm that the current CLI discovers all 16 skills without `--full-depth`:

```bash
npx skills add filip-pilar/skills --list
```

## Licence

Licensed under the [MIT License](LICENSE) unless otherwise noted.

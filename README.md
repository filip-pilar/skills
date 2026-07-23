# Agent Skills

Reusable workflows for coding agents: cleaner commits, sharper decisions, React diagnostics, browser-traffic inspection, macOS automation, and structured UK Global Talent guidance.

```bash
npx skills add filip-pilar/skills --list
```

[Browse the skills](#skills) · [Choose how to install](#install) · [Develop locally](#development)

## Start here

| If you want to… | Start with |
| --- | --- |
| Prepare a repository for a clean, intentional commit | [`gitprep`](skills/gitprep/) |
| Recover focus and move the current task forward | [`lockin`](skills/lockin/) |
| Improve a React Doctor score without gaming it | [`dr-react`](skills/dr-react/) |
| Create, diagnose, or refine an agent skill | [`skill-builder`](skills/skill-builder/) |

## Skills

### Workflow and reasoning

| Skill | Best for |
| --- | --- |
| [`devils-advocate`](skills/devils-advocate/) | Pressure-testing a plan, decision, argument, or piece of research without inventing objections. |
| [`gitprep`](skills/gitprep/) | Inspecting repository and publication state, planning coherent commits, and creating only approved commits. |
| [`lockin`](skills/lockin/) | Recovering the active objective, narrowing the working set, and advancing to progress, completion, or one genuine blocker. |
| [`product-vision-to-prd`](skills/product-vision-to-prd/) | Developing a broad product vision through one adaptive interview into a persistent, product-focused PRD. |
| [`skill-builder`](skills/skill-builder/) | Creating, diagnosing, improving, evaluating, and releasing skills with explicit evidence and authority boundaries. |

### Engineering and integration

| Skill | Best for |
| --- | --- |
| [`dr-react`](skills/dr-react/) | Raising a React Doctor score through small fixes and regression checks. |
| [`setup-cli-proxy-gateway`](skills/setup-cli-proxy-gateway/) | Configuring and validating CLIProxyAPI routes for Codex CLI or Claude Code. |
| [`socket-audit`](skills/socket-audit/) | Auditing supply-chain indicators and managing supported install-time protections. |
| [`web-traffic-inspector`](skills/web-traffic-inspector/) | Inspecting browser traffic and building disposable HTML proof-prototypes for observed website actions. |

### Codex Side companions

These require Codex Side tasks and their linked-parent workflow.

| Skill | Best for |
| --- | --- |
| [`co-prompt`](skills/co-prompt/) | Reasoning through a linked parent task without drafting or sending its final reply. |
| [`reply`](skills/reply/) | Turning a settled Side discussion into the smallest sufficient reply, sent only after explicit approval. |
| [`sidekick`](skills/sidekick/) | Explaining a parent's latest response, resolving decisions, and preparing an approved reply. |
| [`tldr`](skills/tldr/) | Producing an ultra-concise digest of the complete available parent-task state. |

### UK Global Talent Visa

| Skill | Best for |
| --- | --- |
| [`gtv-tech-eligibility`](skills/gtv-tech-eligibility/) | Assessing potential eligibility for the Digital Technology route and producing a reusable GTV Profile. |
| [`gtv-tech-prepare`](skills/gtv-tech-prepare/) | Turning a GTV Profile into factual document-planning material. |
| [`gtv-tech-review`](skills/gtv-tech-review/) | Reviewing self-written application documents from constructive and skeptical perspectives. |

These workflows are not legal advice and intentionally do not generate paste-ready application prose. Always verify current official eligibility, evidence, fees, timing, and authorship requirements.

## Install

List the collection without installing anything:

```bash
npx skills add filip-pilar/skills --list
```

Or install one skill directly—for example, `gitprep` globally in Codex:

```bash
npx skills add filip-pilar/skills --skill gitprep --agent codex --global
```

<details>
<summary>More installation options</summary>

Install the entire collection for Codex in the current project:

```bash
npx skills add filip-pilar/skills --skill '*' --agent codex
```

Install several selected skills:

```bash
npx skills add filip-pilar/skills \
  --skill gitprep \
  --skill lockin \
  --skill devils-advocate \
  --agent codex
```

Target Claude Code instead:

```bash
npx skills add filip-pilar/skills \
  --skill devils-advocate \
  --agent claude-code \
  --global
```

Omit `--global` for a project-scoped install. The CLI may share one installed copy between agent destinations with symlinks; add `--copy` when you explicitly want independent copies. A local-path install targeting only one agent is currently copied, so use the development symlink below when you need edits to appear live.

Be explicit about the selection: the current CLI may install every discovered skill when `--skill` is omitted.

</details>

### Updating

For installs from GitHub, the CLI records source and content metadata in `skills-lock.json`. Refresh project or global installs with:

```bash
npx skills update --project
npx skills update --global
```

Pass a skill name to update only that skill, such as `npx skills update gitprep`. Review `skills-lock.json` before committing it to another project.

The current CLI does not update installs whose recorded source is a local path. Re-run `skills add` to refresh a copied local install, or use a source symlink for live development.

## Compatibility and safety

Most skills follow shared Agent Skills conventions and can be read by compatible agents. A few intentionally depend on Codex Side tasks, Codex tools, or host-specific metadata; each `SKILL.md` is the source of truth.

Review a skill and its bundled scripts before installing it. Pay particular attention to workflows that can access repositories, browsers, messages, credentials, external services, or global configuration.

| Skill | Additional requirements or effects |
| --- | --- |
| `dr-react` | Node.js, a package manager, repository access, and potentially networked `npx` execution. |
| `gitprep` | Git and repository access; intentionally never pushes. |
| `setup-cli-proxy-gateway` | macOS/Linux shell and provider authentication; may change listeners, services, credentials, and agent configuration. |
| `skill-builder` | Python and PyYAML for bundled validation scripts. |
| `socket-audit` | Relevant package managers; online workflows may require network and Socket.dev access. |
| `web-traffic-inspector` | Browser or Chrome control (or `agent-browser`), Python 3, and Node.js; undocumented website mechanisms may change. |

## Development

Every public skill lives at `skills/<skill-name>/SKILL.md`, with optional `agents/`, `assets/`, `references/`, `scripts/`, and `tests/` beside it.

### Checks

The repository has three deliberately separate validation layers:

| Command | Purpose |
| --- | --- |
| `./scripts/check-repo` | Fast, deterministic, network-free structure and regression checks. |
| `./scripts/check-full` | Everything above plus credential-free browser-companion and synthetic gateway integration tests. |
| `./scripts/check-release` | Full validation plus current `npx skills` discovery and release-state checks. |

Run the fast check throughout development:

```bash
./scripts/check-repo
```

It requires Git, Python 3 with PyYAML, Node.js, `jq`, and `zsh`. It validates public skills, catalogue completeness, bundled-resource references, tracked-file hygiene, README links, maintainer commands, and fast deterministic tests.

Before a substantial change or release, run:

```bash
./scripts/check-full
./scripts/check-release
```

The deeper checks start disposable loopback servers. The synthetic gateway integration runs when Ruby, `curl`, `jq`, and CLIProxyAPI are available; `check-full --strict` fails instead of skipping it when they are not.

`check-release` uses the current `npx skills` CLI and therefore requires network access. It requires a clean worktree by default; use `--allow-dirty` only to rehearse it locally. After pushing, verify that public discovery matches and GitHub's default branch is at the local commit:

```bash
./scripts/check-release --remote filip-pilar/skills
```

Live-provider tests, real Messages checks, OAuth flows, and browser-enabled `agent-browser` tests remain explicit manual checks because they require credentials, permissions, or external state.

### Test a skill while editing it

For interactive dogfooding, activate one source skill in the ignored sandbox:

```bash
./scripts/dev-skill lockin
cd local/sandbox
```

Start the agent there. Source edits are visible immediately, and selecting another skill safely replaces the managed link. The command refuses to remove unmanaged sandbox entries or traverse symlinked sandbox directories.

Inspect or remove the active development skill with:

```bash
./scripts/dev-skill --status
./scripts/dev-skill --remove
```

Use the normal installer and `skills update` when testing the copied or published installation path instead.

## License

Licensed under the [MIT License](LICENSE).

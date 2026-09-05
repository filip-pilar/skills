# Agent Skills

Reusable workflows for coding agents: cleaner commits, sharper decisions, browser-traffic inspection, Codex Side coordination, and structured UK Global Talent guidance.

```bash
npx skills add filip-pilar/skills --list
```

[Browse the skills](#skills) · [Choose how to install](#install) · [Develop locally](#development)

## Start here

| If you want to… | Start with |
| --- | --- |
| Prepare a repository for a clean, intentional commit | [`gitprep`](skills/gitprep/) |
| Create, diagnose, or refine an agent skill | [`skill-builder`](skills/skill-builder/) |
| Orchestrate a Codex parent from Side | [`sidekick`](skills/sidekick/) → [`reply`](skills/reply/) → [`supervise`](skills/supervise/) |

## Skills

### Workflow and reasoning

| Skill | Best for |
| --- | --- |
| [`devils-advocate`](skills/devils-advocate/) | Pressure-testing a plan, decision, argument, or piece of research without inventing objections. |
| [`gitprep`](skills/gitprep/) | Inspecting repository and publication state, planning coherent commits, and creating only approved commits. |
| [`product-vision-to-prd`](skills/product-vision-to-prd/) | Developing a broad product vision through one adaptive interview into a persistent, product-focused PRD. |
| [`skill-usage-auditor`](skills/skill-usage-auditor/) | Auditing one custom skill against its contract using version-pinned local Codex task evidence. |
| [`skill-builder`](skills/skill-builder/) | Creating, diagnosing, improving, evaluating, and releasing skills with explicit evidence and authority boundaries. |

### Engineering and integration

| Skill | Best for |
| --- | --- |
| [`codex-skill-usage-analytics`](skills/codex-skill-usage-analytics/) | Cross-referencing current Codex skills with daily skill and plugin invocation analytics from the authenticated private ChatGPT backend. |
| [`web-traffic-inspector`](skills/web-traffic-inspector/) | Inspecting browser traffic and building disposable HTML proof-prototypes for observed website actions. |

### Codex Side companions

These require Codex Side tasks and their linked-parent workflow. All three
orchestration skills are manual-only. The usual sequence is below; Reply is
optional when a clear, current parent-ready prompt already exists:

1. **`$sidekick` — understand and discuss.**
2. **`$reply` — draft the exact parent prompt without sending.**
3. **`$supervise` — send, follow, verify, correct, and hand off accurately.**

| Skill | Best for |
| --- | --- |
| [`sidekick`](skills/sidekick/) | Explaining what a linked parent completed, what remains, and any user-owned decision or next move. |
| [`reply`](skills/reply/) | Turning settled Side discussion into one clear parent prompt in the user's voice without sending it. |
| [`supervise`](skills/supervise/) | Selecting and sending the user's current intended parent prompt, following and verifying the work, continuing in-scope corrections, and preserving decision-critical meaning in the completion handoff. |
| [`recover-side-thread`](skills/recover-side-thread/) | Finding and reconstructing an expired or closed Side chat from local Side-tab state and logs, supplemented by visible evidence, while refusing normal Codex tasks. |

### UK Global Talent Visa

| Skill | Best for |
| --- | --- |
| [`gtv-tech-eligibility`](skills/gtv-tech-eligibility/) | Assessing potential eligibility for the Digital Technology route and producing a reusable GTV Profile. |
| [`gtv-tech-prepare`](skills/gtv-tech-prepare/) | Turning an assessed GTV Profile or equivalent context into factual document-planning material. |
| [`gtv-tech-review`](skills/gtv-tech-review/) | Reviewing self-written application documents from constructive and skeptical perspectives. |

These workflows are not legal advice and intentionally do not generate paste-ready application prose. Always verify current official eligibility, evidence, fees, timing, and authorship requirements.

## Archived skills

Retired packages are preserved unchanged under [`legacy/skills/`](legacy/skills/).
See the [archive catalogue](legacy/README.md) for the list; they are outside the
supported public collection and its validation path.

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

For project installs, the CLI records source and content metadata in
`skills-lock.json`. Global installs use `~/.agents/.skill-lock.json`, or
`$XDG_STATE_HOME/skills/.skill-lock.json` when that environment variable is set.
Refresh project or global installs with:

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
| `codex-skill-usage-analytics` | An authenticated local Codex installation; performs credential-safe GET requests to undocumented ChatGPT analytics endpoints that may change. |
| `gitprep` | Git and repository access; bare invocation plans only. Approved commits proceed within existing authority; publication is a separate request. |
| `skill-builder` | Python and PyYAML for bundled validation scripts. |
| `sidekick`, `reply`, `supervise` | Codex Side, an exact linked parent task, and manual invocation. |
| `web-traffic-inspector` | Browser or Chrome control (or `agent-browser`), Python 3, and Node.js; undocumented website mechanisms may change. |

## Development

Every public skill lives at `skills/<skill-name>/SKILL.md`, with optional `agents/`, `assets/`, `references/`, `scripts/`, and `tests/` beside it.

Start with the smallest package that delivers the behavior. References should hold
substantial conditional knowledge; scripts should provide reliable execution; tests
should protect meaningful failures. Routine instruction edits do not need a new
template, test suite, or evaluation framework. Structural validation checks package
integrity, not preferred editorial wording or model behavior.

The analytics collector emits JSON; the agent handles report presentation.
`--format json` remains supported, while `--format markdown` has been removed.

Repository-specific agent guidance lives in [`AGENTS.md`](AGENTS.md). Install the
pinned Python development dependency with:

```bash
python3 -m pip install --requirement requirements-dev.txt
```

### Checks

The repository has focused iteration plus three deliberately separate validation layers:

| Command | Purpose |
| --- | --- |
| `./scripts/check-skill <name>` | Validate one skill and run its deterministic Python and Node.js package tests. |
| `./scripts/check-repo` | Fast, deterministic, network-free structure and regression checks. |
| `./scripts/check-full` | Everything above plus credential-free browser-companion integration tests. |
| `./scripts/check-release` | Full validation plus current `npx skills` discovery and release-state checks. |

Use the focused check while editing, then run the repository check before handoff:

```bash
./scripts/check-skill gitprep
./scripts/check-repo
```

The focused command excludes credentialed, live-provider, and standalone shell
integration tests. The repository check requires Git, Python 3 with PyYAML,
and Node.js. It validates public skills, catalogue completeness,
bundled-resource references, tracked-file hygiene, README links, maintainer
commands, and fast deterministic tests.

For substantial integration changes, run:

```bash
./scripts/check-full
```

For a release, additionally run:

```bash
./scripts/check-release
```

The deeper checks start disposable loopback servers and run the companion
integration suite. Individual browser tests remain opt-in and may be skipped;
unittest reports their skip count. The final summary counts executed suites,
not individual tests. `check-full --strict` remains accepted for compatibility
and does not enable browser tests.

`check-release` uses the current `npx skills` CLI and therefore requires network access. It requires a clean worktree by default; use `--allow-dirty` only to rehearse it locally. After pushing, verify that public discovery matches and GitHub's default branch is at the local commit:

```bash
./scripts/check-release --remote filip-pilar/skills
```

Live-provider tests, OAuth flows, and browser-enabled `agent-browser` tests remain explicit manual checks because they require credentials, permissions, or external state.

### Test a skill while editing it

For interactive dogfooding, activate one source skill in the ignored sandbox:

```bash
./scripts/dev-skill gitprep
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

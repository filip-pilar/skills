# Agent Skills

Reusable workflows for Codex and Claude Code: cleaner commits, sharper decisions, media tools, and browser-traffic inspection. Skills that require a specific host are labeled below.

[Browse the skills](#skills) · [Choose how to install](#install) · [Develop locally](#development)

## Skills

### Workflow and reasoning

| Skill | Best for |
| --- | --- |
| [`devils-advocate`](skills/devils-advocate/) | Pressure-testing a plan, decision, argument, or piece of research without inventing objections. |
| [`gitprep`](skills/gitprep/) | Inspecting repository and publication state, planning coherent commits, and creating only approved commits. |

### Media

| Skill | Best for |
| --- | --- |
| [`download-media`](skills/download-media/) | Choosing and downloading whole recordings or multiple video/audio clips through compact interactive controls in Codex or ChatGPT Work Local. |
| [`tldr`](skills/tldr/) | Explaining the latest substantive message or selected content through engaging diagrams, illustrated comparisons, and visual sequences in Codex. |
| [`tldw`](skills/tldw/) | Transcribing an English recording locally, then explaining its central ideas through generated visuals in Codex. |
| [`transcribe`](skills/transcribe/) | Transcribing English recording URLs and local audio/video into durable Markdown on Apple Silicon, with optional speaker labels. |

### Engineering and integration

| Skill | Best for |
| --- | --- |
| [`codex-skill-analytics`](skills/codex-skill-analytics/) | Cross-referencing current Codex skills with daily skill and plugin invocation analytics from the authenticated private ChatGPT backend. |
| [`web-traffic-inspector`](skills/web-traffic-inspector/) | Inspecting browser traffic and building disposable HTML proof-prototypes for observed website actions. |

## Archived skills

Archived packages live under [`legacy/skills/`](legacy/skills/).
See the [archive catalogue](legacy/README.md) for the list; they are outside the
supported public collection and its validation path.

## Install

List the collection without installing anything:

```bash
npx skills add filip-pilar/skills --list
```

Install one skill globally for your host:

```bash
npx skills add filip-pilar/skills --skill gitprep --agent codex --global
# Or, for Claude Code:
npx skills add filip-pilar/skills --skill gitprep --agent claude-code --global
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

Install the shared collection for Claude Code in the current project:

```bash
npx skills add filip-pilar/skills \
  --skill devils-advocate \
  --skill gitprep \
  --skill transcribe \
  --skill web-traffic-inspector \
  --agent claude-code
```

Omit `--global` for a project-scoped install. The CLI may share one installed copy between agent destinations with symlinks; add `--copy` when you explicitly want independent copies. Use the development symlink below when you need source edits to appear live.

Be explicit about the selection: the current CLI may install every discovered skill when `--skill` is omitted. `--agent` selects an installation destination; it does not adapt host-specific tools or filter incompatible skills.

</details>

### Updating

Refresh project or global installs with:

```bash
npx skills update --project
npx skills update --global
```

Pass a skill name to select it, such as `npx skills update --global gitprep`.
For installer behavior and further options, use the
[skills CLI documentation](https://github.com/vercel-labs/skills#skills-update).

## Compatibility and safety

Four skills share the same package for Codex and Claude Code. Four retain Codex-specific dependencies; Download Media also supports ChatGPT Work Local. Transcribe works with any listed host that has shell access to an Apple Silicon Mac, including ChatGPT Work Local. Each `SKILL.md` declares its runtime requirements. Installing a skill does not select a model or supply missing tools.

Packages follow the [Agent Skills format](https://agentskills.io/specification), with host-specific invocation settings. All skills except `web-traffic-inspector` are manual-only in their supported hosts. Invoke them with `$skill-name` in Codex or `/skill-name` in Claude Code. Shared manual-only skills include both [Codex's `policy.allow_implicit_invocation: false`](https://learn.chatgpt.com/docs/build-skills#optional-metadata) in `agents/openai.yaml` and [Claude Code's `disable-model-invocation: true`](https://code.claude.com/docs/en/skills#control-who-invokes-a-skill) in `SKILL.md`. Other agents may read the format but are not covered by these invocation settings.

Review a skill and its bundled scripts before installing it. Pay particular attention to workflows that can access repositories, browsers, messages, credentials, external services, or global configuration.

| Skill | Hosts | Additional requirements or effects |
| --- | --- | --- |
| `devils-advocate` | Codex, Claude Code | No additional tools required. |
| `gitprep` | Codex, Claude Code | Git and shell access to the repository; bare invocation plans only. Commits and publication require authorization. |
| `transcribe` | Codex, Claude Code, ChatGPT Work Local | Apple Silicon, macOS 14+, Python 3.10+, FFmpeg/ffprobe, and Swift 6.2+ for the first build; supported JavaScript runtime and EJS for YouTube. Helps set up missing tools; model weights and URL downloads need initial network access. |
| `web-traffic-inspector` | Codex, Claude Code | Browser control and local shell access with Python 3.10+; companions require Node.js 18+, and browser execution also requires `agent-browser`. |
| `codex-skill-analytics` | Codex-specific | Python 3.11+ and an authenticated local Codex installation; performs credential-safe GET requests to undocumented ChatGPT analytics endpoints that may change. Measures Codex usage only. |
| `tldr` | Codex-specific | Built-in image generation and inline image display; generates one or more image cards, with text fallback if generation is unavailable or fails. |
| `tldw` | Codex-specific | Transcribe's Apple Silicon and local-shell requirements, plus built-in image generation and inline image display. Bundles the same transcription pipeline and shares its cache and completed transcripts; no separate Transcribe installation is needed. Explains spoken content, with text fallback if image generation fails. |
| `download-media` | Codex, ChatGPT Work Local; host-specific | Local shell, Python 3.10+, yt-dlp, and FFmpeg/ffprobe; supported JavaScript runtime and EJS for YouTube. Helps set up missing tools. Inline controls require Visualize and the `window.openai` widget bridge, with text fallback when unavailable. Saves only selected media to Downloads. |

## Development

Package layout and repository rules live in [`AGENTS.md`](AGENTS.md).

TLDW bundles copies so it can be installed independently. Maintain its
`scripts/transcribe.py`, `runtime/`, and `references/runtime.md` from Transcribe,
and its `references/visual-explainers.md` from TLDR. Copy changes into TLDW when
editing these sources; `check-repo` rejects mismatched copies.

### Checks

Use the smallest check relevant to the change and reuse its result:

| Command | Purpose |
| --- | --- |
| `./scripts/check-repo` | Check skill names, catalogue, README links, shared bundled files, and file hygiene. |
| `./scripts/check-release` | Repository checks plus current `npx skills` discovery and release-state verification. |

Documentation changes need content and link review. Package, catalogue, and shared
tooling changes need `check-repo`, which uses Git and Python 3's standard library
without credentials or external services.

Check executable changes with targeted temporary fixtures. For skill behavior,
rerun a representative workflow from the request, supplied files, or examples and
inspect its outcome; usage counts do not establish quality. For host-compatibility
changes, check discovery and invocation metadata in each supported host, including
manual-only exclusion from automatic selection. Distinguish these checks from a
completed workflow in that host. Keep evidence outside packages. Live-provider,
OAuth, browser, installation, and publication checks need applicable authorization.

`check-release` uses the current `npx skills` CLI and requires network access and a
clean worktree; use `--allow-dirty` only for local rehearsal. After an authorized
push, verify public discovery and the default branch against the local commit:

```bash
./scripts/check-release --remote filip-pilar/skills
```

### Test a skill while editing it

For routine behavior checks, invoke the source `SKILL.md` by its absolute path in
the target host. To check project discovery with live source edits, start from the
repository root and create a disposable project:

```bash
skill_sandbox=$(mktemp -d)
mkdir -p "$skill_sandbox/.agents/skills" "$skill_sandbox/.claude/skills"
ln -s "$PWD/skills/gitprep" "$skill_sandbox/.agents/skills/gitprep"
ln -s "$PWD/skills/gitprep" "$skill_sandbox/.claude/skills/gitprep"
cd "$skill_sandbox"
```

Start Codex or Claude Code there. Confirm discovery and explicitly invoke
`$gitprep` or `/gitprep`, respectively. This adds the chosen source skill to that
project; globally installed skills may still be available and can take precedence.

Use the normal installer and `skills update` when testing the copied or published installation path instead.

## License

Licensed under the [MIT License](LICENSE).

# Agent Skills

Reusable workflows for GPT-6 Astra in Codex: cleaner commits, sharper decisions, media tools, and browser-traffic inspection.

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
| [`download-media`](skills/download-media/) | Choosing and downloading whole recordings or multiple video/audio clips through compact interactive controls; manual invocation only. |
| [`tldr`](skills/tldr/) | Explaining the latest substantive message or selected content with generated image cards; manual invocation only. |
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

Omit `--global` for a project-scoped install. The CLI may share one installed copy between agent destinations with symlinks; add `--copy` when you explicitly want independent copies. Use the development symlink below when you need source edits to appear live.

Be explicit about the selection: the current CLI may install every discovered skill when `--skill` is omitted.

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

The supported runtime is GPT-6 Astra in Codex. Download Media and Transcribe also support ChatGPT Work Local with local shell access; Transcribe requires an Apple Silicon Mac and its native pipeline is validated on macOS. Packages use Agent Skills conventions, but other models and agents are outside the supported development and validation scope. Each `SKILL.md` owns its runtime contract. Select GPT-6 Astra in the host: installing a skill does not select or enforce a model.

Review a skill and its bundled scripts before installing it. Pay particular attention to workflows that can access repositories, browsers, messages, credentials, external services, or global configuration.

| Skill | Additional requirements or effects |
| --- | --- |
| `codex-skill-analytics` | Python 3.11+ and an authenticated local Codex installation; performs credential-safe GET requests to undocumented ChatGPT analytics endpoints that may change. |
| `gitprep` | Git and repository access; bare invocation plans only. Commits and publication require authorization. |
| `tldr` | Built-in image generation in Codex; generates one or more image cards when invoked. |
| `download-media` | Local shell, Python 3.10+, yt-dlp, and FFmpeg/ffprobe; supported JavaScript runtime and EJS for YouTube. Helps set up missing tools. Visualize for inline controls, with text fallback. Saves only selected media to Downloads. |
| `transcribe` | Apple Silicon, macOS 14+, Python 3.10+, ffmpeg, and Swift 6.2+ for the first build; supported JavaScript runtime and EJS for YouTube. Helps set up missing tools; model weights and URL downloads need initial network access. |
| `web-traffic-inspector` | Browser control and Python 3.10+; companions require Node.js 18+, and browser execution also requires `agent-browser`. |

## Development

Package layout and repository rules live in [`AGENTS.md`](AGENTS.md).

### Checks

Use the smallest check relevant to the change and reuse its result:

| Command | Purpose |
| --- | --- |
| `./scripts/check-repo` | Check skill names, catalogue, README links, and file hygiene. |
| `./scripts/check-release` | Repository checks plus current `npx skills` discovery and release-state verification. |

Documentation changes need content and link review. Package, catalogue, and shared
tooling changes need `check-repo`, which uses Git and Python 3's standard library
without credentials or external services.

Check executable changes with targeted temporary fixtures. For skill behavior,
rerun a representative workflow from the request, supplied files, or examples and
inspect its outcome; usage counts do not establish quality. Keep evidence outside
packages. Live-provider, OAuth, browser, installation, and publication checks need
applicable authorization.

`check-release` uses the current `npx skills` CLI and requires network access and a
clean worktree; use `--allow-dirty` only for local rehearsal. After an authorized
push, verify public discovery and the default branch against the local commit:

```bash
./scripts/check-release --remote filip-pilar/skills
```

### Test a skill while editing it

For routine behavior checks, invoke the source `SKILL.md` by its absolute path in
Codex. To check project discovery with live source edits, start from the repository
root and create a disposable project:

```bash
skill_sandbox=$(mktemp -d)
mkdir -p "$skill_sandbox/.agents/skills"
ln -s "$PWD/skills/gitprep" "$skill_sandbox/.agents/skills/gitprep"
cd "$skill_sandbox"
```

Start Codex there with GPT-6 Astra selected. This adds the chosen source skill to
that project; globally installed skills may still be available.

Use the normal installer and `skills update` when testing the copied or published installation path instead.

## License

Licensed under the [MIT License](LICENSE).

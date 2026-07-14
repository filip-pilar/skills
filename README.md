# Skills

Personal skills I use and share.

Most top-level folders are standalone skills. The `gtv/` folder groups related UK Global Talent Visa skills. Some skills are portable across multiple agent environments; others depend on local tools, browser automation, operating-system permissions, or app-specific integrations.

## Available Skills

- `devils-advocate`: Constructively pressure-test ideas, plans, decisions, arguments, and research without empty contrarianism, surfacing material risks and proportionate responses.
  - Use directly: `Use $devils-advocate to pressure-test this plan.`
- `dr-react`: Run a guarded React Doctor score-improvement workflow with root-cause fixes, concise impact evidence, verification gates, visual regression checks, and anti-score-gaming rules.
  - Use directly: `Use $dr-react to raise this repo's React Doctor score to 70.`
  - Use as a goal loop: `/goal Use $dr-react to raise this repo's React Doctor score to at least 70.`
  - Override the target: `Use $dr-react to raise this repo's React Doctor score to 85.`
- `gitprep`: Inspect the current git diff, propose a clean commit plan, run approved checks, and commit exactly the approved files or hunks. Pushes only when separately requested afterward.
  - Use directly: `Use $gitprep to inspect my current diff and propose a clean commit plan.`
- `optimize-skill`: Remove bloat from an existing skill while preserving its behavior, utility, safety, and task fit.
  - Use directly: `Use $optimize-skill to optimize sidekick without changing its behavior.`
- `poke-negotiator`: Negotiate with Poke by Interaction through macOS Messages/iMessage or Telegram Web, verify checkout links, and stop before payment or account-connection steps.
  - Use directly: `Use $poke-negotiator to start a Poke negotiation.`
- `socket-audit`: Audit local git repos for compromised dependencies and optionally install Socket.dev-based npm/pnpm/Bun protection.
  - Use directly: `Use $socket-audit to audit my local repos for compromised dependencies.`
  - Protection only: `Use $socket-audit to set up going-forward Socket protection.`
- `sidekick`: Use a Codex Side task to immediately explain the newest completed parent response in plain language, identify what it needs from you, and prepare an approved reply.
  - Use directly in a Side task: invoke `$sidekick` initially and again after each parent reply; no additional prompt is required.
- `tldr`: Use a Codex Side task to turn the entire linked parent task into an ultra-concise state digest covering completed work, material bugs, verification, decisions, and open items.
  - Use directly in a Side task: invoke `$tldr` for the complete digest and invoke it again whenever you want a refreshed digest.
- `setup-cli-proxy-gateway`: Audit, install, migrate, configure, validate, and roll back a local CLIProxyAPI gateway for Codex CLI or Claude Code using OpenAI, Anthropic, or xAI routes.
  - Use directly: `Use $setup-cli-proxy-gateway to configure a reversible Claude Code or Codex CLI model route.`
- `gtv/gtv-tech-eligibility`: Assess UK Global Talent Visa Digital Technology eligibility and produce a reusable GTV Profile.
  - Use directly: `Use $gtv-tech-eligibility to assess whether I may qualify for the UK Global Talent Visa Digital Technology route.`
- `gtv/gtv-tech-prepare`: Plan GTV application documents as structured bullet points from a GTV Profile.
  - Use directly: `Use $gtv-tech-prepare to plan my GTV application documents from my GTV Profile.`
- `gtv/gtv-tech-review`: Review self-written GTV application documents without rewriting application prose.
  - Use directly: `Use $gtv-tech-review to review my self-written GTV application documents.`

## Usage

Use the folder for the skill you want. Installation, loading, and invocation depend on the agent environment you are using, so check the skill's `SKILL.md` for its requirements and supported workflows.

## Notes

- Skills are not guaranteed to be portable everywhere.
- Read each skill's `SKILL.md` for supported tools, permissions, and safety stops.
- `dr-react` runs `npx react-doctor@latest`, which may require network/package-manager access in a target repository.
- `gitprep` is manual-only and should be explicitly invoked as `$gitprep`.
- `optimize-skill` is manual-only and should be explicitly invoked as `$optimize-skill`.
- `sidekick` is manual-only and should be explicitly invoked as `$sidekick` inside a Codex Side task.
- `tldr` is manual-only and should be explicitly invoked as `$tldr` inside a Codex Side task.
- `setup-cli-proxy-gateway` can change local authentication, listeners, services, and harness configuration; it requires explicit approval for mutations and paid provider calls.
- `poke-negotiator` can require Full Disk Access and Messages Automation permissions on macOS when using iMessage/Messages.
- `poke-negotiator` requires browser automation for Telegram Web.
- `socket-audit` is manual-only and can require network access, Socket.dev auth, package-manager installs, and explicit approval before modifying shell/package-manager configuration.
- The GTV skills provide application guidance, not legal or immigration advice, and intentionally refuse to generate paste-ready application text.

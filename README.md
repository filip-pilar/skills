# Skills

Personal skills I use and share.

Most top-level folders are standalone skills. The `gtv/` folder groups related UK Global Talent Visa skills. Some skills are portable across multiple agent environments; others depend on local tools, browser automation, operating-system permissions, or app-specific integrations.

## Available Skills

- `co-prompt`: Use a Codex Side task to understand and reason through its linked parent without producing or sending the final reply.
  - Use directly in a Side task: invoke `$co-prompt` to start or restore the discussion.
- `devils-advocate`: Constructively pressure-test ideas, plans, decisions, arguments, and research without empty contrarianism, surfacing material risks and proportionate responses.
  - Use directly: `Use $devils-advocate to pressure-test this plan.`
- `dr-react`: Run a guarded React Doctor score-improvement workflow with root-cause fixes, concise impact evidence, verification gates, visual regression checks, and anti-score-gaming rules.
  - Use directly: `Use $dr-react to raise this repo's React Doctor score to 70.`
  - Use as a goal loop: `/goal Use $dr-react to raise this repo's React Doctor score to at least 70.`
  - Override the target: `Use $dr-react to raise this repo's React Doctor score to 85.`
- `gitprep`: Inspect the current git diff, propose a clean commit plan, run approved checks, and commit exactly the approved files or hunks. Pushes only when separately requested afterward.
  - Use directly: `Use $gitprep to inspect my current diff and propose a clean commit plan.`
- `imessage-autopilot`: Configure and operate an explicitly scoped, current-session iMessage Autopilot through a bundled resident Codex controller.
  - Use directly: `Use $imessage-autopilot to set up my scoped iMessage Autopilot.`
- `skill-builder`: Create, diagnose, semantically improve, compress, evaluate, and release Codex skills through an outcome-first lifecycle with behavioral regression evidence.
  - Use directly: `Use $skill-builder to diagnose this skill from the attached bad output.`
  - Compression only: `Use $skill-builder to compress this skill without changing its behavior.`
- `reply`: Turn a settled Codex Side discussion into the smallest sufficient reply for its linked parent.
  - Use directly in a Side task: invoke `$reply` after the response has been decided.
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
- Manual-only skills are `co-prompt`, `devils-advocate`, `gitprep`, `imessage-autopilot`, `reply`, `sidekick`, `skill-builder`, `socket-audit`, and `tldr`; invoke them explicitly as `$name`.
- `dr-react` runs `npx react-doctor@latest`, which may require network/package-manager access in a target repository.
- `imessage-autopilot` requires explicit Messages database and Automation permissions for live use; its first bounded live smoke remains deferred.
- `skill-builder` uses Improve for intentional behavior changes and Compress for behavior-preserving compression.
  - Its development-only regression cases live under `.evals/skill-builder/`, outside the distributable skill package.
- `setup-cli-proxy-gateway` can change local authentication, listeners, services, and harness configuration; it requires explicit approval for mutations and paid provider calls.
- `socket-audit` can require network access, Socket.dev auth, package-manager installs, and explicit approval before modifying shell/package-manager configuration.
- The GTV skills provide application guidance, not legal or immigration advice, and intentionally refuse to generate paste-ready application text.

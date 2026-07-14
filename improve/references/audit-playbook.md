# Audit playbook

Use the relevant categories plus **Finding format**. Translate examples to the repository's stack. A finding requires direct evidence; a plausible smell without a location is a search lead, not a finding.

## Default skip-list

Skip generated, vendored, cache, and build output unless explicitly targeted:

```text
node_modules dist build out .next .nuxt .svelte-kit .turbo coverage vendor
target .venv venv __pycache__ .mypy_cache .pytest_cache .gradle bin obj Pods
.terraform .serverless .cache .vercel .netlify
```

Skip lockfiles, minified bundles, maps, generated protocol files, and snapshots as audit targets; they may still be evidence. Note additional generated paths discovered during recon.

## 1. Correctness / bugs

- Swallowed errors, empty catches, missing UI error states, and cleanup omitted from failure paths.
- Unawaited work, races, stale closures, missing cancellation, and non-idempotent retries.
- Unsafe null assertions, unchecked indexing, boundary/timezone/overflow errors.
- Invalid state combinations, silently ignored enum/status cases, and broken transactions.
- Type-system overrides clustered on critical paths.
- Leaked files, connections, listeners, subscriptions, or locks.

## 2. Security

Keep findings defensive and evidence-based. Do not include runnable abuse steps or secret values.

- Credentials in code, committed environment files, logs, or history stores. Cite type/location and require rotation.
- Untrusted input reaching SQL, shells, HTML, dynamic execution, privileged APIs, or filesystem paths without a safe boundary.
- Missing server-side identity, authorization, tenant/ownership checks, or request-authenticity protections.
- Unvalidated request bodies, unsafe uploads, mass assignment, or missing size/type limits.
- Reachable high/critical dependency advisories affecting runtime or distribution paths.
- Broad production CORS, weak cookie/header settings, debug behavior, PII logging, or internal errors returned to clients.
- Prompt injection only when evidence shows `untrusted source → AI/automation consumer → instruction-capable context → plausible meaningful effect`. Ordinary imperative text, host-recognized repository instructions, test fixtures, or inert docs are not findings by themselves.

Standard platform behavior and recorded tradeoffs are not findings unless their implementation adds risk. If code and a decision record disagree, report decision drift.

## 3. Performance

- Query/fetch-per-item patterns and missing batching.
- Repeated scans or expensive work inside hot loops where indexing or caching fits.
- Identical computations/fetches repeated across one request or render.
- Unbounded lists, missing pagination, over-fetching, and oversized payloads.
- Frontend waterfalls, unnecessary client work, heavy dependencies, or unoptimized assets when relevant.
- Synchronous backend work that belongs off-path, connection misuse, or indexes implied by verified query/schema evidence.
- Redundant CI work and missing safe caching/parallelization.

## 4. Test coverage

- Critical money, auth, mutation, and core-product paths without meaningful coverage.
- High-churn modules without characterization tests.
- Assertions that prove little, mock-only tests, brittle snapshots, real network/timers, or order dependence.
- Missing integration coverage at boundaries or needlessly expensive end-to-end coverage.
- No reliable one-command verification baseline; treat this as a prerequisite for risky changes.

## 5. Tech debt / architecture

- Divergent duplication in three or more places.
- Circular or reversed dependencies, UI/data-layer leakage, and high-fan-in junk drawers.
- Dead modules, completed flags, abandoned branches, or unused dependencies.
- Files/functions far beyond repository norms, deep conditionals, and excessive parameters.
- Multiple competing patterns for the same concern; prefer the most recent established convention.
- Premature single-use abstractions or changes that require lockstep edits because an abstraction is missing.

## 6. Dependencies / migrations

- Core runtime/framework versions near EOL or security-support cutoffs.
- APIs with documented removal timelines.
- Archived or abandoned dependencies on critical paths.
- Duplicate libraries for the same job, manifest/lock drift, and monorepo pinning inconsistency.
- Estimate blast radius and verification cost; version age alone is not a reason to migrate.

## 7. DX / tooling

- Missing or broken typecheck, lint, formatter, editor, or safe pre-commit setup.
- Slow local feedback, missing watch paths, or avoidably slow CI.
- Incorrect onboarding, undocumented required configuration, or missing safe examples.
- Missing durable agent guidance where agents routinely work in the repository; recommend only the host files the team actually uses.
- Debugging blocked by vague errors, unstructured logs, or absent correlation IDs.

## 8. Docs

Report documentation only when the cost is concrete: undocumented public APIs, unrecoverable active decisions, or instructions/examples that are materially wrong. Missing prose without operational impact is low priority.

## 9. Direction

Every option must cite repository evidence. Strong signals include unfinished feature clusters, stated-but-undelivered intent, asymmetric capabilities, architecture that makes an adjacent feature unusually cheap, and documented manual work users repeatedly perform.

Do not recommend generic category features or revive options rejected by a decision record. State user value, tradeoffs, coarse effort, and grounding confidence. Selected direction work normally becomes a bounded design/spike plan rather than an assumed full build.

## Finding format

```markdown
### [CATEGORY-NN] Imperative title

- **Evidence**: `path/file.ext:line` — verified fact. Use 2–5 strongest sites.
- **Impact**: Concrete failure, cost, or user value.
- **Effort**: S (hours) | M (about a day) | L (multi-day), including tests.
- **Risk**: LOW | MED | HIGH — what the change could break.
- **Confidence**: HIGH | MED | LOW. LOW becomes an investigation, not an asserted fix.
- **Fix sketch**: 1–3 sentences, enough to judge scope; not the implementation plan.
```

## Prioritization

Rank by impact divided by effort, discounted by confidence and fix risk. Float prerequisites, high-confidence security issues, and changes with clean verification. “Not worth doing” is valid; record why so it is not rediscovered next run.

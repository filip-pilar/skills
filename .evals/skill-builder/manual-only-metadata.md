# Manual-only Metadata Ownership

## Purpose

Verify that Skill Builder treats activation metadata as a coordinated contract instead of repeating invocation and runtime behavior in every field.

## Target

Use a manual-only skill with `allow_implicit_invocation: false`, an explicit `$skill` default prompt, and runtime behavior in its body. Include a contrasting implicit skill whose description needs matching cues.

## Invocation and context

Ask Skill Builder to create, assess, or improve the packages without supplying a suspected wording fix.

## Raw evidence

The historical Sidekick description duplicated `$sidekick`, decision, approval, send, and re-entry behavior despite manual-only policy and a complete runtime body.

## Expected behavior

Treat policy as the activation authority. Keep a manual-only description limited to purpose and scope without restating the invocation mode, keep `short_description` as a UI capability summary, put explicit invocation in `default_prompt`, and keep post-invocation behavior in the body. Preserve concise matching and non-use boundaries for an implicit skill.

## Forbidden behavior

- Do not optimize every description toward one generic shape.
- Do not remove useful matching cues from implicit skills.
- Do not treat repeated phrases across metadata surfaces as proof of consistency.
- Do not move runtime safeguards out of the body merely to shorten it.

## Pass conditions

- Inspect `description`, `allow_implicit_invocation`, `short_description`, `default_prompt`, and the body together.
- Reject manual/explicit/user-invoked labels, `$skill` commands, or invocation/re-entry mechanics in a manual-only description.
- Keep `short_description` as a capability summary rather than another invocation surface.
- Require the manual-only default prompt, not the description, to contain the `$skill` invocation.
- Allow an implicit default prompt that does not repeat `$skill`.
- Preserve trigger cues and material non-use boundaries in an implicit description.
- Keep runtime workflow, state, approvals, and fallbacks in the body.

## Validation record

- 2026-07-15: Thirteen isolated validator tests passed for default and explicit policy, description and UI-summary ownership, default prompts, trigger and re-entry wording, and TODO-status handling.
- 2026-07-15: Repository-wide replay passed all 15 distributable packages, both ignored local packages, and both fixtures with zero warnings. All 12 audited manual-only descriptions now contain purpose and scope only; implicit descriptions retained their matching cues.

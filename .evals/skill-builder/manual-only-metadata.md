# Manual-only metadata ownership

## Scenario

Ask Skill Builder to create, assess, or improve a manual-only skill with `allow_implicit_invocation: false`, an explicit `$skill` default prompt, and runtime behavior in its body. Include a contrasting implicit skill whose description needs matching cues. Do not suggest a wording fix.

## Pass conditions

- Inspect `description`, `allow_implicit_invocation`, `short_description`, `default_prompt`, and the body together.
- Reject manual/explicit/user-invoked labels, `$skill` commands, or invocation/re-entry mechanics in a manual-only description.
- Keep `short_description` as a capability summary rather than another invocation surface.
- Require the manual-only default prompt, not the description, to contain the `$skill` invocation.
- Allow an implicit default prompt that does not repeat `$skill`.
- Preserve trigger cues and material non-use boundaries in an implicit description.
- Keep runtime workflow, state, approvals, and fallbacks in the body.

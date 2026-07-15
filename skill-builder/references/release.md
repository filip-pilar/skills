# Release a Skill

Release is an optional stage for an already accepted skill. It does not grant content-change, install, commit, push, publish, or out-of-workspace write authority.

## Readiness checks

1. Inspect the complete diff and current git state; isolate unrelated work.
2. Run `python3 scripts/inspect_skill.py <skill-directory>` for root and applicable `--load` paths, then `python3 scripts/validate_skill.py <skill-directory>` from Skill Builder.
3. Run every added or changed script on representative safe inputs.
4. Verify metadata, links, resource routing, executable permissions, and symlinks. Confirm invocation policy, description, `short_description`, `default_prompt`, and runtime instructions have distinct, consistent ownership.
5. Replay accepted behavioral scenarios and known regressions at the strongest feasible evidence level.
6. Confirm that answer keys, raw benchmark outputs, caches, bytecode, generated outputs, and temporary work are outside the distributable skill directory. Runtime-needed templates may remain.
7. Compare repository, installed, and packaged copies when the request includes synchronization.

Do not silently overwrite a divergent installed copy. Report the difference and use the user-authorized source of truth. Do not commit, push, install globally, or publish without the corresponding authorization.

Report semantic changes, representation changes, affected loading-path size, validation results, evidence level, exact installation or distribution state, and unresolved uncertainty.

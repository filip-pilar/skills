# Closing the loop

The advisor remains source-read-only. An executor may edit only its isolated worktree; the advisor dispatches, verifies, and updates plan records in the original checkout.

`<plans-dir>` means the one directory selected for this run.

## `execute <plan>`

### Preconditions

Stop unless all hold:

- The target is a Git repository.
- The plan exists and every dependency is DONE.
- `Planned at` is a full commit SHA and equals the original checkout's current `HEAD`. If not, reconcile and re-stamp or stop.
- Every in-scope tracked path matches that SHA and no in-scope untracked file exists.
- Other dirty paths are disclosed; stop if the plan or its verification depends on state the clean executor worktree will not contain.
- The selected host adapter can create the isolated worktree, dispatch one executor, identify it, and resume that same executor.

Run the adapter's `create-execution-worktree.sh` command. Record its `BASE_SHA`, `BRANCH`, and `WORKTREE`; these values define the review boundary.

### Executor prompt

Inline the full plan because it may be uncommitted or unavailable in the worktree. Prepend:

> Execute the plan below step by step in this isolated worktree. Touch only its
> in-scope paths. Run every verification and compare the result with the stated
> expectation. Stop immediately on a STOP condition; do not improvise around
> it. Commit according to the plan, but do not push or merge. Do not update the
> plan index; the reviewer owns it. Before reporting, verify every claim against
> an actual result from this session and disclose failures or skipped checks.

Require exactly:

```text
STATUS: COMPLETE | STOPPED
STEPS: each step — done/skipped and verification result
STOPPED BECAUSE: only when stopped
FILES CHANGED: complete list
NOTES: deviations, surprises, or judgment calls
```

Fresh worktrees lack ignored dependencies and build artifacts. Setup inside the executor worktree is allowed when the plan permits it; it is not permission to widen source scope.

### Review

Treat the report and diff as untrusted until checked.

1. Re-run every done criterion in the worktree and record failures or skips.
2. Enumerate all changes relative to `BASE_SHA`, including executor commits, staged/unstaged edits, and untracked files:

   ```text
   git -C <worktree> status --short
   git -C <worktree> diff --name-only <base-sha>
   git -C <worktree> ls-files --others --exclude-standard
   ```

3. Fail scope review for every changed or untracked source path outside the plan's in-scope list. Ignored dependency/build artifacts are not source changes, but inspect unexpected ones.
4. Read the complete `git -C <worktree> diff <base-sha>` and any untracked source files. Confirm every hunk serves a plan step and matches repository conventions.
5. Read new tests; passing commands do not compensate for vacuous assertions.

Because the diff is anchored to `BASE_SHA`, committed executor work cannot disappear from review.

### Verdict and revision

| Verdict | Condition | Action |
|---|---|---|
| APPROVE | Criteria pass, scope clean, implementation solves the stated problem | Return to the original checkout, mark DONE, and report diff summary, branch, worktree, and notes. |
| REVISE | Specific fixable gaps | Send actionable evidence to the same executor through the adapter's resume mechanism. Maximum two rounds. |
| BLOCK | STOP condition, unrecoverable scope violation, missing reliable host mechanism, or exhausted revisions | Return to the original checkout, mark BLOCKED with reason, and refine the plan if warranted. |

Judge disclosed minimal deviations on merit; reject undisclosed drift. Never merge, push, remove the worktree, or commit to the user's branch. Retain the executor branch/worktree for the user unless they explicitly request cleanup.

## `reconcile`

Read the index and plans, then:

- **DONE:** cheaply spot-check current criteria and mark the verification date.
- **BLOCKED:** investigate the recorded obstacle; refresh, replace, or reject the plan.
- **IN PROGRESS:** report stale execution and inspect a recorded worktree if available.
- **TODO:** require exact-base preflight. If `HEAD` changed, verify the finding and excerpts; re-stamp the full current SHA only when the plan remains valid. Reject work fixed independently.

Finish with what is verified, refreshed, rejected, blocked, and executable now.

## `--issues`

The flag explicitly authorizes issue creation.

1. Verify `gh auth status` and a matching GitHub remote; otherwise keep local plans and report the skip.
2. Check repository visibility. For public repositories, obtain explicit confirmation before publishing security, credential-location, or otherwise sensitive material.
3. Show proposed titles before creation.
4. Create one issue per selected plan; use existing labels only and never fail the run over labels.
5. Record each URL in the plan and index. Local plans remain the source of truth.

# DGM-MAT Bounded Worktree Execution Safety — 2026-11-04

Branch: `feat/bounded-worktree-execution-2026-11-04`
Base: `origin/main` at `15bb5704fefb297b55e5cab8e88334162a3419be`

## Findings repaired

The previous execution path had several unsafe or incomplete contracts:
- `WorktreeRuntime` did not implement `create_sandbox` / `cleanup_sandbox`, although `AutonomousExecutor` called them.
- It accepted arbitrary command strings or argument lists, with no fixed command catalogue, timeout or output cap.
- Cleanup could remove a worktree containing unreviewed or ignored local data.
- `SafePatchEngine.apply_patch` applied to the process working directory (the primary checkout by default), without an explicit target.
- `AutonomousExecutor` tried to apply a diff that already existed in its worktree, and its `finally` path could delete pending work.
- `ExecutionSupervisor.validate_plan` accepted every plan.
- `IsolatedRuntime` fell back to an ordinary temporary directory and exposed arbitrary `Popen` execution.

## Changes

### WorktreeRuntime
- Implements deterministic `create_sandbox` and `cleanup_sandbox` APIs with strict task/branch identifiers.
- Verifies repository root, Git worktree registration and exact target roots.
- Creates a linked worktree from a verified commit.
- Removes only worktrees with no tracked, untracked or ignored content; all other work is retained.
- Allows only pytest against one explicit Python file under the resolved `tests/` root.
- Rejects shell strings, `python -c`, pip and all unlisted command shapes.
- Uses `shell=False`, fixed working directory, timeout, streamed stdout/stderr caps and disables bytecode/pytest cache writes.
- Rejects test symlinks resolving outside the worktree's tests directory.

### Patch application boundary

Patch-application hardening is maintained separately in PR #182. This branch
does not change SafePatchEngine and does not apply generated patches.

### Supervisor / executor / compatibility adapter
- Validates task IDs, objectives, approval metadata and rejects caller-supplied command/shell/script fields.
- Validates risk score and impact values before persisting approval requests through the existing ApprovalManager/SafeActionQueue facade.
- Executor no longer re-applies a worktree diff to the primary checkout.
- Empty diffs and unreviewed changes are not reported as completed tasks.
- Cleanup is attempted only for a sandbox created by that invocation; dirty work remains available for recovery.
- `IsolatedRuntime` delegates to the bounded catalogue and has no temporary-directory fallback or arbitrary command execution.

## Verification

**78 focused tests passed** in the isolated bounded-execution validation run across:
- worktree creation, registration, cleanup and preservation of tracked, untracked and ignored data;
- path traversal, symlink escape, allowlisted pytest execution, output caps and timeout handling;
- supervisor metadata/risk validation and durable approval request delegation;
- executor truthful completion and cleanup ownership;
- sandbox compatibility adapter behavior;
- development task store, evidence envelope, QA coordinator, QA queue and caller audit;
- execution director truthfulness.

Additional checks:
- python -m compileall -q core/execution_fabric core/sandbox core/organization core/autonomy ? passed.
- git diff --check ? passed.

The optional specialization-registry test requiring the separate DGM-MAT-Agents package was not part of this focused run.

## Safety boundary / remaining work

- A Git worktree is repository isolation, not an OS sandbox. Tests execute repository code; network isolation and OS resource quotas are not provided. Timeout currently kills the direct child process, not an arbitrary descendant process tree.
- The code-generation/provider stage remains a placeholder. This PR does not make the DGM-MAT capable of independently authoring code.
- This branch is not connected to MissionEngine or SafeActionQueue and does not modify runtime queues, old actions, or services.
- No primary-branch changes, merges, commits, deployments or service restarts were performed by these tests.
- Independent QA and the existing human approval policy remain mandatory before primary-branch integration.

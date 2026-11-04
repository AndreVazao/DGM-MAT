# DGM-MAT Bounded Worktree Execution Safety — 2026-11-04

Branch: `feat/hardened-worktree-execution-2026-11-04`
Base: `origin/main` at `15bb5704fefb297b55e5cab8e88334162a3419be`

## Findings repaired

The previous execution path had several unsafe or incomplete contracts:
- `WorktreeRuntime` did not implement `create_sandbox` / `cleanup_sandbox`, although `AutonomousExecutor` called them.
- It accepted arbitrary command strings or argument lists, with no fixed command catalogue, timeout or output cap.
- Cleanup could remove a worktree containing unreviewed work.
- `SafePatchEngine.apply_patch` applied to the process working directory (the primary checkout by default), without an explicit target.
- `AutonomousExecutor` tried to apply a diff that already existed in its worktree, and its `finally` path could delete pending work.
- `ExecutionSupervisor.validate_plan` accepted every plan.
- `IsolatedRuntime` fell back to an ordinary temporary directory and exposed arbitrary `Popen` execution.

## Changes

### WorktreeRuntime
- Implements deterministic `create_sandbox` and `cleanup_sandbox` APIs with strict task/branch identifiers.
- Verifies repository root, Git worktree registration and exact target roots.
- Creates a linked worktree from a verified commit.
- Removes only clean worktrees; modified, staged and untracked content is retained.
- Allows only pytest against one explicit Python file under the resolved `tests/` root.
- Rejects shell strings, `python -c`, pip and all unlisted command shapes.
- Uses `shell=False`, fixed working directory, timeout, streamed stdout/stderr caps and disables bytecode/pytest cache writes.
- Rejects test symlinks resolving outside the worktree's tests directory.

### SafePatchEngine
- Requires an explicit registered linked worktree and rejects the primary repository.
- Validates patch size and file paths; rejects absolute paths and parent traversal.
- Checks patch applicability before applying, scoped to the selected worktree.
- Generates tracked staged/unstaged diffs, rejects untracked files rather than silently omitting them, and enforces a maximum patch size.
- Does not commit, merge, push or deploy.

### Supervisor / executor / compatibility adapter
- Validates task IDs, objectives, approval metadata and rejects caller-supplied command/shell/script fields.
- Validates risk score and impact values before persisting approval requests through the existing ApprovalManager/SafeActionQueue facade.
- Executor no longer re-applies a worktree diff to the primary checkout.
- Empty diffs and unreviewed changes are not reported as completed tasks.
- Cleanup is attempted only for a sandbox created by that invocation; dirty work remains available for recovery.
- `IsolatedRuntime` delegates to the bounded catalogue and has no temporary-directory fallback or arbitrary command execution.

## Verification

**67 focused tests passed** across:
- worktree creation, registration, cleanup and dirty-work preservation;
- path traversal, symlink escape, patch targeting and patch generation;
- command allowlisting, output caps and timeout behavior;
- supervisor metadata/risk validation and approval persistence;
- executor truthful completion and cleanup ownership;
- sandbox adapter behavior;
- development task store, evidence envelope, QA coordinator and caller audit.

Additional checks:
- `python -m compileall -q core/execution_fabric core/sandbox` — passed.
- `git diff --check` — passed.

One pre-existing test, `tests/execution_fabric/test_execution_fabric.py::test_specialization_registry`, remains outside this focused run because the sibling `DGM-MAT-Agents` package is not available in this checkout (`ModuleNotFoundError: dgm_mat_agents`). The state-machine test in the same file was included and passed.

## Safety boundary / remaining work

- A Git worktree is repository isolation, not an OS sandbox. Tests execute repository code; network isolation and OS resource quotas are not provided. Timeout currently kills the direct child process, not an arbitrary descendant process tree.
- The code-generation/provider stage remains a placeholder. This PR does not make the DGM-MAT capable of independently authoring code.
- This branch is not connected to MissionEngine or SafeActionQueue and does not modify runtime queues, old actions, or services.
- No primary-branch changes, merges, commits, deployments or service restarts were performed by these tests.
- Independent QA and the existing human approval policy remain mandatory before primary-branch integration.

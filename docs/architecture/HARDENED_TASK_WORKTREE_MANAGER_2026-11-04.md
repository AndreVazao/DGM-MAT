# Hardened Task Worktree Manager

Date: 2026-11-04
Branch: `feat/hardened-worktree-manager-2026-11-04`
Base: `origin/main` at `15bb5704fefb297b55e5cab8e88334162a3419be`

## Problem found

`ExecutionEngine.start_execution` called `WorktreeManager.create_worktree` with three arguments even though the manager accepts two. The manager also relied on the process current directory, accepted an unvalidated task ID as a filesystem path segment, did not create missing task branches, and could attempt to attach an existing branch already checked out elsewhere.

Cleanup removed a worktree without checking ignored files, which Git may otherwise delete during removal.

## Changes

- `WorktreeManager` now accepts an explicit repository root and worktree base path. The default repository root is derived from the installed source path, not the process current directory.
- All Git commands use an explicit `git -C <repo>` path, `shell=False`, bounded timeouts and checked exit codes.
- Task IDs are strict path-safe identifiers; branch names are validated by Git and protected branches/prefixes are rejected.
- New task branches are created from the primary repository's current HEAD.
- Existing branches are attached only when not checked out in another worktree.
- Reuse is idempotent only when the exact task path, branch, repository identity and clean state all match.
- Cleanup verifies exact worktree root, common Git directory, registered path and non-protected branch.
- Cleanup refuses tracked modifications, untracked files and ignored data. It never uses force and never deletes the task branch.
- `ExecutionEngine.start_execution` now calls the manager with the correct signature and exposes `cleanup_execution`, which inherits the safe cleanup rules.

## Validation

The test suite creates temporary Git repositories and linked worktrees and verifies:
- branch/worktree creation and primary checkout preservation;
- idempotent reuse of the same clean worktree;
- dirty worktree preservation;
- path traversal and invalid branch rejection;
- protected branch rejection;
- branch sharing refusal;
- cleanup refusal for dirty and ignored data;
- clean worktree cleanup without deleting the branch;
- the corrected ExecutionEngine contract.

Focused validation:
- 18 passed, 1 deselected.
- `compileall` passed.
- `git diff --check` passed.

The deselected specialization-registry test requires the separate `DGM-MAT-Agents` package, not mounted in this isolated worktree.

## Integration boundary

This manager is not yet connected to MissionEngine, SafeActionQueue or the provider. It supplies a reliable task-worktree primitive only. No agent code is executed, no patch is applied and no worktree is automatically created by the runtime.

The next step is to persist the worktree identity and lifecycle in the mission checkpoint, retain worktrees while approval is pending, and combine this manager with the isolated patch guard and fixed QA commands. A terminal mission or rejected task must not silently delete recoverable work.

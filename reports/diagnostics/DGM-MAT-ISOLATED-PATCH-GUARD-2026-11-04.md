# DGM-MAT Isolated Patch Guard — 2026-11-04

## Status

Implemented in an isolated worktree and locally validated. Not merged and not connected to the runtime.

## Critical issue fixed

The old `SafePatchEngine.apply_patch(patch)` invoked `git apply` without an explicit destination, so Git used the process current directory. Its own log message stated it was applying to the main repository. The risk scanner was only a heuristic and did not prevent writes to the primary checkout.

## New enforcement

- Explicit destination worktree and expected repository root are mandatory.
- Main checkout is rejected as a destination.
- Destination must be a linked worktree of the expected repository.
- Detached HEAD and protected branches are rejected.
- Destination must be clean before patch application.
- Diff must be non-empty, text-only and no larger than 512 KB.
- Critical destructive patterns are rejected.
- Git validates the diff first, then applies it with explicit `git -C` and no shell.
- Git's default unsafe-path protection remains enabled.
- The primary checkout is checked unchanged in tests.

## Test results

- 18 passed, 1 deselected.
- `compileall` passed.
- `git diff --check` passed.

The deselected specialization-registry test requires the separate DGM-MAT-Agents package, absent from this isolated worktree. No source changes were made to work around that missing optional repository.

## Not yet solved

- The existing AutonomousExecutor is not ready for integration: it calls missing WorktreeRuntime methods and uses the now-rejected one-argument patch method.
- There is no complete durable lifecycle tying mission -> worktree -> patch -> approval -> QA -> PR.
- This PR does not enable code-writing missions or background autonomy.

No DGM-MAT runtime, service, queue, primary checkout or other repository was modified.

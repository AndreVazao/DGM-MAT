# Isolated Patch Application Guard

Date: 2026-11-04
Branch: `feat/isolated-patch-apply-guard-2026-11-04`
Base: `origin/main` at `15bb5704fefb297b55e5cab8e88334162a3419be`

## Problem found

`core/execution_fabric/safe_patch_engine.py` previously applied a patch using `git apply` without a `cwd` or `git -C` target. It logged that it was applying to the main repository. The method accepted only a patch string, so the destination was implicitly whichever repository happened to be the process current directory.

The risk scanner is heuristic and cannot establish repository isolation.

## New boundary

`SafePatchEngine.apply_patch` now requires both:
- an explicit `worktree_path`;
- an explicit `expected_repo_root`.

Before applying, it verifies:
1. Both paths resolve to exact Git worktree roots.
2. The destination is not the expected primary checkout.
3. Both worktrees share the same Git common directory.
4. The destination is attached to a named, non-protected branch (main/master/develop/release/production/stable/trunk and release/production/stable prefixes are rejected).
5. The destination worktree is clean, including untracked files.
6. The diff is non-empty, textual and at most 512 KB.
7. The existing risk scanner does not identify a critical destructive pattern.
8. `git apply --check --whitespace=error` succeeds.

It then invokes `git -C {target} apply --whitespace=error`, without shell execution or unsafe-path flags, and confirms that changes are visible in the isolated worktree. It returns the branch, target path, changed paths and risk assessment.

The legacy one-argument API is intentionally fail-closed. It never infers a destination from the current working directory.

## Verification

The new test suite creates temporary Git repositories and linked worktrees and verifies:
- patch changes appear only in the isolated worktree;
- primary checkout remains byte-for-byte unchanged;
- legacy invocation is refused;
- primary destination is refused;
- foreign-repository worktrees are refused;
- dirty worktrees are refused;
- protected branches are refused;
- invalid diffs and destructive patterns are refused;
- path traversal is rejected by Git;
- oversized patches are refused.

Focused validation:
- 18 passed, 1 deselected.
- `compileall` passed.
- `git diff --check` passed.

The deselected test requires the separate `DGM-MAT-Agents` package, which is not mounted in this isolated worktree. An initial run confirmed that this unrelated dependency is missing; it did not fail because of the patch guard.

## Important integration boundary

This PR does not connect the patch engine to MissionEngine, SafeActionQueue or AutonomousExecutor.

A source audit found that the current `AutonomousExecutor` calls `WorktreeRuntime.create_sandbox` and `cleanup_sandbox`, methods not present on `WorktreeRuntime`; it also invokes the old one-argument patch API. The executor is therefore not a valid integration path yet. The new API deliberately rejects that legacy call instead of preserving the unsafe main-repository behavior.

The next integration step must first replace that incomplete lifecycle with a durable worktree record, a stable approval checkpoint, patch application to a separate clean worktree, fixed validation commands, and recovery that preserves any worktree awaiting approval. No runtime execution path is enabled by this PR.

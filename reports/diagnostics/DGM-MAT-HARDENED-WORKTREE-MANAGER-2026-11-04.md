# DGM-MAT Worktree Manager Hardening — 2026-11-04

## Result

Implemented a safer task worktree manager and repaired the broken ExecutionEngine call contract. The change is isolated, locally tested and not merged or activated.

## Findings

- ExecutionEngine called WorktreeManager.create_worktree with the wrong argument count.
- WorktreeManager relied on process current directory.
- Task IDs were used as path segments without validation.
- Missing branches were not created.
- Existing branches could be shared/attached without checking whether another worktree already held them.
- Cleanup could remove ignored files without first preserving them.

## Implemented

- Explicit repository root and configurable worktree base.
- Explicit Git paths, no shell, bounded timeouts and checked command results.
- Strict task ID and Git branch validation.
- Automatic branch creation from current HEAD.
- Refusal to share an already checked-out branch.
- Idempotent reuse only for the exact clean worktree/branch pair.
- Cleanup requires a registered non-protected worktree and refuses tracked, untracked or ignored data.
- No force removal and no branch deletion.
- ExecutionEngine now calls the correct method and exposes safe cleanup.

## Tests

- 18 passed, 1 deselected.
- `compileall` passed.
- `git diff --check` passed.

The deselected optional specialization test needs DGM-MAT-Agents, which is not mounted in this isolated worktree.

## Remaining work

This is not yet a full autonomous development lifecycle. MissionEngine, durable approval, worktree persistence, provider-generated diffs, independent QA, PR publication and interrupted-work recovery still need to be connected. The runtime remains unchanged and default-off.

# Governed GitHub self-sync

**Status:** integrated into DGM-MAT main (merge commit a1bc49d0704fbe59097ac52f4346d410c37bb335)
**Tracking:** PR #162 (merged)
**Scope:** DGM-MAT repository only

## Purpose

Bring the latest GitHub main commit onto the PC without replacing or mutating the authoritative local checkout. The operation uses one dedicated detached Git worktree.

## Fixed safety contract

- Remote is fixed to origin, and its URL must identify AndreVazao/DGM-MAT.
- Only refs/heads/main is fetched, into refs/remotes/origin/main.
- Fetch uses --no-tags and a fixed non-forced refspec; it does not prune remote-tracking references.
- The destination is fixed at C:\ProgramasGodMode\_worktrees\dgm-mat-github-main-sync.
- The authoritative checkout HEAD and complete porcelain status (including untracked files) are captured before and after.
- A new worktree is detached at the fetched SHA.
- An existing destination is never adopted or blindly overwritten. It must be a registered, clean, detached worktree. If its HEAD is an ancestor of the fetched SHA, the service advances only this dedicated worktree with a normal non-forced detached checkout; divergent/ahead histories are refused. Ignored local files are protected with --no-overwrite-ignore.
- Any mismatch, dirty destination, attached branch, divergent history, wrong remote, missing worktrees directory or failed Git command blocks the operation.
- No pull, merge, rebase, reset, clean, stash, force update or arbitrary shell input is used. A normal detached checkout is permitted only after merge-base proves fast-forward ancestry.

## Mission behavior

The intent repository_sync_worktree requires explicit operator approval for worktree creation or advancement. It is excluded from AUTO_RUN_READ_ONLY_INTENTS because it changes the dedicated worktree. MissionEngine dispatches the handler only after the SafeActionQueue approval transition. Results distinguish creation, advancement and already-current idempotent verification.

## CLI

From a DGM-MAT checkout:

    $env:DGM_MAT_REPOSITORY_ROOT = 'C:\ProgramasGodMode\DGM-MAT'
    python scripts/sync_github_main.py

The script writes a machine-readable report under reports/diagnostics. It does not print credentials.

## Verified execution evidence (2026-11-03)

### Initial materialization

- Fetched GitHub origin/main at 7b6e3e0ca3d2882d554642b220a25e3940e43edc.
- Created the dedicated detached worktree at that SHA.
- Independently verified matching remote/worktree SHA, clean status, detached HEAD and empty Git prefix.
- A second execution verified idempotence without recreating the worktree.

### Post-merge advancement

- PR #162 was integrated into main at a1bc49d0704fbe59097ac52f4346d410c37bb335.
- DGM-MAT CLI executed from the newly synchronized main worktree and advanced the existing dedicated worktree from 7b6e3e0ca3d2882d554642b220a25e3940e43edc to a1bc49d0704fbe59097ac52f4346d410c37bb335.
- Result: worktree_created=false, worktree_advanced=true, worktree_clean=true, worktree_detached=true; 19 Git commands.
- The CLI was then executed again from the synchronized main worktree. It reported worktree_created=false and worktree_advanced=false, with the same SHA and clean status; 16 Git commands.
- The synchronized main worktree was independently tested after the update: compileall passed and all 8 self-sync tests passed. Its Git status remained clean.
- The authoritative checkout stayed at 7e38d4033968f6a3c4c5113e6c3969f0c9e1652a with 35 dirty/untracked entries preserved. No checkout, reset, clean, stash or branch switch was performed on that checkout.

### Machine-readable evidence

- Initial creation: reports/diagnostics/DGM-MAT-GITHUB-SELF-SYNC-CREATION-2026-11-03.json
- Initial idempotence: reports/diagnostics/DGM-MAT-GITHUB-SELF-SYNC-IDEMPOTENCE-2026-11-03.json
- Post-merge advancement: reports/diagnostics/DGM-MAT-GITHUB-SELF-SYNC-ADVANCE-2026-11-03.json
- Post-merge idempotence: reports/diagnostics/DGM-MAT-GITHUB-SELF-SYNC-POST-MERGE-IDEMPOTENCE-2026-11-03.json

The local focused regression suite on the PR branch passed 63 tests (six existing deprecation/syntax warnings). The synchronized main worktree passed the dedicated 8-test self-sync suite after the real advancement.

## Runtime boundary

The long-running production runtime in the original authoritative checkout was not restarted or replaced. The new CLI/service path has been exercised against the real GitHub repository and local worktree. The new API mission intent still requires a controlled runtime restart from integrated main before claiming a live API mission end-to-end.

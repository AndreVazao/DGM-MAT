# Governed GitHub self-sync

**Status:** implemented on `feat/mission-governed-github-sync-2026-11-03`
**Tracking:** DGM-MAT Issue #162
**Scope:** DGM-MAT repository only

## Purpose

Bring the latest GitHub `main` commit onto the PC without replacing or mutating the authoritative local checkout. The operation uses one dedicated detached Git worktree.

## Fixed safety contract

- Remote is fixed to `origin`, and its URL must identify `AndreVazao/DGM-MAT`.
- Only `refs/heads/main` is fetched, into `refs/remotes/origin/main`.
- Fetch uses `--no-tags`; it does not prune remote-tracking references.
- The destination is fixed at `C:\ProgramasGodMode\_worktrees\dgm-mat-github-main-sync`.
- The authoritative checkout HEAD and complete porcelain status (including untracked files) are captured before and after.
- A new worktree is detached at the fetched SHA.
- An existing destination is never adopted or blindly overwritten. It must be a registered, clean, detached worktree. If its HEAD is an ancestor of the fetched SHA, the service advances only this dedicated worktree with a normal non-forced detached checkout; divergent/ahead histories are refused. Ignored local files are protected with --no-overwrite-ignore.
- Any mismatch, dirty destination, wrong remote, missing worktrees directory or failed Git command blocks the operation.
- No `pull`, merge, rebase, reset, clean, stash, force update or arbitrary shell input is used.

## Mission behavior

The intent `repository_sync_worktree` is supported but requires explicit operator approval. It is deliberately excluded from `AUTO_RUN_READ_ONLY_INTENTS` because creating a worktree changes the filesystem. The MissionEngine dispatches the registered handler only after the SafeActionQueue approval transition.

## CLI

From a DGM-MAT checkout:

```powershell
$env:DGM_MAT_REPOSITORY_ROOT = 'C:\ProgramasGodMode\DGM-MAT'
python scripts/sync_github_main.py
```

The script writes a machine-readable report under `reports/diagnostics`. It does not print credentials.

## Live execution evidence (2026-11-03)

- Fetched GitHub `origin/main`: `7b6e3e0ca3d2882d554642b220a25e3940e43edc`.
- Created detached worktree at `C:\ProgramasGodMode\_worktrees\dgm-mat-github-main-sync`.
- Independently checked that remote SHA and worktree HEAD match.
- Independently checked clean worktree status, detached HEAD and empty Git prefix.
- A second CLI execution passed idempotently: it verified the existing worktree without recreating it.
- Repeated syncs may advance the dedicated worktree only along a verified fast-forward ancestry path; dirty, attached, divergent or backward destinations fail closed. Normal checkout is used without force/reset/clean, with ignored-file overwrite disabled. Mission results distinguish creation, advancement and an already-current idempotent verification.
- Confirmed the authoritative checkout remained at `7e38d4033968f6a3c4c5113e6c3969f0c9e1652a`.
- Confirmed its 35 porcelain entries (including untracked installed files) remained present.
- Machine-readable evidence: `reports/diagnostics/DGM-MAT-GITHUB-SELF-SYNC-2026-11-03.json`.

The existing production runtime was separately exercised with a read-only `repository_status` mission (`mission_eb7dadf7`). The new sync handler is covered by unit tests and the explicit-approval MissionEngine test; the live runtime must load the integrated code before the new API mission intent can be exercised end-to-end.

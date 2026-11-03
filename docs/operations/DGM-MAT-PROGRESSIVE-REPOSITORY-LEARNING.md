# DGM-MAT progressive repository learning

**Status:** implemented as an opt-in runtime worker; first production scan starts when the updated runtime is promoted with `DGM_REPOSITORY_LEARNING_ENABLED=1`.

## Mission

Build a durable map of the local engineering portfolio so later DGM-MAT work can identify the correct repository, current branch, commit, working-tree state, technology markers and project purpose without repeatedly rediscovering unchanged repositories.

## Discovery roots

Default roots:
- `C:\ProgramasGodMode`
- `C:\DevopGodMode`
- `C:\AI`
- `C:\Projects`
- `C:\ProjectFlux`
- `C:\ProjectMind`

Additional roots can be supplied through `DGM_REPO_SCAN_ROOTS`, separated by semicolons. Discovery is recursive to a bounded depth (default 5), detects normal repositories and Git worktrees, and does not follow symlinks. Generated/vendor directories are pruned.

## What is learned

For each repository the worker stores:
- absolute repository path and containing scan root;
- current branch and short HEAD commit;
- tracked working-tree dirty state (untracked files are not enumerated);
- sanitized origin host/path, without embedded credentials;
- top-level technology/build manifest names;
- a short redacted README introduction;
- protected-mirror status, last-seen time and a fingerprint.

`DGM-MAT-FULL-MIRROR` is recorded as a protected metadata-only entry. Its README and project files are not read.

## Progressive, non-repeating behavior

- SQLite ledger: `storage/runtime/cognition/repository_learning/repository_learning.sqlite3`.
- Default batch size: 5 repositories.
- Every repository and cursor advance is committed atomically.
- If the process stops, the next start resumes from the saved cursor.
- If HEAD, branch, tracked dirty state, origin or top-level documentation/manifest timestamps are unchanged, the repository is marked unchanged and its README is not read again.
- After a complete pass, the next refresh defaults to 15 minutes; unchanged repositories are skipped.
- Errors are recorded and the cursor advances, so one inaccessible repository cannot trap the entire worker in an infinite retry.
- No Git checkout, reset, clean, stash, commit, push, file edit, build or project command is performed.

## API

- `GET /runtime/repository-learning` — progress plus a bounded repository metadata page.
- `POST /runtime/repository-learning/start` — operator-only start/resume.
- `POST /runtime/repository-learning/stop` — operator-only pause; the cursor and ledger remain intact.
- `GET /runtime/missions/page?limit=20&offset=0` — bounded durable mission summaries. This avoids the legacy unbounded mission-list response on a runtime with hundreds of checkpoints.

## Startup configuration

Set before runtime startup:
- `DGM_REPOSITORY_LEARNING_ENABLED=1`
- `DGM_REPOSITORY_LEARNING_BATCH_SIZE=5`
- `DGM_REPOSITORY_LEARNING_MAX_DEPTH=5`
- `DGM_REPOSITORY_LEARNING_REFRESH_SECONDS=900`

The worker is deliberately independent of the SafeActionQueue. It does not create hundreds of mission records or auto-approve repository mutations. It is a read-only learning/indexing process; later deep audits and code changes must be separate, evidence-backed tasks.

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

Additional roots can be supplied through `DGM_REPO_SCAN_ROOTS`, separated by semicolons. Discovery is recursive to a bounded depth (default 8), detects normal repositories and Git worktrees (including hidden worktree folders), and does not follow symlinks. Only known generated/vendor directories are pruned.

## Repository tree artifacts

For every non-protected repository, the worker writes a UTF-8 `.tree.txt` sidecar under `Vault/runtime/cognition/repository_learning/trees` by default, or the external directory configured with `DGM_REPOSITORY_TREE_DIR`. Production should use an external directory so generated trees do not dirty the DGM-MAT source checkout. The filename is based on the repository name plus a stable path hash, so same-named repositories do not overwrite one another.

- The tree contains paths only; it never reads file contents.
- With the recommended external `DGM_REPOSITORY_TREE_DIR`, tree generation does not dirty the DGM-MAT source checkout or any inventoried project.
- Unchanged repositories reuse their existing tree. A changed repository regenerates its tree.
- The tree is bounded to 4,000 entries and depth 12; reaching either limit is explicitly marked as truncated.
- Directory enumeration keeps only the remaining entry budget plus one candidate in memory, even when a repository contains a very large directory.
- Git-origin grouping requires a specific repository path (`host/owner/repository` or deeper); host-only and owner-only remotes remain ungrouped for semantic review.
- Git, virtual environments, build output, dependencies, runtime storage, secrets, credential files, private keys and symlinks are excluded.
- The protected full mirror receives no tree artifact.

## What is learned

For each repository the worker stores:
- absolute repository path and containing scan root;
- current branch and short HEAD commit;
- tracked working-tree dirty state (untracked files are not enumerated);
- sanitized origin host/path, without embedded credentials;
- top-level technology/build manifest names;
- a short redacted README introduction;
- protected-mirror status, last-seen time and a fingerprint;
- the `.tree.txt` artifact path, SHA-256, entry count, truncation flag and generation time;
- a provisional project-group suggestion based only on a shared Git origin or multiple repositories under the same non-root parent directory; ambiguous repositories remain marked for semantic review.

`DGM-MAT-FULL-MIRROR` is recorded as a protected metadata-only entry. Its README and project files are not read.

## Progressive, non-repeating behavior

- SQLite ledger: `storage/runtime/cognition/repository_learning/repository_learning.sqlite3`.
- Default batch size: 5 repositories.
- Every repository and cursor advance is committed atomically.
- If the process stops, the next start resumes from the saved cursor.
- If HEAD, branch, tracked dirty state, origin or top-level documentation/manifest timestamps are unchanged, the repository is marked unchanged before the README is opened; its previous summary and tree are reused.
- After a complete pass, the next refresh defaults to 15 minutes; unchanged repositories are skipped.
- Errors are recorded and the cursor advances, so one inaccessible repository cannot trap the entire worker in an infinite retry.
- No Git checkout, reset, clean, stash, commit, push, file edit, build or project command is performed.

## API

- `GET /runtime/repository-learning` — progress percentage, next repository path, scan roots, repository metadata and evidence-based project-group suggestions.
- `GET /runtime/repository-learning/tree?repo_path=...` — reads only the bounded tree artifact already indexed for that repository.
- `POST /runtime/repository-learning/start` — operator-only start/resume.
- `POST /runtime/repository-learning/stop` — operator-only pause; the cursor and ledger remain intact.
- `GET /runtime/missions/page?limit=20&offset=0` — bounded durable mission summaries. This avoids the legacy unbounded mission-list response on a runtime with hundreds of checkpoints.

## Startup configuration

Set before runtime startup:
- `DGM_REPOSITORY_LEARNING_ENABLED=1`
- `DGM_REPOSITORY_LEARNING_BATCH_SIZE=5`
- `DGM_REPOSITORY_LEARNING_MAX_DEPTH=8`
- `DGM_REPOSITORY_TREE_DIR=C:\\ProgramasGodMode\\DGM-MAT-Data\\repository-trees` (recommended external sidecar location)
- `DGM_REPOSITORY_LEARNING_REFRESH_SECONDS=900`
- `DGM_REPOSITORY_LEARNING_COMMAND_TIMEOUT=8` (bounded to 10 seconds; useful for slower repositories)

The worker is deliberately independent of the SafeActionQueue. It does not create hundreds of mission records or auto-approve repository mutations. It is a read-only learning/indexing process; later deep audits and code changes must be separate, evidence-backed tasks.

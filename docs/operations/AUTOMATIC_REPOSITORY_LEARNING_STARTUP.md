# Automatic repository learning at full-runtime startup

**Status:** implemented in PR `feat/repository-learning-autostart-2026-11-09`  
**Scope:** local metadata-only repository inventory; not conversation ingestion or autonomous coding.

## Startup behavior

The full DGM-MAT runtime now starts the existing `RepositoryLearningService` by default. The worker:

- scans only configured roots (`DGM_REPO_SCAN_ROOTS` plus the conservative built-in roots);
- processes bounded batches (default 5 repositories, configurable up to 25);
- persists its cursor and inventory in SQLite so a restart resumes the current cycle;
- records repository name, path, branch, HEAD, dirty state, sanitized origin, manifest stack and a redacted README summary;
- creates bounded path-only `*.tree.txt` artifacts outside the source repository;
- excludes common dependency/build folders and sensitive filenames;
- does not execute project code, modify Git state, edit source files, or read the protected `DGM-MAT-FULL-MIRROR` contents.

## Operator control

Default: enabled when the **full runtime** starts.

Set `DGM_REPOSITORY_LEARNING_ENABLED=0` to disable automatic startup. The existing authenticated/runtime API controls remain available:

- `GET /runtime/repository-learning` — status and inventory
- `GET /runtime/repository-learning/tree?repo_path=...` — read an indexed tree
- `POST /runtime/repository-learning/start` — start/resume
- `POST /runtime/repository-learning/stop` — pause without deleting the cursor

The worker is not a replacement for the GitHub portfolio comparison or branch recovery analyzer. It does not fetch, merge, push or delete branches.

## What this does not yet do

It does not import ChatGPT/Grok/Gemini/Zia conversations, extract scripts from provider sessions, create project context dossiers, or run coding agents. Those require the separate authenticated conversation-ingestion and project-context stages. A repository inventory is evidence about the checkout, not proof that its historical conversations have been recovered.

## Resource profile

The service is intentionally incremental and low-concurrency. On older machines, reduce `DGM_REPOSITORY_LEARNING_BATCH_SIZE` (minimum 1) and increase `DGM_REPOSITORY_LEARNING_REFRESH_SECONDS`. Keep the opt-out available for diagnosis.

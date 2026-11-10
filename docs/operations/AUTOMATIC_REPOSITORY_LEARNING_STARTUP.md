# Automatic repository learning at full-runtime startup

**Status:** implemented for standard profile; LOW_MEMORY startup guard included in this change.  
**Scope:** local metadata-only repository inventory; not conversation ingestion or autonomous coding.

## Startup behavior

The full DGM-MAT runtime starts the existing `RepositoryLearningService` by default on the standard profile. The worker:

- scans only configured roots (`DGM_REPO_SCAN_ROOTS` plus the conservative built-in roots);
- processes bounded batches (default 5 repositories, configurable up to 25);
- persists its cursor and inventory in SQLite so a restart resumes the current cycle;
- records repository name, path, branch, HEAD, dirty state, sanitized origin, manifest stack and a redacted README summary;
- creates bounded path-only `*.tree.txt` artifacts outside the source repository;
- excludes common dependency/build folders and sensitive filenames;
- does not execute project code, modify Git state, edit source files, or read the protected `DGM-MAT-FULL-MIRROR` contents.

## Operator control and resource profile

- Standard profile: automatic startup is enabled by default.
- LOW_MEMORY profile (less than 4 GB total RAM): automatic startup is disabled by default to preserve resources.
- Explicit opt-in: set `DGM_REPOSITORY_LEARNING_ENABLED=1` to enable the worker even on a LOW_MEMORY machine.
- Explicit opt-out: set `DGM_REPOSITORY_LEARNING_ENABLED=0` to disable it on every profile.
- The Windows backend service manager deliberately leaves `DGM_REPOSITORY_LEARNING_ENABLED` unset by default; it must not silently opt a LOW_MEMORY PC back in. An operator-provided value is preserved unchanged.

On older machines, use conservative settings such as `DGM_REPOSITORY_LEARNING_BATCH_SIZE=1` and `DGM_REPOSITORY_LEARNING_REFRESH_SECONDS=3600`. The existing authenticated/runtime API controls remain available:

- `GET /runtime/repository-learning` — status and inventory
- `GET /runtime/repository-learning/tree?repo_path=...` — read an indexed tree
- `POST /runtime/repository-learning/start` — start/resume
- `POST /runtime/repository-learning/stop` — pause without deleting the cursor

The worker is not a replacement for the GitHub portfolio comparison or branch recovery analyzer. It does not fetch, merge, push or delete branches.

## What this does not yet do

It does not import ChatGPT/Grok/Gemini/Claude/DeepSeek/Qwen conversations, extract scripts from provider sessions, create project context dossiers, or run coding agents. Those require the separate authenticated conversation-ingestion and project-context stages. A repository inventory is evidence about the checkout, not proof that its historical conversations have been recovered.


# Automatic free-only help — validation report

**Date:** 2026-11-03  
**Branch:** `feat/auto-help-hub-2026-11-03`  
**Base:** DGM-MAT main including progressive repository learning.

## Delivered

- Durable SQLite help-request queue and 24-hour goal-hash deduplication.
- Unsupported actionable mobile requests are retained in the thread and can enqueue a consult without creating an unsupported mission or queue action.
- Background worker is started only when `DGM_AUTONOMY_HELP_ENABLED=1`.
- Provider allowlist is restricted to Kilo and LLM7. Codex and Claude are not automatically called because their free capacity is not independently verified.
- Secret-like requests are blocked before persistence or external transmission.
- Only the current goal and a short capability-boundary explanation are sent; no source files, prior conversation history, credentials, cookies or tokens.
- Results are persisted as untrusted specialist collaborations and sent for independent review.
- Provider failures, 429/capacity limits and ambiguous restarts are recorded; there is no automatic retry or paid fallback.
- Operator-only start/stop controls and a local-client status endpoint are available.
- ChatGPT, Grok and Gemini are explicitly reported as not integrated Hub adapters.

## Combined validation

- Python compileall passed for all changed runtime, API, service and test modules.
- `git diff --check` passed.
- **101 tests passed** across:
  - repository-learning cursor, resume, unchanged-skip, hidden worktree discovery and progress percentage;
  - bounded mission pagination;
  - auto-help deduplication, secret blocking, free-provider allowlist, restart safety and no-retry behavior;
  - mobile mission routing;
  - DGM-HUB bridge/observer APIs;
  - API security classifications;
  - mission intent and read-only diagnostic handlers;
  - terminal mission-result guards;
  - mission-system and live-mission diagnostic integration.

## Live-execution boundary

All provider calls in tests were mocked. No live external AI provider was contacted and no paid credits were consumed during validation. The live provider readiness check and first real consult occur only after the updated DGM-MAT and DGM-HUB runtimes are promoted with the free-only flags.

# DGM-MAT — Incremental Conversation Memory Hardening Checkpoint
Date: 2026-10-10

## Scope and safety
Continues PR #71 on `feat/conversation-turn-semantics-v1`. Work remains in progress; do not merge prematurely or restart the live Core. No source history was modified remotely, no recovered script was executed, and no credentials were recorded.

## Repository and PR
- DGM-MAT local repository: `C:\\ProgramasGodMode\\DGM-MAT`.
- Feature branch: `feat/conversation-turn-semantics-v1`.
- Last synchronized DGM-MAT commit before this increment: `23b804281ae3d66f4fd3cca24944ff1c673a7b15`.
- PR #71 remains open: https://github.com/AndreVazao/DGM-MAT/pull/71.
- GitHub API returned no PR-triggered workflow runs and no combined status checks for the checked SHA. This is **unverified CI**, not a passing CI result.

## Implemented changes

### 1. Preserve accepted proposal provenance
In `core/conversation_intelligence/knowledge_store.py`, explicitly accepted/rejected proposals protect `source_message_id` and `decision_id` as well as decision state, statement and source conversation.
- Regression: `test_accepted_proposal_preserves_message_and_decision_provenance`.

### 2. Reuse unchanged completed export snapshots
In `core/conversation_intelligence/progress_store.py` and `pipeline.py`:
- Additive SQLite table `source_conversations` stores source fingerprint and ordered conversation membership.
- The pipeline checks a completed source and its fingerprint before parsing.
- If membership count and all cached snapshots are valid, it returns saved audit snapshots without reparsing the export or re-auditing conversations.
- Changed sources, missing/legacy membership and invalid snapshots fall back to the normal parser and processing path.
- Membership is written before the source is marked complete.
- The source bytes are still read for SHA-256 content detection; this deliberately avoids trusting file timestamps alone.

Regression:
- `test_unchanged_completed_source_reuses_cached_audits_without_parsing_export`.

### 3. Recover from missing/interrupted source membership
Added `test_missing_source_snapshot_index_falls_back_to_parser_and_repairs_ledger`. It removes the source membership index while leaving a previously completed source record, then verifies that the pipeline reparses, restores the index, returns the cached audit and leaves the source complete. This confirms that a missing index does not produce an empty cached result.

## Validation actually executed
- `python -m pytest -q tests\conversation_intelligence`: passed after the source-cache change (30 tests) and passed again after adding the interrupted-index recovery regression (31 tests).
- The broader selected suite had previously passed: `tests\conversation_intelligence tests\contracts tests\organization tests\autonomy tests\security tests\cockpit`, exit code 0.
- `git diff --check`: exit code 0 after the recovery regression.
- Earlier broad run emitted deprecation warnings for Starlette TestClient/httpx integration and FastAPI `on_event`; these remain technical debt.
- GitHub Actions for the latest commit remains unverified because the checked API response contains no runs/statuses.

## Live Core safety gate
- `GET http://127.0.0.1:8181/health` previously returned HTTP 200 with healthy status.
- Unauthenticated read-only requests to `/runtime/status`, `/runtime/missions`, and `/runtime/queue` returned HTTP 401. Active missions therefore could not be verified.
- No Core restart, mission mutation or network exposure change was made.

## Local/GitHub synchronization status
- DGM-MAT feature branch was synchronized to remote commit `23b8042` before this new recovery test was added.
- This checkpoint and regression test must be published to the feature branch and then the local feature branch must be fetched and compared with GitHub.
- AndreOS memory repository: the local branch reports three commits ahead of its cached `origin/main`. A direct `git fetch origin` failed because Windows Git Credential Manager could not persist credentials and Git could not prompt. The checkpoint file content had previously been compared against GitHub, but Git history/refs are not synchronized. Do not claim full Git synchronization until remote fetch/push succeeds or refs are reconciled safely.


## 4. Validate interrupted import recovery and changed sources

Added two additional regressions in `tests/conversation_intelligence/test_progress_store.py`:

- `test_interrupted_source_import_resumes_without_reauditing_completed_conversations`: simulates an audit failure on the second conversation, checks that the source is recorded as failed with one completed item, then retries and verifies the first item is reused, the failed item is retried, and the source/index finish complete.
- `test_changed_source_invalidates_source_cache_and_updates_conversation_snapshot`: changes source bytes, title and content; verifies the source-level fast path is bypassed, the conversation is audited again, the updated snapshot is returned and the new source fingerprint is stored.

Local focused test file: 15 tests passed after these additions. The broader selected suite is being rerun; its final exit code will be recorded after completion.

## Updated local/GitHub state

The two new tests have been appended to the feature branch. After publication, fetch and compare the exact remote head before considering the local branch synchronized. PR #71 remains open and unmerged; CI status remains unverified unless GitHub returns explicit checks.


## Next safe actions
1. Finish the selected regression suite and `git diff --check`.
2. Fetch the new remote head locally and verify a clean worktree and exact commit alignment.
3. Continue reviewing knowledge-store transition/provenance behavior and add focused regressions where a concrete gap is demonstrated.
4. Recheck PR workflows/status; keep PR #71 open until required gates are satisfied.
5. Keep the live Core untouched until active missions can be verified through an authorized read path or controlled maintenance is explicitly approved.

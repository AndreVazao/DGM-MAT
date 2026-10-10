# DGM-MAT — Incremental Conversation Memory Hardening Checkpoint
Date: 2026-10-10

## Scope and safety
Continues PR #71 on `feat/conversation-turn-semantics-v1`. Work remains in progress; do not merge prematurely or restart the live Core. No source history was modified remotely, no recovered script was executed, and no credentials were recorded.

## Repository and PR
- DGM-MAT local repository: `C:\\ProgramasGodMode\\DGM-MAT`.
- Feature branch: `feat/conversation-turn-semantics-v1`.
- Latest synchronized local/remote commit: `a6ddbade1f2ec915e99d1902aa9005922043a577`.
- PR #71 remains open: https://github.com/AndreVazao/DGM-MAT/pull/71.
- GitHub returned no PR workflow runs and no combined status checks for the latest checked commit. Remote CI is **unverified**, not passed.

## Implemented changes

### 1. Preserve accepted proposal provenance
In `core/conversation_intelligence/knowledge_store.py`, explicitly accepted/rejected proposals protect `source_message_id` and `decision_id` as well as decision state, statement and source conversation.
- Regression: `test_accepted_proposal_preserves_message_and_decision_provenance`.

### 2. Reuse unchanged completed export snapshots
In `progress_store.py` and `pipeline.py`:
- Additive SQLite table `source_conversations` stores source fingerprint and ordered conversation membership.
- A completed source with an unchanged SHA-256 fingerprint, matching membership count and valid complete snapshots returns cached audit snapshots without reparsing or re-auditing.
- Changed sources, missing/legacy membership and invalid snapshots fall back to normal parsing and processing.
- Membership is written before the source is marked complete.
- Source bytes are still read to calculate SHA-256; timestamps alone are not trusted.

### 3. Recover from missing index, interrupted imports and changed sources
Regression coverage verifies:
- `test_unchanged_completed_source_reuses_cached_audits_without_parsing_export`
- `test_missing_source_snapshot_index_falls_back_to_parser_and_repairs_ledger`
- `test_interrupted_source_import_resumes_without_reauditing_completed_conversations`
- `test_changed_source_invalidates_source_cache_and_updates_conversation_snapshot`

The interrupted-import test confirms that already completed items are reused, the failed item is retried, and the source index is rebuilt before completion.

### 4. Reject silent changes to reviewed provenance
Reviewed intents, user-confirmed decisions and reviewed relations now reject every non-identical rewrite, including changes to source message IDs, evidence or confidence. Exact repeats remain idempotent.
- Regression: `test_reviewed_knowledge_provenance_and_evidence_cannot_be_silently_rewritten` verifies rejected changes leave the original records intact.

## Validation actually executed
- Focused knowledge-store and progress-store tests: passed (26 test cases).
- Broader selected suite passed with exit code 0:
  `python -m pytest -q tests\conversation_intelligence tests\contracts tests\organization tests\autonomy tests\security tests\cockpit`.
- `git diff --check`: exit code 0.
- Warnings remain for Starlette TestClient/httpx integration and FastAPI `on_event` deprecation.

## Local/GitHub synchronization
- DGM-MAT: feature branch fetched from GitHub; blob hashes for the changed implementation, tests and checkpoint matched the remote tree; local branch reset to that exact remote commit after comparison. Worktree is clean at `a6ddbade1f2ec915e99d1902aa9005922043a577`.
- AndreOS memory: checkpoint file content hash matches GitHub main (`e7abcedfd9fa44b6323e668910a4a1e1faf7a7fa)). Git branch references/history are **not** synchronized: local branch still reports four commits ahead of cached `origin/main`, and `git fetch` fails because Windows Git Credential Manager cannot persist credentials or prompt. No reset, force-push or destructive history rewrite was attempted.

## Live Core safety gate
- Last known `GET http://127.0.0.1:8181/health` returned HTTP 200.
- Unauthenticated reads of `/runtime/status`, `/runtime/missions` and `/runtime/queue` returned HTTP 401, so active missions could not be verified.
- No Core restart, mission mutation or network exposure change was made.

## Next safe actions
1. Resolve AndreOS memory Git authentication safely before attempting full refs/history synchronization.
2. Continue focused state-transition and provenance tests only where a concrete gap is identified.
3. Keep PR #71 open until required remote checks/reviews are explicitly available.
4. Do not restart the live Core until active missions can be verified through an authorized read path or controlled maintenance is explicitly approved.

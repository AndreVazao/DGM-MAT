# DGM-MAT — Incremental Conversation Memory Hardening Checkpoint
Date: 2026-10-10

## Scope and safety
Continues PR #71 on `feat/conversation-turn-semantics-v1`. This is work in progress; do not merge prematurely or restart the live Core. No source history was modified remotely, no recovered script was executed, and no credentials were recorded.

## Repository state at start of this checkpoint
- Local repository: `C:\\ProgramasGodMode\\DGM-MAT`.
- Branch: `feat/conversation-turn-semantics-v1`.
- Pre-change HEAD: `b6968f06a8da6b8b1f1fa184e937b41be9dcd1f2`.
- The previous knowledge-store provenance hardening, regression test and checkpoint had been published to the feature branch via the GitHub integration.
- PR #71 remains open.
- GitHub returned no PR-triggered workflow runs and no combined status checks for the checked SHA. Absence of runs is not a passing CI result.

## Changes in this checkpoint

### 1. Preserve accepted proposal provenance
In `core/conversation_intelligence/knowledge_store.py`, `save_proposal` now rejects changes to `source_message_id` and `decision_id` after a proposal has an explicit accepted/rejected state, in addition to protecting its state, statement and source conversation. Exact repeats remain idempotent.

Regression test:
- `test_accepted_proposal_preserves_message_and_decision_provenance`

### 2. Avoid reparsing an unchanged completed export
Previously, `ingest_file` called the parser on every invocation before consulting the per-conversation ledger. The per-conversation audit was skipped when fingerprints matched, but the export was still parsed repeatedly.

Added to `ConversationProgressStore`:
- Additive SQLite table `source_conversations`, storing ordered source membership and the source fingerprint.
- `set_source_conversations(...)` to persist the source-to-conversation index after successful processing.
- `list_source_conversations(...)` to restore the original membership order.

Added to `ConversationIntelligencePipeline.ingest_file`:
- Hash the current source bytes and inspect the durable source ledger before parsing.
- If the source fingerprint is unchanged, source status is complete, membership count matches, and every linked conversation has a valid completed snapshot, return the cached audits without calling the export parser.
- If the source changed, the membership index is missing/legacy, or any snapshot is incomplete, fall back to the normal parser and processing path.
- Write source membership before marking the source complete, so an interrupted update cannot advertise a completed source with a stale membership index.

The source bytes are still read to calculate a content fingerprint. This avoids reparsing/revisiting the conversation structure, while retaining content-based change detection instead of trusting file timestamps alone.

Regression test:
- `test_unchanged_completed_source_reuses_cached_audits_without_parsing_export`

Files changed in this increment:
- `core/conversation_intelligence/pipeline.py`
- `core/conversation_intelligence/progress_store.py`
- `tests/conversation_intelligence/test_progress_store.py`

## Tests actually executed

Focused conversation-intelligence suite:
```powershell
python -m pytest -q tests\conversation_intelligence
```
Result: passed, exit code 0, after both regression tests were added.

Broader regression command:
```powershell
python -m pytest -q tests\conversation_intelligence tests\contracts tests\organization tests\autonomy tests\security tests\cockpit
```
Result: passed, exit code 0. Pytest emitted deprecation warnings for Starlette TestClient/httpx integration and FastAPI `on_event` startup handlers. These warnings are not test failures and remain technical debt.

`git diff --check`: exit code 0.

## Live Core observation
- `GET http://127.0.0.1:8181/health` returned HTTP 200 with `{"status":"healthy","service":"dgm-mat"}`.
- Unauthenticated read-only requests to `/runtime/status`, `/runtime/missions`, and `/runtime/queue` returned HTTP 401. The active mission count could not be verified through these unauthenticated routes.
- The Core was not restarted, missions were not created/modified, and network exposure was not changed.
- HTTP 401 proves only that these unauthenticated requests were denied; it does not establish that every production authentication path is correct.

## Still unverified
- GitHub CI for the latest source-cache change.
- Runtime integration of this pipeline/store in the live Core.
- Complete provider history recovery; this remains an import pipeline, not proof of complete history coverage.
- Full repository-wide tests outside the six selected suites.
- The source fingerprint currently requires reading the source bytes; a future metadata-based shortcut would need a safe fallback to content hashing to avoid missing same-size or timestamp-preserving edits.

## Next safe actions
1. Publish this source-level cache improvement and its tests to `feat/conversation-turn-semantics-v1` only.
2. Verify the new remote head and actual PR checks; keep PR #71 open and unmerged until review and compatibility checks are complete.
3. Continue validating failure recovery and source membership consistency.
4. Keep the live Core untouched until active missions can be verified through an authorized read path or controlled maintenance is explicitly approved.

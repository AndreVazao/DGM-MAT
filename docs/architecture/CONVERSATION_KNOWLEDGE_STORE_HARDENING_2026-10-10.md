# DGM-MAT — Conversation Knowledge Store Hardening Checkpoint
Date: 2026-10-10
Status: implemented locally; focused tests passed; pending commit/push and GitHub CI confirmation.

## Scope
Continues PR #71 on `feat/conversation-turn-semantics-v1`. This checkpoint does not authorize merging the PR or restarting the live Core.

## Verified repository state
- Local repository: `C:\\ProgramasGodMode\\DGM-MAT`.
- Branch: `feat/conversation-turn-semantics-v1`.
- Pre-change HEAD: `5afe452ae78f26e3f0db43c7a6bc3085e9dc4f42`.
- Remote branch tip matched that SHA before this checkpoint's local changes.
- Working tree was clean before the targeted change.
- PR #71 is open.
- No PR-triggered workflow runs or combined status checks were returned for the pre-change SHA by the available GitHub integration. This is not evidence that CI passed.

## Code review finding and correction
In `core/conversation_intelligence/knowledge_store.py`, `save_proposal` already protected an explicitly accepted/rejected AI proposal from changes to its acceptance state, statement, and source conversation. It did not protect `source_message_id` and `decision_id`, so the provenance link could be silently rewritten after the user had made a decision.

The guard now also rejects changes to `source_message_id` and `decision_id` for an explicitly accepted/rejected proposal. An exact repeat remains idempotent. Added regression test:
- `test_accepted_proposal_preserves_message_and_decision_provenance`

Files changed:
- `core/conversation_intelligence/knowledge_store.py`
- `tests/conversation_intelligence/test_knowledge_store.py`

## Tests actually executed
Command:
```powershell
python -m pytest -q tests\conversation_intelligence\test_knowledge_store.py tests\conversation_intelligence\test_progress_store.py tests\conversation_intelligence\test_evidence_aware_models.py tests\conversation_intelligence\test_pipeline.py
```
Result: **29 passed**, exit code 0.
`git diff --check`: exit code 0. Git emitted a line-ending normalization warning for the edited test file; no whitespace errors were reported.

A previous run of `test_progress_store.py` plus `test_knowledge_store.py` also passed (20 tests before the added regression case).

## Live Core safety observation
- `GET http://127.0.0.1:8181/health` returned HTTP 200 and `{"status":"healthy","service":"dgm-mat"}`.
- Read-only requests to `/runtime/status`, `/runtime/missions`, and `/runtime/queue` returned HTTP 401 without a session. Therefore the current mission count could not be verified through these routes in this session.
- The Core was not restarted, no missions were created or modified, and no network exposure was changed.
- HTTP 401 demonstrates route access control for these unauthenticated requests; it does not by itself prove every production authentication path is correct.

## Not yet verified
- The local change has not yet been committed or pushed at the time this document was authored.
- GitHub CI after the new commit has not run/been confirmed.
- The full repository test suite has not been run; only `tests/conversation_intelligence/` was exercised.
- Runtime integration of this conversation-intelligence pipeline and knowledge store is not proven by these unit tests.
- No merge was performed.

## Next safe actions
1. Review the diff and commit the focused provenance guard + regression test + checkpoint.
2. Push only `feat/conversation-turn-semantics-v1`, then inspect PR #71 and its actual checks.
3. If CI is unavailable, record that explicitly and continue with targeted local tests.
4. Review pipeline source-file-level short-circuiting as a separate issue: current code avoids repeating per-conversation audits when fingerprints match, but still parses the source export on each ingest call to discover conversation records.
5. Keep the live Core untouched until its active missions can be verified through an authorized read path or controlled maintenance is explicitly approved.

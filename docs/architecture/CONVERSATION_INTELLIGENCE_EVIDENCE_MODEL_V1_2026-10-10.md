# Conversation intelligence — evidence-aware model v1

Date: 2026-10-10
Status: feature branch `feat/conversation-turn-semantics-v1`; validation not confirmed in this environment; do not merge yet.

## Purpose and operating rule

The archive is institutional memory, not an endless task queue. Process new conversations incrementally. Do not re-audit an unchanged, successfully processed conversation. Revisit old material only when the fingerprint changes, processing was incomplete/failed, relevant new evidence appears, or the user explicitly requests a review. A review task must not force rereading the whole conversation when its imported evidence is already available.

The system must separate:
1. actual user instructions and later changes;
2. assistant proposals;
3. decisions explicitly confirmed by the user;
4. facts verified against repository, tests or runtime.

## Evidence-aware ingestion

- `ConversationMessage` retains message ID, normalized role, content, sequence, timestamp, source path and source metadata.
- JSON ingestion preserves explicit message arrays and the common OpenAI-style `mapping` shape. Unknown roles stay `unknown`; no speaker attribution is guessed.
- Typed models separate `UserIntent`, `AIProposal`, `UserDecision`, `ConversationRelation`, `ImportCoverage` and `ArtifactProvenance`.
- Intent/decision defaults remain unverified. AI proposals are not user decisions.
- Coverage validation rejects impossible counts and a false `complete` label.
- Extracted code artifacts carry conversation/provider/URL/path/fingerprint provenance.

## Incremental progress ledger

`core/conversation_intelligence/progress_store.py` uses SQLite/WAL to persist conversation fingerprints/status and source coverage/checkpoints. Database creation is opt-in through an explicit path.

`core/conversation_intelligence/pipeline.py`:
- skips unchanged conversations only when a reusable audit snapshot exists;
- rebuilds legacy counter-only ledger entries once, instead of treating them as complete knowledge;
- stores reusable audit snapshots including derived findings, project suggestion, artifacts/code and provenance, without storing the full transcript in the snapshot;
- returns cached audits to callers and supports archive-wide `load_saved_audits()`, `summarize()` and `consolidate()`;
- records source failure if an audit raises, retaining a checkpoint/count for completed items.

The source ledger and audit snapshot are derived processing state. Full raw history needs its own private archive and access/retention policy.

## Temporal knowledge persistence

`core/conversation_intelligence/knowledge_store.py` adds a SQLite/WAL current projection and append-only event history for intents, AI proposals, decisions and conversation relations. Each event may carry evidence references such as conversation ID and message ID. Identical evidence events are idempotent. A confirmed/accepted item cannot be silently downgraded; an explicit transition is required and the previous state remains in history.

This is a persistence primitive, not an automated semantic extractor or human-review task queue. Relation candidates still require evidence and review; no relation graph is inferred automatically by this store. It currently does not implement a separate review-task lifecycle.

## Important limitations

- No authenticated provider history has been imported by this code.
- No login, CAPTCHA/MFA bypass, rate-limit bypass, external rename/group operation, automatic script execution, network exposure or live Core restart is performed.
- Lexical project suggestions are suggestions, not verified project facts.
- HTML/text sources without reliable message structure do not get invented speaker roles.
- Local data-store primitives are not yet connected to the office cockpit or authenticated provider session manager.
- Feature branch commits and test files do not prove tests pass. No successful current CI run has been verified. Run the focused tests and broader regression suite in a controlled checkout before changing this status.

## Test coverage authored in this branch

- `tests/conversation_intelligence/test_evidence_aware_models.py`: message roles/order, unknown role preservation, mapping extraction, unverified defaults and coverage invariants.
- `tests/conversation_intelligence/test_progress_store.py`: idempotent reuse, changed-content reprocessing, source checkpoints, cache round-trip, archive-wide summaries/consolidation and legacy snapshot rebuild.
- `tests/conversation_intelligence/test_knowledge_store.py`: separate intent/proposal types, confirmed decision transitions, idempotent evidence and persistence across reopening.

## Gate before merge

1. Run the focused suite and full relevant regression suite; record exact command and exit code.
2. Inspect PR diff and workflow results.
3. Test snapshot serialization for representative imported formats and legacy rows.
4. Confirm database location/ACLs and ensure raw transcripts/secrets never enter Git.
5. Keep the PR draft until these checks pass. Do not merge based on successful file commits alone.


## Validation checkpoint — 2026-10-10 (local Windows checkout)

- Updated the local feature branch to remote commit `dc8c2e3b79a699a78f743942066909d235d8e3c0`.
- `python -m pytest tests/conversation_intelligence -q`: exit code 0; focused tests passed (25 collected/executed by the progress output).
- `python -m pytest tests/conversation_intelligence tests/contracts tests/organization tests/autonomy tests/security tests/cockpit -q`: exit code 0; combined regression suite passed. Pytest output displayed progress through 100%; the remote terminal omitted the final numeric summary line.
- `python -m compileall -q core\conversation_intelligence`: exit code 0.
- `git diff --check`: exit code 0; working tree clean after syncing the feature branch.
- Existing deprecation warnings appeared from Starlette/httpx TestClient integration and FastAPI `on_event`; no test failures were reported.
- The checked commit had no PR-triggered GitHub Actions workflow runs returned by the available lookup. CI status is therefore **not verified**.

This is meaningful local validation, not production validation. The current data layer still lacks provider-history authentication/import, UI review tasks, automatic evidence mining, and end-to-end office/delegation integration. Keep the PR unmerged until those boundaries and compatibility are reviewed.

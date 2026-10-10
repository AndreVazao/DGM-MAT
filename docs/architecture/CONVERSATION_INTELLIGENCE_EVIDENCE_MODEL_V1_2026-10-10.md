# Conversation intelligence — evidence-aware model v1

Date: 2026-10-10
Status: implementation on branch `feat/conversation-turn-semantics-v1`; not yet merged and not yet verified by a local test run.

## What changed

- Added explicit `ConversationMessage` records with message ID, role, text, order, timestamp, source path and source metadata.
- JSON ingestion preserves explicit `messages` arrays and the common OpenAI-style `mapping` shape. Unknown roles stay `unknown`; the importer does not guess the speaker.
- Added structured records for `UserIntent`, `AIProposal`, `UserDecision`, `ConversationRelation`, `ImportCoverage` and `ArtifactProvenance`.
- New intent/decision records default to `unverified`; only explicit reviewed/confirmed fields can indicate user validation.
- Import coverage validates counts and rejects a `complete` label when discovered and imported counts differ.
- Extracted code artifacts now carry conversation-level provenance: provider, URL, source path and code fingerprint.

## Boundaries that remain

This is a compatibility-preserving data-model and ingestion step, not the complete recovery system. It does **not** yet:
- import authenticated histories from provider web apps;
- infer and automatically confirm intent, proposals or decisions;
- persist the intent/decision timeline or conversation-relation graph to a database;
- connect the ledger to authenticated provider sessions or execute real browser imports;
- rename, move or regroup conversations in external AI services;
- prove that all historical messages have been loaded.

Existing aggregate `ConversationRecord.content` remains available for existing pipeline callers. HTML/text imports still have no reliable per-message speaker structure and therefore do not invent messages.

## Tests added

`tests/conversation_intelligence/test_evidence_aware_models.py` covers distinct ordered user/assistant turns, unknown role preservation, OpenAI-style mapping extraction, unverified defaults and import-coverage validation.

**Verification state:** tests are committed to this feature branch but have not been executed in this environment. Do not interpret branch presence or GitHub commit success as a passing test run.


## Incremental progress ledger — added after v1 review

The feature branch now includes `core/conversation_intelligence/progress_store.py`, a SQLite/WAL ledger, and optional pipeline integration through `ConversationIntelligencePipeline(progress_store_path=...)`.

- No database is created unless a local progress-store path is explicitly supplied.
- Each conversation is fingerprinted from its current normalized content and message turns.
- A matching conversation with status `complete` is skipped on later runs.
- Changed content or an incomplete/failed status makes that conversation eligible for processing again.
- Source-file progress records status, counts, fingerprint and checkpoint; invalid count combinations and false `complete` states are rejected.
- The ledger stores reusable derived audit snapshots (artifact code, findings, project classification and provenance) so downstream delegations can reuse prior results without reopening the transcript. It deliberately omits the full raw conversation body/messages from the snapshot.
- `ingest_file()` returns cached audit results for unchanged conversations, so summaries and consolidation remain useful instead of returning an empty delta. `load_saved_audits()`, `summarize()` and `consolidate()` can use the durable ledger without rereading the original export.
- `record_source()` marks a source `failed` if an audit throws, preserving the last completed checkpoint/count.
- Database is local at the caller-selected path; do not place it in a public repository or unprotected shared folder.

Additional tests cover no-repeat behavior, changed content, persistence across reopening the database, blocked login checkpoints and coverage invariants.

**Verification state (2026-10-10):** the focused `tests/conversation_intelligence` suite passed locally (17 tests). The broader regression run across `tests/conversation_intelligence`, `tests/contracts`, `tests/organization`, `tests/autonomy`, `tests/security` and `tests/cockpit` also completed with exit code 0. The broader run exposed an existing clock-injection bug in `HumanInterventionQueue.create_request`; this branch fixes the initial read to use the supplied creation timestamp, and the regression suite now passes. GitHub returned no PR-triggered workflow runs for the latest checked commit, so local tests are confirmed but CI remains absent. Keep the PR in draft until review/compatibility checks are complete.


## Durable knowledge and review ledger — implementation in progress

Added `core/conversation_intelligence/knowledge_store.py`, a separate SQLite/WAL store for evidence-linked user intents, AI proposals, user decisions, conversation relations and explicit review tasks.

- AI proposals remain distinct from user decisions; an AI proposal is never automatically treated as accepted.
- New intents and decisions remain `unverified` by default. A reviewed intent or user-confirmed decision cannot be silently rewritten by a later unreviewed record.
- Relations carry evidence, confidence and a user-review flag; self-relations and invalid confidence are rejected.
- Review tasks have their own open/resolved/cancelled lifecycle. Resolving a review task does not force re-importing or rereading the source conversation.
- The store persists statements and evidence references, not full raw conversation transcripts.
- This is a persistence foundation, not an automatic intent-mining engine, a UI workflow, or a claim that external provider histories have already been imported.

**Verification update (2026-10-10):** the focused `tests/conversation_intelligence` suite passed after the knowledge store was added. The broader regression run across `tests/conversation_intelligence`, `tests/contracts`, `tests/organization`, `tests/autonomy`, `tests/security` and `tests/cockpit` also completed with exit code 0 after the knowledge-store addition. GitHub returned no PR-triggered workflow runs for the latest checked head; local tests are confirmed but CI remains absent.

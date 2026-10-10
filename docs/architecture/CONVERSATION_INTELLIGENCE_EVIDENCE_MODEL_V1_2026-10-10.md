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
- persist relations or intent history to a database;
- provide resumable durable import checkpoints;
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
- Conversation summaries stored in the ledger contain counts/fingerprints rather than a duplicate of full conversation text.
- Database is local at the caller-selected path; do not place it in a public repository or unprotected shared folder.

Additional tests cover no-repeat behavior, changed content, persistence across reopening the database, blocked login checkpoints and coverage invariants.

**Verification remains pending:** these tests have not yet been executed in a real local/CI test run. The implementation remains on the draft feature branch until checks are available and regressions are addressed.

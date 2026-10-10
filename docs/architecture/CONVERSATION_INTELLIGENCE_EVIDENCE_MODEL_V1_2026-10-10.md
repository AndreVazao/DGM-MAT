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

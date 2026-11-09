# DGM-MAT — AI Conversation Archive and Project Context Assembly

## Purpose

Prevent the loss of project decisions, user requests, AI responses, code proposals, and implementation history across ChatGPT, Grok, Gemini, Claude, DGM-HUB, and DGM-MAT-Mobile.

The system must preserve original evidence first, then derive project-specific context summaries. It must never treat an AI proposal as a user-approved decision without explicit evidence.

## Verified baseline (6 November 2026)

The existing local archive run `20261104T090138Z` contains:
- Four DGM-HUB JSONL sources, including the main runtime, backup, and two worktrees.
- One DGM-MAT-Mobile JSON source.
- 177 raw Hub records reduced to 73 unique events.
- 24 Hub conversations and 73 Hub messages.
- 10 mobile threads and 22 mobile messages.
- 34 normalized conversations processed by the conversation intelligence pipeline.
- No ChatGPT, Grok, or Gemini account session was accessed in that run.

The Chrome profile directory `Default` exists. Chrome 156 was installed, but no Chrome process was running during inspection. The current governed browser session is ephemeral and is not an authenticated-profile connector.

The existing provider classes for ChatGPT, Claude, Gemini, and Grok contain placeholder chat responses; they are not conversation-history collectors. The legacy `ConversationIngestionEngine` has an incomplete Claude parser and no Grok/Gemini ingestion path. Do not mistake these stubs for working provider integrations.

## Implemented in this workstream

### Transcript persistence

`ConversationIntelligencePipeline` now persists the conversation's original text and normalized messages in its progress snapshot:
- User and assistant messages remain separate.
- Message IDs, roles, sequence, timestamps, source path, and metadata are retained.
- Cached snapshots created before message persistence are invalidated and reprocessed when the original source is ingested again.
- `build_delegation_context()` remains bounded by default; `include_messages=True` explicitly includes full messages when a downstream agent needs the transcript.

### Chrome extension

Location: `extensions/dgm-mat-conversation-archive`

The unpacked Manifest V3 extension:
- Inventories ChatGPT, Grok, Gemini, and Claude conversation URLs found in Chrome history.
- Captures the currently open conversation using provider-specific DOM selectors.
- Saves JSON files under `%USERPROFILE%\Downloads\DGM-MAT-Conversation-Archive`.
- Does not read cookies, passwords, tokens, localStorage, sessionStorage, or authentication databases.
- Does not send data to external services.
- Marks history inventory as partial and every DOM capture as a partial snapshot until provider-specific scrolling/pagination is verified; unrecognized roles are never invented.

The extension must be installed in the existing Chrome profile by loading the unpacked folder at `chrome://extensions`. The user must review and grant the Chrome history permission.

### Local importer

- `ChromeConversationArchiveImporter` validates the supported JSON schemas.
- Original downloads are copied, never moved or deleted.
- SHA-256 is computed and verified on the archived copy.
- Imports are idempotent for identical files.
- Raw source files are retained under `Vault/providers/chrome-imports`.
- Progress and knowledge snapshots are stored under `Vault/runtime/cognition/conversation_intelligence`.
- Script: `scripts/import_chrome_conversation_archive.py`.
- Operator-only API: `POST /recovery/chrome/import`.



## GitHub repository reference preservation — 9 November 2026

Every conversation archived through the Vault catalogue is scanned for canonical GitHub repository URLs. The scanner:
- accepts only HTTPS links whose host is exactly `github.com` (or `www.github.com`);
- reduces repository subpaths such as `/tree/main`, `/blob/`, `/issues/` and `/pull/` to the canonical `https://github.com/owner/repository`;
- stores the repository URL, provider, conversation ID/title, message ID and source conversation URL, without copying message bodies into the reference index;
- deduplicates repeated links while retaining distinct source occurrences;
- marks new references `pending_verification` rather than assuming that a URL-shaped string is a real repository.

Operator API:
- `GET /recovery/github-references` — paginated inventory and provenance.
- `POST /recovery/github-references/verify?limit=10` — verifies a bounded batch against the public GitHub REST repository endpoint. It sends no credentials and does not access private GitHub data.

Verification states:
- `verified_public`: GitHub returned the matching repository identity and public metadata.
- `not_found_or_private`: GitHub returned 404; this deliberately does not claim that a private/inaccessible repository does not exist.
- `rate_limited` / `unavailable`: retry can happen later; no blind tight retry loop.

ChatGPT JSON/ZIP exports and browser-visible captures are wired into this index. Chrome archive JSON imports also flow through the same Vault catalogue. Raw transcripts remain in the private local archive; the GitHub reference registry stores only URLs and provenance.

## Required next implementation stages

1. Install and run the extension in the existing Chrome profile; obtain real provider URL counts.
2. Validate DOM selectors on one real conversation per provider and record extraction completeness.
3. Add provider-side history traversal, including pagination/scrolling, without assuming Chrome history is complete.
4. Capture every conversation in bounded batches with stable IDs, URL, title, provider, timestamps, message roles, and content.
5. Checkpoint each conversation in the Recovery Ledger; resume after interruption without duplicate writes.
6. Preserve raw captures and hashes before indexing.
7. Generate project-specific context packages from all conversations, not only the latest thread.
8. Each context package must include:
   - User requests and constraints, with source conversation/message references.
   - AI answers and proposals, separated by provider.
   - User-confirmed decisions and their evidence.
   - Rejected or superseded proposals.
   - Code artifacts and their source conversations.
   - Open questions, unfinished work, and current next actions.
   - Conflicts between conversations, marked for review rather than silently resolved.
9. Maintain rolling summaries by project and provider, with token/size thresholds and a full source index.
10. Add completeness metrics: discovered, captured, verified, partial, blocked-login, rate-limited, and failed.

## Safety and integrity rules

- Read-only against provider accounts: no deleting, editing, sending, or reacting to conversations.
- Do not bypass MFA, CAPTCHAs, account restrictions, or rate limits.
- Do not read or export cookies, passwords, or authentication databases.
- Never claim an inventory is complete when it only covers browser history.
- Never discard the raw source after summarization.
- Preserve exact user wording where it defines a requirement or decision.
- Do not infer user approval from an AI response.
- Keep provider capture, raw archival, indexing, and project-summary generation as separately checkpointed stages.

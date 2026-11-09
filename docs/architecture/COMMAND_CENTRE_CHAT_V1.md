# DGM-MAT Command-Centre Chat — Requirements and Delivery Plan

**Status:** requirements approved for implementation planning; no UI/provider integration is claimed by this document.  
**Owner:** operator (André)  
**Tracking issue:** [#313](https://github.com/AndreVazao/DGM-MAT/issues/313)  
**Related work:** #208, #237, #310

## 1. Purpose

The primary DGM-MAT chat is the operator's command centre. It must support durable conversations, recovery of prior work, and controlled consultation of external AI providers using the exact context of the active mission.

The chat is not merely a transient input box. It is the operator-facing entry point into the durable conversation catalogue, mission/task records, project knowledge and governed provider workflows.

## 2. Operator experience

The main chat must expose three persistent actions:

- **Pesquisar histórico** — search prior DGM-MAT conversations, imported provider conversations and mission records.
- **Nova conversa** — create an independent durable thread, optionally linked to a project.
- **Pedir ajuda a uma IA** — prepare a mission-aware consultation for one or more configured providers.

The interface must visibly distinguish the active conversation from the active mission. Starting a new conversation must not clear, overwrite or silently inherit the previous conversation.

### 2.1 Search history

Search filters should include full-text query, conversation title and project, provider/agent, date range, mission/task ID, state and capture completeness.

Search results should display title, provider, project, timestamps, mission association, archive/Vault reference and completeness status. Opening a result should restore its conversation context and permit continuation where supported.

Only indexed/archived content may be returned. The UI must distinguish:

- **complete** — completeness positively established by the source adapter;
- **partial** — known truncation or incomplete capture;
- **metadata-only** — title/URL/metadata exists but transcript content is absent;
- **unavailable** — source has not been captured or cannot currently be read;
- **unknown** — completeness has not been established.

Never label a provider's history as searchable merely because URLs or browser-history metadata were inventoried.

### 2.2 New conversation

A new thread must have a durable ID, creation/update timestamps, title, optional project association and provenance. It may start blank or from a selected project dossier.

Rules:
1. No previous conversation is mutated or deleted.
2. No unrelated transcript is silently copied into the new thread.
3. Project dossier context is an explicit, visible starting context, not a hidden transcript merge.
4. Rename/archive operations preserve the underlying records and mission references.
5. Conversation identity and mission identity remain separate; a conversation may reference multiple missions and a mission may be discussed in more than one conversation.

### 2.3 Ask another AI

The operator may request help in natural language, for example:

> Pergunta ao ChatGPT como resolver isto.

When a mission is active, the DGM-MAT should resolve “isto” against that mission's problem statement and evidence, not ask the operator to manually copy logs or code.

Supported provider choices in the operator's configured roster:
- ChatGPT
- Grok
- Gemini
- Claude
- DeepSeek
- Qwen

Local execution agents must be presented separately:
- Codex Free
- Claude Code Free

They are not interchangeable with conversational providers. Their CLI availability, authentication, FCC compatibility, exact model identity, free quota and execution capability must be verified independently before any invocation is enabled.

#### Context package

Build a bounded, deterministic and reviewable package containing only what is relevant:
- operator's original request and current goal;
- active mission ID, status and current blocking question;
- project/repository, branch and immutable base SHA where relevant;
- selected file excerpts and paths;
- exact errors, test results and CI evidence;
- attempted solutions and their outcomes;
- constraints and safety requirements;
- links to source records and provenance.

Do not include unrelated conversations, secrets, credentials, tokens, cookies, private keys or excluded paths. Redact sensitive values before rendering the preview.

#### Explicit send gate

Before sending, show the exact prompt and included context. The operator can edit the prompt, remove context items, select provider(s), and confirm or cancel. No provider request is sent before explicit confirmation.

Provider transport must be an explicitly supported integration. For browser providers, use the authorized visible UI workflow and stop on login, MFA, CAPTCHA, rate-limit, challenge or unexpected UI state. Do not reverse-engineer hidden endpoints or extract credentials.

#### Response handling

Persist the consultation with provider, verified model identity (or unknown), mission/thread IDs, prompt/context digest, timestamps, transport status, response and source provenance.

External AI responses are **proposals**, not operator decisions. They must not automatically modify files, approve tasks, merge PRs or deploy. The operator may accept/reject individual recommendations, with the decision and its source recorded separately.

## 3. Existing foundations and integration boundaries

Reuse existing components rather than creating parallel stores:
- durable conversation/thread APIs and message persistence;
- mission/task records and task receipts;
- Vault and conversation catalogue;
- RecoveryLedger;
- conversation-intelligence pipeline and project context dossiers;
- governed browser/provider sessions.

Related tracked work:
- **#208** — authenticated visible-UI capture for provider conversations. Capture must preserve provenance and completeness; no credential extraction or hidden APIs.
- **#237** — persistent Vault catalogue, project grouping, deduplication and repository intelligence.
- **#310** — governed headless local-agent execution and authenticated conversation capture.

Before implementation, inspect the existing cockpit chat, task-centre frontend, API contracts and storage models. Extend them coherently; do not introduce a second chat database or a second provider abstraction without proving the existing one is unsuitable.

## 4. Suggested delivery sequence

### Phase A — conversation navigation and history
1. Audit existing conversation/thread APIs, schemas, indexes and frontend routing.
2. Add paginated, bounded, deterministic search over records that are actually present in the Vault/catalogue.
3. Add provenance/completeness fields to result presentation.
4. Add conversation open/resume and active-thread indication.
5. Add independent new conversation creation and project association.
6. Add restart/persistence and isolation tests.

### Phase B — mission-aware context assembly
1. Define a versioned context-package schema.
2. Resolve the active mission and relevant project/repository evidence.
3. Apply path allowlists, size limits, redaction and deterministic ordering.
4. Show a preview with included/excluded items and source references.
5. Test reproducibility, truncation, redaction and prompt-size limits.

### Phase C — governed provider consultation
1. Implement a provider capability/transport registry based on verified integrations.
2. Distinguish conversational providers from local coding CLIs.
3. Add explicit operator confirmation before every external send.
4. Implement one provider at a time, starting with a demonstrably supported transport.
5. Persist requests and responses with digests, status and provenance.
6. Add proposal/decision separation and follow-up turns within the same mission context.
7. Verify real end-to-end behavior for each provider independently before marking it available.

### Phase D — operational hardening
- foreground operator messages preempt background recovery/research;
- background work resumes from durable checkpoints;
- all search/list APIs paginate and enforce bounded result sizes;
- provider failures and unsupported transports are explicit;
- no silent paid fallback;
- logs and GitHub reports contain no private transcript bodies or secrets.

## 5. Acceptance tests

### Search and navigation
- Search finds matching indexed user and assistant messages with stable ordering.
- Pagination has no duplicate or skipped records across pages.
- Metadata-only and partial captures are labelled correctly.
- Search never returns content that has not been captured/indexed.
- Opening an old conversation restores the correct thread without changing its messages.

### New conversations
- New conversation receives a unique durable ID.
- Creating it leaves all previous messages and mission links unchanged.
- Project association is explicit and survives restart.
- Blank conversation does not inherit unrelated transcript content.

### AI consultation
- Context package is deterministic for the same source snapshot and options.
- Prompt preview exactly matches the payload that would be sent.
- No request leaves the system before operator confirmation.
- Excluded paths and secrets do not appear in the prompt or logs.
- Provider login/challenge/rate-limit/failure states stop safely.
- Unsupported provider transport is shown as unavailable; no paid fallback occurs.
- Response provenance is durable and the response is classified as an external proposal.
- No automatic code changes, approvals, merges or deployments occur.

### Regression and delivery
- API, persistence, frontend and end-to-end tests pass.
- Mission E2E Regression Gate and Windows executable build pass.
- Changes ship in small reviewable PRs.
- No local PC/Desktop Commander operation is required during development; reserve it for the consolidated final installation and one intelligent verification pass.

## 6. Current implementation status

This document and issue #313 define the required behavior and delivery sequence. They do **not** claim that searchable history, the new-conversation control, or provider consultation is already implemented.

Provider history capture remains subject to the separate capture work and per-provider completeness evidence. A provider may only be shown as available for consultation after a real supported end-to-end send/response test succeeds.


## 7. Baseline audit — 2026-11-09

Repository inspection identified the actual desktop chat entry point and several similarly named components that must not be confused:

- `cockpit/minimal_chat_window.py` instantiates `CommandConsoleWidget` as the central desktop chat.
- `cockpit/widgets/command_console.py` is currently a mission command console: it submits one directive to the runtime, polls the resulting mission and renders the response. Its `history` is an in-memory Python list only; no durable conversation/thread ID, history search, thread switcher or new-conversation operation is present in this widget.
- `cockpit/workspace/chat_widget.py` is a separate generic widget with a message signal and display buffer. The inspected minimal window does not instantiate it; it is not evidence that the production chat already has conversation persistence.
- `core/api/conversation_archive_api.py` currently exposes Telescope archive status/import routes only. The inspected router does not expose a searchable conversation/message catalogue or create/open/resume chat-thread endpoints.
- `ConversationProgressStore` persists provider/source ingestion progress and can list processing records. It is not, by itself, the operator chat's thread/message store or a full-text search API.
- `ConversationKnowledgeStore` persists evidence-linked intents, proposals, decisions and relations. It should remain a knowledge/evidence layer, not be repurposed as raw chat transcript storage.

### Consequence for Phase A

Do not add buttons that only manipulate the current widget's RAM buffer. First identify the durable mission/task APIs and the canonical message/archive sources, then implement a single persistent conversation index/search service over those sources. New operator threads need their own durable model or a proven existing thread model; do not infer one from ingestion progress records.

### Immediate implementation order

1. Trace the runtime's existing mission list/detail APIs and identify whether any canonical user-chat thread model already exists outside the inspected archive router.
2. Define the thread/conversation persistence contract and migration strategy only after that audit.
3. Add a read-only paginated search endpoint backed by indexed transcript records, returning provenance and completeness.
4. Add thread creation/open/resume APIs and tests for isolation and restart persistence.
5. Wire the three controls into `CommandConsoleWidget` (the actual desktop entry point), with asynchronous requests and visible active-thread/active-mission identity.
6. Only then begin provider consultation/context packaging.

This audit is a source-code inspection, not a live-PC/runtime test. No claim is made that any of the requested UI features is available yet.

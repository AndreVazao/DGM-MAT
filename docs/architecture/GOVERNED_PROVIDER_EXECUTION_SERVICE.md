# Governed Provider Execution Service
<!-- Path: C:\ProgramasGodMode\DGM-MAT\docs\architecture\GOVERNED_PROVIDER_EXECUTION_SERVICE.md -->

Status: AUTHENTICATED API AND HUMAN APPROVAL FLOW IMPLEMENTED; PROVIDER REGISTRATION REMAINS SAFE-OFF.
Date: 2026-10-09

## Scope

core/provider_sync/governed_provider_service.py provides one bounded chat call. The authenticated HTTP boundary is core/api/provider_execution_api.py. It does not expose tool use, browser actions, file writes, or shell execution.

## HTTP contract

- POST /provider-execution/requests: API-token authenticated. Validates a bounded message envelope and creates a durable approval record. It does not call a provider.
- GET /provider-execution/approvals: operator-token authenticated. Lists pending provider requests, including the exact messages the operator must review.
- POST /provider-execution/approvals/{approval_task_id}/decision: operator-token authenticated. Records approve/reject decisions durably. A decision does not execute a provider.
- POST /provider-execution/execute: API-token authenticated. Takes only an approval task ID and executes the exact message envelope stored in the approved durable record. The client cannot replace messages at execution time.

## Authentication and activation

The endpoints fail closed with HTTP 503 unless both environment variables are set and different:

- DGM_PROVIDER_API_TOKEN: secret bearer token for request creation and execution.
- DGM_PROVIDER_OPERATOR_TOKEN: separate secret bearer token for approval queue access and decisions.
- DGM_PROVIDER_OPERATOR_ID: optional operator label recorded in audit entries; defaults to authenticated-operator.

Tokens must be supplied as Authorization: Bearer <token>. Never commit tokens or put them in source files, logs, URLs, or request bodies. These credentials are application-level bearer secrets, not per-user identity management; use separate, privately held tokens and rotate them if exposed.

## Approval and audit safety

1. Request IDs and message shape are bounded; extra fields are rejected.
2. The durable approval stores provider ID, request ID, exact messages, and a SHA-256 fingerprint of the canonical request envelope.
3. The operator can review the exact stored messages before approving.
4. Execution reuses the stored envelope; the service rechecks the fingerprint and claims approval atomically for one execution.
5. Provider approval records remain is_approved=False, so the generic action consumer cannot interpret them as executable actions.
6. A non-sensitive outcome event records success/failure code and elapsed time. Provider response text is not written to the audit trail.
7. Replays are rejected. Failed preflight before claim leaves the approved request unconsumed; a failure after claim consumes it and is audited.
8. Provider response output is bounded and common credential patterns are redacted.

## Bounds

- Maximum 40 messages; each must contain exactly role and content.
- Provider IDs max 128 characters; request IDs max 256 characters.
- Maximum 12,000 characters per message and 30,000 total input characters.
- Maximum 50,000 characters in a response.
- Default timeout 30 seconds; maximum configurable timeout 60 seconds.
- Process-local sliding-window limit: 10 requests per provider per minute. This is not a distributed quota.

## Security limits and activation gates

- The route is authenticated, but the rest of the legacy API is not globally authenticated by this change.
- The service does not activate or register providers. Provider registration remains safe-off.
- Unit tests use fake adapters; they do not prove a production provider is ready.
- The approval storage and claim behavior have SQLite integration coverage. Production database behavior still needs environment-specific validation.
- Rate limiting is process-local and resets on restart.
- Adapter cancellation after timeout is adapter-dependent.
- Tool/browser/execute/write remain unsupported and must stay denied until separate capabilities, policies, handlers, and tests exist.
- Before remote use, ensure the API is exposed only on a trusted network and bearer secrets are managed privately.

## Tests

tests/provider_sync/test_governed_provider_service.py, tests/provider_sync/test_durable_provider_approval_store.py, and tests/integration/test_provider_execution_api.py cover bounded execution, durable single-use approval, authentication separation, exact-envelope review, approval decision flow, replay denial, and tamper rejection.

# Governed Provider Execution Service
<!-- Path: C:\\ProgramasGodMode\\DGM-MAT\\docs\\architecture\\GOVERNED_PROVIDER_EXECUTION_SERVICE.md -->

Status: LIMITED CHAT EXECUTION IMPLEMENTED; NOT EXPOSED BY HTTP API; PROVIDER REGISTRATION REMAINS SAFE-OFF.
Date: 2026-10-09

## Scope

`core/provider_sync/governed_provider_service.py` is the first bounded execution service. It supports one provider chat call only. It does not expose an HTTP route, execute tools, browse, write files, or run shell commands.

## Execution contract

1. Validate request/provider IDs and bounded message shape/content.
2. If a durable approval task ID is supplied, retrieve its approval record and require status `APPROVED`, non-empty operator, decision timestamp, and a SHA-256 fingerprint matching the exact provider ID, request ID, and canonical message envelope. Unscoped or mismatched approvals fail closed.
3. Apply `ProviderRequestPolicy`: explicit registration, accepted provider availability, approval gate, rate reservation.
4. Resolve the registered provider and call its async `chat` method once, under `asyncio.wait_for`.
5. Do not retry. Sanitize exceptions to stable error codes. Reject non-string and oversized responses, and redact common bearer/API-key patterns from returned text.

## Bounds

- Maximum 40 messages; each message must contain exactly `role` and `content` (no tool-call or adapter-option fields).
- Provider IDs are limited to 128 characters; request IDs to 256 characters.
- Maximum 12,000 characters per message and 30,000 total input characters.
- Maximum 50,000 characters in a response.
- Default timeout 30 seconds; configurable maximum 60 seconds.

## Security limits and activation gates

- The service is not wired to public API/orchestrator routes. This avoids creating a network execution surface before authentication, authorization, quotas, audit policy, and operator approval UX are reviewed.
- Provider registration remains safe-off. Unit tests with fake adapters do not prove a production provider is ready.
- `DurableProviderApprovalStore` uses a conditional database update to claim an approved task once. The approval record moves to `RUNNING` with `is_approved=False`, keeping it out of the generic action consumer. SQLite integration tests verify that a claim succeeds once, subsequent claims fail, and a mismatched fingerprint does not consume the approval. The configured production database still requires environment-specific validation before high-impact use.
- Rate limits remain in-memory and process-local.
- Tool/browser/execute/write are not supported by this service and must remain denied until dedicated handlers and tests exist.
- No retry is attempted. Adapter cancellation after timeout is adapter-dependent.

## Tests

`tests/provider_sync/test_governed_provider_service.py` covers approved/denied execution, exactly-once invocation per request, unavailable and unregistered providers, malformed input, approval store errors, timeouts, response bounds, and exception sanitization.

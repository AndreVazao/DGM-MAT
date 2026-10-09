# DGM-MAT Governed Provider Execution Service — 2026-10-09

## Implemented locally — validation passed; publication pending

- Added `core/provider_sync/governed_provider_service.py`: bounded asynchronous chat-only execution, message/input bounds, timeout, no retries, generic exception codes, response type/size checks, and common credential-pattern redaction.
- Added `core/provider_sync/durable_provider_approval_store.py`: durable provider approval request helper and conditional database update to claim an approval once.
- Approval is bound by SHA-256 to the exact provider ID, request ID and canonical messages. An unrelated approval or changed request is rejected before adapter invocation.
- Added `tests/provider_sync/test_governed_provider_service.py` with fake-provider checks for successful one-call execution, no calls on denial, approval binding and reuse prevention, unavailable/unregistered providers, malformed/oversized input, timeout, oversized/non-string output, and sanitized exceptions.
- Added `tests/provider_sync/test_durable_provider_approval_store.py` with SQLite integration coverage for single-use claims and fingerprint mismatch.
- Added `docs/architecture/GOVERNED_PROVIDER_EXECUTION_SERVICE.md`.

## Safety boundaries

- Not connected to runtime HTTP endpoints, cockpit controls, or autonomous orchestration.
- Provider registration remains safe-off; no credentials were retrieved and no live adapter was activated.
- Only chat is supported. Tool/browser/execute/write operations are not exposed by this service.
- Rate limiting remains in-memory and process-local.
- SQLite integration tests cover single-use claims and mismatched fingerprints; configured production database behavior still needs environment-specific validation before high-impact use.
- Timeout does not guarantee remote provider-side cancellation; no retry is performed to avoid duplicate calls.
- Focused service and SQLite approval-store tests passed (exit code 0). Full pytest suite passed after final code changes (exit code 0). `git diff --check` and `py_compile` passed. Commit/push and repository synchronization remain pending.

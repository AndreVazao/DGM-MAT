# DGM-MAT Provider API + Human Approval Integration
<!-- Path: C:\ProgramasGodMode\DGM-MAT\reports\DGM-MAT_PROVIDER_API_APPROVAL_INTEGRATION_2026-10-09.md -->

Date: 2026-10-09
Status: IMPLEMENTED LOCALLY; VALIDATION IN PROGRESS; PROVIDERS REMAIN SAFE-OFF.

## Implemented

- Added core/api/provider_execution_api.py with four authenticated routes:
  - POST /provider-execution/requests — creates a durable approval request only.
  - GET /provider-execution/approvals — operator-only pending queue with exact message envelope for review.
  - POST /provider-execution/approvals/{approval_task_id}/decision — operator-only approve/reject.
  - POST /provider-execution/execute — executes the stored, approved envelope only.
- Included the router in core/api/api_server.py.
- Extended DurableProviderApprovalStore to persist provider ID, request ID, exact bounded messages, and the request fingerprint, and to record a non-sensitive execution outcome in the durable audit trail.
- The approval is consumed atomically by the existing claim method. The generic queue consumer cannot execute provider approval records because their is_approved flag remains false.
- API and operator bearer tokens must be distinct. If either is missing or both match, provider API routes fail closed with HTTP 503. Invalid/missing credentials return HTTP 401.
- The operator review endpoint returns the exact stored messages. Execution accepts only the approval task ID, so the caller cannot substitute a different message after approval.
- Provider output is returned to the caller after existing size checks and redaction; output text is not persisted in the durable audit trail.

## Environment configuration

Required secrets, configured outside source control:
- DGM_PROVIDER_API_TOKEN
- DGM_PROVIDER_OPERATOR_TOKEN

Optional audit label:
- DGM_PROVIDER_OPERATOR_ID (default authenticated-operator)

Do not commit tokens or add them to URLs, request bodies, logs, or source files. The operator token is a shared bearer secret, not an individual identity system.

## Validation performed so far

- py_compile succeeded for the changed API, store, and test modules.
- Focused provider service, durable approval store, and API integration tests passed (30 tests; exit code 0), including review-envelope persistence and durable execution-outcome audit checks.
- git diff --check passed.
- Existing deprecation warnings come from the installed Starlette TestClient/httpx integration and the existing API startup event; no Pydantic model warnings remain.
- Full repository suite passed: python -m pytest -q --disable-warnings (exit code 0). Pytest emitted progress dots without a numeric test summary.
- Production-database smoke tests were intentionally not run against the active runtime database; approval-store behavior is covered by isolated SQLite tests.
- Commits/pushes remain pending.

## Boundaries / known risks

- No real provider was registered, called, or enabled.
- The route uses the existing provider registry and fails closed if no provider is explicitly registered/available.
- The API server's existing non-provider routes were not globally secured by this change.
- The rate limiter is process-local and allows 10 requests/provider/minute per process.
- Production database semantics need validation before any high-impact use.
- API auth uses two application-level bearer secrets; secure private distribution and rotation remain operational responsibilities.
- C:\ProgramasGodMode\DGM-MAT-FULL-MIRROR was not accessed.

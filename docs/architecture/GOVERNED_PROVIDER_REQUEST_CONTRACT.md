# Governed Provider Request Contract
<!-- Path: C:\\ProgramasGodMode\\DGM-MAT\\docs\\architecture\\GOVERNED_PROVIDER_REQUEST_CONTRACT.md -->

Status: DESIGN / PREFLIGHT ONLY — NOT CONNECTED TO A LIVE REQUEST PATH
Date: 2026-10-09

## Purpose

Define the minimum fail-closed contract before any provider adapter can be activated by DGM-MAT. The policy layer makes a decision only; it does not send network requests, invoke tools, read secrets, or execute code.

## Required request envelope

- `provider_id`: exact ID of a provider explicitly registered by trusted runtime code.
- `request_id`: caller-generated non-empty correlation ID for logs and audit.
- `operation`: one of `chat`, `completion`, `tool`, `browser`, `execute`, or `write`. Unknown operations are denied.
- `approval_required`: trusted service classification for additional side-effecting/high-impact operations. The policy also imposes a built-in approval floor on `tool`, `browser`, `execute`, and `write`, even if a caller omits the flag.
- `approved`: approval result obtained from the durable approval mechanism, never inferred from a UI click, default, or caller-supplied free text. The preflight module cannot itself prove the provenance of this boolean; only the trusted service may supply it.

## Preflight order

1. Validate identifiers and allowlisted operation.
2. If approval is required, require an explicit approved state before proceeding.
3. Resolve an explicitly registered provider. Disk discovery is never registration.
4. Require a successful, accepted availability observation. Unknown, stale, cooldown, and exceptions deny.
5. Apply provider-specific rate control. Errors and limit exhaustion deny.
6. Return a structured decision and correlation identifiers. This module does not execute the operation.

Rate budget is consumed only after request shape, approval, registration, and availability pass. The current rate controller is an in-memory process-local limiter; it is not distributed, persistent, or proven effective until a service call site is wired and tested.

## Security invariants

- No credentials are retrieved during preflight. Secret access belongs to the concrete adapter/service at execution time and must be scoped to the registered provider and operation.
- No provider code is auto-imported from disk.
- No operation with side effects may execute without a durable, explicit approval decision.
- Unknown operation, registry exception, health exception, rate-control exception, and missing evidence all fail closed.
- The policy decision is not proof of successful provider execution, billing/quota status, or remote health beyond the accepted observation.
- Logs must include request ID, provider ID, decision code, and timestamps, but never tokens, prompt secrets, or credential values.

## Current limitations / gates before activation

- This preflight policy is deliberately not wired to API, orchestrator, or adapter call sites.
- The future public service layer must classify additional risky operations and obtain the approved state from the durable approval store; callers must not be allowed to self-label risky operations as read-only.
- The in-memory rate controller now uses a lock, monotonic time, positive-integer limit validation, provider-ID validation, and regression tests. It remains process-local, non-persistent, and not effective until a governed service call site is wired.
- A provider execution interface must enforce timeouts, bounded retries, response-size limits, cancellation, and redaction.
- Integration tests must prove that denied requests never call an adapter and approved requests call it exactly once.
- Only after those gates pass can provider registration move from safe-off to a controlled opt-in.

## Implementation and test

- Policy module: `core/provider_sync/provider_request_policy.py`
- Unit tests: `tests/provider_sync/test_provider_request_policy.py` and `tests/provider_sync/test_provider_rate_control.py`
- Test command: `python -m pytest tests/provider_sync/test_provider_request_policy.py tests/provider_sync/test_provider_rate_control.py tests/provider_sync/test_provider_contract.py -q`

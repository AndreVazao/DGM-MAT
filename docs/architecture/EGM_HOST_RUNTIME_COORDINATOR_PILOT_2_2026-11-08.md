# EGM host-runtime coordinator — pilot 2

- Date: 2026-11-08
- Branch: feat/egm-runtime-review-coordinator-2026-11-08
- Base: PR #287 head `58f77409f3af697a4091e6d512d87a7d06e0dac2`
- Scope: host-attested review session contract, coordinator and durable task receipt

## Implementation

- `core/organization/design_review_coordinator.py` defines the host adapter protocol, runtime isolation attestation and coordinator.
- The coordinator requires an existing task in RUNNING state, assigned to `agent:design-review-coordinator`, with metadata `task_kind=independent_design_review`.
- The brief must match the existing task and mission IDs.
- All reviewer sessions are created before any reviewer is invoked.
- Each session receives only its own ReviewerPacket. No reviewer output is fed into another session.
- Every session must supply a typed attestation issued by the host runtime, with a distinct context ID, fresh session, no prior history, no cross-reviewer sharing, tools/write access disabled and credentials excluded.
- The coordinator stores reviewer results and attestations via the existing `OrganizationTaskManager.complete_with_result` path. No second database or queue is introduced.
- Task manager exposes `durable_persistence_enabled`; the coordinator refuses to start when SQLite-backed task persistence is not configured.

## Failure behaviour

- Wrong task state/owner/kind or mismatched task/mission IDs are blocked before sessions are created.
- Shared context IDs, reused session objects, invalid attestations and invalid findings fail closed.
- Failed reviews leave the task RUNNING and do not create a success receipt.
- The coordinator does not approve changes, execute tools, mutate repositories or enable any production flags.

## Important runtime limitation

This PR supplies a typed adapter contract and coordinator, not a concrete ChatGPT/Claude/Gemini/browser provider adapter. A provider integration must implement `create_fresh_session` using an actually new conversation context and must truthfully attest the isolation properties. The dataclass is a trust contract for host-owned code, not cryptographic proof against a malicious adapter. Never accept the attestation from model-generated content.

## Tests

`tests/organization/test_design_review_coordinator.py` covers successful independent fake sessions with task-linked SQLite receipt, non-durable blocking, shared-context rejection, unsafe attestation rejection, task binding, task kind and task state.

CI execution is required before considering this pilot validated.

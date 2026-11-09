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


## Browser adapter investigation — 2026-11-08

Inspection of the free-tier browser consultation implementation on PR #283's recovery branch found an incompatibility with independent EGM review:

- The current extension polls already-open provider tabs and requires a recognized existing `source_id`.
- `sendMessageThroughVisibleUi` rejects a page without an existing conversation identifier.
- `executeBrowserOperatorTask` verifies that the current page still matches the existing conversation before sending.
- Therefore the current browser consultation path can send a reviewed prompt into an existing conversation, but it does not create or attest a fresh conversation. It must not be wired directly into this coordinator as an independent reviewer.
- The browser queue also requires an operator approval for each consultation and completes asynchronously. The current coordinator contract is synchronous. A real adapter therefore needs a durable start/resume workflow rather than blocking a worker while waiting for manual approval.
- The next implementation must add a distinct fresh-review browser protocol: blank/new conversation preflight, no visible prior messages, one isolated provider tab per reviewer, manual approval, newly created conversation ID after submission, durable completion polling, and host-verifiable evidence. Existing conversation-recovery and browser-operator routes remain unchanged.
- Until this exists and passes live Windows/Chrome acceptance, no browser result can be marked as an independent EGM review.


## Post-implementation hardening — 2026-11-09

The coordinator now catches packet-builder `TypeError`/ `ValueError` and returns `BLOCKED` with an `invalid_review_packet` reason before creating any provider sessions. Regression cases cover too few reviewers, duplicate IDs, blank IDs, and a mutable list supplied instead of the required tuple. The task remains RUNNING and no session or success receipt is created.

The commit containing this hardening must be validated on the current PR head; previous Focused/Windows runs apply only to the earlier head. Snyk status remains unapproved/unknown.


Windows executable CI was enabled for this stacked review branch; the current PR head must pass the full frozen executable build before any merge decision.

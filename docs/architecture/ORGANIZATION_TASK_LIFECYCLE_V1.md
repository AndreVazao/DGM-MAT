# Organization task lifecycle — implementation checkpoint v1

**Date:** 2026-11-07  
**Status:** Durable store merged; MissionEngine integration under review  
**Primary issue:** [DGM-MAT #245](https://github.com/AndreVazao/DGM-MAT/issues/245)

## Implemented

### Durable storage

PR #259 merged the versioned `organization_tasks` table into the existing `InternalMessageBus` SQLite database. No second task database was introduced.

The record stores the canonical task envelope:
- task and mission identity, title and description;
- owner department and assigned agent;
- lifecycle status and priority;
- dependencies, inputs and outputs;
- evidence and timestamps;
- approval requirement/reason;
- retry counters and metadata.

The store provides:
- insert with duplicate-ID conflict protection and identical-retry idempotency;
- transactional optimistic revision updates;
- raw record inspection;
- versioned restore;
- fail-closed behavior for malformed or unsupported records, retaining the original row.

`OrganizationTaskManager()` without a bus remains process-local for isolated tests. Passing the existing bus enables persistence. Returned tasks are detached copies; mutations must go through manager lifecycle methods.

### MissionEngine integration — PR #260

The current proposal creates one manager from the MissionEngine-owned `organization_bus`, then one `DelegationEngine` using the existing office registry and `WorkerRuntime`.

The proposed API surface is deliberately bounded:
- create a task;
- read a detached task snapshot;
- delegate/assign to a registered agent whose declared capabilities, department, skills and permissions satisfy the task.

Delegation only assigns work. It does not execute descriptions, commands, code, or arbitrary message content.

Readiness distinguishes SQLite durability from injected in-memory test mode and continues to report `task_validated=false`.

## Validation evidence

- PR #259 focused workflow `42355370414`: **success** on the exact PR head.
- PR #259 merged to `main` as `42be7164a99e79b2a3fddac3cae5d341c38a8bb7`.
- PR #260 adds MissionEngine restart/reopen and capability-gated delegation integration tests. Its CI result is pending review at the time this checkpoint was written.
- No local Windows acceptance is claimed while the operator PC is offline.

## Not yet implemented

- A task-to-fixed-worker-operation dispatcher.
- Task-level execution receipts linked to task revision and mission.
- Recovery reconciliation for a crash between a worker receipt and task status transition.
- Isolated code-patch workers, worktree approval, independent QA and rollback acceptance.
- Production API exposure for task creation/delegation.
- Local Windows restart/power-loss acceptance.

## Next gates

1. Pass exact-head CI for PR #260.
2. Review API compatibility and constructor side effects; merge only if focused tests pass.
3. Add a typed task dispatcher that maps only explicit task kinds to fixed worker operations. Never infer operations from free-form descriptions.
4. Make worker completion and task transition reconciliation idempotent, using durable message receipts and task revisions.
5. Validate real allowlisted repository tasks on the Windows host when it returns online.
6. Keep code mutation separate until the isolated worktree, approval-bound patch digest, test and rollback gates are accepted.

## Independent security blocker

PR #236 remains unmerged. The direct browser task creation endpoint still has a documented server-side approval bypass: request input can set `approval_required=false` without a server-verified parent mission state. Do not merge or enable that path until the shared service boundary and both endpoint test matrices enforce the approval invariant.

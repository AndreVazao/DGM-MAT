# Organization task persistence gate — 2026-11-07

## Purpose

Record the verified persistence boundary before connecting the internal engineering workforce to MissionEngine. This is a design/acceptance checkpoint, not a claim that the task lifecycle is durable.

## Verified current implementation on main

- `core/organization/task_manager.py` stores `Task` objects in a process-local `dict`, protected by an `RLock`.
- The manager exposes create/get/dependency checks/assign/transition/ready_tasks, but has no load, save, reopen, or recovery contract.
- `core/organization/message_bus.py` already owns a SQLite database and creates durable `organization_messages` and `organization_dispatch_receipts` tables. It supports restart-safe message/receipt retrieval when initialized with a persistent database path.
- `core/organization/worker_runtime.py` dispatches registered handlers and persists a receipt plus message acknowledgement atomically through the existing bus.
- `core/organization/read_only_worker_orchestrator.py` already uses deterministic message IDs and the durable bus for the three bounded read-only specialists.
- `core/organization/delegation.py` requires a real WorkerRuntime handler and declared capabilities before assigning a task, but it assigns only inside the in-memory task manager.
- Search of the default branch found no production MissionEngine construction/use of `OrganizationTaskManager`; current references are the manager/delegation modules and focused tests.

## Consequence

A process restart can preserve worker messages and dispatch receipts while losing the task registry's task objects and lifecycle state. Therefore:
- `AVAILABLE` is not task readiness.
- A durable worker receipt is not a durable organization task.
- Delegation assignment is not restart-safe.
- No task-level end-to-end completion claim is justified yet.

## Required next implementation

1. Extend the existing `InternalMessageBus` SQLite store with a versioned, transactional task-record persistence API; do not create a second task database.
2. Serialize the complete canonical Task envelope: identity, mission, title/description, owner/assignee, status, priority, dependencies, inputs/outputs, evidence, approval fields, retry policy, metadata and timestamps.
3. Make `OrganizationTaskManager` accept the existing bus/store as its persistence backend while retaining an explicit in-memory mode for isolated tests.
4. Persist create/assign/transition atomically; reject conflicting task IDs rather than overwriting.
5. On manager construction, reload persisted tasks and validate schema/version and enum values. Corrupt or unsupported records must fail closed and remain inspectable; do not silently discard them.
6. Add restart/reopen, duplicate-ID conflict, dependency recovery, assignment recovery, transition recovery and malformed-record tests.
7. Only then wire a single MissionEngine-owned task manager and DelegationEngine instance into a bounded task dispatch path. The task dispatcher must map a task to a fixed worker operation/capability contract; never interpret task descriptions as executable instructions.
8. Keep current read-only workers read-only. Code mutation requires a separate worktree, backup-first executor, approval-bound exact patch digest and rollback acceptance.

## Acceptance evidence required

- Focused organization persistence tests pass on CI.
- Cross-instance SQLite reopen test proves state survives manager/bus reconstruction.
- Existing message-bus and read-only-worker tests remain green.
- No parallel task DB is introduced.
- No local Windows/PC acceptance is claimed until the operator PC is online.

## Related work and open gates

- Issue #245 — governed internal engineering workforce and self-evolution.
- PR #254–#257 — explicit specialist registration, read-only dispatch and roster/readiness integration.
- PR #236 — browser task sending is a separate execution channel. It must remain unmerged until approval is enforced server-side; request payloads must not be allowed to disable approval merely by setting `approval_required=false`.
- PR #238 — Vault persistence is separate from organization task persistence; do not assume its SQLite catalogue automatically makes OrganizationTaskManager durable.

## Current status

`VERIFIED_GAP`: task manager is in-memory; message bus is SQLite-backed. No task persistence implementation or MissionEngine task dispatch is claimed by this document.

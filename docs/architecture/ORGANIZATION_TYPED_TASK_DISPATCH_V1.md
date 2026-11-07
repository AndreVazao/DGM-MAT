# Typed organization task dispatch v1

**Date:** 2026-11-07  
**Status:** Proposed implementation; exact-head CI and merge pending  
**Depends on:** PR #259 and PR #260

## Objective

Connect persisted organization tasks to the three already implemented read-only specialists without interpreting free-form task descriptions as instructions.

## Fixed task-kind map

Only these exact metadata values are dispatchable:

| `metadata.task_kind` | Fixed agent | Fixed worker operation |
|---|---|---|
| `repository_inventory` | `agent:repository-cartographer` | `inventory_repository` |
| `python_source_analysis` | `agent:python-source-analyst` | `analyze_python_repository` |
| `python_test_inventory` | `agent:python-test-inventory` | `inventory_python_tests` |

The dispatcher verifies:
- task exists and is in `ASSIGNED` state;
- task kind is in the fixed map;
- assigned agent exactly matches the mapped agent;
- the assigned agent is still eligible under the existing DelegationEngine rules;
- a real handler is registered and declares the mapped capabilities;
- a stable `repository_id` is supplied. The host-owned worker allowlist resolves it to a path; task metadata cannot supply a filesystem path.

Task title, description and other free-form text are never parsed into commands or operations.

## Durable execution sequence

1. MissionEngine delegates the task using the existing AgentRegistry, DelegationEngine and WorkerRuntime.
2. Dispatcher invokes ReadOnlyWorkerOrchestrator with the fixed agent, repository ID, mission ID, task ID and deterministic task correlation ID.
3. The message bus persists the task ID on the worker message.
4. WorkerRuntime executes only the explicitly registered read-only handler and stores its durable receipt atomically with message acknowledgement.
5. Dispatcher marks the organization task COMPLETED only when the orchestrator returns a durable receipt and a JSON-safe result.
6. The task manager stores the receipt message ID and result in task metadata under `worker_execution`.

## Crash/retry behavior

- If the worker message is queued behind an older inbox message, the task remains ASSIGNED; it is not falsely reported as running or complete.
- If the handler fails before a receipt is committed, the message remains unread and the task remains ASSIGNED for controlled retry/review.
- If the process stops after a durable worker receipt but before the task completion update, a repeated dispatch returns `ALREADY_COMPLETED` from the message bus and completes the task without rerunning the worker.
- Optimistic task revisions reject stale completion writes. A restarted manager reloads the latest task revision before retrying.
- A response without a durable receipt is reported as `RESULT_UNVERIFIED`; it cannot complete the task.

## Safety boundary

This increment dispatches only read-only repository inventory, Python source AST analysis and Python test inventory. It does not execute tests, imports, shell commands, arbitrary scripts, network requests or code mutation.

No code-patch worker is enabled. Worktree isolation, backup-first patch application, exact-digest approval, independent QA and rollback remain separate future gates.

## Acceptance

- Focused CI must pass on the exact PR head.
- Tests must prove all three fixed task kinds dispatch and persist their task-linked receipt/result.
- Tests must prove unknown task kinds, mismatched agents, unassigned tasks and missing receipts fail closed.
- Local Windows acceptance remains pending until the operator PC is online; CI is not a substitute for real host acceptance.

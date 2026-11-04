# DGM-MAT — Generic Mission Execution: Consolidation Design Gate

Date: 2026-11-04  
Status: EVIDENCE-BASED DESIGN / NO RUNTIME ACTIVATION  
Base: `main` at `15bb5704fefb297b55e5cab8e88334162a3419be`

## 1. Decision

Do not add a second autonomous executor and do not activate the legacy execution-fabric path. DGM-MAT already contains mission planning, durable action approval, worktree helpers, command allowlists, patch assessment, QA review and recovery components. The current gap is the absence of one verified, end-to-end execution path connecting those capabilities.

The next implementation should consolidate existing contracts behind a single bounded execution registry. It must not expose arbitrary shell text, execute instructions embedded in task descriptions, or write to a user's active checkout.

## 2. Evidence inspected

The following source files and tests were inspected in the clean isolated worktree based on `main`:

- `core/autonomy/mission_engine.py`
- `core/autonomy/mission_models.py`
- `core/autonomy/mission_intent_router.py`
- `core/autonomy/safe_autonomous_executor.py`
- `core/operations/command_executor.py`
- `core/execution/approval_manager.py`
- `core/execution/execution_engine.py`
- `core/execution/worktree_manager.py`
- `core/execution_fabric/autonomous_executor.py`
- `core/execution_fabric/safe_patch_engine.py`
- `core/development/feature_planner.py`
- `core/development/validation_engine.py`
- Relevant autonomy, execution, approval, mission-result and development safety tests.
- `reports/DGM-MAT_EXECUTION_TOOL_SYMBOL_MATRIX.md`
- `reports/DGM-MAT_EXECUTION_APPROVAL_BOUNDARY_CHECKPOINT_2026-10-06.md`

### Confirmed runtime boundary

1. `MissionEngine.create_mission()` persists a mission and enqueues `MISSION_EXECUTION` in `SafeActionQueue`.
2. Automatic approval is limited to the explicit `AUTO_RUN_READ_ONLY_INTENTS` allowlist and supported non-mutating intents.
3. `_handle_queue_execution()` reloads the durable mission checkpoint, rejects terminal missions, and dispatches only explicit handlers.
4. Unknown approved missions are decomposed as proposals and fail closed with `NotImplementedError`; proposed subtask completion flags are not accepted as proof of mission success.
5. `ApprovalManager` is a compatibility facade over the durable `SafeActionQueue`, not an independent in-memory approval authority.
6. `CommandExecutor` exposes a small bounded read-only command catalogue, with allowed-root checks, timeouts and output limits.
7. QA review has a separate persisted queue/coordinator and does not execute commands supplied by a result.

### Confirmed fragmentation and unsafe legacy path

- `core/execution/execution_engine.py` and `core/execution/worktree_manager.py` provide basic branch/worktree creation, but do not implement a complete task lifecycle.
- `core/autonomy/safe_autonomous_executor.py` has a small command whitelist, but is not the mission-level tool registry.
- `core/execution_fabric/autonomous_executor.py` is not a safe integration candidate as-is: its implementation step is explicitly simulated; its approval handling is not shown to be the durable mission/action lifecycle; and its `finally` cleanup removes the sandbox even when approval is pending.
- `core/execution_fabric/safe_patch_engine.py` applies a patch using `git apply` without an explicit repository/worktree `cwd`. Its own comment says it applies to the main repository. It must not be connected to autonomous mission execution.
- `core/autonomous_dev/AutonomousDevEngine` and `RoadmapExecutor` are skeletal orchestration stubs, not production executors.
- `FeaturePlanner` creates deterministic planning metadata only. `ValidationEngine` deliberately refuses to certify implementation while no real validators are configured.

These findings explain why adding another loop or setting subtask statuses to completed would create false progress rather than verified autonomy.

## 3. Target execution lifecycle

Every mutating engineering mission must follow this sequence:

1. **Intake** — persist goal, repository identity, actor, correlation ID, constraints and requested outcome.
2. **Evidence and plan** — inspect repository state, callers, tests and ownership; produce a bounded plan with explicit file scope and acceptance criteria.
3. **Plan validation** — reject unknown tools, path escapes, unsupported operations, unbounded work and missing test strategy.
4. **Action proposal** — create one durable action per executable step, with tool descriptor, normalized arguments, risk class, timeout, resource budget and idempotency key.
5. **Approval gate** — read-only actions may use a separately tested allowlist. Mutating, external, credential, destructive or broad-scope actions remain pending for explicit operator approval. Approval is bound to the exact action digest; changed arguments require a new approval.
6. **Isolation** — create a uniquely named worktree from a recorded base SHA. Never use the active dirty checkout. Verify the worktree path and repository identity before each operation.
7. **Bounded execution** — dispatch only registered tools. No arbitrary shell string, no shell interpolation, no implicit administrator elevation, no hidden network access. Enforce per-action timeout, output cap, cancellation and total mission budget.
8. **Checkpoint** — persist each transition and structured result before reporting progress. Resume only from validated non-terminal checkpoints; never replay an action whose outcome is uncertain without idempotency reconciliation.
9. **Verification** — run only configured test/validation adapters against the isolated worktree. Record exact commands, exit codes, duration and affected paths. A missing validator is a failure, not a pass.
10. **Independent QA** — a reviewer distinct from the implementation actor checks diff, acceptance criteria, tests and policy. QA must not trust the implementer's success flag.
11. **Proposal and integration** — produce a diff/report and PR. Merge remains a separate guarded operator decision; no automatic merge to `main`.
12. **Retention and cleanup** — preserve the worktree and evidence while approval/review is pending. Cleanup only after a terminal, reconciled outcome and retention policy; never delete a user's pre-existing data.

## 4. Canonical contracts to reuse or extend

Prefer the existing durable contracts and stores rather than creating parallel authorities:

- `SafeActionQueue` / `ExecutionRequest` / `ExecutionResult` for durable action lifecycle.
- `ToolDescriptor` and existing contract package for discoverable, typed tool metadata.
- `CommandExecutor` as a reference implementation for fixed read-only operations only.
- `WorktreeManager` and Git utilities only after path, base-SHA, collision and cleanup behavior are covered by tests.
- `MissionEngine` as mission authority, with the smallest possible adapter to the new execution coordinator.
- Existing QA review coordinator/queue for independent review.
- Existing audit and runtime state stores for durable evidence.

Before implementation, inspect all callers and import paths for these contracts. Do not create a second approval store, mission store, event authority or tool registry.

## 5. Required invariants

- Default mode is observe/plan; no mutating execution starts implicitly.
- Each action is independently authorized; approval is never inferred from mission approval alone when the action scope changes.
- A plan or subtask status is not execution evidence.
- A task cannot claim success without persisted outputs and passing configured verification.
- A stale worker cannot overwrite a terminal checkpoint.
- A failed/uncertain operation is not retried blindly.
- User changes, untracked files and dirty worktrees are never reset, cleaned, stashed or overwritten.
- Network and provider access are separate capabilities and require explicit policy.
- Secrets are never copied into mission logs, diffs, reports or prompts.
- Cancellation is checked between actions and within long-running adapters.
- All resource limits are configurable, conservative and observable.
- The runtime remains idle when no approved mission exists; no busy-loop or heartbeat polling is introduced merely to appear autonomous.

## 6. Staged implementation plan

### Stage A — Contract and caller audit
- Map every caller of `SafeActionQueue`, `ExecutionRequest`, `ToolDescriptor`, `ApprovalManager`, `WorktreeManager` and QA coordinator.
- Confirm durable action transitions and cross-process behavior.
- Add contract tests for action digest, approval binding, idempotency and terminal-state protection.
- No runtime behavior change.

### Stage B — Read-only execution registry
- Introduce a registry adapter over existing descriptors and the current read-only command catalogue.
- Validate schema, capability, target root, timeout and output budget before dispatch.
- Add positive and negative tests; existing read-only mission behavior must remain unchanged.
- No shell-string tool and no write-capable tools in this stage.

### Stage C — Isolated mutation proposal
- Add a worktree preparation/proposal flow that records base SHA and path.
- Generate a diff only; do not apply it to the active checkout.
- Persist proposal and retain worktree while approval is pending.
- Test collisions, path traversal, dirty base repository, cancellation and process restart.

### Stage D — Explicitly approved bounded mutation
- Add a minimal set of typed file-edit operations, scoped to declared files in the isolated worktree.
- Require per-action approval bound to exact arguments and diff.
- Add budgets, timeouts, cancellation, checkpoint/resume and idempotency reconciliation.
- No unrestricted shell or self-modifying runtime.

### Stage E — Verification and independent QA
- Add real test adapters with explicit allowlists and deterministic environments.
- Persist logs/exit codes and test evidence.
- Require independent QA PASS before PR-ready status.
- Failure, missing evidence or reviewer disagreement blocks completion.

### Stage F — Controlled pilot
- Start with one non-critical repository and one small task.
- Keep the runtime disabled by default; operator explicitly enables the pilot.
- Measure completion accuracy, false-success rate, recovery, resource use and audit completeness.
- Expand only after the pilot passes.

## 7. Acceptance gates for the first implementation PR

The first code PR should be small and should not activate autonomous writes. It must include:

- A caller/import map for the chosen contracts.
- A registry contract and adapter tests, or a documented reason to reuse an existing exact contract unchanged.
- Tests proving unknown tools, invalid arguments, unauthorized targets, over-budget actions and missing approval are rejected.
- Tests proving approved read-only actions still work and mutating actions remain pending.
- Cross-process persistence and stale-worker regression coverage.
- A report of the exact tests run and the unchanged runtime behavior.

Do not merge if required CI/security checks are failing or indeterminate. Do not merge this design document as a substitute for implementation.

## 8. Current status and explicit non-claims

- Four bounded read-only missions were successfully dispatched and completed on 2026-11-04 using the existing runtime allowlist.
- The queue worker returned to idle after those finite missions.
- No generic engineering task has been executed by the mission runtime.
- The 801 historical queued actions and four historical queued mission records remain untouched.
- This document is a design gate only. It does not enable continuous execution, arbitrary commands, code mutation or automatic merging.

## 9. Next engineering action

Complete Stage A by generating the caller/import map and tests around the existing durable action contracts. Then implement Stage B as a read-only registry adapter. Keep the active dirty main checkout untouched and use isolated worktrees for all code changes.

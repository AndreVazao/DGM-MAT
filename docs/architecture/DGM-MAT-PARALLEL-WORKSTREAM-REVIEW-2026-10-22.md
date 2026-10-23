# DGM-MAT — Parallel Specialist Workstream Review

**Date:** 2026-10-22  
**Scope:** DGM-MAT repository only  
**Mode:** Parallel source review against GitHub files; no local PC access, no tests executed, no Actions started.  
**Decision:** Keep work isolated; do not merge or open another PR until the existing governance PR and focused validation gates are resolved.

## Workstream A — Programming lifecycle and truthful execution

**Files reviewed:** `core/development/development_engine.py`, `implementation_engine.py`, `execution_fabric.py` on `main`.

Findings from source:
- `DevelopmentEngine.process_request` plans a feature, appends an in-memory task to `ExecutionFabric`, calls `ImplementationEngine.execute_implementation`, records the returned status and returns the feature ID.
- `ExecutionFabric` stores tasks in a process-local list; it is not a durable worker queue.
- `ImplementationEngine.execute_implementation` creates a plain timestamped copy of `.env` when present, then returns `IN_PROGRESS`; it does not apply code.
- Therefore, this path must not be presented as completed implementation and should not be invoked merely to inspect status because it may copy secrets into the working directory.

**Next action:** Finish a repository-wide caller/entry-point map before altering this legacy API. Then define one safe Python pilot that uses an explicit workspace, dry-run patch review, real configured tests, independent QA and durable result evidence.

## Workstream B — Governance and approval boundary

**Files reviewed:** PR #143 `core/api/governance_api.py`, `core/api/auth_middleware.py`, `core/api/local_auth_api.py`, `core/api/security_policy.py`, and `core/governance/meeting_registry.py`.

Positive source observations:
- Privileged CEO/owner routes use separate server-configured credentials with a minimum length and reject identical values.
- Role checks use constant-time comparisons and do not infer privileged roles from client-supplied actor labels.
- Meeting records explicitly state that approval is not execution; plan digest and execution integration still require verification.
- The API installs `LocalSessionAuthMiddleware` after route and optional static-mount registration in `main`.

**Unclosed gates:** tests remain unexecuted; confirm negative cases for missing/invalid credentials, operator-session privilege escalation, actor spoofing, CORS preflight, all new route classifications, and digest binding at the actual execution boundary. Review the complete PR diff and regression suite before merge. No security approval or runtime readiness is claimed.

## Workstream C — Durable task state and evidence contract

**Files reviewed:** `core/development/task_result.py`, `core/development/task_store.py`, and their focused tests on this audit branch.

Findings and change made:
- The task contract requires explicit validation and independent-QA evidence before `verified`.
- SQLite persistence records state, evidence and append-only events, with legal transitions and optimistic revision checks.
- A source review found that task creation could accept evidence in a `planned` result but silently discard it. The store now rejects evidence at creation, and a regression test checks both the rejection and that no task row was created.
- The store is not wired into Mission Engine, Execution Fabric, API or cockpit, and it does not authenticate callers or validate evidence authenticity.

**Next action:** Run focused tests in a controlled environment; add concurrency/reopen/rollback coverage if needed; only then design a narrow adapter to the real mission lifecycle. Do not treat caller-supplied evidence references as cryptographic proof.

## Coordination and boundaries

1. Each workstream owns only its listed scope; no broad refactor or deletion of legacy APIs.
2. No production path is wired to planning-only catalogue or the task store until compatibility and callers are mapped.
3. No changes to other AndreOS repositories in this work session.
4. No GitHub Actions were triggered, no PR was merged, and no claim of test execution is made.
5. The current programming audit branch remains separate from PR #143; preserve the one-open-PR policy.

## Immediate priority order

1. Execute the new task-contract/store tests and the existing focused development tests in a controlled checkout.
2. Map imports, dynamic imports, DI, entry points, tests and configuration for the legacy development modules.
3. Complete PR #143 security-negative tests and confirm approval-to-executor digest binding.
4. Implement one minimal, reversible Python patch lifecycle end-to-end; only after that consider integration with the cockpit.

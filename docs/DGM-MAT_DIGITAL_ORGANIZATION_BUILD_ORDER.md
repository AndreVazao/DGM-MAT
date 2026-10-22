# DGM-MAT Digital Organization Build Order

## Objective

Turn DGM-MAT into a functioning digital engineering organization without
creating a fragile swarm of agents.

## Programming department readiness checkpoint — 2026-10-22

The evidence-based readiness audit is tracked in [DGM-MAT-PROGRAMMING-DEPARTMENT-READINESS-AUDIT-2026-10-22.md](architecture/DGM-MAT-PROGRAMMING-DEPARTMENT-READINESS-AUDIT-2026-10-22.md).

This pass confirmed source-level placeholders in the default branch: `CodeGenerationEngine.generate_code()` and `DeadCodeDetector.find_dead_code()` return empty lists; `ValidationEngine.validate_implementation()` reports success unconditionally; `ArchitectureValidator` references an unimported `Any` and has no implemented rules; `ImplementationEngine` only backs up `.env`/logs/returns IN_PROGRESS; `ExecutionFabric` is an in-memory list; and `FeaturePlanner` uses process-randomized `hash()` for IDs. These findings are detailed in the readiness audit. Callers and compatibility impact are not fully mapped, so do not wire, delete, or replace the legacy subsystem blindly.

A planning-only language catalogue and unit tests are on branch `audit/programming-department-readiness-2026-10-22`. Nineteen unit tests (language catalogue, allowlisted toolchain probes, and development safety gates) passed against isolated temporary copies; the full repository suite and Windows PC checks remain pending. A fixed-allowlist, no-shell, bounded-time version probe is now available as a separate primitive. The legacy implementation validator and architecture validator now fail closed rather than certifying unchecked work; feature IDs use stable SHA-256 values. It must not be described as an installed-tool detector or a functioning code executor. A side-effect-free shared result contract now exists on the audit branch (`core/development/task_result.py`): `planned`, `blocked`, `not_implemented`, `running`, `failed`, `verified`. `verified` requires explicit validation + independent QA pass flags and evidence references whose outcomes are `passed`; failed evidence cannot be overridden by caller-supplied pass flags. Eleven focused contract tests have been added but not executed. This contract is not yet wired to Mission Engine, Execution Fabric, API, durable storage or cockpit. The next gate remains executing the new tests, completing the local AST/import/caller map, then designing one real Python patch lifecycle with configured checks and independent QA.

## Phase 1 — Organization Kernel

Status: **started**

Implemented:

- agent/department models
- agent registry
- internal message bus
- task lifecycle manager
- shared workspace contract
- organization tests

## Phase 2 — Runtime Integration

Next:

1. connect organization tasks to existing Mission Engine;
2. emit organization events through the existing Event Bus;
3. connect task state to Execution Fabric;
4. expose organization state through the API;
5. persist durable state;
6. synchronize institutional records with AndreOS memory.

## Phase 3 — Governance

Implement:

- ownership matrix
- permission evaluation
- approval categories
- evidence requirements
- cross-department change requests
- release gates

## Phase 4 — Worker Lifecycle

Implement:

- worker registration
- worker heartbeat
- assignment
- execution
- timeout
- retry
- failure
- quarantine
- recovery
- shutdown

## Phase 5 — Pilot Departments

Do not spawn dozens of workers.

Pilot with:

1. HQ / Orchestrator
2. Python Engineering
3. QA + Bug Hunting
4. Conversation Intelligence
5. AI Provider Liaison
6. DevOps

These six areas validate the organization model against the most important
DGM-MAT workloads.

## Phase 6 — Conversation Intelligence Fleet

Add provider-specific workers and browser/scroll workers behind a normalized
contract.

The recovery lifecycle remains:

`RAW -> CONTEXTUALIZED -> CANDIDATE -> CONSOLIDATED -> IMPLEMENTED`

## Phase 7 — Project Task Forces

For complex projects, HQ assembles temporary multidisciplinary teams.

Example:

- project lead
- domain specialist
- Python
- frontend
- database
- research
- QA
- security
- DevOps

The task force is archived and its lessons returned to organizational memory.

## Phase 8 — Evaluation and Evolution

Measure:

- task success
- regression rate
- bug escape rate
- review score
- human correction rate
- evidence quality
- efficiency
- reliability

Promote improved worker versions only after evaluation.

## Phase 9 — Scale

Only after the kernel is stable:

- additional languages
- additional AI providers
- specialized domain departments
- autonomous project assembly
- distributed workers
- richer cockpit
- cross-device operation

## Non-negotiable rule

Do not optimize for the number of agents.

Optimize for:

**correct work + evidence + coordination + recoverability + controlled autonomy.**


## Canonical operating contract — 2026-10-21

The [canonical end-to-end operating model](architecture/DGM-MAT-CANONICAL-OPERATING-MODEL-END-TO-END-AND-DEPARTMENTS-2026-10-21.md) is the operational reference for department boundaries, programming specializations, the owner liaison role, Conversation Intelligence, separate Research and Answer Evaluation Lab responsibilities, real office telemetry, and future multi-PC placement.

Update to the build sequence: before expanding the number of agents or visual departments, prove one request through persistent intake → executable plan → policy/approval → real worker → independent validation → durable terminal state → truthful final answer. Planning-only outcomes must never be counted as execution. Start with the smallest useful pilot: HQ/owner liaison, Python engineering, independent QA/bug hunting, Research, and Conversation Intelligence. Add language specialists and separate lab workers only after real demand, contracts, resource limits and tests are demonstrated.

The status labels in this document are historical planning notes. They do not prove current implementation; reconcile every phase against current code, tests and runtime before marking it complete.


## Programming department follow-up — contract/caller audit — 2026-10-22

Targeted searches exposed the legacy call chain but did not prove a complete production caller graph. The current visible `DevelopmentEngine.process_request` path plans a feature, appends a task to an in-memory list, invokes an implementation method that only backs up `.env` and returns `IN_PROGRESS`, records that status and returns a feature ID. It does not generate/apply code or invoke validation. Do not treat it as a working coding pipeline, and do not connect the new language catalogue to it yet. See the audit for exact limitations and the required local AST/import/caller scan.

Security/reliability note: avoid invoking the legacy implementation method merely to obtain a status because it may copy `.env` (potential secrets) into a plain backup file. Do not delete or broadly refactor legacy APIs until callers and compatibility tests are mapped. A shared truthful task-result contract and SQLite-backed task registry now exist on the audit branch, with legal state transitions, revision checks, evidence storage and persistent event history. They are deliberately not wired into the legacy pipeline yet. Next: execute the focused tests in a controlled local environment, complete the local AST/import/caller map, then build one end-to-end Python pilot that produces a real patch, runs configured checks, receives independent QA, and persists truthful evidence. PR #143 remains the only open PR; no new PR or GitHub Actions run was created in this audit pass.

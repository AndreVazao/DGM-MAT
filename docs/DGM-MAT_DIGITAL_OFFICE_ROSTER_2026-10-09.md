# Path: C:\ProgramasGodMode\DGM-MAT\docs\DGM-MAT_DIGITAL_OFFICE_ROSTER_2026-10-09.md

# DGM-MAT Digital Office — roster and delegation foundation
Date: 2026-10-09
Status: role registry and deterministic delegation foundation implemented; workers are not yet autonomously executing through this registry.

## Design principle

DGM-MAT should behave like a governed engineering office, not a swarm of interchangeable chatbots. HQ interprets the request, decomposes it into owned tasks, chooses specialists by skills and permissions, and routes implementation through independent review. No worker may certify its own work solely because it ran.

## Organizational chart

- **HQ / Orchestrator** — mission intake, decomposition, priority, ownership, dependency graph and final synthesis.
- **Front Office / Requirements Analyst** — interprets user intent, writes acceptance criteria, identifies ambiguity and obtains approval when needed.
- **Back Office / Operations Coordinator** — tracks assignments, evidence, checkpoints, schedules and cross-project handoffs.
- **Backend & Reliability Engineer** — headless service, FastAPI, process lifecycle, recovery, logs, health and performance.
- **API Contract Integrator** — HTTP/WebSocket contracts, OpenAPI, compatibility and client migration.
- **Frontend & Cockpit Engineer** — PC dashboard and Android/mobile experience; only after backend/API contract is stable.
- **Python/General Engineering** — implementation and refactoring within assigned ownership.
- **Independent Bug Hunter** — reproduces defects, performs negative/regression tests and reports evidence; does not silently modify the implementation being reviewed.
- **QA / Validator** — verifies acceptance criteria, runs relevant and regression suites, checks artifacts and reports residual risk.
- **Repository Cartographer** — inventories repository files, produces deterministic project trees, maps modules and detects drift; read-only by default.
- **Security Engineer** — threat models, scopes, HTTP/WebSocket auth, credential handling and remote-exposure gates.
- **DevOps / Release Engineer** — builds, workflows, packaging, health checks and rollback evidence.
- **Research / Provider Liaison** — grounded external research and provider-specific adapters, without letting provider quirks leak into core contracts.
- **Memory & Documentation Steward** — records verified state, decisions, provenance and next steps in AndreOS/andreos-memory.
- **Conversation Intelligence** — recovers context and code from AI conversations and links artifacts to projects.
- **Capability Scout / Skill Forge** — proposes new skills/workers; promotion remains gated by evaluation and approval.

## Current code foundation

- `core/organization/models.py`: agent, department, task, message and evidence models.
- `core/organization/registry.py`: thread-safe registry.
- `core/organization/task_manager.py`: lifecycle and dependency checks.
- `core/organization/message_bus.py`: in-process message semantics.
- `core/organization/office.py`: expanded role roster, safe/idempotent bootstrap.
- `core/organization/delegation.py`: deterministic matching by availability, skills, permissions, department and dependency readiness.
- `core/repository_intelligence/snapshot.py`: read-only inventory and tree generation, skip rules, depth/entry bounds, no symlink traversal, sensitive-name marking and overwrite refusal.
- Tests: `tests/organization/test_office_delegation.py`, `tests/repository_intelligence/test_snapshot.py`.

The delegation engine assigns work; it does not execute code. The snapshot module inventories names/metadata only and never reads file contents. The existing organization registry and message bus are in-memory foundations, not yet a durable distributed worker runtime.

## Mandatory coding workflow

1. Front Office/HQ turn intent into explicit acceptance criteria and task boundaries.
2. Cartographer captures the repository baseline and identifies ownership before edits.
3. Architect/lead decomposes work and assigns one owner per file/domain.
4. Implementer changes code only inside approved scope and preserves pre-change evidence for edits to existing files.
5. Bug Hunter independently attempts to reproduce faults and probe edge cases.
6. QA runs targeted tests, full relevant regression tests and build/health checks.
7. Security reviews auth-sensitive, external-input, filesystem and process-control changes.
8. Integrator reconciles conflicts and verifies final working tree and artifacts.
9. Memory Steward records commit IDs, test evidence, limitations and next action.
10. HQ reports success only for work actually verified.

For security-critical or structural changes, no automatic merge or deployment based solely on worker self-report. Destructive actions, secret access, new spending, remote exposure and irreversible repo restructuring remain approval-gated.

## Routing contract

Tasks can specify `metadata.required_skills`, `metadata.required_permissions` and `metadata.preferred_department`. A candidate must be AVAILABLE, belong to an active department, satisfy every required skill and permission, and meet task dependency constraints. Ties resolve deterministically by score then agent ID. If no safe candidate exists, delegation fails closed and surfaces a blocker.

## Staged integration roadmap

1. **Current:** role catalogue, bounded deterministic delegation and safe repository inventory.
2. Connect organization task lifecycle to Mission Engine/Event Bus without falsely marking unexecuted work complete.
3. Persist tasks, agent heartbeats, evidence and audit records.
4. Add worker leases, timeouts, retries, quarantine and controlled shutdown.
5. Enforce HTTP/WebSocket auth and migrate PC clients before any remote pairing.
6. Connect implementer → independent bug hunter → QA → integrator workflow.
7. Add model/provider routing and resource-aware local inference; avoid assuming a small PC can run large models.
8. Only after backend reliability is proven, develop PC cockpit; Android mobile cockpit follows and remains the main daily user interface.
9. Evaluate success rate, regression escape rate, evidence quality, time, resource use and human correction rate before promoting new agent versions.

## Cloud Free — future integration only

The user reports that the Cloud Free project has undergone substantial structural changes. Treat its current layout and interfaces as changed/unknown until re-inventoried. Keep its future use as a possible specialized agent/provider within DGM-MAT open, as previously discussed. Do not integrate, overwrite, deploy, rename, or assume compatibility as part of the current DGM-MAT backend work. Revisit only after the user explicitly prioritizes it and its current repository/state has been inspected read-only.

## Current next gate

Run the full test suite and inspect the live backend health. Then address route-level authorization and client migration before remote access. The expanded office roster is a controlled foundation, not a claim that every role already has an independent running model or autonomous execution loop.


## Implementation checkpoint — 2026-10-09

The first complete pass is now validated:
- Full repository test suite: 100%, exit code 0.
- New office/delegation/inventory/truthful-cycle/resource-monitor focused batch: 19 passed.
- Backend health remains healthy on loopback, PID 6876.
- The independent Bug Hunter audit also corrected two false-status defects: unexecuted placeholder tasks were previously reported as `VALIDATED`, and cycle finalization could overwrite `FAILED` with `COMPLETED`.
- Resource monitor now stops promptly and is joined before governance executor shutdown; the full suite no longer emitted the prior closed-console Loguru error.
- Final inventory (excluding its own output directory to avoid self-reference): 1,597 files, 220 directories, 118 skipped; see `reports/repository_inventory/DGM-MAT_INVENTORY_FINAL_VERIFIED_2026-10-09.json` and `reports/repository_inventory/DGM-MAT_TREE_FINAL_VERIFIED_2026-10-09.txt`.

Still not complete: specialist profiles are registered definitions, not separate live AI processes; delegation is not yet wired to actual task execution or durable state. Existing HTTP/WebSocket routes still need scoped auth and PC client migration before remote pairing.

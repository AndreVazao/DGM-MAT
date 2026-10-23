# DGM-MAT — Digital Organization Build Order

## Objective

Turn DGM-MAT into a functioning digital engineering organization without
creating a fragile swarm of agents.

## Programming department readiness checkpoint — 2026-10-22

The evidence-based readiness audit is tracked in [DGM-MAT-PROGRAMMING-DEPARTMENT-READINESS-AUDIT-2026-10-22.md](architecture/DGM-MAT-PROGRAMMING-DEPARTMENT-READINESS-AUDIT-2026-10-22.md).

This pass confirmed source-level placeholders in the default branch: `CodeGenerationEngine.generate_code()` and `DeadCodeDetector.find_dead_code()` return empty lists; `ValidationEngine.validate_implementation()` reports success unconditionally; `ArchitectureValidator` references an unimported `Any` and has no implemented rules; `ImplementationEngine` only backs up `.env`/logs/returns IN_PROGRESS; `ExecutionFabric` is an in-memory list; and `FeaturePlanner` uses process-randomized `hash()` for IDs. These findings are detailed in the readiness audit. Callers and compatibility impact are not fully mapped, so do not wire, delete, or replace the legacy subsystem blindly.

A planning-only language catalogue and unit tests are on branch `audit/programming-department-readiness-2026-10-22`. Nineteen unit tests (language catalogue, allowlisted toolchain probes, and development safety gates) passed against isolated temporary copies; the full repository suite and Windows PC checks remain pending. A fixed-allowlist, no-shell, bounded-time version probe is now available as a separate primitive. The legacy implementation validator and architecture validator now fail closed rather than certifying unchecked work; feature IDs use stable SHA-256 values. It must not be described as an installed-tool detector or a functioning code executor. A side-effect-free shared result contract now exists on the audit branch (`core/development/task_result.py`): `planned`, `blocked`, `not_implemented`, `running`, `failed`, `verified`. `verified` requires explicit validation + independent QA pass flags and evidence references whose outcomes are `passed`; failed evidence cannot be overridden by caller-supplied pass flags. Its focused contract tests are included in the cross-platform validation run linked in the final checkpoint below. This contract is not yet wired to Mission Engine, Execution Fabric, API, durable storage or cockpit. The next gate remains executing the new tests, completing the local AST/import/caller map, then designing one real Python patch lifecycle with configured checks and independent QA.

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

## Follow-up: conversation continuity, Obsidian and adaptive installation — 2026-10-22

The programming department audit now has a dedicated specification: [Conversation memory, Obsidian and adaptive inventory](architecture/DGM-MAT-CONVERSATION-MEMORY-OBSIDIAN-AND-ADAPTIVE-INVENTORY-2026-10-22.md).

Build in this order; do not skip ahead to autonomous self-modification:

1. **Archive before summarizing:** define and test import of authorized full conversation exports, retaining raw message text/order/speaker/attachments metadata, source IDs, capture coverage and checksums. A summary never replaces raw history.
2. **Context and decisions:** build separate indexed views for user requirements/decisions, AI proposals, observed evidence, superseded choices and the architecture evolution timeline. Link every summary/decision to source messages.
3. **Reconcile against code:** map current requirements to actual repositories, revisions, files, callers, tests and runtime evidence; report gaps and contradictions without silently inventing intent.
4. **Obsidian adapter:** inspect the existing Obsidian installation and vault on the PC; identify the supported local write/read interface; perform a harmless round-trip and verify it before declaring shared persistent memory active. Reuse AndreOS-Memory/task storage where appropriate; do not create competing stores or duplicate notes.
5. **Portable inventory:** generate a dated Markdown and machine-readable environment manifest from one canonical model, including required/optional/conditional dependencies, repository revisions, health checks, recovery steps and detected hardware capability. Export to USB only after verifying the destination and excluding secret values.
6. **Resource-aware execution:** choose native checks, a connected device, container, emulator/VM or stronger authorized machine based on measured resources and test needs. Do not install an Android emulator on a low-resource PC merely because an APK is being built.
7. **Bounded autonomy:** allow routine reversible checks within scope; require approval for destructive changes, broad installs, privilege/secrets changes, external sharing, canonical architecture changes and protected merges.

Current status is **specification documented; runtime integration pending**. The current environment has not established a live Obsidian connector or access to the PC's vault, so no claim of a completed Obsidian connection is made. The implementation gate requires a real PC read/write verification.

## Primary mission update — recovery-first development and cross-AI continuity — 2026-10-22

The new [Recovery-First Development, Cross-AI Continuity and Reverse-Engineering contract](architecture/DGM-MAT-RECOVERY-FIRST-CROSS-AI-CONTINUITY-AND-REVERSE-ENGINEERING-2026-10-22.md) establishes the primary mission order. **Recover and understand existing work before starting new implementation.**

Required sequence:

1. Search authorized local conversation exports/history, project folders, downloads, backups, repositories, scripts and attachments. Preserve originals, source metadata and capture limits.
2. Group related conversations and artifacts by project/context, detect duplicates and conflicting versions, and propose clear project/folder names. Stage moves/renames reversibly and verify copies before approved changes.
3. Recover scripts, requirements, decisions and dependency/build instructions with provenance. Separate user-approved decisions, AI suggestions and observed evidence.
4. When a program exists but its conversation is missing, reverse-document the program from source files, entry points, manifests, tests, Git history, logs and release artifacts; label uncertainty and continue from a recovered project brief.
5. Reconcile recovered context against actual files and callers; assemble the smallest safe patch into the correct original files, not by replacing complete files with isolated snippets.
6. Research official web documentation and use the best currently available authorized AI provider. Send versioned context bundles between providers; if one is blocked, unavailable, at quota, or unable to solve the task, log the reason and try another legitimate provider without losing context. Never bypass access controls or quotas, or disclose secrets/private source without approval.
7. Integrate, test and independently review the change. Mark a task verified only with evidence tied to the actual revision/run.

The Reverse Engineering department/tooling is a **later phase**. First inventory the user's earlier reverse-engineering work and candidate open-source repositories; review maintenance, Windows/resource fit, security and license obligations. Prefer documented CLI/API/plugin integration over copying internals. Reuse source only where the license permits it, preserve notices/attribution, and analyze only software the user is authorized to inspect. Start with a bounded, read-only pilot and explicit tests; do not grant this department unrestricted self-modification authority.

This is a documented requirement and build sequence, not evidence that local conversation discovery, cross-provider browser automation or reverse-engineering tools are already operational. All source discovery and PC-side capabilities must be verified on the target PC before being reported as complete.

## First-start priority — recovery, project tree, progress ledger and deletion candidates — 2026-10-22

The first major mission after DGM-MAT is installed on a PC is to recover authorized AI conversations and existing project artifacts, not to begin unrelated development. Follow the detailed [first-run recovery and cross-AI contract](architecture/DGM-MAT-RECOVERY-FIRST-CROSS-AI-CONTINUITY-AND-REVERSE-ENGINEERING-2026-10-22.md).

Required sequence: (1) discover/capture raw conversations and artifacts, including explicit scroll coverage; (2) create a master inventory and group/rename by project using reversible plans; (3) index user statements, AI responses, scripts, decisions and evidence; (4) reconcile every project with existing local folders and Git repositories before proposing a new repo; (5) create each project's PROJECT_TREE.txt before assembling scripts, separating observed files from proposed/missing files; (6) assemble scripts into the right paths, validate them, and update the tree/manifest with every structural change; (7) produce a reviewable list of conversations eligible for provider-side deletion only after full capture, integrity/read-back checks, indexed context, source links and recoverability are verified.

Persist a master ledger and forward-only processing cursor. After each conversation/stage, checkpoint its status so restart resumes at the next unprocessed source rather than beginning again at conversation one. Processed sources remain searchable locally; revisit them only for a concrete reason such as a missing dependency, contradiction, new requirement or user request, and record the reason. Prefer the local archive/index over repeated web browsing when the captured context is sufficient and current.

Provider-side conversation deletion is irreversible in some services. Default behavior is archive and list candidates, **never automatic deletion**. Require explicit user authorization for the relevant deletion scope, exact source identification, verified complete transcript/attachments, integrity checks and a recovery path; record the provider's result. Partial/truncated capture or ambiguous matches are never eligible. This gate prevents freeing space at the cost of losing the only copy of code or user intent.

This is the required workflow specification; PC-local discovery, actual provider scrolling/deletion, durable cursor and tree generation are not yet claimed as operational. Keep main unchanged and validate each capability on the target PC before reporting completion.

## Recovery implementation checkpoint — 2026-10-22

First implementation increment added on the work branch:

- `core/recovery/recovery_ledger.py`: SQLite source ledger, stable provider/source identity,
  deterministic ordering, durable cursor, atomic source claiming, restart requeue,
  explicit retry queue, and local archive SHA-256 verification for `verified` status.
- `tests/test_recovery_ledger.py`: 14 focused tests covering idempotent registration,
  ordering, restart, cursor progression, partial/failure retry, and archive integrity.

**Verification boundary:** these tests are authored, not executed. No local checkout or
Windows runtime test has been performed in this increment. The component is not yet
connected to the Mission Engine, API, startup recovery flow, search index, project
inventory, or cockpit. It does not access provider history or delete anything.

### Next implementation sequence

1. Obtain/refresh a full local checkout of this exact branch and run the focused test file.
2. Fix any failures and review the SQLite transaction/cursor behavior.
3. Inspect current startup, Mission Engine, API and storage interfaces before wiring the
   ledger in; avoid parallel or duplicate registries.
4. Add a read-only recovery inventory endpoint/report and checkpoint visibility.
5. Add authorized source adapters one at a time, preserving raw exports and attachments.
6. Build the searchable index and project grouping/tree from captured evidence.
7. Only after archive, index, provenance and project reconciliation are independently
   verified, produce a deletion-candidate report. Provider deletion remains disabled
   until explicit user approval and a supported, verifiable provider interface exist.

### Read-only progress API increment

Added the read-only operator endpoints:

- `GET /recovery/status` — aggregate ledger counts and explicit `ledger_only` /
  provider-connectors-disabled / provider-deletion-disabled state.
- `GET /recovery/sources?limit=50&offset=0` — paginated source metadata without
  transcript bodies.
- Router registered in `core/api/api_server.py`; both paths are classified as
  operator-only in `core/api/security_policy.py`.
- Focused API tests are in `tests/api/test_recovery_api.py`.

The endpoint creates/opens the local ledger on first use, but does not import conversations.
It is not yet a cockpit screen or a working provider importer. Test execution remains
pending because this work has been made against the GitHub branch, not a full local checkout.

### First local-export adapter increment

Added a standard-library ChatGPT JSON-export adapter:

- `core/recovery/chatgpt_export_importer.py` reads the top-level JSON array incrementally,
  preserves the supplied source file, archives each conversation separately, and writes
  a derived JSONL record for every retained message/mapping node.
- `tests/test_chatgpt_export_importer.py` contains ten focused tests, including ZIP path-safety/size limits, small
  chunk boundaries, unchanged source bytes, idempotency, conflict preservation, attachment
  incompleteness and malformed exports.
- Attachment references are detected but the files are not copied yet. Such records are
  marked partial; other records remain completeness-unknown. No deletion capability exists.

The importer accepts either an already-extracted `conversations.json` or a ZIP containing
exactly one such member. ZIP handling streams only that JSON member to private staging;
arbitrary archive members are not extracted. Attachment recovery, full-text search, project
grouping, project-tree generation, cockpit upload and startup orchestration remain future steps. The focused regression set subsequently passed in GitHub Actions on Windows and Linux (101 tests plus compile check); see the final validation checkpoint below.

### Memory and project-tree correction

The recovery status endpoint now uses SQL aggregates, and the source inventory applies
pagination in SQLite instead of loading every source into Python memory. This is better
suited to the target low-memory PC.

Added root `PROJECT_TREE.txt` as an evidence-backed partial snapshot of the paths
inspected/changed for this recovery increment. It explicitly states that it is not a full
repository or Windows filesystem scan, and lists known gaps separately from observed files.


## Validation checkpoint — 2026-10-22

The recovery/programming branch passed its targeted GitHub Actions validation on both Windows and Ubuntu with Python 3.12: repository compile check plus 101 focused recovery/programming regression tests. Evidence: https://github.com/AndreVazao/DGM-MAT/actions/runs/39845826169. This does **not** mean the full repository suite passed, does not prove provider/browser integration, and is not a local Windows-PC runtime test. The importer remains limited to authorized ChatGPT JSON exports/ZIP intake; attachment files, provider connectors, startup orchestration, full-text search and cockpit integration remain pending.

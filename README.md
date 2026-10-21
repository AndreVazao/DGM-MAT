# DGM-MAT

> **Norma arquitetural vinculativa (2026-10-18):** a recuperação/unificação junta o trabalho do PC e do GitHub; **não junta as repos satélite**. DGM-MAT permanece o cérebro central soberano, os departamentos mantêm fronteiras modulares e o cockpit é opcional. Esta regra só pode ser alterada por aditamento explicitamente autorizado pelo proprietário.

Constituição arquitetural: [DGM-MAT Architecture Constitution — Modular Departments](docs/architecture/DGM-MAT-ARCHITECTURE-CONSTITUTION-MODULAR-DEPARTMENTS-2026-10-18.md). Esta é a referência normativa para modularidade, departamentos, dependências entre repos, escritório virtual e recuperação de conversações. Os documentos especializados continuam a ser complementares; documentação histórica não deve ser apagada sem inventário e preservação.

Inventário documental da recuperação e arquitetura: [DGM-MAT Recovery & Unification Inventory — 2026-10-18](docs/architecture/DGM-MAT-RECOVERY-UNIFICATION-INVENTORY-2026-10-18.md).

Modelo operacional canónico para end-to-end, departamentos multi-agent, especialização por linguagem, recuperação de conversas e expansão multi-PC: [Modelo Canónico de Operação, Departamentos e End-to-End (2026-10-21)](docs/architecture/DGM-MAT-CANONICAL-OPERATING-MODEL-END-TO-END-AND-DEPARTMENTS-2026-10-21.md). Este aditamento complementa — não substitui — a Constituição Arquitetural e a Diretiva Primária de Missão/Verdade.

Esquemática integral do escritório virtual, cockpit, pisos lógicos, contratos e avatar CEO: [Blueprint do Escritório Virtual (2026-10-21)](docs/architecture/DGM-MAT-VIRTUAL-OFFICE-SYSTEM-SCHEMATIC-2026-10-21.md) · [Diagrama SVG](docs/architecture/assets/dgm-mat-virtual-office-system-schematic.svg). A fotografia de referência do CEO é `1792476724975.jpg`; o avatar careca derivado permanece pendente de criação e aprovação.

DGM-MAT is the central engineering intelligence and orchestration system of the DevOps God Mode ecosystem.

## Current role

DGM-MAT is the current authority for the God Mode / AI-DevOps / multi-agent engineering family.

It is responsible for:
- repository and workspace intelligence;
- evidence-first technical audits;
- architecture and dependency analysis;
- project/grouping proposals;
- multi-agent engineering orchestration;
- controlled execution and approvals;
- runtime health and reality state;
- controlled self-diagnosis and self-repair;
- extracting useful concepts from legacy, lab and upstream repositories without blindly merging them.

## Operating principle

The system must operate in this order:

OBSERVE -> AUDIT -> CLASSIFY -> PLAN -> APPROVE WHEN REQUIRED -> APPLY -> VALIDATE -> RECORD

Audits are read-only. Structural operations such as moving, renaming, deleting, regrouping repositories, changing remotes, committing, pushing or triggering external workflows are never performed implicitly by the audit layer.

## Repository intelligence

DGM-MAT now contains its own evidence-first portfolio auditor:

- core/repository_intelligence/portfolio_auditor.py
- local Git state and origin inspection;
- repository metadata and commit count;
- language/manifest detection;
- README/purpose analysis;
- classification and logical project grouping;
- protected-path detection;
- risks and recommended action;
- read-only GitHub metadata lookup.

The canonical workspace is:

C:\\ProgramasGodMode

The frozen DGM-MAT-FULL-MIRROR is protected and must remain untouched.

## Self-repair

Controlled self-repair lives in:

core/self_healing/self_repair_engine.py

The repair engine separates diagnosis from mutation. Safe self-tests may run automatically; structural or authority-changing operations remain approval-gated.

## Governance API

The running DGM-MAT API exposes:

- GET /governance/audit/self
- GET /governance/audit/workspace
- GET /governance/repair/self/plan
- POST /governance/repair/self/apply

The API is intended to become the cockpit/mission entry point for future automated audit, repair and portfolio organization workflows.

## Ecosystem boundary

DGM-MAT may absorb knowledge, architecture, techniques and validated snippets from upstream, cloned, legacy and lab repositories.

The default flow is:

UPSTREAM / CLONE -> STUDY -> AUDIT -> EXTRACT CONCEPT -> REIMPLEMENT / ADAPT -> VALIDATE -> PRODUCT

Whole-repository copying is not the default.

## Family scope

All God Mode, AI DevOps and multi-agent engineering/programming work belongs to the DGM-MAT family.

Independent product families such as VAZÃO EVSE, ProVentil, Automotive and Sovereign Trader remain separate products even when they reuse DGM-MAT technology.

## Development policy

- stability > features;
- reality > assumptions;
- manual control > destructive automation;
- evidence before restructuring;
- small validated changes;
- every meaningful architectural conclusion is recorded in andreos-memory.

DGM-MAT is the sovereign engineering intelligence and runtime of the DevOps God Mode ecosystem. **The brain is primary. The Headquarters/cockpit is a read-only projection of what the brain is actually doing.**

## Authority and architecture boundaries

- **DGM-MAT brain:** owns reasoning, decisions, research, memory retrieval, task execution, agent lifecycle, approvals, runtime state, testing and controlled self-improvement.
- **Headquarters / cockpit:** visualizes verified runtime events, status and agent activity. It must not decide, orchestrate, authorize, or control the brain. Characters and animations are consequences of real activity, never the source of it.
- **Research laboratory:** receives third-party repositories only through an explicit, approved import for inspection, licensing/security review, tests and selective code/script reuse. No automatic cloning of satellite, private or unrelated repositories into the DGM-MAT workspace.
- **Persistent memory/archive:** preserves source provenance, conversations, decisions, context and supersession history; local retrieval is preferred over revisiting external AI websites.
- **AndreOS memory:** canonical cross-project memory and repository governance record: [AndreVazao/andreos-memory](https://github.com/AndreVazao/andreos-memory), local operational copy `C:\\AndreOS-Memory`.

## Current responsibilities

- repository/workspace intelligence and evidence-first audits;
- architecture and dependency analysis;
- multi-agent engineering and controlled execution;
- runtime health, event truth, diagnosis and repair;
- research and validated reuse from isolated lab material;
- conversation ingestion, searchable memory and provenance;
- controlled self-improvement with validation and approval boundaries.

## Operating principle

`OBSERVE -> AUDIT -> CLASSIFY -> PLAN -> APPROVE WHEN REQUIRED -> APPLY -> VALIDATE -> RECORD`

Audits are read-only. Moving, renaming, deleting, regrouping repositories, changing remotes, committing, pushing, cloning external code, or triggering workflows must never happen implicitly. Preserve unmerged work and user changes before cleanup.

## Repository intelligence

The evidence-first portfolio auditor lives under `core/repository_intelligence/` and should inspect local Git state, remotes, metadata, manifests, README purpose, dependencies, protected paths and risks before recommending a change.

Canonical development workspace: `C:\\ProgramasGodMode`.

`DGM-MAT-FULL-MIRROR` is explicitly protected and must remain untouched.

## Self-repair

Controlled self-repair lives under `core/self_healing/self_repair_engine.py`. Diagnosis is separate from mutation. Safe self-tests may run automatically; destructive or authority-changing operations remain approval-gated.

## Governance API

The runtime exposes self/workspace audit and repair-plan/apply endpoints under `/governance/`. These APIs belong to the brain. A cockpit may display their verified outputs, but must not become a second authority or silently trigger privileged actions.

## External code reuse

`DGM-MAT-Labs` is the designated external-code laboratory. Imports must be explicit and reviewed; never clone private or satellite repositories automatically. The default flow is:

`APPROVED IMPORT -> ISOLATE -> STUDY -> REVIEW LICENSE/SECURITY -> TEST -> EXTRACT CONCEPT -> ADAPT -> VALIDATE -> PRODUCT`

Do not execute untrusted code by default. Whole-repository copying is not the default.

## Conversation archive direction

Audit the current persistence implementation before adding a second one. Target a local-first searchable archive that preserves original exports and normalizes conversation/message records with provider, source IDs, timestamps, role, content and provenance. SQLite with full-text search is the initial candidate, not an assumption that should override an existing proven implementation. Keep summaries, decisions, project links and supersession metadata separate from source messages. Retrieve local records first; contact external AI websites only when needed.

## Satellite and product boundaries

- `DGM-Cockpit-Frontend`: presentation-only cockpit.
- `DGM-MAT-Mobile`: lightweight remote chat/cockpit; PC brain remains the execution authority.
- `DGM-Contracts`: public shared contracts only.
- `DGM-MAT-Deploy`: minimal node discovery/rendezvous; not an execution plane or conversation store.
- `DGM-MAT-Agents`: standalone agents only while the migration boundary remains validated.
- `DGM-MCP` and `DGM-HUB`: separate projects, not silently merged into the core.
- Keep only satellites with a verified purpose and consumer. Do not add dependencies merely because a repository exists.

The live repository inventory, retention recommendations and consolidation gate are maintained in [the canonical memory governance record](https://github.com/AndreVazao/andreos-memory/blob/main/AndreOS/02_PROJETOS/DGM-MAT/REPOSITORY_GOVERNANCE_AND_CONSOLIDATION_2026-10-18.md).

## Development policy

- stability > features;
- reality > assumptions;
- manual control > destructive automation;
- evidence before restructuring;
- preserve history and unmerged work;
- small validated changes;
- record meaningful decisions in `andreos-memory`;
- prefer local validation and do not add/run GitHub Actions workflows without a specific approved need.

## Primary mission

Recover and organize conversation memory and documentation before non-urgent engineering work. Always distinguish user requests, AI proposals, current decisions, superseded solutions and verified reality. Preserve provenance and temporal evolution; never let legacy/superseded material silently govern current work.

Historical mission reference: [DGM-MAT_PRIMARY_MISSION_AND_EVOLVING_TRUTH_2026-10-10.md](docs/DGM-MAT_PRIMARY_MISSION_AND_EVOLVING_TRUTH_2026-10-10.md). Do not bulk-delete historical documentation: inventory, classify, link successors and preserve backups first.

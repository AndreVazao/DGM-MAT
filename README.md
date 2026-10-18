# DGM-MAT

> **Norma arquitetural vinculativa (2026-10-18):** a recuperação/unificação junta o trabalho do PC e do GitHub; **não junta as repos satélite**. DGM-MAT permanece o cérebro central soberano, os departamentos mantêm fronteiras modulares e o cockpit é opcional. Esta regra só pode ser alterada por aditamento explicitamente autorizado pelo proprietário.

Constituição arquitetural: [DGM-MAT Architecture Constitution — Modular Departments](docs/architecture/DGM-MAT-ARCHITECTURE-CONSTITUTION-MODULAR-DEPARTMENTS-2026-10-18.md). Esta é a referência normativa para modularidade, departamentos, dependências entre repos, escritório virtual e recuperação de conversações. Os documentos especializados continuam a ser complementares; documentação histórica não deve ser apagada sem inventário e preservação.

Inventário documental da recuperação e arquitetura: [DGM-MAT Recovery & Unification Inventory — 2026-10-18](docs/architecture/DGM-MAT-RECOVERY-UNIFICATION-INVENTORY-2026-10-18.md).

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

## Autonomous engineering mission

DGM-MAT is intended to operate as the user's autonomous engineering counterpart: ingesting AI conversations, classifying them by project, extracting code with provenance, checking code against context, consolidating duplicate implementations, detecting syntax/structural defects, auditing incomplete repositories, implementing approved repairs, testing, validating, and recording outcomes in persistent memory.

Conversation intelligence is implemented under `core/conversation_intelligence/` and exposed through `POST /governance/conversations/analyze`.

Microsoft Project Telescope is installed locally as an observability source for AI coding agents and MCP activity. Vercel project `dgm-mat-rendezvous` provides node discovery so the home PC and mobile cockpit can find each other without manually entering IP addresses.


## Diretiva primária vigente — 2026-10-10

A prioridade operacional atual é **recuperar e reorganizar primeiro a memória das conversas e a documentação**, antes de novo trabalho de engenharia não urgente. DGM-MAT deve separar sempre pedidos do utilizador, respostas/propostas das IAs, decisões vigentes e realidade verificada. Reconstrói a evolução temporal, atualiza o contexto quando pedidos posteriores substituem soluções antigas, preserva a razão e a proveniência e impede que conteúdo LEGACY/SUPERSEDED volte a orientar o trabalho.

Norma completa: [DGM-MAT_PRIMARY_MISSION_AND_EVOLVING_TRUTH_2026-10-10.md](docs/DGM-MAT_PRIMARY_MISSION_AND_EVOLVING_TRUTH_2026-10-10.md).

Não apagar documentação histórica em lote: inventariar, classificar, ligar sucessores e criar backup antes de qualquer remoção definitiva. A prioridade antiga de engenharia continua válida apenas quando compatível com esta diretiva.

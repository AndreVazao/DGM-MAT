# DGM-HUB / DGM-MCP — Role Decision Checkpoint

Date: 2026-10-06

## User clarification

The user no longer remembers the original purpose of DGM-HUB. Therefore DGM-HUB must NOT be treated as an assumed DGM-MAT dependency or architectural authority. Its role is determined only by audited evidence.

The user clearly remembers DGM-MCP as a tool intended to let an AI/system operate on the PC: filesystem, commands, PowerShell, Git/repository operations, tests and related machine actions. This matches the audited implementation: an MCP-facing tool registry/adapter over a guarded runtime with filesystem, command, PowerShell, repository, test and Git tools.

## DGM-HUB decision

Classification: LEGACY / RESEARCH / REUSE SOURCE.

Do not merge DGM-HUB wholesale into DGM-MAT.
Do not make DGM-MAT depend on DGM-HUB.
Do not delete or modify it during this migration stage.

Evidence from previous runtime audits:
- main entrypoint: run_dgm_hub.py -> AgentLoop
- alternate entrypoints: cognitive agent, HTTP bridge, UI, task runner
- RuntimeSession/TaskExecutor coordinate repository execution
- UnifiedToolManager exposes filesystem, command, PowerShell, repository, test and Git tools
- TruthLayer provides repository truth/hash/HEAD verification concepts
- PatchOrchestrator/ApprovalEngine/PatchApplyEngine provide patch execution concepts
- many parallel autonomous/repair/evolution engines are shadow or duplicated
- PatchApplyEngine uses destructive git rollback (git checkout . / git clean -fd), which conflicts with DGM-MAT's manual-control/non-destructive principle

Therefore DGM-HUB is valuable primarily as an archaeological source for patterns, comparisons and lessons learned. Reuse must be symbol-level and reimplemented behind DGM-MAT public contracts.

## DGM-MCP decision

Classification: SPECIALIZED SYSTEM / PC CONTROL AND MCP INTEGRATION BOUNDARY.

DGM-MCP should be treated as the historical implementation of the PC-operation/tool boundary, not as a generic AI core.

Observed responsibilities:
- MCP protocol lifecycle and JSON-RPC handling
- tool registry and tool metadata
- tool adapter / dispatch
- filesystem tools
- command and PowerShell execution
- repository/Git operations
- test execution
- PathGuard security boundary
- audit/logging/runtime telemetry

Architectural destination candidate:
- MCP protocol adapter -> DGM-MAT-Connectors or a dedicated MCP boundary
- public tool contracts/schemas -> DGM-Contracts
- PC-operation implementations -> controlled DGM-MAT execution/tool subsystem
- security policy/path guarding -> DGM-Core-Backend security boundary
- provider-specific integrations remain Providers, not MCP

Important distinction:
DGM-MCP is a mechanism for operating the machine. It must not become the owner of DGM-MAT business state, mission state, autonomy state, memory, or orchestration.

## DGM-MAT target relationship

Preferred direction:

Cockpit / Agent / external client
        |
        v
DGM-MAT public contracts
        |
        v
Execution / Tool boundary
        |
        +--> local filesystem
        +--> PowerShell / command execution
        +--> Git / repository operations
        +--> test runners
        +--> other controlled PC tools

MCP is one transport/interface into that execution boundary, not the authority behind it.

MissionEngine, CognitionLoop, EventBus, RuntimeStateStore and persistent domain storage remain DGM-MAT authorities.

## Required next audit

Before any physical migration:
1. Compare DGM-MCP ToolRegistry/ToolAdapter/PathGuard/AuditLogger against DGM-MAT connectors/providers/plugins/security/tools.
2. Identify exactly which DGM-MAT components should own PC operations.
3. Define one execution contract so Cockpit, agents and MCP cannot each invent separate execution paths.
4. Compare DGM-HUB AgentLoop/ToolReasoner/PatchOrchestrator/TruthLayer against DGM-MAT autonomy/execution/governance/recovery only to recover reusable concepts and eliminate duplicates.
5. Update the final ownership matrix before M3/M4 migration work.

## Safety

DGM-MAT-FULL-MIRROR remains untouched and read-only.
No physical migration has been performed from this decision checkpoint.

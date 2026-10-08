
# DGM-HUB / DGM-MCP INTEGRATION AUDIT
## 2026-10-06

> Auditoria de sistemas reais externos ao DGM-MAT. Nenhum código movido.

## DGM-HUB

Observed domains:
- core/truth_layer.py: TruthSnapshot + repository hashing + git HEAD verification; candidate reference for integrity/truth concepts.
- agent/agent_loop.py: AgentLoop coordinates RuntimeSession, ToolReasoner, PatchOrchestrator, ErrorAnalyzer, FileLoader, ReviewGate and Telemetry.
- execution/patch_apply.py: PatchApplyEngine uses PermissionManager + TruthLayer and performs destructive git rollback on exception.
- execution contains command runner, diff/error analysis, file loading, patch proposal/apply and test pipeline.
- agent contains several overlapping autonomous/evolution/self-repair engines.

Preliminary decision:
- DGM-HUB is a legacy/research system with reusable patterns, not a direct production dependency.
- TruthLayer concepts may inform DGM-MAT Core governance/observability, but must be reimplemented behind DGM-MAT contracts rather than imported from DGM-HUB.
- AgentLoop overlaps DGM-MAT agents/autonomy/development and must be compared symbol-by-symbol before any promotion.
- PatchApplyEngine is NOT safe to promote unchanged: its snapshot verification occurs immediately after mutation, so normal mutation can be interpreted as truth violation; its rollback uses git checkout . and git clean -fd, which conflicts with DGM-MAT's manual-control/non-destructive principle.

## DGM-MCP

Observed domains:
- mcp/adapter.py: validates tool arguments with JSON Schema and invokes runtime tools.
- mcp/tool_registry.py: public tool registry with listing/pagination.
- core/runtime.py: owns PathGuard, AuditLogger, tool registration, TaskManager, Worker, CognitiveAgent, LLMManager and observability.
- security/path_guard.py: resolved-path whitelist enforcement including traversal/symlink escape protection.
- tools include filesystem, git, shell, patch and repo operations.

Preliminary decision:
- DGM-MCP is a real integration/runtime system, not a shell and not a Lab.
- Its strongest reusable boundary is the MCP protocol/tool adapter/registry/security contract.
- It should remain a specialized repo until DGM-MAT-Connectors or a dedicated MCP boundary is defined.
- DGM-MAT must not import DGM-MCP private runtime classes. Integration should be protocol/API/contract based.
- PathGuard/AuditLogger patterns are valuable security references for DGM-MAT connectors and tools.

## Cross-system dependency check
- No direct textual imports from dgm_hub or dgm_mcp were found inside DGM-MAT.
- No direct textual imports from dgm_mat were found in DGM-HUB or DGM-MCP.
- Therefore these systems are currently parallel codebases, not hard runtime dependencies.

## Required next comparison
1. Compare AgentLoop/ToolReasoner/PatchOrchestrator with DGM-MAT agents/autonomy/development/execution.
2. Compare DGM-HUB TruthLayer with DGM-MAT RuntimeStateStore/RealitySnapshot/validation/recovery.
3. Compare DGM-MCP ToolRegistry/ToolAdapter/PathGuard with DGM-MAT providers/connectors/plugin boundaries.
4. Identify reusable algorithms and contracts, not repositories to copy.
5. Promote only after isolated tests prove equivalence or improvement.

## Safety
FULL-MIRROR untouched. No DGM-HUB or DGM-MCP source was changed.
# DGM-MAT Internal Architecture Reuse Audit — 2026-10-08

## Scope

Comparison of canonical DGM-MAT against the independent DGM-HUB and DGM-MCP repositories.

Rule: DGM-HUB and DGM-MCP remain independent repositories. No direct runtime dependency or source copy is introduced by this audit.

## Findings

### 1. Truth / reality verification

DGM-HUB provides `TruthLayer`, which snapshots Git HEAD plus SHA-256 hashes of repository files and can detect drift.

DGM-MAT already has a stronger system-level equivalent:
- `core/runtime/reality_snapshot.py`
- `core/runtime/runtime_state_store.py`
- `core/runtime/runtime_path_validator.py`
- runtime health/degradation/recovery layers

Conclusion: do not import DGM-HUB TruthLayer. Its useful algorithmic idea is already represented at DGM-MAT level, while DGM-MAT covers runtime, providers, repositories, processes, canonical paths and governed queue state.

Potential future improvement: add explicit immutable/hash-based execution evidence to the DGM-MAT execution/validation pipeline where useful. This should be a focused change, not a source transplant.

### 2. Agent loop / autonomous development

DGM-HUB contains a large AgentLoop family, ToolReasoner, patch orchestration, error analysis and autonomous repair components.

DGM-MAT already has broader governed equivalents across:
- `core/agents`
- `core/autonomy`
- `core/development`
- `core/execution_fabric`
- `core/governance`
- `core/self_evolution`
- `core/recovery`

Conclusion: no direct import. DGM-HUB is useful as an algorithmic reference for focused repair loops and tool-selection heuristics, but DGM-MAT must remain the canonical orchestration/governance layer.

### 3. Tool management / security

DGM-HUB has UnifiedToolManager, ToolRegistry and PathGuard.
DGM-MCP has BaseTool, PathGuard and audited tool execution.

DGM-MAT already has connector/provider boundaries, governance, SafeActionQueue, execution controls and repository/worktree isolation.

Important distinction:
- DGM-HUB/MCP demonstrate reusable patterns for explicit tool contracts and path validation.
- DGM-MAT must not duplicate their tool registries or introduce unrestricted command execution into the canonical runtime.

Conclusion: retain the repositories as independent capability sources. Reuse contracts/patterns only after isolated tests prove a concrete gap.

### 4. Concrete DGM-MAT debt discovered

Two DGM-MAT modules are currently placeholders and are not referenced by other Python files found in the core tree:

- `core/development/test_orchestrator.py`
  - `run_suite()` logs the request and always returns True.
- `core/execution_fabric/validation_pipeline.py`
  - `validate_result()` logs the execution and always returns True.

These are not acceptable as authoritative validation mechanisms under the DGM-MAT principle "reality > assumptions".

They were not modified in this audit because they are currently unreferenced and changing them without first establishing their intended contract could create unnecessary instability.

Recommended next action: either remove/quarantine these dead placeholders or replace them with real adapters over the existing tested validation/test infrastructure, with explicit tests.

## Decision

No DGM-HUB or DGM-MCP code was imported into DGM-MAT.

The useful capabilities are classified as:
- Truth verification: already covered by DGM-MAT, with possible evidence-hardening opportunity.
- Agent/tool reasoning: reference only.
- Path/tool security: reference only; existing DGM-MAT governance remains authoritative.
- Test/validation: DGM-MAT has two suspicious dead placeholders requiring cleanup/contract clarification.

## Stability rule

Do not increase DGM-MAT surface area merely because another repository contains a similar module. Prefer consolidation, deletion of dead code, or narrow tested adapters over duplication.

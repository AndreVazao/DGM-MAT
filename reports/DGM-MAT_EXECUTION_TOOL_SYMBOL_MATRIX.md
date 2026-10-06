# DGM-MAT — Execution / Tool / HUB Symbol-Level Comparison

Date: 2026-10-06
Status: architectural audit; no physical migration.

## Executive decision

DGM-MCP is the strongest historical implementation of the PC operation boundary. DGM-MAT currently contains several overlapping execution mechanisms. We will reuse DGM-MCP boundaries by contract, not copy the repository wholesale.

DGM-HUB is a reference source only. Useful concepts are truth snapshots, agent-loop composition and patch review. Its ToolReasoner is skeletal and its patch flow is not suitable as a DGM-MAT authority.

## Ownership decisions

- MCP transport / JSON-RPC -> DGM-MAT-Connectors.
- ToolDescriptor and public tool schemas -> DGM-Contracts.
- Executable tool registry and dispatch -> DGM-Core-Backend execution boundary.
- Path authorization -> DGM-Core-Backend Security.
- Machine-action audit -> DGM-Core-Backend Observability.
- Filesystem, command, Git, repository and patch operations -> one controlled DGM-Core-Backend execution boundary.
- Approval -> one durable DGM-MAT authority; current overlapping models must converge.
- Worktree/branch management -> DGM-Core-Backend execution.
- Truth/drift verification -> DGM-Core-Backend verification, informed by HUB TruthLayer.
- Agent reasoning and orchestration -> DGM-MAT Autonomy/Agents.
- LLM providers -> DGM-MAT Providers.
- Domain memory -> DGM-MAT Memory.
- Runtime lifecycle/state -> DGM-MAT Core/Runtime.

## Public contract to establish

ExecutionRequest: request_id, actor, tool_name, operation, arguments, target, risk, approval requirement, idempotency key, timeout, correlation_id.

ExecutionResult: request_id, success, status, message, structured data, error, timestamps, duration, audit reference.

ToolDescriptor: name, description, input schema, capabilities, risk class, allowed transports.

MCP must become an adapter to this boundary. It must not own mission state, autonomy state, memory or orchestration.

## First authoritative migration matrix

| FILE | ROLE | CURRENT | DESTINATION | REWRITE | AUTHORITY |
|---|---|---|---|---|---|
| dgm_mcp/mcp/adapter.py | MCP dispatch | DGM-MCP | DGM-MAT-Connectors | dispatch through ExecutionRequest | Connectors |
| dgm_mcp/mcp/tool_registry.py | tool catalog | DGM-MCP | DGM-Contracts + Core execution | split descriptor from runtime registry | Contracts/Core |
| dgm_mcp/security/path_guard.py | path policy | DGM-MCP | DGM-Core-Backend/security | policy/config abstraction | Core Security |
| dgm_mcp/security/audit_logger.py | action audit | DGM-MCP | DGM-Core-Backend/observability | structured journal/event | Core Observability |
| dgm_mcp/tools/base_tool.py | tool result contract | DGM-MCP | DGM-Contracts + Core execution | replace private result type | Contracts |
| dgm_mcp/tools/filesystem_tool.py | filesystem | DGM-MCP | Core execution/tools | centralize | Execution |
| dgm_mcp/tools/shell_tool.py | command execution | DGM-MCP | Core execution | centralize with policy | Execution/Security |
| dgm_mcp/tools/git_tool.py | Git operations | DGM-MCP | Core workspace/execution | route through policy/approval | Workspace/Execution |
| dgm_mcp/tools/repo_tool.py | repository operations | DGM-MCP | Core workspace | centralize | Workspace |
| dgm_mcp/tools/patch_tool.py | patch preview/write | DGM-MCP | Core execution | durable proposal + approval | Execution |
| core/local_runtime/local_executor.py | local commands | DGM-MAT | Core execution | merge into common service | Execution |
| core/autonomy/safe_autonomous_executor.py | safe commands | DGM-MAT | Core execution/security | policy layer over common service | Security/Execution |
| core/execution/approval_manager.py | approval | DGM-MAT | Core durable approval | remove process-local authority | Approval |
| core/execution/execution_engine.py | worktree execution | DGM-MAT | Core execution | minimal | Execution |
| core/autonomy/mission_engine.py | mission authority | DGM-MAT | Core autonomy | preserve, later boundary rewrite | Mission authority |
| core/runtime/safe_action_queue.py | durable actions | DGM-MAT | Core runtime/execution | keep; unify approval semantics | Runtime/Execution |
| core/runtime/runtime_state_store.py | runtime projection | DGM-MAT | Core runtime | clarify as projection | Runtime |
| DGM-HUB/agent/agent_loop.py | agent orchestration | DGM-HUB | reference only | do not migrate wholesale | DGM-MAT Autonomy |
| DGM-HUB/agent/tool_reasoner.py | heuristic tool selection | DGM-HUB | reference only | reimplement only if useful | DGM-MAT Agents |
| DGM-HUB/agent/patch_orchestrator.py | patch flow | DGM-HUB | reference only | reuse concepts behind contracts | Core Execution |
| DGM-HUB/core/truth_layer.py | truth snapshot | DGM-HUB | reference -> Core verification | reimplement safely | Core Verification |

## Risks confirmed

1. DGM-MAT has multiple command-execution paths.
2. DGM-MAT has multiple approval authorities.
3. DGM-MCP hardcodes tool schemas inside its adapter; these belong in Contracts.
4. DGM-MCP Git mutation can bypass a higher-level approval policy.
5. Path security alone is insufficient; command, repository and operation risk must also be governed.
6. HUB TruthLayer is useful for drift detection, but unchanged snapshots cannot be the success criterion after an intentional edit.
7. HUB ToolReasoner is not mature enough to become an authority.

## Migration gate

Do not extract physical code until the execution contract, approval authority, command service, security policy and patch lifecycle are unified; MissionEngine to SafeActionQueue cross-process behavior is proven; Cockpit private Core imports are removed; and the final ownership matrix is updated.

DGM-MAT-FULL-MIRROR remains untouched.

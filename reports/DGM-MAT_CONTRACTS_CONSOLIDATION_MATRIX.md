# DGM-MAT Contracts Consolidation Matrix

Date: 2026-10-06
Status: IMPLEMENTATION STARTED / NO PHYSICAL MIGRATION

Contracts become the stable language between Core, Agents, Connectors, Providers and Cockpit. Existing runtime/storage models are evidence, not automatically authoritative.

| CURRENT TYPE / FILE | SEMANTIC ROLE | CURRENT OWNER | TARGET CONTRACT | PROCESS BOUNDARY | MIGRATION RISK |
|---|---|---|---|---|---|
| core/autonomy/mission_models.py :: Mission | durable mission domain state | Core Autonomy | MissionReference + MissionState | mission storage/API | HIGH |
| core/runtime/safe_action_queue.py :: ActionStatus | durable execution lifecycle | Core Runtime | ExecutionStatus | SQLite/cross-process | HIGH |
| core/storage/models.py :: ActionRecord | durable queued action | Core Storage | ExecutionRequest persistence envelope | SQLite/cross-process | VERY HIGH |
| core/execution/approval_manager.py :: ApprovalStatus | process-local approval | Core Execution | ApprovalRequest/Decision | must become durable | VERY HIGH |
| mission_engine.py :: pending_approvals | legacy approval state | Core Autonomy | remove as authority | currently unsafe cross-process | VERY HIGH |
| DGM-MCP ToolDefinition | public tool metadata | DGM-MCP | ToolDescriptor | API/MCP boundary | HIGH |
| DGM-MCP adapter schemas | transport-owned schema | DGM-MCP | ToolDescriptor adapter | transport boundary | HIGH |
| shared/models/event.py :: Event | event envelope | shared/Core | EventEnvelope | event boundary | VERY HIGH |
| core/storage/models.py :: EventRecord | durable event projection | Core Storage | EventStore persistence derived from EventEnvelope | SQLite | HIGH |
| EventBus queue | process-local routing | Core | internal implementation | process-local | MEDIUM |
| RuntimeStateStore | process-local projection | Core Runtime | RuntimeSnapshot/projection | process-local | HIGH |

## Authoritative contracts

- ExecutionRequest: semantic execution request; SafeActionQueue stores a durable representation.
- ExecutionResult: normalized execution outcome.
- ToolDescriptor: public tool capability/schema metadata.
- ApprovalRequest / ApprovalDecision: durable approval vocabulary.
- EventEnvelope: public event vocabulary.
- MissionReference / MissionState: cross-process mission identity/lifecycle.

## Decisions

1. SafeActionQueue is the leading candidate for one durable execution/approval authority, but is not itself the public contract.
2. ApprovalManager and MissionEngine.pending_approvals must converge on that durable authority.
3. EventBus is process-local routing; EventStore is persistence; RuntimeStateStore is projection only.
4. MCP is transport/integration, not DGM-MAT authority.
5. Contracts must not import Core storage/filesystem/provider implementations.
6. Physical repository extraction waits for compatibility adapters and cross-process lifecycle tests.

## Implementation checkpoint

DGM-Contracts now contains the first contract package and serialization tests. DGM-MAT autonomy tests were repaired where they asserted an obsolete .runtime/runtime_state.json artifact instead of the actual scheduler behavior. The repaired focused suite is green: 4 passed.

FULL-MIRROR remains untouched.

## Next gate

Build compatibility adapters in DGM-MAT, then prove durable approval and cross-process mission execution. Only after those gates pass will repository extraction begin.

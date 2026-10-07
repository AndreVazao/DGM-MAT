# DGM-MAT Contracts Consolidation Matrix

Date: 2026-10-06
Status: IMPLEMENTATION CHECKPOINT / NO PHYSICAL MIGRATION

## Decision
Contracts become the stable language between Core, Agents, Connectors, Providers and Cockpit. Existing runtime/storage models are evidence, not automatically authoritative.

## Matrix

| CURRENT TYPE / FILE | SEMANTIC ROLE | CURRENT OWNER | DUPLICATES / OVERLAP | TARGET CONTRACT | READERS | WRITERS | PROCESS BOUNDARY | MIGRATION RISK | TESTS |
|---|---|---|---|---|---|---|---|---|---|
| core/autonomy/mission_models.py :: Mission | durable mission domain state | Core Autonomy | MissionEngine in-memory + JSON persistence + API projection | MissionReference + MissionState | MissionEngine, API, CognitionLoop, UI | MissionEngine | Cross-process via mission storage/API | HIGH | mission serialization, reload, lifecycle |
| core/autonomy/mission_models.py :: SubTask | mission decomposition item | Core Autonomy | autonomous task models elsewhere | SubTask contract | MissionEngine, agents | MissionEngine/agents | Cross-process if exposed | MEDIUM | serialization, assignment |
| core/runtime/safe_action_queue.py :: ActionStatus | durable execution lifecycle | Core Runtime | MissionStatus, ApprovalStatus | ExecutionStatus | queue, API, execution | queue | Cross-process durable | HIGH | state transitions, concurrency |
| core/storage/models.py :: ActionRecord | durable queued action | Core Storage | SafeActionQueue payload + approval fields | ExecutionRequest persistence envelope | SafeActionQueue, API | SafeActionQueue | SQLite / cross-process | VERY HIGH | restart/reload, approval, exactly-once guard |
| core/execution/approval_manager.py :: ApprovalStatus | compatibility view over durable approval | Core Execution | ActionRecord approval | ApprovalStatus + ApprovalRequest/Decision | API, Core | SafeActionQueue | Durable | HIGH | approval persistence, duplicate decisions |
| core/autonomy/mission_engine.py :: pending_approvals | legacy process-local approval | Core Autonomy | ApprovalManager, ActionRecord | REMOVE AS AUTHORITY; use ApprovalRequest | runtime API, mission flow | currently MissionEngine | Cross-process currently unsafe | VERY HIGH | restart between request/decision |
| core/execution/execution_models.py :: ExecutionTask | minimal execution DTO | Core Execution | SafeActionQueue ActionRecord | superseded by ExecutionRequest/Result | execution code | execution code | process-local today | HIGH | schema validation |
| DGM-MCP mcp/tool_registry.py :: ToolDefinition | public tool metadata + input schema | DGM-MCP | adapter hardcoded schemas | ToolDescriptor | MCP, Core, Agents, Cockpit | tool registration | cross-process/API | HIGH | schema roundtrip, listing |
| DGM-MCP mcp/adapter.py :: _schema_for | transport-bound tool schema | DGM-MCP | ToolDefinition | REMOVE DUPLICATE; consume ToolDescriptor | MCP adapter | none | transport boundary | HIGH | MCP list/call compatibility |
| DGM-MCP tool result model (runtime tool results) | execution result | DGM-MCP | MCP response envelope | ExecutionResult + transport adapter | Connectors, MCP, agents | execution service | cross-process | HIGH | success/error/structured data |
| shared/models/event.py :: Event | event envelope | shared/Core | EventRecord + state broadcasts + mission result payload | EventEnvelope | Core, Cockpit, Agents, Connectors | EventBus | cross-process/event boundary | VERY HIGH | validation, persistence, replay |
| core/storage/models.py :: EventRecord | durable event projection | Core Storage | EventEnvelope fields | EventStore persistence model derived from EventEnvelope | EventStore | EventStore | SQLite | HIGH | persist/reload/replay |
| core/event_bus/event_bus.py :: EventBus queue | process-local routing | Core EventBus | EventStore + realtime stream | Internal transport implementation; not public contract | subscribers | EventBus | process-local | MEDIUM | ordering, dedup, DLQ |
| core/observability/event_stream.py | live event adapter | Core Observability | WebSocket/realtime | EventEnvelope -> live projection | Cockpit | stream adapter | process/API boundary | HIGH | reconnect/replay semantics |
| core/runtime/runtime_state_store.py | process-local state projection | Core Runtime | mission JSON + API | RuntimeSnapshot (projection only) | API/Cockpit | runtime components | process-local | HIGH | restart must reconstruct |

## Proposed authoritative contracts

### ExecutionRequest
Fields: request_id, actor/source, tool_name, operation, arguments, target/resource, risk_class, approval_requirement, idempotency_key, timeout, correlation_id, mission_id optional, created_at.

### ExecutionResult
Fields: request_id, success, status, message, stdout, structured_data, error, started_at, completed_at, duration_ms, audit_event_id, correlation_id.

### ToolDescriptor
Fields: name, description, input_schema, capabilities, risk_class, approval_policy, allowed_transports, version.

### ApprovalRequest
Fields: approval_id, request_id/mission_id, requested_by, operation summary, diff/preview optional, risk_class, impact, created_at, expires_at, status.

### ApprovalDecision
Fields: approval_id, decision, decided_by, decided_at, reason, correlation_id.

### EventEnvelope
Fields: event_id, timestamp, source, target, event_type, payload, priority, scope, domain, ttl, ecosystem, trace_id, parent_trace_id, depth, schema_version.

### MissionReference / MissionState
Mission identity and lifecycle are separated from the full mutable Mission aggregate. Cross-process consumers should not depend on MissionEngine.active_missions.

## Key design decisions

1. ExecutionRequest is the higher-level semantic request. SafeActionQueue stores a durable execution record containing the request envelope; the queue is not the public contract itself.
2. SafeActionQueue is the leading candidate for the single durable execution/approval authority, but its schema must be upgraded and tested before it is declared authoritative.
3. ApprovalManager and MissionEngine.pending_approvals must not remain independent authorities.
4. EventEnvelope is public; EventBus is an implementation; EventRecord is persistence.
5. RuntimeStateStore is a projection, never source of truth.
6. MCP remains a transport/integration boundary. MCP-specific response formatting must adapt to ExecutionResult instead of defining a second execution model.
7. Contracts must not import Core storage, filesystem, database, or provider implementations.
8. No new contract code is promoted until cross-process serialization and lifecycle tests pass.

## Implemented checkpoint â€” 2026-10-06
- DGM-Contracts package is operational and contains the public schemas.
- DGM-MAT has compatibility adapters for queue actions, approvals, events and missions.
- DGM-MCP ToolDefinition -> ToolDescriptor is implemented as a one-way adapter without importing DGM-MCP internals.
- MissionEngine no longer owns a `pending_approvals` dictionary; approval entry points delegate to durable storage through ApprovalManager.
- Duplicate SafeActionQueue approval implementation was removed.
- Focused contract/queue/cross-process suite: 10 passed.

## Immediate next implementation gate
Consolidate Event -> EventEnvelope -> EventStore/EventBus with persistence and replay tests, then run the broader regression suite before any physical repository extraction.

## 2026-10-07 — Event contract gate completed
- Event -> EventEnvelope conversion is now the public event boundary.
- EventStore persists the complete envelope and supports get/replay.
- Existing SQLite event tables receive envelope_json non-destructively.
- Legacy records remain readable.
- EventBus/live stream use the complete contract projection.
- Focused validation: 13 passed.

Next gate: broader regression suite. Physical extraction remains blocked until that validation passes.

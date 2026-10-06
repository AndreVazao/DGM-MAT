# DGM-MAT — File Ownership & Migration Matrix

This is the semantic ownership layer over the factual dependency graph in reports/dgm_mat_dependency_graph.json.

## Ownership rules

| Current area | Target | Authority | Main rewrite |
|---|---|---|---|
| core/api | API boundary / DGM-Cockpit-Frontend boundary | API contracts | imports become contract/service calls |
| core/agents | DGM-MAT-Agents | Agent contracts | agents stop importing private internals |
| core/storage | DGM-Core-Backend | Core persistence interfaces | storage contracts become explicit |
| core/runtime | DGM-Core-Backend or DGM-MAT-Runtime after proof | runtime contract | separate durable state from process state |
| core/autonomy | DGM-Core-Backend initially | mission/task contracts | queue and mission boundaries |
| core/event_bus | DGM-Core-Backend initially | event contracts | Event envelope moves to DGM-Contracts |
| core/realtime | cockpit/runtime boundary | websocket contract | UI transport decoupled from core |
| core/providers | DGM-MAT-Providers | provider contract | provider adapters behind interface |
| core/connectors | DGM-MAT-Connectors | connector contract | external integrations isolated |
| core/memory | DGM-MAT-Memory | memory contract | global AndreOS memory remains external authority |
| core/knowledge + knowledge_graph | Memory/Core after dependency proof | semantic-memory contract | remove direct filesystem assumptions |
| core/cognition | Core initially | cognition contract | split only when independent |
| core/kernel | Core | kernel contract | retain nucleus until proven otherwise |
| core/governance + security | Core | governance policy | no UI ownership |
| core/observability + telemetry | Core | observability contract | shared event/log/metric interfaces |
| core/workspace + repository_* | Core initially | workspace/repository service | later split only if independent |
| core/autonomous_dev | Core initially | development execution contracts | avoid duplicate execution engines |
| core/evolution + self_evolution | Core initially | evolution policy | review duplication before split |
| core/recovery + self_healing | Core/runtime | recovery contract | one recovery authority |
| core/distributed + federation + fabric | Cluster/Orchestrator candidate | node/federation contracts | do not move until active dependency proof |
| core/import_fabric + migration | Core tooling | migration contracts | keep migration machinery together |
| core/planning + strategy | Core | planning contracts | consolidate duplicate planners |
| core/research + labs | DGM-MAT-Labs candidate | experimental boundary | no production authority |
| cockpit/ | DGM-Cockpit-Frontend | HTTP/WebSocket contracts | remove core-private imports |
| shared/models + shared/enums + shared/config | DGM-Contracts | public contracts | eliminate shared implementation logic |
| scripts/ | DGM-MAT root/Deploy/Docs depending function | operational contract | scripts must target public interfaces |
| tests/ | follow tested component | component owner | imports rewritten with migration |
| embedded DGM-MAT-* dirs | corresponding satellite repo only after content verification | repo contract | do not infer from name |

## Critical file ownership

| File | Role | Target | Reads/Writes | Key dependencies | Risk |
|---|---|---|---|---|---|
| core/api/api_server.py | API application root | API boundary | reads routers; serves HTTP/WS | runtime/mobile routers | HIGH |
| core/api/runtime_api.py | runtime API | API boundary | reads truth, missions, queue, providers | many Core services | VERY HIGH |
| core/api/mobile_bridge.py | mobile transport | API boundary | websocket I/O | realtime | HIGH |
| core/autonomy/mission_engine.py | mission authority | Core | mission JSON, queue, state, broadcast | storage/queue/runtime | VERY HIGH |
| core/autonomy/mission_models.py | mission DTO/state | DGM-Contracts | model only | MissionEngine/tests | HIGH |
| core/runtime/safe_action_queue.py | durable action executor | Core Runtime | SQLite | storage/logger | VERY HIGH |
| core/runtime/runtime_state_store.py | process-local runtime snapshot | Core Runtime | memory only | logger | VERY HIGH |
| core/event_bus/event_bus.py | event routing | Core | SQLite + memory + broadcast | validator/store | VERY HIGH |
| core/storage/event_store.py | durable events | Core persistence | SQLite | DB/models | HIGH |
| core/storage/database.py | DB engine/session | Core persistence | SQLite | shared config | HIGH |
| core/storage/models.py | durable schemas | Contracts + persistence | DB rows | SQLAlchemy | VERY HIGH |
| core/storage/storage_manager.py | filesystem persistence | Core persistence | runtime files | logger | HIGH |
| core/autonomy/active_runtime/cognition_loop.py | autonomous orchestrator | Core Runtime/Orchestrator | cycles/broadcast/memory | many autonomy services | VERY HIGH |
| scripts/autostart/start_daemon.py | runtime entrypoint | Runtime/Deploy | process lifecycle | CognitionLoop/queue | HIGH |
| core/agents/base_agent.py | agent contract | Agents + Contracts | event/log | Event contract/logger | HIGH |
| core/agents/repo_agent.py | repository specialist | Agents | event/log | BaseAgent/Event | MEDIUM |
| core/observability/event_stream.py | event-to-live adapter | Core/Cockpit transport | event/broadcast | realtime | HIGH |
| core/realtime/realtime_broadcast.py | live delivery | Cockpit transport | websocket | manager | HIGH |
| core/workspace/workspace_manager.py | workspace authority | Core repository service | filesystem | config/logger | HIGH |
| core/kernel/cognitive_kernel.py | central coordinator candidate | Core nucleus | event/context/registry | federation/context | HIGH |

## Required rewrites

1. Move shared Event/DTO/schema definitions to DGM-Contracts.
2. Make SafeActionQueue consume a public action envelope instead of a private MissionEngine callback contract.
3. Make MissionEngine recover durable mission state through a service boundary.
4. Define RuntimeTruthState as a public read model; process-local cache must not be global truth.
5. Make cockpit consume HTTP/WebSocket contracts only.
6. Make agents consume event contracts and agent runtime interfaces only.
7. Centralize Windows paths in configuration.
8. Identify and retire duplicate autonomy/execution engines before extracting repositories.
9. Keep FULL-MIRROR read-only and outside migration operations.

## Migration order

1. DGM-Contracts
2. Core persistence/state boundaries
3. DGM-Core-Backend
4. Runtime/daemon
5. Agents
6. Cockpit
7. Providers/Connectors/Memory
8. Cluster/Orchestrator/Federation only when dependency proof exists
9. Labs/Experimental
10. remove obsolete duplicates only after cross-repo tests pass

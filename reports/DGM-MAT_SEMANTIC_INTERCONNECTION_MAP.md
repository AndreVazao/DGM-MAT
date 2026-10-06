# DGM-MAT — Semantic Interconnection Map

Generated from the current core/ Python source. This is a factual pre-migration map; it does not move or edit production modules.

## Semantic model

| Concern | Current mechanism | Authority | Boundary |
|---|---|---|---|
| Mission creation | FastAPI -> MissionEngine.create_mission | MissionEngine | API |
| Mission durable state | JSON under runtime missions/ | MissionEngine + filesystem | Cross-process |
| Action queue | SQLite safe_action_queue | SafeActionQueue | Cross-process |
| Runtime truth | RuntimeStateStore singleton | current process only | Process-local |
| Events | EventBus + EventStore | EventBus/EventStore | mixed |
| Live UI updates | realtime_broadcast/WebSocketManager | current process | WebSocket |
| Autonomous cycle | CognitionLoop | daemon process | Process |
| Agents | BaseAgent + event handlers | Agents domain | Event contract |
| Repository discovery | WorkspaceManager / RepoScanner / MissionEngine scanners | multiple current owners | Filesystem |
| Persistent runtime data | RuntimeStorageManager | storage layer | Filesystem |
| Global project memory | AndreOS/OS-Memory | external persistent memory | External |

## Critical flow 1 — API to mission execution

POST /runtime/missions -> MissionEngine.create_mission() -> mission JSON + SafeActionQueue.enqueue(MISSION_EXECUTION) -> SQLite safe_action_queue -> operator/system approval -> SafeActionQueue consumer claims APPROVED action -> registered MISSION_EXECUTION handler -> execution/decomposition -> mission JSON + RuntimeStateStore + broadcast.

Authority:
- API accepts the request.
- MissionEngine owns mission lifecycle.
- SafeActionQueue owns action lifecycle.
- SQLite owns durable queue state.
- Mission JSON owns durable mission state.
- RuntimeStateStore owns only the current process snapshot.

## Critical flow 2 — Runtime truth to cockpit

Core services -> RuntimeStateStore.dispatch(...) -> in-memory RuntimeTruthState -> FastAPI /runtime/status, /state, /truth, /health -> cockpit/websocket consumers.

Important finding: RuntimeStateStore is called a single source of truth, but it is process-local. It cannot by itself be the cross-process source of truth.

## Critical flow 3 — EventBus

EventBus.publish(Event) -> validation -> governance -> EventStore.persist(Event) [SQLite] -> stream_event(Event) -> safe_broadcast() -> WebSocket clients.

At the same time EventBus queue + subscribers are in memory. Durable event history and live event delivery are separate guarantees.

## Critical flow 4 — autonomous daemon

scripts/autostart/start_daemon.py -> starts CognitionLoop and SafeActionQueue consumer.

CognitionLoop -> mission_engine.process_missions() -> repository observation -> StrategicPlanner -> ObjectiveEngine -> ExecutionDirector -> validation -> LearningLoop -> memory/self-improvement -> cycle persistence.

## Commands / obeys / reads / writes

### Commands
- FastAPI route handlers command MissionEngine, WorkspaceManager, scanners and state access.
- CognitionLoop commands mission processing, planning, execution and learning.
- SafeActionQueue commands registered handlers after approval.
- EventBus commands subscribed callbacks after event publication.

### Obeys
- SafeActionQueue obeys persisted action status and approval fields.
- Queue handlers obey action_type registration.
- Event subscribers obey event_type subscriptions.
- CognitionLoop obeys runtime configuration and loop lifecycle.

### Creates
- MissionEngine creates missions and queue actions.
- EventBus creates event delivery work.
- CognitionLoop creates autonomy cycles.
- Agents react to event contracts.

### Approves
- SafeActionQueue owns durable action approval.
- MissionEngine still contains a legacy in-memory approval mechanism.
- These two approval models are currently overlapping and must be reconciled.

### Persists
- Mission JSON: mission lifecycle/result.
- SQLite safe_action_queue: durable actions/approval/audit.
- SQLite events: EventBus event history.
- RuntimeStorageManager: domain files for runtime state/memory/snapshots/etc.
- CognitionLoop: autonomy cycle artifacts.

## Process boundaries

Process-local: MissionEngine.active_missions, pending_approvals, RuntimeStateStore.state, EventBus.subscribers/queue, websocket connections, singleton instances.

Cross-process durable: mission JSON, SQLite safe_action_queue, SQLite events, runtime storage files.

## Current hardcoded infrastructure paths

- C:/ProgramasGodMode
- C:/DevopGodMode/runtime
- C:/DevopGodMode
- config/autonomous_runtime.json
- config/protected_assets.yaml

## Public boundary candidates

1. Contracts/events/DTOs
2. Queue action schema
3. Mission persistence schema
4. Runtime truth API
5. Event envelope
6. Agent event contract
7. Repository/workspace service interface
8. Memory service interface

## Migration risks

1. Moving core/ without changing imports will break direct module imports.
2. Moving MissionEngine without its queue/persistence contract will recreate the cross-process failure.
3. Moving agents while retaining imports of private Core internals will create reverse coupling.
4. Moving cockpit before stable API contracts will force repeated rewrites.
5. Moving RuntimeStateStore without defining cross-process truth will preserve the current architectural ambiguity.
6. Splitting EventBus and EventStore without defining delivery semantics can produce lost or duplicated events.
7. Hardcoded filesystem paths can silently point a new repo at the old runtime.
8. Singleton construction side effects can cause hidden startup dependencies.

## Migration gate

No production file should be moved until this semantic map and the ownership matrix are complete and checked against the factual dependency graph.

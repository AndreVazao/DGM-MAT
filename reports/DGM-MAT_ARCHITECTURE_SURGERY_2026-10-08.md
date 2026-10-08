# DGM-MAT Architecture Surgery — 2026-10-08

## 1. Stale development subsystem

The legacy `core/development` subsystem was removed from canonical DGM-MAT and preserved in `DGM-MAT-OS/archive/DGM-MAT-stale-development-subsystem-2026-10-08`.

Evidence:
- no tests exercised it;
- no production callers existed beyond Runtime's optional bootstrap/event hook;
- ValidationEngine returned unconditional success;
- ImplementationEngine did not implement changes;
- FeaturePlanner used process-randomized `hash()`;
- its local ExecutionFabric was disconnected from the canonical execution fabric.

Canonical Runtime no longer initializes or subscribes to it.

## 2. Execution architecture audit

Reference tracing shows two distinct layers with different responsibilities:

- `core/execution/`: Git/worktree primitives and approval facade. `ExecutionEngine` exists but has no production/test callers and is therefore a low-priority legacy candidate, not yet removed.
- `core/execution_fabric/`: current autonomous execution orchestration: TaskDispatcher → AutonomousExecutor → WorktreeRuntime/SafePatchEngine/ExecutionSupervisor, with approval integration.
- `core/runtime/safe_action_queue.py`: durable governance/control boundary used by Runtime and MissionEngine.
- `core/autonomy/mission_engine.py`: mission-level orchestration and governed queue entry.

Conclusion: do not merge these layers blindly. The current canonical high-level path is mission/autonomy + SafeActionQueue + execution_fabric. The `core/execution` layer remains as lower-level Git/worktree infrastructure and needs a separate caller audit before any deletion.

## 3. Fake provider adapters

Reference tracing found no imports/callers for:
- `core/model_router/local_provider_adapter.py`
- `core/providers/ollama/ollama_provider.py`

Both were removed from canonical DGM-MAT and preserved in `DGM-MAT-OS/archive/DGM-MAT-fake-provider-adapters-2026-10-08`.

Why:
- LocalProviderAdapter always returned `True` from a simulated health check.
- OllamaProvider forced `ok` without checking Ollama availability.
- OllamaProvider chat returned a placeholder instead of contacting Ollama.

This violated the project rule that capability state must reflect observed reality.

## 4. Regression state

Before this surgery the canonical suite had 183 passing tests.
After removing the unreferenced fake adapters, the suite exposed an unrelated existing event-store test failure:
`tests/contracts/test_event_boundary.py::test_event_store_persists_and_replays_complete_envelope`.

The failure is in `EventStore.replay()`: it orders records ascending and limits to 20, so a newly persisted event can fall outside the returned window when the SQLite test database already contains more than 20 records of that event type. `EventStore.get()` still retrieves the event correctly.

This was not caused by the provider-adapter deletion. The issue is now recorded as the next stability fix; no broad database behavior was changed during this surgery.

## 5. Contamination audit

Repository scan for Remote Desktop wrapper contamination (`[executed on device:]` and `[Reading ... lines from start]`) is clean in tracked source/document formats after correction of the historical audit report.

## 6. Next canonical work

1. Fix and test deterministic EventStore replay semantics without hiding records.
2. Audit `core/execution/execution_engine.py` caller graph and decide whether it is lower-level canonical infrastructure or dead code.
3. Audit ProviderBase's default `ok` semantics and provider subclasses for reality-grounded health checks.
4. Continue synchronization into AndreOS memory after each proven architectural change.

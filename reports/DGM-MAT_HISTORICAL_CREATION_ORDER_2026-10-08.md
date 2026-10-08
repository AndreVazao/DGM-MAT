# DGM-MAT — Historical Creation-Order Audit

Date: 2026-10-08

## Purpose

This audit adds a second dimension to architectural surgery: not only what exists and what calls what, but when each important component first entered the repository and how it evolved.

The source of truth is Git history of AndreVazao/DGM-MAT. This is first Git introduction history, not Windows filesystem creation time.

## Important limitation

Git does not preserve the original NTFS creation timestamp as a first-class field. It preserves first commit introduction, later modifications, inferred renames, and commit timestamps. Therefore this report uses first Git introduction plus evolution lineage.

## Initial chronology

The repository began on 2026-05-22 and expanded extremely rapidly:

1. 184bdd6 — Initial commit — 2026-05-22
2. f5569f3 — README/project structure
3. b00135c — architecture freeze/core principles
4. 691f539 — bootstrap DGM-MAT core architecture and schemas
5. c4fe86b — repository ecosystem structure
6. 64b76ba — Ecosystem Binding Protocol
7. 7d38546 — Phase 4 Live Core + Validation
8. 3b8ff83 — Phase 5 Active Agent Ecosystem + Memory
9. c18f3ef — Phase 6 Self-Healing
10. 27c9b72 — Phase 7 Prompt Intelligence / Meta-Learning
11. 7dbddfb — Phase 8A real foundation runtime
12. 4e7f8a4 — persistent engine and cockpit
13. cbd8686 — Repository Intelligence Engine
14. dbb0e69 — Memory Engine + Provider Connectors
15. 4fbceba / d388849 — Phase 14 autonomous task engine
16. 8135a73 — Phases 15–17
17. 702f1e8 — Phases 18–20
18. 485aced — Phases 21–22
19. 8501cd5 — Phases 23–25
20. 63fcc33 — Phases 26–28
21. Later phases continued through 33, 35, 37–42 and October 2026 contract/architecture work.

A very large amount of the architecture was therefore created during 2026-05-22/23/24 before later stabilization layers were introduced.

## Key component origins

### Core runtime / foundation

691f539 — bootstrap DGM-MAT core architecture and schemas.

7dbddfb — Phase 8A real foundation core runtime.

4e7f8a4 — persistent engine and cockpit.

This is the historical origin found for EventStore. Event persistence therefore predates the later EventEnvelope contract boundary by months.

### Memory and provider layer

dbb0e69 — Phase 12 Memory Engine and Phase 13 Provider Connectors.

The historical ProviderBase lineage begins here and later receives orchestration/reality layers.

55afee0 — Phase 42.2-LITE Dynamic Provider Orchestration Layer.

### Execution layer

8135a73 — Phases 15–17.

This is the historical introduction point for the original core/execution/execution_engine.py lineage.

a396bef — Phase 33 autonomous execution and self-development fabric.

This is the historical introduction point for the core/execution_fabric lineage.

The old ExecutionEngine and later ExecutionFabric are therefore separate generations and must not be treated as equivalent by name alone.

### Reality / stability layers

9e1c004 — Phase 42.1-LITE.

6b5d40e — Phase 42.4-LITE Reality Sync Engine and Safe Ecosystem Governance.

These phases introduced stronger runtime-truth and governance concepts after the original rapid architecture build.

### Mission / autonomy lineage

MissionEngine is heavily evolved through Phase 41/42 and later repairs:

- 391f2f6 — Phase 41-Lite: Real Productivity Operation
- 9e1c004 — Phase 42.1-LITE
- 8c77ab0 — Phase 42.5.1 unified runtime truth
- d6b38c6 — Phase 42.5.2 mission lifecycle / health alignment
- 147a280 — Phase 42.5.3 mission consumer recovery
- 56e3710 — Phase 42.5.5 SafeActionQueue consumer recovery
- 9c24ce3 — Phase 42.5.3 Lite execution-flow patch
- c23b0f9 — Phase 42.6.2-LITE
- 22ef8fb — regression/durable approval stabilization
- 47d60ef — capability-gap routing to Capability Scout

MissionEngine is therefore a convergence point of many later corrections, not an untouched original component.

## EventStore finding

EventStore is much older than its current contract shape.

Lineage:

- 4e7f8a4 — persistent engine/cockpit origin
- 6b5d40e — later reality/stability evolution
- baa2c4e — idempotent/non-critical database initialization
- 56019e4 — EventEnvelope boundary

The current test failure was caused by shared local SQLite history: replay ordered ascending and limited the first 20 matching rows, so a new event could fall outside the test window.

The product replay semantics were kept chronological. The test was corrected to use a unique event type, removing dependence on accumulated local state. Full suite returned green.

## Execution lineage finding

Structural audit showed that the assumed path Mission → SafeActionQueue → ExecutionFabric is not the actual current runtime path.

The proven current path is:

MissionEngine → SafeActionQueue → registered MISSION_EXECUTION handler in MissionEngine → mission execution/decomposition logic.

The old Phase 15–17 ExecutionEngine had no production callers. It also called WorktreeManager with an obsolete signature. It and its orphaned supporting components were quarantined into:

DGM-MAT-OS/archive/DGM-MAT-legacy-execution-engine-2026-10-08

Preserved:

- execution_engine.py
- worktree_manager.py
- branch_manager.py
- repair_loop.py
- rollback_engine.py
- merge_guard.py
- execution_context.py
- execution_models.py

GitUtils was retained because it still has real callers.

The full regression suite remained green after this quarantine.

Important: core/execution_fabric was not removed wholesale. WorktreeRuntime still has a live reference from core/sandbox/isolated_runtime.py and therefore requires a separate ownership audit.

## Provider lineage finding

Provider archaeology exposed a second major false-reality stack.

The original provider connector lineage begins at dbb0e69. Later 55afee0 added dynamic discovery and capability orchestration. The actual adapter implementations were not real execution paths:

- ChatGPT chat() returned a placeholder and its browser authentication declared success without verifying a session.
- Claude, DeepSeek, Gemini, Grok and OpenAI returned placeholder responses.
- Several health checks treated credential/configuration presence as ok rather than observing the remote service.
- Open WebUI was explicitly placeholder-only.
- The provider mesh had no production callers and its tests encoded placeholder behavior/capability scores.
- The local AI fabric had a real Ollama HTTP adapter but no production caller; Open WebUI remained placeholder-only.
- Browser provider/recovery code had no canonical production callers.

These components were quarantined into:

DGM-MAT-OS/archive/DGM-MAT-unproven-provider-stack-2026-10-08

ProviderBase and the provider registry contract remain canonical because they can host future real adapters.

The absence of registered providers is now more truthful than a registry populated with simulated providers.

The full regression suite remained green: 178 tests passed after removal of the tests whose only purpose was proving the unproven provider stack.

## Historical creation index

A complete first-add index was generated as:

reports/DGM-MAT_FILE_CREATION_INDEX_2026-10-08.md

It records every tracked path for which Git history could identify a first-add event, including first commit, commit date and commit subject.

This gives the project a reusable archaeological map rather than relying on memory or current directory appearance.

## Four broad generations

### Generation A — rapid architecture construction

2026-05-22 to 2026-05-24.

Architecture, schemas, runtime, memory, providers, autonomy, cognition, governance, federation and development fabric were introduced in rapid succession.

### Generation B — capability expansion

Late May 2026.

Provider orchestration, reality synchronization, self-development, federation and operational layers accumulated.

### Generation C — stabilization / Lite phases

Phase 41 onward.

Operational truth, persistent workstation behavior, health alignment, recovery, approval, safe execution and regression enforcement increasingly became the focus.

### Generation D — October 2026 consolidation

The current surgery.

Fake/unconnected implementations, dead placeholders, stale development subsystems, ungrounded provider adapters and obsolete execution generations are being removed from canonical DGM-MAT while preserving recoverable history in DGM-MAT-OS.

## New governing rule

Every future architecture audit uses two axes:

1. Structural reality — current callers, imports, tests, runtime paths and data flow.
2. Historical reality — first introduction, phase lineage, replacements, migrations and renames.

Old does not mean canonical.

Late does not mean disposable.

A component must be understood in both dimensions before deletion or promotion.

## Next historical passes

1. Storage/Event/EventBus lineage.
2. ExecutionFabric ownership and WorktreeRuntime/sandbox lineage.
3. ProviderBase health semantics and registry contract.
4. Runtime/bootstrap lineage.
5. MissionEngine/SafeActionQueue/approval lineage.
6. Conversation Intelligence and memory lineage.
7. October 2026 contract consolidation lineage.

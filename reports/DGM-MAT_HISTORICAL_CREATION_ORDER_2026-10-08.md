# DGM-MAT — Historical Creation-Order Audit

Date: 2026-10-08

## Purpose

This audit adds a second dimension to the architectural surgery: not only what exists and what calls what, but when each important component first entered the repository and how it evolved.

The source of truth is the Git history of AndreVazao/DGM-MAT on the local canonical clone. Git history is deliberately separated from filesystem timestamps.

## Important limitation

Git does not preserve the original Windows filesystem creation timestamp as a first-class field. It does preserve the first commit in which a path appears, subsequent modifications, inferred renames, and the commit graph/timestamps.

Therefore this report uses first Git introduction plus evolution history, not NTFS creation time.

## Initial chronology

The repository began on 2026-05-22 and expanded extremely rapidly through numbered phases:

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
17. 702f1e8 — Phases 18–20: Cognition, Recovery, Development Fabric
18. 485aced — Phases 21–22: Governance + Knowledge Fabric
19. 8501cd5 — Phases 23–25: Strategic, Research, Federation
20. 63fcc33 — Phases 26–28
21. Later phases continued through 33, 35, 37–42 and the October 2026 contract/architecture work.

This chronology is architecturally significant: a very large amount of the current system was created in a very short period on 2026-05-22/23/24, before later stabilization layers were introduced.

## Key component origins

### Core runtime / foundation

691f539 — 2026-05-22 15:03 UTC

bootstrap DGM-MAT core architecture and schemas.

This is the earliest identified architectural bootstrap commit.

7dbddfb — 2026-05-22 18:26 UTC

Phase 8A real foundation core runtime.

This is the early transition from schemas/architecture into a real runtime foundation.

4e7f8a4 — 2026-05-22 18:53 UTC

persistent engine and cockpit.

This is the historical origin currently found for core/storage/event_store.py. Event persistence therefore predates the later EventEnvelope contract boundary by months.

### Memory and provider layer

dbb0e69 — 2026-05-22 19:42 UTC

Phase 12 Memory Engine and Phase 13 Provider Connectors.

The historical provider_base lineage begins here and was subsequently evolved through several provider/orchestration phases.

55afee0 — 2026-05-27 18:12 +0100

Phase 42.2-LITE Dynamic Provider Orchestration Layer.

This later layer matters because current ProviderBase health semantics are inherited by multiple provider implementations. It therefore needs to be audited against the original provider assumptions rather than judged only from current code.

### Execution layer

8135a73 — 2026-05-23 10:12 UTC

Implement DGM-MAT Phases 15, 16, and 17.

This is the historical introduction point for core/execution/execution_engine.py.

a396bef — 2026-05-24 19:56 UTC

Phase 33 autonomous execution and self-development fabric.

This is the historical introduction point for the current core/execution_fabric/execution_fabric.py lineage.

Important distinction: the older ExecutionEngine and later ExecutionFabric are not automatically equivalent simply because both contain execution in their names. The current surgery must prove whether the older engine is still a real dependency or historical residue.

### Reality / stability layers

9e1c004 — Phase 42.1-LITE.

This introduced the current storage/runtime stabilization lineage.

6b5d40e — 2026-05-28 14:14 +0100

Phase 42.4-LITE Reality Sync Engine and Safe Ecosystem Governance.

This is the historical point where the project explicitly introduced stronger runtime-truth and governance concepts.

The present surgery must distinguish original optimistic architecture from later reality/stability corrections.

### Mission / autonomy lineage

The current core/autonomy/mission_engine.py is heavily evolved. Its history includes the Phase 41/42 stabilization line and later execution-flow repairs:

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

This shows that MissionEngine is not an original isolated component anymore; it is a convergence point of many later repairs.

## EventStore historical finding

EventStore is much older than its current contract shape.

Historical lineage:

- 4e7f8a4 — original persistent engine/cockpit lineage
- 6b5d40e — later reality/stability evolution
- baa2c4e — database initialization made idempotent/non-critical during bootstrap
- 56019e4 — EventEnvelope boundary introduced

The current implementation stores the complete EventEnvelope while maintaining compatibility with older rows through the fallback projection.

### Current test failure

The regression is not evidence that persistence itself is broken. The current failure is caused by a test using a shared persistent SQLite database and a fixed event type: EVENT_REPLAY_TEST.

replay(limit=20, event_type=...) filters matching rows, orders by record id ascending, and then limits the matching rows. With more than 20 historical records of the same type, the newly inserted event can be outside the first 20.

EventStore.get() still retrieves the event by unique event id.

The architectural question is therefore test isolation and explicit replay semantics, not a blind change from chronological replay to reverse ordering.

The first correction should preserve chronological replay semantics and make the contract test independent of accumulated local state. A separate test should pin the intended ordering/limit semantics.

## Historical architecture hypothesis

The history suggests four broad generations.

### Generation A — rapid architecture construction

2026-05-22 to 2026-05-24.

Large amounts of architecture, schemas, runtime, memory, providers, autonomy, cognition, governance, federation and development fabric were introduced in rapid succession.

### Generation B — capability expansion

Late May 2026.

Provider orchestration, reality synchronization, self-development, federation and operational layers accumulated.

### Generation C — stabilization / Lite phases

Phase 41 onward.

The project increasingly added operational truth, persistent workstation behavior, health alignment, recovery, approval, safe execution and regression enforcement.

### Generation D — October 2026 architectural consolidation

The current surgery.

The project is removing fake/unconnected implementations, dead placeholders, stale development subsystems and ungrounded provider adapters while consolidating public contracts, durable execution and governance.

## New rule for the surgery

Architectural auditing should now use two axes:

1. Structural reality: current callers, imports, tests, runtime paths and data flow.
2. Historical reality: first introduction, phase lineage, replacements, migrations, renames and later stabilization patches.

A component that looks redundant today but is historically foundational must not be deleted until its descendants/replacements are proven.

Conversely, a component added late as a repair layer but never connected to the canonical path is a strong candidate for quarantine after caller/test verification.

## Next historical passes

1. Storage/Event/EventBus lineage.
2. ExecutionEngine to ExecutionFabric to AutonomousExecutor lineage.
3. ProviderBase to provider subclasses to RealitySnapshot/health monitoring lineage.
4. Runtime/bootstrap lineage.
5. MissionEngine/SafeActionQueue/approval lineage.
6. Conversation Intelligence and memory lineage.
7. October 2026 contract consolidation lineage.

The objective is not to preserve old code merely because it is old. The objective is to understand what was the original authority, what replaced it, what survived accidentally, and what currently has no legitimate owner.

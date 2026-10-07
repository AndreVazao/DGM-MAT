# DGM-MAT Event Boundary Checkpoint — 2026-10-07

## Result

The Event boundary is now implemented and verified as:

Event -> EventEnvelope -> EventStore -> replay -> EventBus/live stream

## Changes

- EventStore persists the complete public EventEnvelope as envelope_json.
- Existing SQLite events tables are migrated non-destructively by adding the nullable envelope_json column when needed.
- Existing legacy event rows remain replayable through a backward-compatible reconstruction path.
- EventStore.get() and EventStore.replay() return EventEnvelope contracts.
- event_stream now broadcasts the complete public envelope instead of a partial event projection.
- EventBus now handles both timezone-aware and naive event timestamps safely.
- Duplicate persistence is updated by event_id rather than creating another event row.

## Validation

Focused suite: 13 passed.

Included Event mapping, complete persistence, replay, EventBus persistence, MCP ToolDescriptor adapter, execution/approval adapters, queue boundary and cross-process mission lifecycle.

## Architectural consequence

EventEnvelope is now the public event contract. Event remains a DGM-MAT runtime model during the compatibility phase.

Physical extraction is still blocked until the broader regression suite passes.

FULL-MIRROR remains untouched.

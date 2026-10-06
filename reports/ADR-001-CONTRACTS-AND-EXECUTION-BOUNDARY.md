# ADR-001 — DGM-MAT Contracts and Execution Boundary

Date: 2026-10-06
Status: IMPLEMENTED IN DGM-MAT COMPATIBILITY LAYER / PHYSICAL EXTRACTION BLOCKED

## Context
DGM-MAT currently has several overlapping representations of missions, actions, execution tasks, approvals and events. SafeActionQueue is durable across processes while MissionEngine and ApprovalManager also keep process-local state. DGM-MCP defines transport-specific tool schemas and result envelopes.

This creates the exact failure mode already observed: one process can own in-memory state while another process consumes a durable queue record.

## Decision
Establish one public contract layer:

- ExecutionRequest
- ExecutionResult
- ToolDescriptor
- ApprovalRequest
- ApprovalDecision
- EventEnvelope
- MissionReference
- MissionState

The contracts are transport- and storage-neutral.

SafeActionQueue becomes the candidate durable execution boundary. It stores an ExecutionRequest-derived durable record and durable approval state. It is not itself the public contract.

MissionEngine remains the mission authority during migration, but it must reference durable mission state rather than assuming its in-memory dictionary is globally authoritative.

ApprovalManager and MissionEngine.pending_approvals are compatibility layers only and must converge on the durable approval authority.

EventBus remains an in-process dispatcher. EventStore remains persistence. EventEnvelope becomes their common public language.

DGM-MCP remains an integration/transport boundary. Its ToolDefinition becomes compatible with ToolDescriptor, while MCP response formatting adapts from ExecutionResult.

## Consequences
Positive:
- clear cross-repository boundaries
- safe process separation
- one execution vocabulary
- easier mobile/cockpit integration
- MCP becomes replaceable transport
- future agents can use the same contracts

Negative:
- temporary adapters and duplicate representations during migration
- schema/versioning work
- more integration tests required

## Non-goals
- no repository extraction in this ADR
- no final .exe/build architecture
- no destructive cleanup
- no modification of FULL-MIRROR
- no blind merge of DGM-HUB or DGM-MCP

## Migration gates
1. Implement contracts and schema tests. **DONE**
2. Add adapters from existing MissionEngine/SafeActionQueue models. **DONE**
3. Prove cross-process queue execution and mission reload. **DONE**
4. Prove durable approval boundary. **DONE**
5. Prove EventEnvelope persistence and live projection. **NEXT**
6. Adapt DGM-MCP ToolDefinition to ToolDescriptor without Core importing MCP internals. **DONE (compatibility adapter)**
7. Only then physically extract repositories. **BLOCKED until Event gate + broader regression pass.**

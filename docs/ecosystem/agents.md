# Agent Contract Standard

## 1. AGENT IDENTITY SCHEMA
Each agent within the ecosystem is defined by:
- `agent_id`: Unique global identifier.
- `satellite_id`: The ID of the repository hosting the agent.
- `contract_version`: The schema version the agent adheres to.
- `capabilities`: A list of allowed event-driven operations.

## 2. RESPONSIBILITY MODEL
- **Governance Agents**: Reside in Core; manage ecosystem health.
- **Domain Agents**: Reside in Satellites; handle specific tasks (e.g., Connector Agent).
- **Execution Agents**: Short-lived workers spawned for single tasks.

## 3. ISOLATION RULES
- Agents cannot read files outside their designated repository scope unless authorized by Core.
- Agents cannot maintain persistent network connections; they must use the Event Bus.
- Process-level isolation must be enforced by the Runtime Engine.

## 4. MEMORY ACCESS RULES
- **Read**: Agents have read-only access to relevant sub-graphs of the Semantic Memory.
- **Write**: Agents emit events to update memory; Core performs the final mutation.
- **Full**: Only the Core Memory Sovereign has full read/write access.

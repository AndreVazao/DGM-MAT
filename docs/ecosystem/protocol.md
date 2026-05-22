# Ecosystem Protocol (DGM-MAT v1.0)

## 1. COMMUNICATION PRINCIPLES
All inter-system communication within the DGM-MAT ecosystem must adhere to the following principles:
- **Asynchronicity**: All inter-repo interactions are non-blocking.
- **Event-Driven**: Systems communicate by emitting and consuming events.
- **Statelessness (Satellites)**: Satellites do not persist global state; they react to events from Core.
- **Centralized Routing**: All events must pass through the DGM-MAT Core Event Bus.

## 2. BOUNDARIES
### DGM-MAT Core
- Owns the Event Bus.
- Manages the Global Orchestration State.
- Handles Governance and Security Sovereignty.
- Decides task sequencing.

### Satellites
- Execute specific domain logic (e.g., UI, provider calls, deployment).
- Emit status and result events.
- Have NO knowledge of other satellites except through the Core.

## 3. DEPENDENCY RULES
- **Core Dependency**: Satellites can depend on Core contracts and schemas.
- **Core-to-Satellite**: Core must NOT depend on satellite implementation details.
- **Cross-Satellite**: Direct dependencies between satellites are STRICTLY FORBIDDEN.
- **Shared Libraries**: Shared utility logic must be abstracted into the Core or a specific shared contract package.

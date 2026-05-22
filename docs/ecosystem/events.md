# Shared Event Model

## 1. EVENT TYPES
Events are categorized by their intent:
- **COMMAND**: Instructs a satellite to perform an action (e.g., `PROVIDER_CALL_EXECUTE`).
- **SIGNAL**: High-priority broadcast for state changes (e.g., `CORE_REBOOT`).
- **FACT**: Notifies the ecosystem of a completed action (e.g., `DEPLOYMENT_SUCCESS`).
- **ERROR**: Reports a failure in the ecosystem.

## 2. ROUTING RULES
- **Fan-out**: Signals are broadcast to all relevant satellites.
- **Direct-to-Satellite**: Commands are routed to the specific target satellite.
- **Reporting**: All Satellite events must be routed back to the Core.

## 3. PRIORITY SYSTEM
- **P0 (CRITICAL)**: Governance/Security signals (must be processed immediately).
- **P1 (HIGH)**: Interactive UI events and blocking tasks.
- **P2 (NORMAL)**: Background agent tasks.
- **P3 (LOW)**: Logging, telemetry, and background asset sync.

## 4. TRACE SYSTEM
Every event must include:
- `trace_id`: UUID following a request through the entire ecosystem.
- `span_id`: Local ID for the specific processing unit.
- `origin`: The ID of the emitting agent/satellite.
- `timestamp`: RFC3339 format.

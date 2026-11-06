# Read-only specialist task dispatch v1

MissionEngine exposes `run_readonly_repository_worker` as a narrow, mission-scoped
entry point for three explicitly configured specialists:

- Repository Cartographer — `inventory_repository`
- Python Source Analyst — `analyze_python_repository`
- Python Test Inventory — `inventory_python_tests`

The caller supplies only the worker ID, stable allowlisted repository ID, mission ID and
correlation ID. The operation and capabilities are selected from a fixed internal map.
The caller cannot supply a path, shell command, arbitrary operation or output destination.

## Delivery and recovery

Requests are written to the existing SQLite-backed InternalMessageBus. Message IDs are
deterministic over worker/repository/mission/correlation/request, making retries idempotent.
WorkerRuntime dispatches at most one unread message. If an older inbox message is handled
first, the API reports the new request as QUEUED rather than attributing the older result
to the new task. Successful dispatch receipts are persisted by the existing bus.

## Safety and maturity

The orchestrator verifies the handler is registered and that its declared capabilities
cover the fixed operation. A missing handler or capability fails closed. Worker results
remain read-only metadata. The API does not execute tests, code, shell commands, or
external providers. Handler registration and declared capabilities are not proof of
task-level validation; a successful durable receipt is evidence that this particular
bounded handler invocation completed, not independent verification of its findings.

The operator allowlist remains opt-in via the existing workspace environment variables.

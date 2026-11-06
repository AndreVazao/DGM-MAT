# Worker office roster and readiness reconciliation v1

The office roster now declares the three read-only specialist roles:
- Repository Cartographer
- Python Source Analyst
- Python Test Inventory

All three begin in `OFFLINE` / `ROLE_DEFINED_ONLY` state. A role existing in the roster
does not imply that its handler is installed or callable.

MissionEngine bootstraps the existing full office registry and passes it to the
operator-configured worker registration gate. When a valid host-owned repository
allowlist is present and a handler is registered, that profile transitions to
`AVAILABLE`. With missing or invalid configuration, the profiles remain `OFFLINE`.

MissionEngine exposes `organization_readiness()`, which reports roster status,
handler registration and declared capabilities separately. It explicitly reports
`task_validated: false`; registration and declarations are not successful-task evidence.

The registry is an in-memory runtime roster at this stage. Persistent organization
roster/task lifecycle integration remains a separate increment and must reuse the
existing mission/Vault persistence rather than creating a parallel store.

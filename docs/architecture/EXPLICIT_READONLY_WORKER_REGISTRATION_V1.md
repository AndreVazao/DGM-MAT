# Explicit read-only worker registration v1

The Repository Cartographer, Python Source Analyst and Python Test Inventory Worker can be registered by the host
application only when both environment variables are deliberately configured:

- `DGM_READ_ONLY_WORKSPACE_ROOT`: existing workspace directory.
- `DGM_READ_ONLY_REPOSITORIES`: JSON object mapping stable repository IDs to paths
  relative to that workspace, for example `{"dgm-mat":"DGM-MAT"}`.

Absolute paths, parent traversal and resolved paths outside the workspace are rejected.
The message bus payload cannot alter this allowlist or request arbitrary filesystem paths.
If configuration is absent or invalid, both workers remain unregistered and startup
continues in the disabled state. Registration is idempotent.

These workers remain read-only: no shell, code execution, source writes, network access
or provider calls. This registration proves only that a handler is configured; it does
not claim task-level validation or successful real-repository analysis.

Windows path, permission, symlink and restart acceptance must be completed on the
operator's PC before enabling the configuration there.

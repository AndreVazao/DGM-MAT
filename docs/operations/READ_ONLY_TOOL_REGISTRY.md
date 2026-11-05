# Read-only Tool Registry

The `ReadOnlyToolRegistry` is a typed adapter over the existing
`core.operations.command_executor.CATALOG`. It exposes only the six fixed
commands already implemented by `CommandExecutor`.

## Scope

- List typed `dgm_contracts.ToolDescriptor` records.
- Return one descriptor by exact command ID.
- Dispatch only exact registered IDs with structured arguments.
- Permit `target_path` only for `git.status`; the existing executor performs
  the final allowed-root and Git-working-tree checks.
- Reject unknown IDs, arbitrary command fields, shell options, timeout overrides,
  and all additional arguments.
- Keep the existing executor responsible for fixed argv construction,
  `shell=False`, process timeouts and bounded output.

## Important boundary

This registry is a metadata/dispatch adapter, not an authorization authority.
Descriptors deliberately retain `approval_policy=REQUIRED`. Existing mission
auto-run allowlists and the durable SafeActionQueue remain the only authorities
for approval and execution. This PR does not register the registry with
MissionEngine, add new mission intents, start workers, or enable autonomous writes.

## API

```python
from core.operations.read_only_tool_registry import ReadOnlyToolRegistry

registry = ReadOnlyToolRegistry()
tools = registry.list_tools()
git_status = registry.execute(
    "git.status",
    {"target_path": r"C:\ProgramasGodMode\DGM-MAT"},
)
```

The command IDs and implementation remain sourced from the existing fixed
`CATALOG`; the adapter does not create fallback descriptors for unknown tools.

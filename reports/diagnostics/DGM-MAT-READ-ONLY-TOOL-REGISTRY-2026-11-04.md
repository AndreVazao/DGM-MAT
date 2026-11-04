# DGM-MAT Read-only Tool Registry — Implementation Evidence

Date: 2026-11-04
Branch: `feat/read-only-tool-registry-2026-11-04`
Base: `main` at `15bb5704fefb297b55e5cab8e88334162a3419be`
Status: implementation complete locally; PR pending.

## Changes

1. Added `core/operations/read_only_tool_registry.py`.
   - Adapts the existing fixed `CommandExecutor.CATALOG` to typed
     `dgm_contracts.ToolDescriptor` objects.
   - Exposes exact-ID listing, lookup and structured dispatch.
   - Rejects unknown tool IDs, extra argument keys, arbitrary shell/command
     parameters, invalid target types and missing target paths.
   - Retains the existing executor as the final enforcement point for allowed
     roots, Git working-tree checks, fixed argv, `shell=False`, timeout and
     bounded output.
   - Keeps `approval_policy=REQUIRED`; descriptor metadata does not grant
     execution authority.

2. Added `tests/test_read_only_tool_registry.py`.
   - Catalog order and descriptor metadata.
   - Strict JSON-schema argument boundaries.
   - Unknown tool denial.
   - Rejection of shell, command, timeout and unexpected fields.
   - Required target validation.
   - Delegation to existing executor and allowed-root enforcement.
   - Descriptor mutation isolation.

3. Added `docs/operations/READ_ONLY_TOOL_REGISTRY.md`.

## Validation

Executed on the isolated Windows worktree:

```powershell
python -m pytest -q tests/test_read_only_tool_registry.py tests/test_command_executor.py tests/contracts/test_mcp_tool_descriptor.py tests/contracts/test_queue_boundary.py tests/autonomy/test_read_only_diagnostic_missions.py
python -m compileall -q core/operations
git diff --check
```

Result: **42 tests passed**; compileall passed; `git diff --check` passed.
Python emitted two pre-existing `SyntaxWarning` notices for invalid escape
sequences in regex strings in `command_executor.py`; this PR does not alter
that file or those expressions.

## Safety and non-claims

- No MissionEngine integration or runtime handler registration was changed.
- No mission queue rows, approvals, historical actions or checkpoints were read
  for mutation or altered.
- No process/service was started or restarted.
- No arbitrary shell, write, patch, network, credential or administrator tool
  was added.
- The registry's presence does not mean DGM-MAT can yet execute general
  engineering missions.
- The active dirty main checkout was not touched. Work was performed in the
  isolated worktree listed above.

## Next gate

Review the descriptor and argument contracts, then add a separate integration
change only after proving the exact SafeActionQueue/ExecutionRequest boundary.
Do not activate generic mission execution in this PR.

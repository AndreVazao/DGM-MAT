# Governed Command Executor v1

## Included in this branch

- `core/operations/command_executor.py`: explicit read-only command catalog; no arbitrary shell input.
- `GET /governance/commands/catalog`: returns the allowed command IDs and current limitations.
- `POST /governance/commands/run`: runs one catalog command and returns bounded stdout/stderr, exit code, duration and status.
- `core/operations/operation_audit.py`: append-only JSONL audit records with redacted metadata.
- `core/api/security_policy.py`: explicitly classifies both routes as operator-only; the existing local-session middleware must authenticate the request.
- `tests/test_command_executor.py`: unit tests for unknown command denial, target path boundaries, shell=False, timeout reporting, output caps, fail-closed working directory, PowerShell arguments, engine inventory privacy and diagnostic error redaction.
- `tests/test_operation_audit.py`: audit append, schema/redaction, invalid-event rejection and fail-closed storage tests.
- `tests/security/test_api_global_auth_enforcement.py`: negative/positive coverage for missing, read-only and operator session access, audit persistence and refusal to execute when the audit destination is unavailable.
- `tests/security/test_api_security_policy.py`: confirms both command routes remain operator-only and classified.

## Available command IDs

- `system.summary`: read-only host/runtime summary using PowerShell.
- `process.top`: bounded process listing using PowerShell.
- `engines.inventory`: identifies likely Ollama/Claude Code processes and returns only process names and IDs. It does not return full command lines, start/stop processes, or establish ownership.
- `git.status`: read-only Git status for an existing working tree under `DGM_COMMAND_ALLOWED_ROOTS`.
- `ollama.status`: calls `ollama list` if the executable is available; it never starts or stops Ollama.
- `claude.status`: calls `claude --version` if the CLI is available; it does not read auth files or submit prompts.

## Additional read-only software inventory

- `software.inventory` reads application metadata from the standard HKLM 64-bit, HKLM WOW6432Node and HKCU uninstall registry locations.
- Returns only display name, version, publisher and install date; it does not return uninstall commands, install paths, registry paths, user profile paths or command-line arguments.
- Excludes entries without a display name and entries marked as Windows system components; output is bounded to the first 150 distinct entries.
- Deliberately does not use `Win32_Product`, because querying that WMI class can trigger Windows Installer consistency checks/repairs.
- This is a bounded inventory slice, not proof that every installed/portable application has been discovered. Microsoft Store packages, portable apps and per-user package managers may need separate read-only adapters.
- The command remains read-only, non-elevated, fixed-script PowerShell with `shell=False`, timeout and output cap. It does not install, update, repair or uninstall anything.

## Audit behavior

Before a governed command is executed, the API must persist a `command.requested` event. If audit storage is unavailable, execution is refused. A `command.completed` or `command.denied` event is then appended. Records include UTC timestamp, event, command ID, status, session ID, duration and return code where available. They do not include stdout/stderr, credential values, or target paths.

The default path is `%LOCALAPPDATA%\\DGM-MAT\\audit\\command-audit.jsonl` on Windows. `DGM_COMMAND_AUDIT_PATH` can override it for controlled testing. Appends are serialized within the process and flushed with `fsync`. This is an application-level audit trail, not tamper-proof forensic storage; local administrators can still alter files and multi-process writers need further validation.

## Security behavior

The executor never accepts a raw command string. It invokes subprocesses with `shell=False`, bounded timeouts and capped output. It refuses to execute if none of the configured allowed roots exists instead of silently falling back to the process's current directory. Host diagnostics use fixed PowerShell scripts. Operating-system launch errors return the exception type, not the raw OS message, which could reveal a local path.

The route middleware requires an operator-scoped local session for both command endpoints. This is not a substitute for keeping the API bound to loopback or an explicitly trusted private network. The static policy inventory and tests are evidence of intended enforcement; tests still need to be run in a checkout.

## Deliberate limitations

This is a first implementation slice, not unrestricted machine control. It does **not** accept arbitrary PowerShell/CMD strings, perform administrator elevation, install software, start/stop services, change files, or manage credentials. The default allowlisted repository roots are `C:\\ProgramasGodMode` and `C:\\DevopGodMode`; override them with the semicolon-separated `DGM_COMMAND_ALLOWED_ROOTS` environment variable only after reviewing the scope.

The engine inventory is observational only; it does not reliably identify which process instance was started by DGM-MAT. Do not add stop/restart actions until process ownership can be established using a DGM-MAT-created process record and a verified PID/start-time pair.

## Validation status

The code and tests have been added to the branch. The connected Desktop Commander reports the target PC offline, so tests have not been executed from this session. No claim is made that this branch is installed or active on the PC. The work so far is code-level/static review only.

## Next steps

1. Run the focused unit/security tests in a development checkout and fix any failures.
2. Validate the audit file's permissions and multi-process behavior on Windows.
3. Implement lifecycle actions only for processes explicitly started and tracked by DGM-MAT, with confirmation and timeout handling.
4. Add a separate approved elevation broker; never pass administrator passwords to the LLM or shell.
5. Integrate executor and engine status into the PC cockpit.
6. Implement isolated self-repair and browser automation as separate branches.


## PC cockpit integration — 2026-10-16

The companion frontend branch `AndreVazao/DGM-Cockpit-Frontend:feat/pc-only-chat-cockpit-v1` now includes a governed-command panel wired to the two API routes documented above:

- `GET /governance/commands/catalog` is queried using the current authenticated session. The UI only reports the catalog as healthy when `mode=read-only-allowlist` and `arbitrary_shell=false` are explicitly returned.
- The cockpit populates a command selector from the authenticated catalog. A user must explicitly press **Executar diagnóstico**; only catalog command IDs are submitted. Commands that declare `requires_target=true` reveal a target-path field, but the backend remains responsible for validating the path against its configured allowed roots.
- `engines.inventory` is the default selection. Its returned process names and PIDs are rendered with DOM `textContent`; full command lines are not requested or shown. Output is capped in the frontend and diagnostics do not trigger process lifecycle changes.
- Catalog permission failures, audit-storage failures, missing sessions and command errors remain visible as failures; the UI must not mark an operation successful based on a click alone.
- Catalog checks are throttled; the process inventory is never run on the 30-second status polling loop, avoiding repetitive audit noise.

**Integration status:** source changes are committed to the frontend PR branch, but this is not yet a validated live integration. The backend executor branch is still a draft and has not been installed on the target PC; end-to-end validation requires the backend branch to be safely integrated, focused tests to pass, and the PC runtime to be reachable. Do not describe the executor as active until that occurs.


## Focused verification additions — 2026-10-16

- The cockpit now rejects an empty or malformed catalog, requires every advertised command to have a constrained ID, `risk=READ`, and a boolean `requires_target`, and disables execution if the catalog fetch/validation fails. This prevents stale catalog entries being reused after a failed refresh.
- The backend target validator now converts invalid path normalization errors (including embedded NUL characters) into a controlled `CommandDenied` response rather than an unexpected server error.
- Added a regression test for invalid target-path characters.
- Two manual-only GitHub Actions workflows are being added: focused Python security/executor tests in DGM-MAT, and dependency-free Node syntax/contract checks for the cockpit. They are deliberately `workflow_dispatch` only to avoid spending Actions minutes on every push.
- These additions are not yet runtime-verified. A successful GitHub Actions run and PC end-to-end test remain required before merge/activation.


## Automated test entry points — 2026-10-16

A manual-only workflow is available at `.github/workflows/governed-executor-tests.yml`. It runs the focused executor, audit and API-auth/security tests and is intentionally not triggered by pushes or pull requests. It has been committed to the feature branch but has **not** been dispatched in this session. Do not treat the tests as passing until the workflow run is observed as successful.


## Latest branch verification — 2026-10-16 19:32 UTC

- Latest DGM-MAT executor branch head: `3394d20d579edcc9d315a6d26b7293a170d4650c`.
- Added malformed target-path regression and strengthened the audit-storage test so it fails if executor execution is attempted before a request audit is persisted.
- Focused workflow is present and `workflow_dispatch` only. It has not been run; this session's GitHub integration does not expose a workflow-dispatch action.
- GitHub reports PR #74 `mergeable_state=clean`; this only describes mergeability, not test success. Keep it draft until the manual test workflow and Windows-PC validation pass.


The pre-existing `autonomy-smoke.yml` workflow on the default branch is also extended in this feature branch to run these focused backend tests and clone/run the cockpit's Node contract tests. Because the workflow already exists on the default branch, it can be manually dispatched from GitHub Actions with branch `feat/governed-command-executor-v1` selected. No push or pull-request trigger was added. The workflow has not yet been dispatched in this session.


## Read-only PATH diagnostics

- \`environment.path_diagnostics\` reads the Machine, User and current Process PATH scopes and returns up to 120 entries with scope, index, path, existence and duplicate indicators.
- The command preserves the PATH entry text so an operator can identify the exact item requiring attention. Treat this output as local machine configuration data; do not publish it to shared/cloud logs without review.
- Existence checks expand environment-variable references and test directory presence. A missing directory is diagnostic evidence, not permission to remove or rewrite the entry.
- The command does not modify PATH, registry values, environment variables, files or permissions. It does not elevate, install software or restart processes.
- Repair remains a separate future capability: it must produce a proposed before/after diff, preserve the original value, create a backup, require approval for the exact change, and verify the result in a fresh process/session.
- Windows host acceptance is still required; CI mocks validate command construction and safety boundaries only.

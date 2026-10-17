# DGM-MAT — PowerShell, CMD and Git Playbook

Use PowerShell by default for structured output and error handling; CMD for legacy batch commands; Git CLI for repository operations. Verify the environment before acting.

## Environment and resources
```powershell
$PSVersionTable.PSVersion
Get-Location
whoami
Get-Date
Get-PSDrive -PSProvider FileSystem
Get-Command git, python, node, ollama, claude -ErrorAction SilentlyContinue | Select-Object Name, Source
Get-CimInstance Win32_OperatingSystem | Select-Object Caption, Version, FreePhysicalMemory, TotalVisibleMemorySize
```

## Files and processes
```powershell
Test-Path -LiteralPath 'C:\ProgramasGodMode\DGM-MAT'
Get-ChildItem -LiteralPath 'C:\ProgramasGodMode\DGM-MAT' -Force
Get-Process | Sort-Object CPU -Descending | Select-Object -First 15 Name, Id, CPU
Get-Service | Where-Object { $_.Name -match 'DGM|Ollama' } | Select-Object Name, Status, StartType
```
Avoid whole-disk recursive scans. Begin with known project roots, cap results and exclude secrets, browser profiles, caches and generated folders.

## Local API and Ollama probes
```powershell
try { Invoke-RestMethod 'http://127.0.0.1:8181/health' -TimeoutSec 3 } catch { $_.Exception.Message }
try { Invoke-RestMethod 'http://127.0.0.1:11434/api/tags' -TimeoutSec 3 } catch { $_.Exception.Message }
```
Confirm ports and endpoints against the current configuration. An HTTP 200 or running process alone does not prove the functional capability is healthy.

Before starting Ollama, check whether it is already running and whether a job needs it. Do not start duplicates or terminate a user-owned process. Stop only a process DGM-MAT started and still owns, after active jobs finish.

## Git command map
| Goal | Command | Meaning |
|---|---|---|
| Current state | `git status --short --branch` | Branch and changed files |
| Current branch | `git branch --show-current` | Branch name |
| History | `git log -10 --oneline --decorate` | Recent commits |
| Check whitespace | `git diff --check` | Detect whitespace issues |
| Change summary | `git diff --stat` | Change size |
| Review changes | `git diff` | Unstaged diff |
| Review staged | `git diff --cached` | Proposed commit contents |
| New branch | `git switch -c feature/name` | Create/switch branch |
| Compare | `git diff main...HEAD --stat` | Changes since common ancestor |
| Commit summary | `git show --stat --oneline HEAD` | Current commit summary |

Never infer merge safety from ahead/behind alone. Inspect conflicts, exact diff, tests and dirty working-tree state. Do not reset/clean, force-push, merge or push automatically without appropriate authorization.

## Exit codes
For native executables, inspect `$LASTEXITCODE`; for PowerShell cmdlets use exceptions and `-ErrorAction Stop` when failure must be caught.
```powershell
& git status --short --branch
$code = $LASTEXITCODE
if ($code -ne 0) { throw "git status failed with exit code $code" }
```
Never treat empty output as success. Capture stdout/stderr separately and distinguish timeout from failure.

## Learning from a failed command
1. Preserve the command and sanitized error.
2. Record OS, PowerShell version, tool version, working directory and exit code.
3. Ask official documentation or an approved external AI for candidate explanations.
4. Treat advice as a hypothesis, not an instruction; validate against official docs and local state.
5. Test the smallest safe candidate in an isolated folder/worktree.
6. Save symptom, cause, fix, versions, test and confidence only after reproducible verification.
7. Never send passwords, cookies, tokens, private keys or private data to an external AI.

## Review before high-impact commands
Deletion, registry edits, execution-policy/security changes, software installation, service/startup changes, broad permissions changes and termination of non-owned processes require scope review and possibly human approval.
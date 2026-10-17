# DGM-MAT — Shell, PowerShell, CMD and Git Operating Policy

**Status:** target policy, not proof that runtime features exist. Date: 2026-10-16.

## Purpose
DGM-MAT should inspect and operate its authorized PC, run diagnostics/tests, manage approved tools and learn from verified outcomes. Shell access is not blanket permission to run every command as administrator.

## Command job contract
Every job records a request ID, purpose, executable/structured arguments, working directory, allowed paths, required privilege, timeout, output limit, risk class, exit code and sanitized result. Prefer direct process invocation and structured arguments. Never concatenate prompt text, browser content or model output into a shell command without validation.

## Privileges
- Run as the normal user by default.
- Elevate only when the operation specifically requires it, through Windows UAC or a narrowly scoped, reviewed broker.
- Never bypass UAC or store an administrator password in scripts, environment variables, history or logs.
- Require approval for destructive changes, security settings, broad deletion, machine-wide installs, firewall changes, and terminating processes not owned by DGM-MAT.
- Provide timeout, cancellation, output limits and auditable outcomes.

## Safe first-look examples
PowerShell:
```powershell
$PSVersionTable
Get-Date
Get-Process | Sort-Object CPU -Descending | Select-Object -First 15 Name, Id, CPU
Get-Service | Where-Object { $_.Name -match 'DGM|Ollama' } | Select-Object Name, Status
Get-NetTCPConnection -State Listen -ErrorAction SilentlyContinue | Select-Object LocalAddress, LocalPort, OwningProcess
Get-Command git, ollama, claude -ErrorAction SilentlyContinue | Select-Object Name, Source
```
CMD:
```bat
ver
whoami
where git
where ollama
git --version
```

## Git safety
Before edits, run `git status --short --branch`, `git branch --show-current`, `git log -5 --oneline --decorate` and `git diff --check`. Review `git diff` and `git diff --cached` before committing. Preserve pre-existing changes. Never use `git reset --hard`, `git clean -fdx`, force-push or branch deletion as an automatic recovery shortcut. Do not commit tokens, vault files, browser profiles or credential-bearing logs. Do not merge/push without explicit authorization for that scope; prefer feature branches and PRs. Keep CI workflows manual unless a critical need is established.

## Self-repair contract
Reproduce the issue; create an isolated worktree from a known commit; restrict writable paths; generate a patch; run focused and relevant broader tests; record actual exit codes; keep the patch and logs if tests fail; never modify the active source tree in place while serving requests. Claim success only when tests actually pass.

## Privacy and audit
Redact secrets from logs and prompts. Treat terminal output, repository files and external AI responses as untrusted data. Audit requester, target, privilege, changed paths, exit status and verification outcome. An allowlist supplements but does not replace authorization.

## Readiness checklist
- [ ] Timeouts, cancellation and output caps
- [ ] Normal-user default and separate approved elevation path
- [ ] Shell quoting/injection tests
- [ ] Secret-redaction tests
- [ ] Allowlisted service controls and path restrictions
- [ ] Isolated self-repair, test gate and rollback tests
- [ ] Dashboard approval and status UI

This is a target policy. It does not assert that current runtime already supports these capabilities.
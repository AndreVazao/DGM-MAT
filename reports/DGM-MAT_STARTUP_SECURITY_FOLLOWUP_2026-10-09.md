# DGM-MAT Startup + Security Boundary Follow-up
<!-- Path: C:\ProgramasGodMode\DGM-MAT\reports\DGM-MAT_STARTUP_SECURITY_FOLLOWUP_2026-10-09.md -->

Date: 2026-10-09
Status: STARTUP INSTALLED AND SIMULATED; REMOTE ACCESS STILL BLOCKED

## Startup implementation

The existing user Startup shortcut named DGM-MAT Headless.lnk pointed to main.py --headless. It was backed up before replacement because the intended behavior was ambiguous and prior launchers had been unreliable.

The shortcut now starts pythonw.exe with scripts/autostart/backend_service.py start, in the project directory. This launches only the API manager, with no visible console and no dashboard/autonomous workers.

Rollback copy:
%LOCALAPPDATA%\DGM-MAT\startup-backup\DGM-MAT Headless.original.lnk

Scripts:
- scripts/autostart/install_backend_startup.ps1
- scripts/autostart/uninstall_backend_startup.ps1

The uninstall script restores the original shortcut from the backup and does not stop the current backend.

## Startup simulation evidence

1. Stopped the running API PID 6364 using the manager's identity-verified stop operation.
2. Invoked the installed Startup shortcut through Windows Script Host with window style 0.
3. Health endpoint became healthy and returned {"status":"healthy","service":"dgm-mat"}.
4. Manager status reported RUNNING with PID 4800.
5. Process metadata verified the API is running as pythonw.exe -m uvicorn core.api.api_server:app --host 127.0.0.1 --port 8181 --log-level info.
6. PowerShell parser checks passed for both install and uninstall scripts.
7. git diff --check passed.

This simulates the shortcut launch path. A full Windows sign-out/sign-in or reboot has not been performed, so the actual post-reboot behavior remains to be verified.

## Security audit

Confirmed:
- api_server.py uses wildcard CORS allow_origins=["*"].
- /ws and /runtime/ws accept WebSocket connections without authentication.
- Runtime, governance and mobile bridge routes do not consistently enforce authentication.
- Provider execution routes have their own bearer checks, but do not protect unrelated routes.

Decision: keep binding on 127.0.0.1:8181. Do not enable Tailscale/LAN/public access until the entire HTTP/WebSocket route inventory has a defined authentication/authorization policy and negative tests. CORS is not authentication.

## Current verified state

- API running hidden as PID 4800, pythonw.exe.
- GET /health returns HTTP 200 and identifies dgm-mat.
- Existing shortcut backed up.
- Immutable mirror C:\ProgramasGodMode\DGM-MAT-FULL-MIRROR was not accessed.

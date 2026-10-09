# DGM-MAT Headless Backend Service
<!-- Path: C:\\ProgramasGodMode\\DGM-MAT\\docs\\architecture\\HEADLESS_BACKEND_SERVICE.md -->

Date: 2026-10-09
Status: IMPLEMENTED LOCALLY; VALIDATION IN PROGRESS

## Purpose

The backend API is an independent Windows background process. It must not require
the desktop dashboard, mobile cockpit, a visible terminal, or the autonomous
cognition/action-queue loops to be running.

## Entry point

`scripts/autostart/backend_service.py` provides three actions:

- `start`: starts only `uvicorn core.api.api_server:app`, with stdin detached,
  stdout/stderr appended to `logs/backend-service.log`, and a hidden Windows
  process console. It waits up to 12 seconds for a verified `/health` response.
- `status`: checks the API health endpoint and reports the saved PID if present.
- `stop`: terminates only a process whose metadata verifies it is the expected
  Python/Uvicorn API process. If identity cannot be verified, it refuses to kill it.

The manager records process metadata atomically in
`storage/runtime/backend_service.json`. It does not store credentials.

## Safety boundaries

- Default bind remains `127.0.0.1:8181`; no public or LAN exposure is enabled.
- This service manager does not start the cockpit, cognition loop, action queue,
  providers, browser automation, shell agents, or repair tasks.
- Existing APIs outside the provider-execution routes still require a separate
  authentication review before any remote-network exposure. CORS restrictions
  alone are not authentication.
- The process manager does not create a Windows Scheduled Task or logon startup
  entry. Persistent auto-start will be a separate, explicit and testable step.
- If `/health` is already served, start is idempotent. If the recorded API PID
  is alive but unhealthy, start refuses to create a duplicate and points to logs.
- Log output is local and must be reviewed for secrets before expanding logging.

## Validation gate

Before enabling auto-start or mobile connectivity, verify Python/Uvicorn
availability, successful start/status/stop, duplicate-start behavior, failure
logging, and that the dashboard can close without stopping the API.

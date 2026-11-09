# DGM-MAT Headless Backend Service

<!-- Path: C:\\ProgramasGodMode\\DGM-MAT\\docs\\architecture\\HEADLESS_BACKEND_SERVICE.md -->

Date: 2026-11-09
Status: IMPLEMENTED; Windows full-runtime startup and queue-worker readiness verified on the operator PC.

## Purpose

The DGM-MAT backend is the primary runtime. The PC cockpit is an optional presentation client and is not the execution authority. The runtime can operate headlessly, without an open dashboard or visible terminal.

## Entry point

`scripts/autostart/backend_service.py` provides three actions:

- `start --mode api`: starts only `uvicorn core.api.api_server:app`. This is an HTTP-only mode and does not claim that the mission runtime or durable action-queue worker is running.
- `start --mode full`: starts the installed `installed/DGM-MAT.exe --headless` when present, otherwise `python main.py --headless`. It applies bounded repository-learning defaults and keeps automatic external AI help disabled unless explicitly configured.
- `status --mode api|full`: checks HTTP health; full mode additionally exchanges a local bootstrap session and verifies `/runtime/status` reports `running` and `/runtime/queue` reports `worker_alive=true`.
- `stop`: terminates only a process tree whose metadata verifies as the DGM-MAT API or full runtime. If process identity cannot be verified, it fails closed.

The manager records process metadata atomically in `storage/runtime/backend_service.json` and appends stdout/stderr to `logs/backend-service.log`. It does not store credentials in the state file.

## Full-mode defaults

Unless the operator has explicitly set an override, full mode configures:

- `DGM_REPOSITORY_LEARNING_ENABLED=1`
- `DGM_REPOSITORY_LEARNING_BATCH_SIZE=2`
- `DGM_REPOSITORY_LEARNING_MAX_DEPTH=6`
- `DGM_REPOSITORY_LEARNING_REFRESH_SECONDS=1800`
- `DGM_REPOSITORY_LEARNING_COMMAND_TIMEOUT=4`
- `DGM_AUTONOMY_HELP_ENABLED=0`

Full mode is loopback-only. It refuses a non-loopback host. The manager waits up to 180 seconds for full runtime readiness (120 seconds for API-only mode). A failed readiness check causes the newly spawned child to be terminated and the stale state file to be removed; an existing unhealthy DGM-MAT process prevents a second process from being started.

## Cockpit relationship

The cockpit is not started by `backend_service.py`. It is a separate optional client, launched only after the backend is ready, using:

```powershell
DGM-MAT.exe --cockpit-only
```

The cockpit must not be treated as a second brain or runtime. Closing it must not stop the headless backend. A process tree may contain both a PyInstaller parent and its child process; this is not, by itself, evidence of duplicate installations. Verify executable path, command line, parent/child relationship and listener ownership before terminating anything.

## Safety boundaries

- Default API bind is `127.0.0.1:8181`; full mode explicitly refuses network-exposed hosts.
- Automatic external AI help remains disabled by default. Free-provider consultation is separate, opt-in, quota-limited and never has a paid fallback.
- Repository learning is metadata-oriented and bounded; it does not grant a coding agent write access.
- The local bootstrap token is read only for a readiness session exchange and is never written to the service state file or log.
- The service manager does not create a Windows Scheduled Task or logon startup entry. Persistent auto-start remains a separate, explicit and testable step.
- CORS restrictions alone are not authentication. Do not expose the API to a LAN or public network without a separate authentication and transport-security review.
- Logs remain local and must be reviewed for secrets before expanding logging.

## Windows acceptance evidence — 2026-11-09

On the operator PC, the installed executable was updated from the verified Windows CI artifact. The previous installation was preserved in an update backup.

The first launch attempt exposed a stale recorded PID and an unhealthy API. Investigation established that the two `DGM-MAT.exe` entries were the parent/child processes of the frozen executable, not two independent installations. Only the identified `--cockpit-only` launchers were closed before starting the managed full runtime.

The official service manager then reported:

```text
STARTED: DGM-MAT full runtime ready; queue worker alive at 127.0.0.1:8181; mode=full; PID=4072
HEALTH_BODY={"status":"healthy","service":"dgm-mat"}
HEALTHY=True
DGM_BACKEND_AND_COCKPIT_STARTED
```

The cockpit-only process was launched after the backend passed readiness. This is process-launch evidence, not a visual/UI interaction test. A mission execution through an external coding agent has not been validated by this acceptance run.

## Remaining acceptance gates

1. Confirm the cockpit renders and communicates with the live backend through a visual/UI check.
2. Execute one bounded read-only mission end to end and inspect its durable mission checkpoint and queue receipt.
3. Implement and validate a separate isolated-worktree coding-agent executor, with explicit approval, fixed test commands, independent QA, immutable diff evidence and rollback.
4. Only after these gates pass, consider a longer autonomous mission. A running API or queue worker alone is not evidence that Codex/Claude coding execution is integrated.

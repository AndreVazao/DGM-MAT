# DGM-MAT — live mission dispatch E2E

**Date:** 2026-11-04  
**Runtime:** local Windows PC, API on `127.0.0.1:8181`  
**Purpose:** prove that an authorized local client can submit a bounded read-only mission and observe its durable completion.

## Authentication and worker

- `GET /health`: HTTP 200, `status=healthy`.
- `POST /auth/session`: HTTP 201 using the protected PC-local bootstrap credential.
- Session scopes: `local-client`, `operator`. No bearer token was printed or persisted.
- Queue worker: `worker_alive=true`.
- Registered handler: `MISSION_EXECUTION` (one handler).

## Missions executed

| Mission | Action | Handler | Final status | Evidence |
|---|---:|---|---|---|
| `mission_2b8c2f60` | 1079 | `local_research` | COMPLETED | 250 files scanned; 8 snippets across 3 files; 0 external calls; 0 commands |
| `mission_1cb8ed52` | 1080 | `local_research` | COMPLETED | 250 files scanned; 8 snippets across 3 files; 0 external calls; 0 commands |
| `mission_884fb111` | 1081 | `architecture_summary` | COMPLETED | CLI reported overall PASS; initial console status label exposed a truncation-reporting defect |
| `mission_30b0fd26` | 1082 | `architecture_summary` | COMPLETED | Final CLI E2E reported `Overall: PASS` and `Mission: ... / COMPLETED` |

The first two local-research runs completed quickly and returned limited/noisy search evidence. They prove dispatch and bounded local search, not deep autonomous engineering.

## Queue integrity

| Metric | Before | After |
|---|---:|---:|
| Completed mission checkpoints | 22 | 26 |
| Queued mission checkpoints | 4 | 4 |
| Failed historical mission checkpoints | 557 | 557 |
| Completed queue actions | 130 | 134 |
| Queued historical queue actions | 801 | 801 |
| Failed queue actions | 1 | 1 |
| Rejected queue actions | 2 | 2 |

The four new actions were auto-approved by the existing read-only intent allowlist and completed. The 801 historical queued actions were not approved, replayed, rejected, or modified.

## Findings and limitations

1. The local bootstrap-to-session path works; the client does not need to bypass pairing or authentication.
2. The runtime auto-approves only the existing bounded read-only intent allowlist. The diagnostic client itself never calls an approval endpoint.
3. The queue worker is alive and returns to idle after the finite mission completes.
4. The current mission engine still has no generic executor for arbitrary engineering work. Unsupported goals can be decomposed into proposed subtasks, but the code explicitly records that those proposals are not executed.
5. This E2E proves real read-only mission dispatch and completion. It does **not** prove continuous planning, autonomous code changes, or unattended multi-hour development.

## Change in this PR

The diagnostic CLI now accepts a custom goal only when the local intent router classifies it into the read-only auto-run allowlist. It checks session scopes and worker health before submission, refuses unsupported/mutating/approval-required goals, confirms the runtime auto-approved the new action, and reports the durable terminal status even when the checkpoint preview is truncated.

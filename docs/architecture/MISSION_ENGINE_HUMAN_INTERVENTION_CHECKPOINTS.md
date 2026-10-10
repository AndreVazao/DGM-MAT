# DGM-MAT — MissionEngine: persistent human handoff and checkpoints

Date: 2026-10-10
Status: **INTEGRATED LOCALLY; NOT EXPOSED REMOTELY**

## Implemented

- `MissionStatus.WAITING_FOR_USER` pauses a single mission. `process_missions()` skips that mission without applying execution timeout; it continues iterating other missions in the same scheduler cycle.
- `MissionStatus.CANCELLED` is a terminal state for an explicit reject/cancel response.
- `MissionEngine` owns a durable `HumanInterventionQueue` at the runtime task storage path.
- `request_human_intervention()` writes the request to SQLite, records request ID/step/status/checkpoint timestamp in the mission JSON, then persists/syncs the mission as `WAITING_FOR_USER`. Duplicate calls return the existing active handoff for that waiting mission.
- Mission JSON now persists subtask IDs, descriptions, status, agent/task links and timestamps; `_load_missions()` reconstructs subtasks on restart.
- Mission checkpoint JSON writes are atomic (temporary file + flush/fsync + replace), reducing risk of a truncated mission record after power/process failure.
- Startup reconciles active SQLite handoffs against persisted mission records, recovering the crash window where a queue request was committed but the mission checkpoint was not yet replaced.
- `resolve_human_intervention()` checks mission/request/step identity and the decision actor identity, requires a consumed decision, handles reject/cancel as terminal, allows `NEED_CONTEXT` to create a new bounded handoff, and will only mark an approval resumed if the caller explicitly supplies a successful verification and short non-sensitive evidence.
- Running mission timeout is measured from `execution_started_at` when available, rather than from original creation time. A human wait itself is not timed out by the mission scheduler.

## Deliberate limits

- This is a local MissionEngine interface only. There is no HTTP/WebSocket endpoint, no mobile notification, no device pairing, and no remote browser-control path.
- `verified=True` is a trust boundary: it must only be provided by a trusted local verifier after checking actual external state. The current change does not implement that browser/service verifier or a secure phone interaction channel.
- A resumed mission continues its existing persisted checkpoint/state. It does not imply that arbitrary unfinished subtasks are automatically executed; current scheduler/workers remain responsible for real task execution.
- CAPTCHA/MFA stays manual. No secrets in prompts, logs, memory, SQLite or generic message bus. `reason`, `instructions`, and verification evidence must be non-sensitive.
- API stays loopback-only until global HTTP/WebSocket authentication, device pairing/scopes, revocation, replay protection and client migration are completed.

## Test plan

New file: `tests/autonomy/test_mission_human_intervention.py`.

Acceptance cases: waiting mission persists and does not time out; other missions remain schedulable; subtasks survive engine recreation; approval cannot resume without verified outcome; verified approval resumes; rejection cancels and cannot be replayed; orphan queue request recovers; interrupted verification requires a fresh check; verified resume recovers across restart. The focused battery passed **22 tests** including the existing intervention queue, local auth, mission lifecycle and cross-process contract. The broader suites `autonomy`, `organization`, `contracts` and `security` also passed: **104 tests total, 0 failures**. `compileall` and `git diff --check` passed.

## Next brain-first work

1. Confirm tests and inspect actual diffs.
2. Add concurrency/restart fault-injection around request creation, mission JSON write and response consumption; improve atomic checkpoint writes if required.
3. Implement a local read-only status/query contract for the future PC cockpit, with no remote exposure.
4. Audit and close HTTP/WebSocket auth gaps before any mobile/API exposure.
5. Build PC cockpit against a local-only API, then Android APK only after device pairing and transport security.

Cost/safety: FREE-ONLY / PAID-DENY. No public ports. Do not modify `C:\\ProgramasGodMode\\DGM-MAT-FULL-MIRROR`.

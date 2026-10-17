# DGM-MAT Backend End-to-End Stabilization Gate

Date: 2026-10-17  
Base audited: `main` at `db1334bd72bcfd963087054550aaa53228d01403`  
Branch: `fix/backend-end-to-end-stabilization-2026-10-17`  
Status: **AUDIT IN PROGRESS — NOT VERIFIED END TO END**

## Scope

The only current delivery goal is a stable DGM-MAT backend and a minimal PC chat cockpit that submits natural-language missions, shows the actual mission lifecycle, and returns evidence-backed results or a clear blocker. Digital office visuals and the mobile cockpit are explicitly out of scope until this gate passes.

## Evidence inspected

- `core/api/api_server.py`: FastAPI app includes runtime, governance, provider-execution, mobile and local-auth routers; `/health` only confirms the API process responds, not that mission execution works.
- `core/api/runtime_api.py`: `POST /runtime/missions` calls `mission_engine.create_mission`; `GET /runtime/missions` returns mission records. There is no mission-action approval/rejection endpoint in this router. Its existing `/approvals/{request_id}` delegates to `ApprovalManager`, not the durable `SafeActionQueue` action ID used for mission execution.
- `core/autonomy/mission_engine.py`: a created mission is placed in `SafeActionQueue`; normal actions remain unapproved. The only observed auto-approval is a string match for goals containing both “lista” and “repos”. An approved generic mission is decomposed into subtasks and marked RUNNING; decomposition alone does not prove that the subtasks were executed.
- `core/runtime/safe_action_queue.py`: the consumer selects only actions with status APPROVED and `is_approved == True`. Therefore, a queued mission cannot execute through this consumer until an approval path changes its durable queue record.
- `core/autonomy/active_runtime/cognition_loop.py`: its cycle code explicitly records `PLANNED — EXECUTION NOT WIRED` when no task execution adapter is connected. The runtime bootstrap inspected in `core/runtime/runtime.py` starts the SafeActionQueue consumer but does not visibly construct/start this CognitionLoop. This must be resolved by tracing every startup entry point before changing lifecycle ownership.
- `cockpit/widgets/command_console.py`: a non-blocking HTTP console exists and posts a directive to the mission API, but its success message means only “mission created”; it does not wait for or prove a final result.
- `cockpit/main_window.py`: the desktop window is a multi-tab operations console with a command panel, not the intended minimal chat cockpit.

## Blocking findings

1. **Mission creation is not mission completion.** The current cockpit reports the ID after creation only. It must show the real status and result/error, and must not imply execution succeeded just because the POST succeeded.
2. **Normal mission execution is approval-gated without a matching operator path in the mission API.** The existing approval endpoint addresses a different approval subsystem. Do not bypass governance by auto-approving arbitrary user prompts.
3. **Generic task decomposition is not an execution adapter.** Subtasks being present or a mission being RUNNING is not evidence that an agent performed the work. The runtime must connect each supported mission type to a real executor, or return a precise unsupported/blocked status.
4. **Runtime lifecycle ownership is unclear.** Trace whether and where `CognitionLoop` is instantiated and started; ensure one consumer/loop owner, deterministic startup/shutdown, and no duplicate execution.
5. **A successful API health response is insufficient.** Health, authentication, persistence, mission processing, execution, output delivery, and restart recovery require separate assertions.
6. **Runtime/API auth is a separate safety gate.** Do not expose this API to LAN, Tailscale or the public internet as part of this work. Keep it local until every HTTP route and WebSocket has a tested auth contract.

## Required end-to-end contract

A test is only PASS when it proves the following sequence against an isolated temporary runtime store:

1. Runtime boot reports its real state; missing required subsystems are reported as degraded, not nominal.
2. A cockpit-style authenticated request submits a natural-language directive and receives a mission ID.
3. The mission is durably stored and is visible through the read API.
4. The intent is classified into a supported action type; unsupported intent is explicitly reported rather than falsely “completed”.
5. The durable queue and governance path produce an explicit, auditable decision. No broad or phrase-based auto-approval is permitted.
6. The registered executor runs exactly once and records output, status, timestamps and errors.
7. The cockpit retrieves and displays the actual final result, failure, or human-intervention requirement.
8. A runtime restart preserves mission history and does not silently replay an uncertain side effect.
9. Duplicate submissions, invalid input, timeouts, missing providers, missing handlers, denied approval, queue failure, and corrupt persisted checkpoints have deterministic outcomes.
10. Shutdown stops consumers cleanly and restart starts exactly one consumer.

## Required test layers

### A. Unit tests
- Intent classification and unsupported-intent responses.
- Mission state transitions and valid/invalid transitions.
- Durable queue approval/rejection, no execution before approval, and exactly-once/duplicate handling.
- Executor success/failure/timeout and structured result persistence.
- Mission serialization, corrupted checkpoint isolation, and restart recovery.

### B. API contract tests
- Health versus runtime health distinction.
- Authenticated mission creation, mission listing/detail, queue state, approval/rejection, and result retrieval.
- 401/403 on missing/invalid scope for protected routes; WebSocket auth denial.
- Invalid payloads and short/blank goals must not return a misleading “created successfully” result.

### C. End-to-end tests
- Start the runtime in an isolated process with temporary storage.
- Submit a harmless deterministic read-only test mission from the same HTTP path used by the PC cockpit.
- Assert durable creation, policy decision, actual executor invocation, terminal result, cockpit-visible output, and restart persistence.
- Run a second case where execution fails and prove the cockpit displays the real error without claiming success.
- Run a third case that requires operator input and prove the mission pauses rather than hangs or falsely completes.

### D. Desktop cockpit tests
- One primary conversation view, no dependence on terminal use.
- HTTP runs off the GUI thread.
- Each submitted message is correlated to a mission ID.
- UI displays QUEUED / APPROVAL_PENDING / RUNNING / WAITING_FOR_USER / COMPLETED / FAILED / CANCELLED accurately.
- Polling/reconnection does not duplicate mission submissions.
- User and executor text are HTML-escaped.
- Offline, authentication failure, and unknown timeout outcome are explicit.

## Completion rule

Do not call the backend “stable”, “fully functional”, or “end-to-end verified” until the above test layers have been run against the actual code and their results are recorded. Repository inspection and static assertions are useful evidence but are not a substitute for running the test suite, starting the API/runtime, exercising the executor, and verifying the Windows cockpit.

Do not start the digital office or mobile cockpit until this gate is closed.
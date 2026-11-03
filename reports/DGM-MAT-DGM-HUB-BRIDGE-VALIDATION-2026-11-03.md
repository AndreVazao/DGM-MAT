# DGM-MAT ↔ DGM-HUB MultiChat — local validation

**Date:** 2026-11-03  
**Branch:** `feat/dgm-hub-multichat-agent-bridge-2026-11-03`  
**Local worktree:** `C:\ProgramasGodMode\_worktrees\dgm-hub-multichat-agent-bridge-2026-11-03`  
**Authoritative checkout:** left untouched.

## Automated Windows validation

Exact focused command:

```powershell
python -m compileall -q core/organization/dgm_hub_multichat_bridge.py core/api/dgm_hub_agents_api.py core/api/api_server.py core/api/security_policy.py tests/organization/test_dgm_hub_multichat_bridge.py tests/api/test_dgm_hub_agents_api.py tests/security/test_api_global_auth_enforcement.py tests/security/test_api_security_policy.py
python -m pytest -q tests/organization/test_dgm_hub_multichat_bridge.py tests/api/test_dgm_hub_agents_api.py tests/security/test_api_security_policy.py tests/security/test_api_global_auth_enforcement.py tests/autonomy/test_mission_specialist_lifecycle.py tests/organization/test_specialist_collaboration.py tests/organization/test_foundation.py
git diff --check
```

**Result (final PR head `a74be4837558f4162fa5353492182b66c8ff136a`):** compileall passed; **72 tests passed in 5.90s**; `git diff --check` passed; exit code 0. GitHub Actions Focused PR Validation run #90 also completed successfully. Only existing FastAPI `on_event` deprecation warnings were emitted.

The tests cover:
- loopback-only Hub URL, exact port 8770, no remote host or alternate local service;
- allowlisted provider IDs and observer/room-leader semantics;
- no automatic provider enablement;
- provider readiness and task correlation;
- no retry or paid fallback on rate limits;
- model identity from transport metadata, not model self-claims;
- operator-only route inventory and global session enforcement;
- durable command audit before any provider request, with session/correlation metadata; fail-closed behavior if the initial audit cannot be written; real authenticated HTTP middleware path exercised in tests;
- free-capacity confirmation, secret-like context rejection, untrusted result persistence and truthful partial completion;
- existing specialist collaboration and internal message-bus regressions.

## Live DGM-MAT API → DGM-HUB consultation

Using the new DGM-MAT route with an authenticated operator session, one real Hub task was submitted to all four external providers.

Hub task: `c2b40190-298e-42de-bf37-3cda8223a0ab`.

| Provider | Hub outcome | DGM-MAT ledger outcome |
|---|---|---|
| Codex Free | timeout at Hub's 75 s CLI limit | `WAITING_FOR_FREE_CAPACITY`; no result promoted |
| Claude Code/FCC | timeout at Hub's 180 s CLI limit | `WAITING_FOR_FREE_CAPACITY`; no result promoted |
| Kilo Gateway | `ok`, 28.1 s, model `nvidia/nemotron-3.5-lightning:free` | `RESULT_RECEIVED`, untrusted, review required |
| LLM7 | `ok`, 14.25 s, model `gpt-oss:20b` | `RESULT_RECEIVED`, untrusted, review required |

DGM-MAT returned HTTP 200. Two successful answers were persisted in a temporary collaboration ledger and passed to the specialist review-intake method; the other two were paused without retry or paid fallback. The test harness intercepted the internal bus send for this four-provider exercise, so this particular run does not claim durable QA delivery.

A truthful aggregate-status correction was then added: if any selected provider is paused or fails, the API returns `status=partial`, with `successful_count` and `paused_count`; it no longer labels a mixed outcome as fully completed. The regression test passes.

## Free-capacity stop behavior

A subsequent single-provider LLM7 consultation reached the Hub, which returned HTTP 429 Too Many Requests. DGM-MAT returned `status=partial`, stored the collaboration as `WAITING_FOR_FREE_CAPACITY`, and performed no retry or paid fallback. This is expected behavior. The Hub does not expose numeric remaining quota, so the API requires explicit operator free-capacity attestation and records the limitation; it does not claim a quota measurement.

## Durable independent-review intake

A separate local test, using no external provider call, created a specialist packet, recorded a synthetic result through the real `MissionEngine.record_specialist_result` method, and read the message back from the real SQLite-backed internal inbox.

Evidence:
- collaboration state: `RESULT_RECEIVED`;
- one unread message delivered to `agent:bug-hunter`;
- message correlation ID exactly matched the collaboration ID;
- `DURABLE_QA_BUS_PASS=True`.

This proves the durable local handoff path independently of provider availability.

## What is now proven

- DGM-MAT can discover the existing Hub room over loopback.
- An operator-authenticated DGM-MAT route can submit a consultation to selected ready Hub providers.
- Successful provider responses are persisted as untrusted specialist results.
- The existing MissionEngine review-intake method can route a result to the independent Bug Hunter inbox.
- Provider timeouts and HTTP 429 capacity limits are stopped without automatic retries or paid fallback.
- DGM-MAT remains an observer in the Hub room; the operator remains room leader.

## What is not yet proven / remaining gate

- Numeric remaining quotas for Codex, Claude Code, Kilo and LLM7 are not exposed by the Hub; current free capacity is operator-attested, not independently measured.
- Codex and Claude Code timed out on the longer multi-agent review prompt; their CLI timeout/latency needs a separate bounded tuning exercise.
- The Hub task store is process-memory based; a Hub restart during a task loses the task result, which DGM-MAT handles as a failed/paused consultation rather than replaying.
- This bridge is consultative. It does not yet grant external agents write access, apply patches, or execute software repairs.
- Autonomous code work still needs a separate isolated-worktree patch proposal, fixed local test runner, independent QA and explicit promotion approval. No agent write mode is enabled by this change.

No changes were made to the authoritative DGM-MAT checkout or to the uncommitted DGM-HUB integration files.


## Audit hardening addendum

Before any Hub provider request, DGM-MAT now writes a durable `command.requested` audit event containing the authenticated operator session and selected provider IDs. If this initial audit cannot be persisted, the API returns HTTP 503 and refuses to create collaboration packets or contact providers. After the consultation it records `command.completed` with outcome and duration; a failure to write only the completion event is returned as an explicit `audit_warning`, because the initial request record is already durable.

A new authenticated TestClient regression exercises the real API router and session middleware with a controlled Hub transport. It verifies the operator session, untrusted result, and both audit events. The full local regression suite is now **72 passed**.

# Browser Operator approval boundary v1

**Date:** 2026-11-07  
**Status:** Replacement implementation under focused validation  
**Supersedes:** The approval behavior in the original browser-operator PR #236

## Security invariant

A client request must never disable the approval gate by supplying `approval_required=false`.

The direct `POST /browser-operator/tasks` endpoint does not accept that field. Its Pydantic model forbids unknown fields and the endpoint always enqueues with `approval_required=True`. A client attempting to supply the field receives HTTP 422.

The mission-specific `POST /runtime/missions/{mission_id}/browser-task` endpoint may request the existing RUNNING-only automatic-send policy. Before enqueueing it reloads the durable mission checkpoint and rejects missing, terminal or non-RUNNING parents when per-task approval is disabled.

## Shared queue enforcement

The SQLite queue requires a host-supplied mission-status resolver:
- enqueue rejects a missing/unavailable parent checkpoint;
- enqueue rejects terminal parents;
- `approval_required=false` is accepted only when the freshly resolved parent state is exactly `RUNNING`;
- the queue stores `approval_required` as a durable column;
- idempotency compares the approval requirement as part of the task envelope, so a retry cannot change the gate;
- claim-time resolution is repeated immediately before the browser extension receives the task;
- a missing or terminal parent moves queued work to `needs_review`;
- a nonterminal but non-RUNNING parent leaves queued work waiting; no message is sent until it is RUNNING.

This protects the low-level queue as well as both HTTP entry points. The client cannot supply the resolver result.

## Existing-task migration

Older queue databases gain an `approval_required` column with a safe default of true. Existing rows previously auto-approved by the internal `mission-engine` creator are backfilled as `approval_required=false` so the new claim-time parent check applies to them. Existing explicit operator approvals remain approval-required.

## Negative acceptance tests

- Direct API rejects client-controlled `approval_required=false`.
- Queue rejects bypass for APPROVAL_PENDING, missing and terminal missions.
- Queue accepts bypass only for RUNNING parent missions.
- Claim rechecks parent status and moves terminal/missing-parent work to review.
- Approved tasks wait while the parent is non-RUNNING.
- Idempotency keys cannot change approval policy.
- Mission route rejects missing and terminal parent checkpoints.
- Existing lease expiry still moves ambiguous browser sends to review without replay.

## Scope and limits

This gate authorizes only the browser extension's visible-UI task queue. It does not bypass provider login, MFA, CAPTCHA, rate limits or provider controls. It does not read browser cookies, tokens or browser databases. A lease expiry remains ambiguous and is never automatically replayed.

Local acceptance with authenticated ChatGPT, Grok, Gemini, DeepSeek and Qwen tabs is still required when the operator PC is online.

## Extension-side send boundary (PR #271)

The extension no longer exposes a popup message composer or a direct `DGM_SEND_MESSAGE` content-script listener. A local `window.confirm()` is not an approval record and cannot authorize a provider send. The only send-capable content-script message is `DGM_EXECUTE_BROWSER_TASK`, reached by the service worker after the server has claimed a task from the durable, approval-gated queue.

The popup toggle only permits processing of tasks already approved by DGM-MAT; it does not create or approve tasks. CI must run both complementary fixtures:
- `test_message_send.js`: rejects the removed direct-send message type;
- `test_browser_operator_task.js`: proves the approved server-claimed path still sends once, validates provider/conversation identity and handles blocked/unverified/timeout states without replay.


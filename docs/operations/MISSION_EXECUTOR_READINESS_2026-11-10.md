# Mission executor readiness and approval preflight

**Date:** 2026-11-10  
**Issue:** #341  
**Status:** Integrated in PR #342; Windows build and Mission E2E Regression Gate passed on 2026-11-10.

## Contract

Mission creation must establish that a real execution handler exists before it creates an approval-capable queue action.

- Built-in read-only intents are ready only when the intent router identifies a supported fixed handler.
- The isolated GitHub worktree sync remains executable but always requires explicit operator approval.
- Typed organization missions require an available roster agent, an explicitly registered runtime handler, and all capabilities declared by the fixed task-kind policy.
- Unknown, unsupported, or currently unstaffed work enters `WAITING_FOR_CAPABILITY`. No approval request or queue action is created.
- The mission checkpoint retains the readiness result, reason code, required agent/capabilities where relevant, and approval-block reason.
- When a compatible handler is later registered, a subsequent operator request can be submitted again; this preflight does not silently resume or replay waiting missions.
- Legacy or stale queue actions are still checked by the execution handler. A plan or approval is never treated as execution evidence.

## Safety boundaries

This change does not add a generic shell executor, interpret task descriptions as commands, auto-approve mutations, or bypass existing approval requirements. Existing allowlists, durable task receipts, checkpoint validation, and failure reporting remain authoritative.

## Verification evidence — 2026-11-10

- PR #342 was integrated into main at `fdae0ce102c35d15ff3c4564039bdd4396aa139a`.
- Windows executable build: SUCCESS, workflow run [42806219347](https://github.com/AndreVazao/DGM-MAT/actions/runs/42806219347).
- Mission E2E Regression Gate: SUCCESS, workflow run [42806219343](https://github.com/AndreVazao/DGM-MAT/actions/runs/42806219343).
- The installed executable was subsequently verified on PC-Vazao-Anjos; authenticated `GET /runtime/status` and `GET /runtime/queue` returned HTTP 200, with runtime running and worker alive.
- These checks validate build, regression gate and runtime health. They do not establish completion of a new read-only mission with a durable receipt.

## Verification targets

- Unsupported mission: waiting for capability, no queue action, no approval.
- Typed mission without a compatible worker: waiting for capability, with required capability evidence.
- Typed mission with a compatible registered worker: queue action created and read-only auto-approval permitted by the existing allowlist; completion still requires a durable worker receipt.
- Cockpit polling stops on `WAITING_FOR_CAPABILITY` instead of timing out while the mission is deliberately waiting.

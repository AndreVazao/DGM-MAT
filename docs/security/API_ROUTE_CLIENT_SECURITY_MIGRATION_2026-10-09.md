# DGM-MAT API Security Boundary — Route/Client Inventory
**Date:** 2026-10-09  
**Status:** Audit and migration design only; no API behavior changed.

## Scope and safety
The headless API remains bound to `127.0.0.1:8181`. This audit did not enable LAN/Tailscale/public binding and did not modify runtime source files. The immutable `C:\\ProgramasGodMode\\DGM-MAT-FULL-MIRROR` was not accessed.

## Route inventory

| Boundary | Routes | Exposure / risk | Current client dependency |
|---|---|---|---|
| Liveness | `GET /health` | Minimal service metadata; intentionally public for local process health check | `scripts/autostart/backend_service.py` |
| Root realtime | `WS /ws` | No authentication; connection is accepted and can receive manager broadcasts | `cockpit/realtime_client.py`, streaming clients |
| Runtime realtime | `WS /runtime/ws` | Same unauthenticated WebSocket boundary | Compatibility clients |
| Runtime read endpoints | `GET /runtime/health,status,state,truth,reality,degradation,repo_scan,memory/stats,memory,providers,governance,autonomy,workspace/scan,obsidian/index,missions,approvals,queue` | Some responses expose workspace, memory, mission, provider and queue details; repo/workspace scans can be expensive | Desktop cockpit widgets; tests |
| Runtime mutations | `POST /runtime/missions`, `POST /runtime/approvals/{request_id}` | Can create missions and make approval decisions without authentication | Desktop cockpit / potential clients |
| Mobile bridge | `/mobile/status`, `/mobile/threads`, `/mobile/capabilities`, `/mobile/capability-scout` | Conversation content/history and capability discovery; writes and discovery actions are unauthenticated | Mobile bridge/service; intended mobile cockpit |
| Governance | `/governance/audit/workspace`, `/governance/audit/self`, `/governance/repair/self/plan`, `/governance/repair/self/apply`, `/governance/conversations/analyze` | Workspace metadata and potentially mutating self-repair; apply requires confirm=true but no authentication | No complete client inventory established |
| Provider execution | `/provider-execution/requests`, `/approvals`, `/approvals/{id}/decision`, `/execute` | Has distinct API/operator bearer checks and durable approval gate; credentials must be configured privately | Integration tests; intended governed provider clients |
| Static mobile UI | `/app/*` if configured/present | Same-origin static assets; security depends on protected API boundary | Optional PWA shell |

CORS currently permits all origins, methods and headers (without credentials). CORS is not authentication and does not protect WebSockets.

## Client compatibility evidence
- `cockpit/realtime_client.py` and related clients connect directly to `ws://127.0.0.1:8181/ws` without an authentication handshake.
- Desktop widgets make direct HTTP calls to `/runtime/providers`, `/runtime/missions`, `/runtime/status`, `/runtime/approvals`, `/runtime/workspace/scan`, and `/runtime/truth` without bearer headers.
- `tests/integration/test_api_endpoints.py` explicitly expects unauthenticated `/runtime/repo_scan` and `/runtime/memory/stats` to return 200.
- Provider execution tests already assert missing credentials fail closed and role separation works.
- Therefore, adding a global auth dependency immediately would knowingly break current desktop clients and existing compatibility tests. Leaving the current routes unauthenticated is also not acceptable for any remote exposure.

## Recommended migration — additive, fail-closed, no remote exposure yet

### Phase A — auth primitives and test contract
1. Add a dedicated API security module with explicit public health allowlist and separate roles/scopes: local-client, operator, read-only.
2. Never use the provider tokens as global API credentials. Do not log secrets, authorization headers, conversation content, or session tokens.
3. Add route inventory tests that fail when a new HTTP or WebSocket route is unclassified.
4. Add negative tests for absent, malformed, invalid, expired/revoked and wrong-scope credentials. Health is the only intended unauthenticated route.
5. Keep bind address loopback-only throughout this phase.

### Phase B — desktop migration without silent trust bypass
1. Add a local pairing/bootstrap flow that generates a high-entropy secret on the PC and stores it with user-only Windows ACLs.
2. Migrate desktop HTTP and WebSocket clients to use the new credential/session contract; do not infer trust solely from localhost or Origin.
3. Provide a temporary, explicit compatibility mode only for local development/tests, disabled by default in installed runtime and never usable when non-loopback binding is enabled.
4. Test the full desktop flows (missions, approvals, provider status, workspace scan and realtime events) before enforcing authentication globally.

### Phase C — mobile pairing and operator sessions
1. Pair mobile through a short-lived, single-use code shown locally on the PC; exchange it for a revocable, scoped session token.
2. Use TLS for remote traffic; do not expose raw HTTP over Tailscale. Verify actual certificate/serve configuration before claiming secure transport.
3. Authenticate both WebSocket paths during handshake, enforce origin policy for browser clients, and close sockets on session revocation/expiry.
4. Keep operator-only actions (repair apply, approval decisions, capability discovery that triggers work) behind explicit operator scope and audit them.

### Phase D — enforce and verify
1. Protect all sensitive HTTP routes and both WebSockets.
2. Replace wildcard CORS with a small explicit allowlist for actual browser clients; keep native desktop access separate from browser-origin policy.
3. Add bounded request sizes, rate limits, structured security events and redaction.
4. Run API, mobile, desktop, WebSocket and full-repository tests; only then consider a controlled remote-access trial.

## Acceptance gates before any remote binding
- All routes and sockets classified.
- Unauthenticated and wrong-scope requests denied by default.
- Local desktop workflows pass with auth enabled.
- Mobile pairing, expiry, revocation and reconnect tested.
- TLS verified end-to-end; no HTTP fallback for remote sessions.
- No credentials in Git, logs, reports or client source.
- Loopback-only remains the operational default unless all gates pass.

## Validation performed
- Read-only inspection of the five API modules and relevant desktop clients/tests.
- Baseline targeted tests: `python -m pytest -q tests\\integration\\test_api_endpoints.py tests\\integration\\test_provider_execution_api.py` — **7 passed**, exit code 0 (11.04 s). Only existing FastAPI/Starlette deprecation warnings were reported.
- No runtime/API code changed in this audit; no source backup was needed.

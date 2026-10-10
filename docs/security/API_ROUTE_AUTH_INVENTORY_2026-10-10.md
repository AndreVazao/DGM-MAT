# Path: C:\ProgramasGodMode\DGM-MAT\docs\security\API_ROUTE_AUTH_INVENTORY_2026-10-10.md

# DGM-MAT API route inventory and authentication gate
Date: 2026-10-10

## Purpose
Record the currently declared FastAPI routes before global authentication and cockpit/mobile client migration. This is a static AST inventory of Python decorators in `core/api/*.py`; it is not a penetration test and does not prove that a route is safe.

## Verified server boundary
- Default bind: `DGM_API_HOST=127.0.0.1`, port `8181`.
- `core/api/api_server.py` configures `CORSMiddleware` with `allow_origins=["*"]`.
- `POST /auth/session` is explicitly loopback-only and checks the bootstrap bearer credential, origin allowlist, and rate limit.
- `LocalSessionManager` can issue/validate/revoke short-lived scoped sessions, but existing routes do not consistently call it. Session issuance is not global enforcement.
- Two WebSocket routes currently accept connections without session authentication: `/ws` and `/runtime/ws`.
- The `/app` static UI may be mounted when its files are found. The UI being static does not protect the API endpoints it can call.
- Keep loopback binding; do not override to LAN/Tailscale/public until the auth gate below is satisfied.

## Route inventory (40 declarations)

| Method | Path | Current classification / required gate |
|---|---|---|
| GET | `/health` | Minimal health only; public exception, loopback server boundary |
| WEBSOCKET | `/ws` | Must require authenticated session before joining event manager |
| POST | `/auth/session` | Existing exception: loopback + bootstrap bearer + origin allowlist + rate limit |
| GET | `/governance/audit/workspace` | Operator scope |
| GET | `/governance/audit/self` | Operator scope |
| GET | `/governance/repair/self/plan` | Operator scope; plan may reveal internal details |
| POST | `/governance/repair/self/apply` | High-impact mutation; operator + explicit action approval |
| POST | `/governance/conversations/analyze` | Operator scope; treat content as private |
| GET | `/mobile/status` | Paired-client read scope; redact local network/provider details as needed |
| GET | `/mobile/threads` | Paired-client conversation-read scope |
| POST | `/mobile/threads` | Paired-client conversation-write scope |
| GET | `/mobile/threads/{thread_id}` | Paired-client conversation-read scope; enforce ownership |
| POST | `/mobile/threads/{thread_id}/messages` | Paired-client conversation-write scope; enforce ownership |
| POST | `/mobile/threads/{thread_id}/rename` | Paired-client conversation-write scope; enforce ownership |
| GET | `/mobile/capabilities` | Paired-client read scope or explicitly documented public metadata |
| POST | `/mobile/capability-scout` | Operator/paired-client action scope; bounded mission creation |
| POST | `/provider-execution/requests` | Operator scope; create governed request only |
| GET | `/provider-execution/approvals` | Operator approval-read scope |
| POST | `/provider-execution/approvals/{approval_task_id}/decision` | Approval-decision scope; identity, expiry, replay and request binding |
| POST | `/provider-execution/execute` | Execution scope plus durable approval and zero-cost policy gate |
| WEBSOCKET | `/runtime/ws` | Must require authenticated session before joining event manager |
| GET | `/runtime/health` | Authenticated local-client read scope; consider minimal public health only if needed |
| GET | `/runtime/status` | Local-client read scope |
| GET | `/runtime/state` | Local-client read scope |
| GET | `/runtime/truth` | Local-client read scope; may expose operational details |
| GET | `/runtime/reality` | Local-client read scope |
| GET | `/runtime/degradation` | Local-client read scope |
| GET | `/runtime/repo_scan` | Operator scope; filesystem/repository metadata |
| GET | `/runtime/memory/stats` | Local-client read scope; avoid exposing memory content |
| GET | `/runtime/memory` | Local-client read scope |
| GET | `/runtime/providers` | Local-client read scope; no secret values |
| GET | `/runtime/governance` | Operator scope |
| GET | `/runtime/autonomy` | Local-client read scope |
| GET | `/runtime/workspace/scan` | Operator scope; filesystem metadata |
| GET | `/runtime/obsidian/index` | Operator scope; private vault indexing |
| POST | `/runtime/missions` | Mission-create scope; bounded input, cost policy and audit metadata |
| GET | `/runtime/missions` | Mission-read scope; enforce operator/project ownership |
| POST | `/runtime/approvals/{request_id}` | Approval-decision scope; bind identity and request |
| GET | `/runtime/approvals` | Approval-read scope |
| GET | `/runtime/queue` | Operator scope; queue data may reveal internal operations |

## Known clients to migrate
Static scan found at least these desktop call sites:
- `cockpit/main_window.py`: initial `/runtime/truth` hydration.
- `cockpit/providers/management_widget.py`: `/runtime/providers`.
- `cockpit/streaming/realtime_client.py`: WebSocket and its HTTP helper.
- `cockpit/widgets/command_console.py`: `/runtime/status` and `/runtime/missions`.
- `cockpit/widgets/operational_dashboard.py`: multiple legacy runtime calls; review every route and remove obsolete duplicate clients only after proving callers/tests.
- Other API consumers must be found with a full repository search before enabling enforcement.

## Required implementation sequence
1. Create one shared dependency/middleware contract that validates bearer sessions, expiry, required scope, and revocation; fail closed on missing/invalid credentials.
2. Define route-by-route scopes and explicit exceptions. Never trust a client-supplied scope or identity.
3. Replace wildcard CORS with a small explicit allowlist; CORS is not authentication and non-browser clients must still authenticate.
4. Authenticate WebSocket before calling `manager.connect`. Do not put bearer tokens in query strings, URLs, event payloads or logs.
5. Migrate every PC cockpit caller and the mobile web client. Ensure refresh/re-auth does not log tokens and that the Core remains independent from UI lifecycle.
6. Add negative tests for missing, invalid, expired, revoked and insufficient-scope credentials on every route; test both WebSockets; test origin denial, replayed approval, ownership binding and rate limits.
7. Only after tests pass, add a read-only pending-human-interventions endpoint with read scope. Decision endpoints require separate write scope and trusted local verification; remote clients must never submit a `verified=True` assertion.
8. Re-test the live loopback API. Do not enable LAN/Tailscale/public bind as part of the auth migration unless separately authorized and proven secure.

## Explicitly out of scope in this checkpoint
- No code-level global authentication changes.
- No new intervention HTTP/WebSocket endpoint.
- No remote bind or Tailscale Serve changes.
- No Android APK.
- No provider calls, paid API, credit consumption or GitHub Actions.

Source implementation note: `docs/architecture/PC_COCKPIT_NONBLOCKING_COMMAND_CONSOLE.md`.


## Follow-up 2026-10-10 — enforcement implemented in source
- Added core/api/auth_middleware.py and wired it into core/api/api_server.py after route registration. Private inventoried HTTP/WebSocket routes now require short-lived bearer sessions; GET /health remains public and POST /auth/session remains the protected bootstrap exchange.
- Removed wildcard CORS and restricted it to the local desktop origins. Both WebSockets now require Authorization header.
- Added cockpit/api_client.py and migrated desktop HTTP clients; WebSocket client exchanges bootstrap to a short-lived token in memory only. No token in URL/logs.
- Added tests/security/test_api_global_auth_enforcement.py (7 tests).
- Important: running API process was not restarted; new enforcement is implemented in source but not yet verified as active in the live server. Do not expose remote access before controlled restart + live E2E checks.
- Browser/mobile pairing is not implemented. Static /app shell may load but its private API calls are protected.
- Detailed implementation note: docs/security/GLOBAL_API_AUTH_ENFORCEMENT_2026-10-10.md.

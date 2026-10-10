# Path: C:\\ProgramasGodMode\\DGM-MAT\\docs\\security\\GLOBAL_API_AUTH_ENFORCEMENT_2026-10-10.md

# DGM-MAT â€” global API authentication enforcement
Date: 2026-10-10

## Implementation
- Added `core/api/auth_middleware.py`, a fail-closed ASGI middleware for inventoried HTTP and WebSocket routes.
- `GET /health` remains the only public API route.
- `POST /auth/session` remains a protected exception handled by the existing loopback-only bootstrap exchange, strict origin check and rate limit.
- Other inventoried HTTP routes require a valid in-memory bearer session with the appropriate server-defined scope. Missing/invalid/expired/revoked sessions return HTTP 401; insufficient scope returns HTTP 403.
- Both `/ws` and `/runtime/ws` require the bearer token in the WebSocket Authorization header. Query-string tokens are not supported.
- Unclassified known routes fail closed. Unknown paths remain FastAPI 404s.
- CORS wildcard was removed. Allowed origins are limited to `http://127.0.0.1:8181` and `http://localhost:8181`; methods and headers are explicit.
- Added `cockpit/api_client.py`: reads the bootstrap credential from the protected local file, exchanges it for a 30-minute session, caches the session in process memory only, refreshes after HTTP 401 and never logs or persists tokens.
- Migrated desktop cockpit HTTP callers (initial state, provider status, command console and operational dashboard) to the authenticated client.
- Migrated realtime WebSocket handshake to an Authorization header; no token is put in the URL.
- The static `/app` shell is served without an access token because it contains no private data; its API calls remain protected. Browser/mobile pairing is not implemented in this checkpoint.

## Security tests
New test file: `tests/security/test_api_global_auth_enforcement.py`.
Covers:
- only `/health` is public;
- missing session rejected;
- valid local session accepted;
- revoked session rejected;
- insufficient scope rejected;
- unauthenticated WebSocket rejected;
- authenticated WebSocket accepted;
- untrusted CORS preflight rejected.

## Important live-runtime boundary
The API server already running on the PC was deliberately not restarted during this change. Therefore these tests validate the new code through FastAPI's in-process TestClient, but do not prove that the live process has loaded the middleware. The existing live process must be restarted through a controlled, authorized maintenance step before the new enforcement is active in production. Until that step and a live end-to-end test are complete:
- do not expose the API to LAN/Tailscale/public access;
- do not claim the live API is already enforcing these changes;
- keep the current loopback-only binding;
- do not start the Android APK work yet.

## Remaining security gates
1. Confirm the bootstrap file exists and its Windows ACL restricts access to the intended local user/service; do not print its contents.
2. Plan and execute a controlled API restart, without stopping the independent Core or losing mission state.
3. Validate live HTTP and WebSocket behavior: health public; private route 401 without session; private route 200 with session; websocket 1008 without session and successful handshake with session.
4. Add/verify auth-client handling for the static browser/mobile app through an explicit pairing ceremony. Do not put the bootstrap token in JavaScript, static files, query strings, logs or persistent storage.
5. Review per-route scope mapping, rate limiting for sensitive actions, revocation operations and audit events.
6. Add test coverage for both WebSockets, all registered routes, expired/revoked tokens, replay/ownership rules for approval endpoints, and cross-origin browser behavior.
7. Only then plan Tailscale pairing and the Android APK.

## Constraints
No public bind, port opening, reverse proxy, Tailscale Serve or Vercel tunnel was enabled. No GitHub Actions, paid API, external provider or credits were used. Core process lifecycle remains independent from the desktop UI. Never touch `C:\\ProgramasGodMode\\DGM-MAT-FULL-MIRROR`.

## Final validation
- Global auth enforcement tests: 7 passed.
- Combined security + cockpit suite after final console patch: exit code 0 (33 tests observed).
- Broader autonomy/organization/contracts/security/cockpit suites: exit code 0.
- compileall and git diff --check passed.
- Live API process was not restarted; source enforcement is not yet confirmed active in production.



## Live maintenance gate check — 2026-10-10
- Live /health returned healthy. Listener is pythonw.exe running uvicorn core.api.api_server:app on 127.0.0.1:8181; this is the pre-change process and has not loaded the new middleware yet.
- Mission queue summary only: 385 total; 380 FAILED, 3 RUNNING and 2 QUEUED. Because five missions are non-terminal, the API/Core process was NOT restarted. No mission goals or outputs were read or printed.
- Bootstrap file exists. ACL shows explicit FullControl only for SYSTEM and the current Windows user; secret contents were not read.
- Next safe step: inspect why the 3 RUNNING/2 QUEUED missions remain non-terminal, allow them to finish or obtain explicit maintenance approval, then perform a controlled API restart and verify live 401/200/WebSocket behavior.


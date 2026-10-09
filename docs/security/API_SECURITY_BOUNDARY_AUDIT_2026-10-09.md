# DGM-MAT API Security Boundary Audit
<!-- Path: C:\ProgramasGodMode\DGM-MAT\docs\security\API_SECURITY_BOUNDARY_AUDIT_2026-10-09.md -->
Date: 2026-10-09
Status: LOOPBACK-ONLY CONTAINMENT VERIFIED; REMOTE ACCESS NOT APPROVED

## Findings
1. core/api/api_server.py configures CORS with allow_origins=["*"]. CORS is a browser policy, not authentication; this must not be treated as an access-control boundary.
2. Root /ws and compatibility /runtime/ws WebSockets currently accept connections without an authentication dependency.
3. Existing runtime, governance and mobile-bridge routes do not consistently declare authentication dependencies. They can expose workspace/runtime information and can invoke state-changing operations.
4. Provider execution routes have their own bearer-token checks, but those checks do not secure unrelated routes.
5. The current service binds to 127.0.0.1:8181; direct health verification returned HTTP 200. This prevents ordinary direct LAN connections to the API while loopback binding remains in force, but does not protect against other local processes or local browser-origin risks.

## Decision
- Keep the service bound to loopback.
- Do not configure Tailscale/LAN binding, public tunnels, reverse proxies, or mobile connectivity yet.
- Do not add a global authentication middleware without mapping existing clients and tests; that could break the current desktop workflows or create false security.
- Before remote access: inventory every HTTP route and WebSocket; define authentication/session lifecycle, CSRF/origin protections where applicable, per-route authorization, rate limits, audit logs, and tests for unauthenticated denial.
- Replace wildcard CORS with explicit origins when the desktop/mobile client origins are finalized. This is additional browser protection, not a substitute for authentication.

## Evidence gathered
The route inventory covered api_server.py, runtime_api.py, governance_api.py, mobile_bridge.py, and provider_execution_api.py. Both WebSocket endpoints and wildcard CORS were found. The API is running only on loopback at the time of audit.

## Acceptance gate
Remote access is not accepted until all exposed routes/WebSockets enforce the chosen security model and negative tests prove that requests without valid credentials are denied.

# Path: C:\ProgramasGodMode\DGM-MAT\docs\architecture\PC_COCKPIT_NONBLOCKING_COMMAND_CONSOLE.md

# PC Cockpit — non-blocking command console

Date: 2026-10-10  
Scope: desktop cockpit only. The Core process and API are not restarted by this change.

## Implemented

- HTTP requests for mission creation and runtime status run in a dedicated Qt worker thread; the GUI thread does not wait on network timeouts.
- Input and send controls are disabled while a request is in flight, preventing duplicate clicks from launching concurrent submissions.
- Runtime-offline state is retained when a worker completes; a completed request must not silently re-enable an offline console.
- The UI reports timeout as an unknown outcome and tells the operator to inspect Missions before retrying. It does not claim that a timed-out mission failed or succeeded.
- Mission creation is reported as successful only when the response has a success status and a mission ID.
- User-entered directives are no longer written to the general observability log by this widget.
- Text inserted into the chat display is HTML-escaped to prevent user/provider text from becoming active markup.
- The console uses the explicit loopback address `127.0.0.1:8181`.

## Validation

- Cockpit test suite: 10 tests passed, including worker-thread execution, HTML escaping, offline-control state, and realtime integration.
- Syntax compilation and `git diff --check` passed.
- Wider autonomy, organization, contracts, security and cockpit suites completed with exit code 0 in this checkpoint.

## Security boundary — not cleared for remote access

This change does not claim that the API is globally authenticated. The current API server still has wildcard CORS, and legacy runtime/mobile/governance/provider routes are not consistently protected by the local session manager. The local bootstrap endpoint issues a short-lived session, but issuing a session is not equivalent to enforcing it on every HTTP route and WebSocket.

Therefore:

1. Keep the API bound to loopback by default.
2. Do not add a human-intervention HTTP endpoint or decision/mutation endpoint yet.
3. Do not expose the API through LAN, Tailscale Serve, a public address, or a reverse proxy until global HTTP/WebSocket authentication, origin policy, scopes, revocation, replay protection and client migration have been implemented and tested together.
4. CAPTCHA, MFA and external verification remain manual. Session tokens and bootstrap credentials must never be put in mission prompts, general logs, persistent memory or rendezvous metadata.
5. The human-intervention queue remains local-only. A remote caller must not be allowed to assert `verified=True` and resume a mission.

## Next gate

Complete a route inventory and global authentication contract; migrate the PC cockpit and WebSocket clients to short-lived scoped sessions; add denial tests for every protected route and WebSocket; then implement a read-only pending-interventions view. Only after those checks pass should intervention decisions, pairing, Tailscale access and the Android APK proceed.


Route-by-route security inventory and required migration gate: `docs/security/API_ROUTE_AUTH_INVENTORY_2026-10-10.md`.

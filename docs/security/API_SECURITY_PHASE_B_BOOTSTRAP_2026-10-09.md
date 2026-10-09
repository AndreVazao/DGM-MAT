# Path: C:\ProgramasGodMode\DGM-MAT\docs\security\API_SECURITY_PHASE_B_BOOTSTRAP_2026-10-09.md

# DGM-MAT — Phase B: local session bootstrap

## Current state

- The API registers `POST /auth/session` through `core/api/local_auth_api.py`.
- The route only issues a short-lived local session after a bootstrap bearer credential is verified.
- Session scopes are selected by server policy; the caller cannot request elevated scopes.
- Session tokens are held in memory as digests by `LocalSessionManager`; restarting the backend invalidates sessions.
- The route is loopback-only. This is not a completed migration of existing API routes: existing HTTP and WebSocket endpoints remain outside global session enforcement.
- Do not expose the API through LAN, Tailscale, reverse proxies, or the public internet at this stage.

## Provision the bootstrap credential

Run `scripts/autostart/install_local_bootstrap_credential.ps1` from an elevated or normal PowerShell session under the Windows account that runs DGM-MAT. The script generates a cryptographically random 64-byte secret (128 hexadecimal characters), writes it without a trailing newline to:

`%LOCALAPPDATA%\DGM-MAT\security\bootstrap.token`

The script applies explicit Windows ACLs for the current account and SYSTEM, disables inherited ACLs on the security directory and credential file, does not display the secret, and refuses to overwrite an existing credential unless deliberately invoked with `-Force`.

The API reads this file at request time. If it is absent or invalid, session issuance fails closed. Keep the file local; do not commit it, copy it into logs, or send it through chat. Rotating the credential invalidates future exchanges using the old value, but does not revoke sessions already issued; restart the backend to invalidate all process-local sessions.

## Validation and remaining work

Focused tests cover session issuance, invalid/missing credentials, origin rejection, malformed payloads, session-manager behavior, and route inventory. These tests validate the endpoint and helpers, not a full security boundary for the API.

Remaining before remote pairing:
1. Migrate all legitimate PC clients to request and retain short-lived sessions safely.
2. Add route-level HTTP and WebSocket enforcement by scope, with denial tests.
3. Add session revocation/logout, audit events, and lifecycle handling.
4. Review Origin/CSRF behavior, rate-limit persistence, and credential rotation.
5. Test the installed service restart and verify the live process serves the new route.
6. Keep the backend loopback-only until all items above are verified.

## Safety note

A successful `/auth/session` exchange does not mean the other API routes are authenticated. Do not describe this phase as complete remote security.

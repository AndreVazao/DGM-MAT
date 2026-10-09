# DGM-MAT API Security Phase A — Inventory Enforcement
**Date:** 2026-10-09  
**Status:** Implemented; authentication is NOT globally enforced yet.

## Changes
- Added `core/api/security_policy.py` with an explicit scope vocabulary and route inventory for HTTP routes, both WebSockets, docs and the optional mobile static mount.
- Added a constant-time bearer comparison helper that rejects absent/empty configuration and malformed token syntax. It does not issue sessions or change existing provider token behavior.
- Added `tests/security/test_api_security_policy.py`. It fails if a new route appears without a classification and asserts only `GET /health` is classified public.
- Classified repository/workspace scans, vault indexing, mission creation, approvals, mobile writes/capability discovery and self-repair as operator-scoped in the policy inventory.
- Existing client and API behavior is unchanged in this phase.

## Important limitation
These classifications are an inventory contract, not enforcement. Existing desktop/mobile clients still lack the new DGM-MAT session credential. Provider execution retains its separate API/operator credentials. Do not expose the API outside loopback and do not claim the API is secured by this module.

## Next
Implement PC-local session bootstrap, migrate desktop HTTP and WebSocket clients, then enforce authentication on sensitive HTTP and WebSocket routes with negative and compatibility tests. Mobile pairing remains blocked until TLS and revocation are verified.

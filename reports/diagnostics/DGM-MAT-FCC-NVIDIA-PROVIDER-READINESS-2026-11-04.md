# FCC / NVIDIA NIM Provider Readiness — 2026-11-04

## Result

A free-tier model route is available in the NVIDIA model catalog, but the current local FCC proxy configuration is not safe to activate. The new DGM-MAT adapter is implemented and tested with a local mock server only. It remains disabled by default.

## Evidence

- FCC server 6.10.4 is installed and configured for NVIDIA NIM.
- Active model route: `nvidia_nim/nvidia/nemotron-3.5-super-vl-120b-a12b`.
- No paid provider fallback was observed in the current default route.
- NVIDIA's model catalog currently marks Nemotron 3.5 Super VL as a Free Endpoint. Hosted use remains subject to NVIDIA API Trial Terms and rate limits:
  - https://build.nvidia.com/nvidia/nemotron-3.5-super-vl-120b-a12b
  - https://docs.api.nvidia.com/nim/reference/nvidia-nemotron-3_5-super-vl-120b-a12b
- FCC currently binds `0.0.0.0:8082`; earlier local inspection reported proxy authentication disabled / no usable strong API token. This is rejected by the adapter.
- The current FCC API uses `ANTHROPIC_AUTH_TOKEN` for proxy authentication; a blank value disables authentication. Secret values are masked in the admin config response.
- FCC's current model list exposes gateway-prefixed IDs; the adapter checks the exact advertised variants rather than assuming the raw provider model ID.
- Ollama is not running; port 11434 is closed. Available physical memory was approximately 0.76 GB, below the adapter's configured minimum for local inference.
- Plain Claude Code authentication is not active.
- The FCC server was stopped after inspection. No inference request was made.

## Implementation

- Added `FccNvidiaProvider`, an Anthropic-compatible local proxy adapter.
- Provider is registered only with explicit `DGM_FCC_NVIDIA_ENABLED=1`.
- Health requires loopback bind, matching active port, a strong vault credential, unauthenticated 401/403 plus authenticated model discovery, the exact free-model allowlist, safe Claude tier routes and matching active server state.
- Chat requests have bounded input/output, no tools, no shell and no file access; redirects and unknown provider options are rejected.
- SQLite local budget: 5 calls/day, 25,000 reserved tokens/day, 4,096 reserved tokens per request.
- Every inference must first pass the existing provider quota policy; direct ungoverned chat is refused.
- No automatic fallback to paid providers.

## Verification

Provider and governance tests passed:
- FCC adapter health and security rejection cases.
- Active bind and port checks.
- Auth enforcement and authenticated model discovery using FCC's actual gateway model ID format.
- Rejection of paid/unverified tier routes.
- Daily budget reservation, persistence, concurrency and exhaustion.
- Anthropic-compatible chat request shape.
- No-tools contract and direct-call quota rejection.
- Default-off provider registration and explicit opt-in.
- GovernedProviderService integration.

No real inference was executed. The adapter remains inactive until FCC is secured and its proxy token is stored in the DGM-MAT vault.

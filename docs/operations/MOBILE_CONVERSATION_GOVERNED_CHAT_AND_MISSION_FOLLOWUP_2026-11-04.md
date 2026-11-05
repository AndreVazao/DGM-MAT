# Mobile conversation and governed mission follow-up — 2026-11-04

## Purpose

The mobile thread API is the operator's persistent conversation surface. This change makes ordinary conversation capable of using a deliberately opt-in, governed free-tier provider and makes mission state changes visible when the thread is read again.

## Governed conversational AI

The feature is disabled unless:

- `DGM_MOBILE_GOVERNED_CHAT_ENABLED=1`
- `DGM_FCC_NVIDIA_ENABLED=1` (when the selected provider is `nvidia_nim`)
- FCC is bound to loopback, requires a strong proxy token, uses the verified free model route, and the same token is stored in the DGM-MAT credential vault.

Optional provider selection:

- `DGM_MOBILE_GOVERNED_PROVIDER=nvidia_nim`

The service uses `GovernedProviderService` and `ProviderRequestPolicy`. It does not call provider adapters directly. A provider must be explicitly registered, currently healthy, verified as free-tier, within its quota, and able to reserve its own quota. No paid fallback, tool calls, shell, filesystem or browser operations are exposed.

Only ordinary chat messages use this conversational provider path. Actionable requests continue through deterministic intent routing and the durable mission/approval queue. A model response cannot authorize or execute an action.

Before any external chat request, the service:

- checks the explicit opt-in flag;
- checks recent thread content for secret-like values and refuses external transmission if found;
- sends only the most recent eight user/assistant messages, bounded to 7,600 characters;
- adds a system instruction to preserve context, speak PT-PT, and never claim execution without runtime evidence;
- uses a unique request ID and the governed provider quota/rate policy.

If the provider is unavailable, disabled, unhealthy, out of quota, or the request is blocked, the existing local-only response path remains in place.

## Mission follow-up in conversation

Reading `GET /mobile/threads/{thread_id}` now refreshes linked mission checkpoints from durable storage. When a mission's status or action status changes, one assistant update is appended to the same thread.

The update distinguishes queued/approved/running/completed/failed/cancelled states. A completion message is emitted only when the durable mission checkpoint is actually `COMPLETED`; failed work is never retried automatically. The update is idempotent across repeated thread reads.

## What this does not yet enable

- It does not turn an LLM response into permission to execute code.
- It does not add a generic code-generation or patch-application handler to MissionEngine.
- Unsupported implementation requests remain blocked or consultative until a separately reviewed generic executor is connected.
- FCC is not activated or reconfigured by this change. The feature remains opt-in and the previously observed unsafe FCC bind/token configuration must be repaired first.
- No background worker is started by this change.

## Verification

The implementation is covered by unit tests for:
- governed free-provider opt-in and policy use;
- secret-like conversation content blocking external transmission;
- disabled-by-default readiness reporting;
- mission completion update persistence and idempotency;
- existing conversation, auto-help, and intent-routing boundaries.

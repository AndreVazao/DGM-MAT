# Path: C:\ProgramasGodMode\DGM-MAT\docs\security\ZERO_COST_PROVIDER_POLICY_2026-10-09.md

# DGM-MAT — Zero-Cost Provider Policy
Date: 2026-10-09
Status: **partially enforced; browser free-tier routing not yet implemented**

## Binding rule

DGM-MAT must use local resources first. If local resources cannot solve the task, it may use only a provider whose free-tier status, billing mode, remaining quota, and quota reservation are explicitly verified. Paid APIs, paid fallbacks, credit consumption, upgrades, and subscriptions are blocked by default. If pricing or quota is unknown, fail closed. If the free quota is exhausted, wait for reset or use another verified free route; never silently switch to paid.

## Route order

1. Local code, tests, repository memory, installed tools, and local models (Ollama only when resource checks allow it).
2. A legitimate browser session for a provider's free mode, only after a compliant browser adapter and quota/status verification exist.
3. Another verified free provider with capacity.
4. Defer the task and record a concrete help request if no free route remains.

The route order is a design requirement; it must not be reported as fully operational until end-to-end tests prove it.

## Enforced in this change

- Provider execution policy now requires capabilities.cost_profile == "free", config.billing_mode == "free_tier", and config.cost_verified is True.
- Free quota must have known integer quota_used and positive integer quota_limit; exhausted quota blocks before adapter invocation.
- A provider adapter must implement reserve_free_quota() and return exactly True; missing, failing, or exhausted reservation blocks execution. Each production adapter must implement this as an atomic local reservation against its verified quota state. A stale observation alone is not enough.
- The base provider cost profile defaults to "unknown", not a presumed price.
- ProviderCostOptimizer no longer selects a paid model as a fallback. It returns "local-first", a verified free provider ID, or "wait-for-free-capacity".
- Tests prove that paid, unverified, unknown-quota, exhausted-quota, and non-reservable routes do not invoke the provider adapter.

## Reality and limitations found during the audit

- The governed provider HTTP execution route is the only direct ProviderBase.chat() call found in the core source scan; it now applies the zero-cost preflight before the adapter call.
- The mobile conversation runtime tries local Ollama first (with memory checks) and otherwise uses deterministic fallback text. It does not yet route to browser-based free AI sessions.
- core/connectors/adapters/AIClient2API_adapter.py and gpt4free_adapter.py are empty skeletons. They are not a verified browser-free integration and must not be treated as working providers.
- The current provider registry initializes from saved configuration but does not auto-register active external adapters. No production free-tier adapter with a verified quota reservation was found.
- Therefore this change establishes a fail-closed cost boundary and safe selection behavior, **not** a completed multi-browser AI fallback. Until a real adapter implements the contract and is tested, external provider execution should remain blocked.
- ProviderCostOptimizer is a selector primitive; the runtime must still call it from a real route planner to deliver end-to-end local-first behavior.

## Required tests before enabling a browser provider

- No provider call on unknown cost, unknown quota, paid billing mode, exhausted quota, failed reservation, approval failure, storage failure, or provider unavailability.
- Quota reservation is atomic and persists across process restarts or multiple workers, or the provider's official quota endpoint is checked immediately before execution.
- No automatic API fallback from browser mode; no retry after quota errors; reset time is recorded only when supplied by reliable provider evidence.
- Browser automation follows provider terms and does not bypass authentication, CAPTCHAs, anti-bot controls, free-tier limits, or account restrictions.
- Secrets and session cookies remain local, never enter prompts/logs/repository, and external calls disclose the minimum necessary context.
- A task stops or asks for user help when all verified free routes are exhausted.

## Safety boundary

This policy does not authorize remote API exposure. Existing HTTP/WebSocket authentication and session enforcement work remains a separate blocker before any remote cockpit pairing.


## Enterprise architecture clarification (2026-10-09)

This financial policy applies regardless of organizational maturity: external AIs may be temporary specialist collaborators, while DGM-MAT remains the orchestrator and must retain validated lessons in its own memory. The internal-first order is local code/tools/memory/models, then legitimate free browser sessions, then another verified free route, then wait/ask for help. Paid adapters may be available for future configuration, but FREE-ONLY / PAID-DENY remains the default and requires specific explicit user authorization to change. Full organizational, recruitment and self-improvement requirements are in `docs/DGM-MAT_ENTERPRISE_AUTONOMY_AND_ZERO_COST_CHARTER_2026-10-09.md`.

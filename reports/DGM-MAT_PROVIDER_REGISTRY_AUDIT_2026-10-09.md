<!-- Path: C:\ProgramasGodMode\DGM-MAT\reports\DGM-MAT_PROVIDER_REGISTRY_AUDIT_2026-10-09.md -->

# DGM-MAT Provider Registry and Runtime Audit — 2026-10-09

## Scope and safety

This audit began from canonical commit `f102ca7` and continued through the narrowly scoped provider-truth fixes listed below. Canonical repository: `C:\ProgramasGodMode\DGM-MAT`; branch: `main`; latest published code commit for this audit: `518c1d1`. Earlier baseline findings are retained where they remain valid; fixed findings are explicitly marked as fixed.

The historical source for each modified provider/recovery contract was preserved in `C:\ProgramasGodMode\DGM-MAT-OS\archive` before canonical edits. `C:\ProgramasGodMode\DGM-MAT-FULL-MIRROR` was not accessed or modified. Credential material was not read.

## Executive status

- Recovery success is no longer reported unless an action succeeds and the repair chain is non-empty and exception-safe.
- Provider API now distinguishes endpoint success from registry state and only treats availability as reported when the snapshot marks it as an actual observation (`availability_observed`), not merely because an `available` boolean exists.
- The base provider health check no longer pretends that an invocation is a real health observation.
- Provider registration now rejects mismatched names and silent replacement of an existing adapter.
- The legacy provider-sync facade now fails closed (`False`) instead of importing the unverified sync implementation; the old implementation and related artefacts are preserved in DGM-MAT-OS, but the other legacy source files have not been removed from canonical yet.
- Provider integrations remain in safe-off posture: the registry is explicit-registration-only, and no productive registration call was found in the audited canonical source. No provider was installed or activated by this work.
- Full pytest suite after the availability-observation correction completed with **196 collected tests, 196 progress dots, and exit code 0**. The focused suite after that correction completed with **18 passed, 0 failed**.

## Canonical state and runtime evidence

- Repository: `C:\ProgramasGodMode\DGM-MAT`
- Branch: `main`
- Initial audit baseline: `f102ca7` — `refactor: make provider health and discovery reality based`
- Latest audit code commit: `518c1d1` — `fix: fail closed for legacy provider sync`
- The initial runtime check found `http://127.0.0.1:8181/runtime/providers` refused the connection and no Python runtime process was present. The runtime was not started by the audit. This is historical evidence from the initial check, not a claim about its present state.
- Historical provider registrations and provider-mesh activity in logs dated 2026-10-07 are not proof that the currently quarantined adapters exist or work.

## Findings and remediation

### P1 — Recovery previously reported success without doing recovery — FIXED

The original `ProviderRecovery.recover_provider()` only logged an intention and returned `True`. The original `RuntimeRecovery.recover()` similarly reported success without a verified restart. `RepairChain.execute()` also treated an empty chain as success and did not safely convert exceptions into failure.

**Fix:** commit `dfdf058` (`fix: make recovery outcomes reflect verified actions`).
- Provider and runtime recovery now return `False` until real recovery actions and verification exist.
- Empty repair chains, failed steps, and exceptions return `False`.
- Seven deterministic regression tests cover these false-success paths.
- Exact original files preserved in DGM-MAT-OS commit `b473985`.

### P1 — Provider API conflated endpoint success with provider operation — FIXED

Previously, `/runtime/providers` returned `status: success` even when no providers were registered, which could be misread as operational health.

**Fix:** commit `3d6d782` (`fix: expose truthful provider subsystem state`).
- The response retains existing fields for compatibility.
- It adds `provider_subsystem` state, registered count/names, reported-availability count, and an explicit `availability_reported` flag.
- States distinguish an empty registry, registered providers with no availability report, and reported availability.
- The API's own success is not evidence that a provider is healthy or reachable.

### P2 — Base health-check timestamp was misleading — FIXED

The base `ProviderBase.check_health()` cannot prove remote health, but previously updated `last_check` whenever called.

**Fix:** commit `cb3359d` (`fix: separate provider health attempts from observations`).
- `last_check_attempt` records invocation of the base health check.
- `last_check` is reserved for an actual health observation.
- The base implementation retains `unknown` status and cannot promote an unverified provider to available.
- Exact pre-change file preserved in DGM-MAT-OS commit `60e91da`.

### P1/P2 — Availability API could mistake a default boolean for an observation — FIXED

The first API truth correction still treated `available: false` as equivalent to “no availability was reported”, while the reality snapshot always emitted `available: false` for unregistered source files and deferred checks. The boolean therefore could not distinguish a default from a measured result, and a false availability result was not counted as a report.

**Fix:** commit `dcbedfb` (`fix: report provider availability only when observed`).
- `RealitySnapshotService` emits `availability_observed: false` by default.
- It sets the marker only when a recognized health result (`ok`, `degraded`, or `error`) is accompanied by a nonzero `ProviderBase.health_metrics.last_check` observation timestamp.
- Unregistered source presence, deferred checks, and base `unknown` checks do not become reported availability.
- The API counts observation records independently from the number currently reported available, so an observed unavailable/error state is still a real report.
- Added regression tests for source-only providers, base checks without observations, and reported-but-unavailable providers.
- Exact pre-change files preserved in DGM-MAT-OS archive commits `4d5c3ee` and `eca0f9f` (archive README finalized in `afeecee`).

### P1 — No productive provider registration path found — OPEN / SAFE-OFF

The registry remains explicit-registration-only. The audited source search found no productive `provider_registry.register(...)` call; bootstrap verifies imports but does not register concrete adapters. The agent/runtime path can therefore iterate an empty registry in the current source state.

This is deliberate safe-off behavior after unproven adapters were quarantined. It also means external model-provider functionality is not currently proven to be wired into the canonical runtime. Do not install, import, or auto-promote adapters without a separately governed provider-service contract.

### P2 — Registry contract gaps — FIXED

The previous `register(name, adapter)` allowed a registry key different from `adapter.name` and silently replaced a different adapter at the same key.

**Fix:** commit `d7c9b59` (`fix: enforce explicit provider registry contract`).
- Missing name / non-`ProviderBase` still raises `TypeError`.
- A key that differs from `adapter.name` raises `ValueError`.
- Replacing a registered provider with a different instance raises `ValueError`.
- Registering the same instance under the same name remains idempotent.
- Added three regression tests.
- Exact pre-change registry file preserved in DGM-MAT-OS commit `c528d45`.

Still worth reviewing separately: the priority list retains legacy names such as `poisongpt`; `load_configs()` applies config only to already registered providers and silently ignores unknown names. Neither issue justifies auto-loading provider code.

### P1/P2 — Legacy routing, benchmark, and sync artefacts remain unproven; archive preserved, canonical quarantine pending

Call-site search found no productive canonical consumers for the fixed/heuristic benchmark, scoring, cost, affinity, capability-matrix, or routing classes. The only external source reference to the routing engine was the incompatible stress script. The old provider-sync facade had no productive callers; its implementation called a missing method. Exact originals of 16 source/test files were preserved and hash-verified in DGM-MAT-OS archive commit `ac163bc`.

**Safe-off fix:** commit `518c1d1` changes the compatibility facade to return `False` with a warning until verified synchronization exists. Its replacement regression test passes. The archived legacy performance/routing/sync files themselves remain present in canonical because quarantine/removal has not yet been completed; do not claim they have been deleted.



The following modules contain fixed, heuristic, incomplete, or incompatible behavior and must not be represented as measured production capabilities:

- `core/providers/performance/provider_benchmark.py`: fixed latency/throughput/success values.
- `core/providers/performance/provider_scoring.py`: constant score.
- `core/providers/performance/provider_cost_optimizer.py`: fixed model choice by task priority.
- `core/providers/performance/provider_affinity_engine.py`: fixed model choice.
- `core/providers/performance/provider_memory_profiles.py`: static name-prefix heuristic.
- `core/providers/performance/provider_capability_matrix.py`: hard-coded capability scores without measurements.
- `core/providers/performance/provider_routing_engine.py`: no productive consumer found in the audit; depends on ungrounded capability data.
- `core/research/provider_benchmarking.py`: method body is `pass`.
- `scripts/stress_test_providers.py`: imports adapters absent from canonical source and expects obsolete interface fields/method signatures.
- `core/provider_sync/provider_memory_sync.py`: calls missing `ProviderSync._sync_provider()`.
- `tests/integration/test_provider_sync.py`: manual validation script expects methods/attributes absent from current `ProviderSync`.
- `core/provider_sync/sync_engine.py`: expects conversation methods/identifiers absent from `ProviderBase`.
- `core/providers/performance/health_monitor.py`: acknowledges that a real ping is needed, calls health checks twice per cycle, and had no productive caller found.
- `ProviderRateControl.allow_request()` is defined/constructed but no enforcement call was found in the audit.

These items require individual call-site and test review before any quarantine or retirement. Preserve exact source in DGM-MAT-OS before removing canonical files.

### P2 — Cockpit provider controls remain partially inactive

The provider management widget is instantiated, but the audit found “Test Fallback” and “Browser Recovery” controls without connected handlers. The widget also falls back to direct registry/vault access, coupling UI to internal authority. Do not connect these controls until a public provider-service/API contract and approval behavior are defined.

### P2 — Installed-provider detection is a narrow file heuristic

`RealitySnapshotService._scan_installed_providers()` recognizes a narrow directory/file naming convention. Source presence does not prove importability, credentials, remote reachability, or health; other valid package layouts may be missed. Any future field should explicitly describe what it observes, rather than claim operational status.

## Test evidence

- Earlier focused baseline: provider sync plus agent boundary — 8 passed.
- Recovery-focused run after the recovery correction — 13 passed.
- Provider/API/recovery/snapshot run before the availability-observation correction — 26 passed, 0 failed.
- Focused run after the availability-observation correction — **18 passed, 0 failed**, process exit code 0.
- Full `python -m pytest -q --disable-warnings` run after the availability-observation correction completed with **196 collected, 196 progress dots, exit code 0**.
- After the legacy sync facade was changed to fail closed, the full suite was rerun: **196 progress dots, exit code 0**. Focused sync/provider/API/reality-snapshot suite: **19 passed, 0 failed**.
- Tests can emit expected warning/error logs while verifying negative paths; those log lines are assertions of failure handling, not failed pytest tests.
- The live runtime endpoint was not available during the initial audit. No credentials were read and no provider adapters were activated.

## Commits and preservation

| Repository | Commit | Purpose |
|---|---|---|
| DGM-MAT | `dfdf058` | Recovery results reflect verified actions |
| DGM-MAT | `3d6d782` | Truthful provider subsystem API state |
| DGM-MAT | `cb3359d` | Separate health attempts from observations |
| DGM-MAT | `d7c9b59` | Enforce provider registry contract |
| DGM-MAT | `dcbedfb` | Report availability only when observed |
| DGM-MAT | `518c1d1` | Fail closed for legacy provider sync |
| DGM-MAT-OS | `b473985` | Preserve original recovery stubs |
| DGM-MAT-OS | `60e91da` | Preserve original provider base health contract |
| DGM-MAT-OS | `c528d45` | Preserve original provider registry |
| DGM-MAT-OS | `4d5c3ee` | Preserve pre-change availability API/snapshot/tests |
| DGM-MAT-OS | `eca0f9f` | Preserve pre-change snapshot tests |
| DGM-MAT-OS | `afeecee` | Finalize availability archive note |
| DGM-MAT-OS | `ac163bc` | Preserve unverified provider routing and sync files |

The archive commits were pushed to `AndreVazao/DGM-MAT-OS`; canonical code commits were pushed to `AndreVazao/DGM-MAT`.

## Remaining recommended order

1. Verify canonical and archive working trees are clean and both branches are synchronized with their remotes.
2. Complete canonical quarantine/removal of the archived legacy performance/routing/sync files only after the remaining security gate permits the operation; exact originals are already preserved in DGM-MAT-OS.
3. Define the public provider-service/API contract before repairing cockpit controls or adding adapters.
4. Audit the legacy `core/provider_sync/provider_health.py` status cache and confirm whether it has any real callers before changing or retiring it.
5. Only then decide whether to implement a verified provider registration/health path or leave the provider subsystem explicitly disabled.

## Change control

All code changes were narrowly scoped to recovery truth, provider API truth, base health timestamps, registry registration invariants, and explicit availability-observation semantics. Regression tests were added for each behavior. Exact original source for edited files was preserved before changes. No adapter was installed or registered, no credential material was read, no destructive cleanup was performed, and no workflow was triggered. `DGM-MAT-FULL-MIRROR` remains untouched.

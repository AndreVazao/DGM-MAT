<!-- Path: C:\ProgramasGodMode\DGM-MAT\reports\DGM-MAT_PROVIDER_REGISTRY_AUDIT_2026-10-09.md -->

# DGM-MAT Provider Registry and Runtime Audit — 2026-10-09

## Scope and method

The initial discovery pass audited the canonical repository after commit `f102ca7` using local file inspection, directory inventory, source-reference searches, existing tests, runtime process inventory, API reachability, and runtime logs. A subsequent narrow recovery-truth remediation is documented below. The immutable `DGM-MAT-FULL-MIRROR` was not accessed or modified.

## Canonical state observed

- Repository: `C:\ProgramasGodMode\DGM-MAT`
- Branch: `main`
- HEAD and `origin/main`: `f102ca7` — `refactor: make provider health and discovery reality based`
- Working tree was clean when checked.
- `ProviderBase` and the governed registry remain canonical; unproven concrete provider adapters are absent from the current `core/providers` source tree.
- Current runtime is not live-verifiable: `http://127.0.0.1:8181/runtime/providers` refused the connection, and the PC process inventory showed no Python runtime process. No attempt was made to start or alter the runtime.

## Confirmed findings

### P1 — Provider recovery could report success without recovery (fixed)

At discovery time, `core/recovery/recovery_engine.py::_execute_chain` added `ProviderRecovery.recover_provider("default")` for a provider crash. The original method only logged an intention and returned `True`; it did not refresh credentials, reopen a browser, check a session, or verify recovery. The original `RepairChain.execute()` also returned `True` for an empty chain and allowed exceptions from steps to escape.

**Fix shipped in `dfdf058`:** provider and runtime recovery now return `False` until real actions and verification exist. Empty repair chains, failed steps, and exceptions now return `False`. Seven regression tests cover the false-success paths. The exact original files are preserved in `DGM-MAT-OS` commit `b473985`.

### P1 — No productive registration path for providers was found

The registry's explicit-registration rule is safer than importing arbitrary source from disk. However, a repository-wide Python source search found no productive call to `provider_registry.register(...)`; the only confirmed registration is in a contract test. `bootstrap_engine._prepare_providers()` validates that the registry module can be imported but does not register adapters. The startup `ProviderAgent -> CoreProviderServiceAdapter -> ProviderRuntime` path therefore iterates an empty registry in the current source state.

This is an intentional safe-off posture after quarantining unproven adapters, but it means external model-provider functionality is currently not wired into the canonical runtime.

### P1 — Provider status endpoint can imply more than it proves

`core/api/runtime_api.py::list_providers` returns `{"status": "success", ...}` when the endpoint succeeds, including when both `providers` and `registered` are empty. `RealitySnapshotService._get_providers_status()` emits no entries when there are no registered adapters and no files matching its narrow adapter-file convention. The endpoint does not distinguish “endpoint worked” from “provider subsystem operational/empty/disabled”.

**Recommendation:** expose explicit registry/subsystem state and a count, while preserving HTTP/endpoint success as a separate field. Do not label the overall runtime healthy solely because the API request succeeded.

### P2 — Health observation timestamp is misleading

`ProviderBase.check_health()` updates `health_metrics["last_check"]` even though the base implementation explicitly cannot prove remote health. Status remains `unknown`, which is correct, but the timestamp can be mistaken for the time of a real health observation.

**Recommendation:** distinguish last check attempt from last successful/observed health result; only advance the latter when a concrete adapter performs a real check.

### P1/P2 — Remaining routing/performance modules are not operational evidence

The following canonical modules are placeholders or contain ungrounded fixed outputs, and repository searches found no productive callers outside their own definitions and the obsolete stress script:

- `core/providers/performance/provider_benchmark.py`: fixed latency/throughput/success-rate values.
- `core/providers/performance/provider_scoring.py`: always returns `95.0`.
- `core/providers/performance/provider_cost_optimizer.py`: returns fixed model names by task priority.
- `core/providers/performance/provider_affinity_engine.py`: always returns a fixed Claude model.
- `core/providers/performance/provider_memory_profiles.py`: static name-prefix heuristic.
- `core/providers/performance/provider_capability_matrix.py`: hard-coded capability scores without measurements.
- `core/providers/performance/provider_routing_engine.py`: no productive consumers found; relies on the ungrounded matrix and an adapter contract that is no longer present in the canonical provider tree.
- `core/research/provider_benchmarking.py`: method body is `pass`.

These should not be described as real benchmarking, measured capability, cost optimization, or production routing.

### P1 — Historical provider stress script is incompatible with current source

`scripts/stress_test_providers.py` imports `core.providers.chatgpt.chatgpt_provider` and `core.providers.claude.claude_provider`, which are absent from the current canonical source tree. It calls `handle_failover` with one argument although the current method requires two, and expects `provider_id` although `ProviderBase` exposes `name`. The script cannot serve as current failover evidence.

### P1/P2 — Legacy provider sync contracts are broken or unverified

- `core/provider_sync/provider_memory_sync.py` calls `ProviderSync._sync_provider()`; that method is absent from the current `core/operator/provider_sync.py`. Exceptions are caught per provider, so `sync_all()` can finish while all sync attempts fail.
- `tests/integration/test_provider_sync.py` expects `track_prompt_lineage`, `prompt_lineage`, `map_identity`, and `identity_map` on `ProviderSync`; the current class exposes none of them. It is a manual `validate()` script, not a pytest-style test.
- `core/provider_sync/sync_engine.py` expects `provider_id`, `list_conversations()`, and `sync_conversation()`, none of which are part of `ProviderBase`. No productive callers were found.
- `core/providers/performance/health_monitor.py` explicitly comments that a real ping would be needed, calls `check_health()` twice per cycle via `broadcast_health()`, and has no productive caller found in source searches.
- `ProviderRateControl.allow_request()` is defined and instantiated by GovernanceEngine, but source searches found no call to `allow_request()`; therefore the provider-specific limiter is not currently enforcing provider requests.

### P2 — Cockpit provider panel is present but only partially functional

`ProviderManagementWidget` is instantiated in `cockpit/main_window.py`. It first calls the runtime API, then falls back to direct Core registry/vault access, coupling UI and authority. The “Test Fallback” and “Browser Recovery” buttons have no connected handlers. With an empty registry and no installed adapters found by the current file-name heuristic, the panel cannot register or operate a provider.

### P2 — Installed-provider detection is a narrow file heuristic

`RealitySnapshotService._scan_installed_providers()` only recognizes immediate child directories containing `<directory-name>_provider.py`. This is not proof that a provider is installed, importable, authenticated, or operational; it can also miss adapters using another valid package layout. The field should represent source presence under an explicit definition, not operational health.

### P2 — Registry contract gaps

- `register(name, adapter)` does not validate that `name == adapter.name`.
- Registering the same key silently overwrites the previous instance.
- The priority list retains legacy names, including `poisongpt`, despite the adapter stack being quarantined.
- `load_configs()` only applies settings to already registered adapters; it silently ignores config entries for unregistered names. No `provider_configs.json` was found under the canonical repository during the file search; runtime overrides were not independently inspected.
- Current contract tests cover unknown status, expired cooldown, no auto-discovery, and explicit registration. The new recovery-truth tests cover false-success paths; API empty-state semantics, timestamp semantics, registry-name mismatch, and legacy sync failures remain untested.

## Test and runtime evidence

- Previously recorded focused tests: `tests/provider_sync` plus `tests/contracts/test_agent_boundary.py`: **8 passed**.
- During follow-up remediation, focused tests for recovery truth, provider contracts, and runtime snapshot passed: **13 passed**.
- Full suite rerun after remediation completed with exit code 0 and progress at 100%; **184 tests passed, 0 failures** (counted from the three pytest progress groups: 72 + 72 + 40).
- Runtime endpoint check at audit time: connection refused on `127.0.0.1:8181`; process inventory showed no Python runtime process. Runtime was not started by this audit.
- Runtime log search found historical provider registrations and provider-mesh/ChatGPT activity from 2026-10-07. This is historical evidence only and must not be treated as proof that the quarantined adapters are present or operational now.
- Credential material under `storage/runtime/governance` was not read.

## Remediation performed — 2026-10-09

The first high-priority recovery-truth defect has now been corrected in canonical source:

- `ProviderRecovery.recover_provider()` returns `False` until a real recovery action and verification exist.
- `RuntimeRecovery.recover()` returns `False` until a real restart and verification exist; the prior implementation was another false-success stub.
- `RepairChain.execute()` returns `False` for an empty chain, a failed step, or a step that raises, instead of letting empty or exceptional paths look successful.
- Added `tests/unit/test_recovery_truth_contract.py` with seven deterministic tests covering these cases and failed recovery recording.
- Exact pre-change copies of the three edited recovery files were SHA-256 checked and preserved in `DGM-MAT-OS/archive/DGM-MAT-unverified-recovery-stubs-2026-10-09/`.

Commits:
- Canonical DGM-MAT recovery correction: `dfdf058` — `fix: make recovery outcomes reflect verified actions`, pushed to `origin/main`.
- Archive preservation: `DGM-MAT-OS` commit `b473985`, pushed to `origin/main`.

## Remaining recommended order of work

1. Define truthful provider state semantics: empty/disabled, registered, loaded, health observed, available.
2. Add tests for `/runtime/providers` and `RealitySnapshotService` empty and registered states.
3. Correct `ProviderBase.last_check` semantics without promoting unknown providers.
4. Quarantine or clearly mark the uncalled fake routing/performance and incompatible sync artefacts, preserving their exact history in `DGM-MAT-OS` before any removal.
5. Repair or retire the cockpit's inactive controls and direct registry/vault fallback only after defining the public provider-service contract.
6. Update the 2026-10-07 provider architecture report as historical, linking this post-`f102ca7` audit.

## Change control

The initial discovery pass was read-only. A subsequent, narrowly scoped recovery-truth fix changed only `core/recovery/provider_recovery.py`, `core/recovery/runtime_recovery.py`, and `core/recovery/repair_chain.py`, with seven regression tests added. Original versions were preserved and hash-verified in `DGM-MAT-OS`. No adapter was installed or registered. No credentials were read. No destructive cleanup, adapter promotion, or workflow was triggered. `DGM-MAT-FULL-MIRROR` remains untouched.

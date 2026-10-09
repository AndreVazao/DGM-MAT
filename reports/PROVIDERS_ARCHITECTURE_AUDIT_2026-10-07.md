# DGM-MAT Providers Architecture Audit — 2026-10-07

> **Historical snapshot — superseded for current runtime/provider-state facts by [DGM-MAT Provider Registry and Runtime Audit — 2026-10-09](DGM-MAT_PROVIDER_REGISTRY_AUDIT_2026-10-09.md).** This document records the topology observed on 2026-10-07; its provider implementation inventory and dynamic-discovery description are not a statement of the current canonical tree. Subsequent safety work quarantined unproven adapters, made discovery observation-only, and kept provider registration explicitly governed. As of the 2026-10-09 audit, no productive provider registration path was found and provider operation must not be inferred from endpoint success or historical logs.

## Decision

**DO NOT physically extract `core/providers` yet.**

Providers are a larger and more coupled subsystem than Agents or Connectors. The correct next step is to establish the provider public contract and authority model before moving implementation code.

## Current topology

### Provider implementations

`core/providers` currently contains:

- ProviderBase and provider implementations:
  - ChatGPT
  - Claude
  - Custom
  - DeepSeek
  - Gemini
  - Grok
  - Ollama
  - OpenAI
  - OpenRouter
  - OpenWebUI
  - PoisonGPT
  - Qwen
  - Z
- browser/recovery support
- local AI fabric:
  - Ollama adapter
  - Open WebUI adapter
  - provider factory
- performance/routing:
  - health monitor
  - affinity
  - benchmark
  - capability matrix
  - cost optimizer
  - memory profiles
  - routing engine
  - scoring
- conversation/knowledge helpers
- session management
- conversation ingestion/synchronization.

### Registry/runtime layer

`core/provider_sync` currently owns:

- ProviderRegistry
- dynamic provider discovery
- configuration persistence
- configuration loading
- provider health support
- memory/conversation synchronization
- sync engine.

`core/providers/provider_runtime.py` is an orchestration wrapper around `provider_sync.provider_registry`.

## Active consumers

Direct active consumers found outside the provider subsystem:

1. `core/agents/service_adapters.py`
   - imports `ProviderRuntime`
   - exposes it through the public Agent `ProviderService` port.

2. `core/api/runtime_api.py`
   - imports `provider_registry`
   - exposes provider management through the runtime API.

3. `cockpit/providers/management_widget.py`
   - imports `provider_registry`
   - this is a frontend-to-Core coupling that must eventually be replaced by API/contracts.

4. Provider-focused tests
   - registry
   - orchestration
   - provider sync
   - provider mesh.

## Coupling findings

### 1. ProviderBase is not standalone

`ProviderBase` imports Core realtime broadcasting and Core credential vault.

Therefore extracting provider implementations without first defining injected services would simply move the Core dependency problem to another repository.

### 2. Registry owns persistence

`ProviderRegistry` imports Core StorageManager and Core logging.

Its configuration authority therefore remains in Core until a persistence/service boundary is defined.

### 3. Dynamic discovery is path-dependent

The current registry scans the relative path `core/providers` and constructs import names such as:

`core.providers.<name>.<name>_provider`

This is incompatible with a clean standalone package and must be replaced by package-aware discovery/registration.

### 4. ProviderRuntime is an orchestration boundary

Agents already consume it through `ProviderService`. This is the strongest existing boundary and should be preserved.

### 5. Cockpit coupling is not acceptable as final architecture

The cockpit currently imports the registry directly. The target architecture is:

`Cockpit -> public API/contracts -> Core provider authority`

not:

`Cockpit -> Core provider registry`.

### 6. Provider ecosystem is larger than "model adapters"

The provider area includes routing, health, cost, memory, local AI, browser recovery, and conversation synchronization. These should not automatically become one giant standalone package.

## Proposed ownership

### DGM-MAT-Providers

Implementation authority for:

- provider adapter implementations
- ProviderBase-equivalent public implementation
- local AI adapters
- provider-specific protocol handling.

### DGM-Contracts

Public contracts for:

- ProviderDescriptor
- ProviderCapability
- ProviderHealth
- ProviderRequest
- ProviderResponse
- ProviderRegistration
- ProviderSelection / routing result.

These should be designed before extraction.

### DGM-MAT Core

Authority for:

- provider registry/service
- credential/security policy
- persistence
- governance
- routing policy
- health aggregation
- approval/security boundaries
- lifecycle/orchestration.

### DGM-Cockpit-Frontend

Must consume provider state through public API/WebSocket contracts rather than importing `ProviderRegistry`.

## Existing public boundary

The existing Agent `ProviderService`:

`run() -> None`

is useful for the current health/sweep operation but is **not sufficient** as the final provider contract.

Do not expand it blindly. Provider request/response semantics must be designed from actual consumers.

## Validation

Provider-focused local suite:

**9 passed**

Validated:

- ProviderRegistry persistence/registration
- provider orchestration
- provider sync
- provider mesh
- Agent provider boundary.

No provider extraction was performed during this checkpoint.

No GitHub Actions were triggered.

FULL-MIRROR was untouched.

## Next gate

1. Inventory actual ProviderRegistry API consumers.
2. Inventory provider request/response methods actually used.
3. Define minimal provider contracts in DGM-Contracts.
4. Introduce Core provider service facade.
5. Remove cockpit direct registry dependency.
6. Adapt Agents ProviderService to the Core facade.
7. Only then extract provider implementations into DGM-MAT-Providers.

This is intentionally a **design/contract gate**, not a physical migration gate.

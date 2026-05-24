# DGM-MAT Architecture Guardrails

This document defines the strict boundaries and rules for the DGM-MAT ecosystem. These rules are mandatory to ensure system stability, modularity, and maintainability.

## 1. Bootstrap Layer
- **Rule:** `BootstrapEngine` is responsible ONLY for preparation (environment check, dependency validation, profile loading).
- **Rule:** `BootstrapEngine` MUST NOT orchestrate UI or long-running services.
- **Rule:** System preparation must be deterministic and capable of running in HEADLESS mode.

## 2. API Layer
- **Rule:** The API Layer (`core/api/`) is a passive interface.
- **Rule:** API endpoints can READ runtime state but MUST NOT modify core state directly.
- **Rule:** The core runtime MUST NOT depend on the API layer for its internal logic.

## 3. UI / Cockpit Layer
- **Rule:** The Cockpit UI is optional and decoupled from the runtime.
- **Rule:** The runtime MUST NOT import UI-specific modules (e.g., PySide6).
- **Rule:** UI failures must not affect the background runtime service.

## 4. Execution & Kernel Layer
- **Rule:** The `Cognitive Kernel` is the sole orchestrator of cognitive tasks.
- **Rule:** Subsystems must communicate primarily via the `Event Bus`.
- **Rule:** No direct agent-to-agent communication; all interactions pass through the Event Bus.

## 5. Memory & Storage
- **Rule:** The `RuntimeStorageManager` is the central authority for path resolution.
- **Rule:** Source code and runtime data must be strictly separated.
- **Rule:** The memory layer is isolated from the execution layer; memory access should be via dedicated managers.

## 6. Federation & Distributed
- **Rule:** Federation logic must not depend on the UI.
- **Rule:** Distributed nodes must be capable of surviving in isolation (HEADLESS) if the central brain is unavailable.

## 7. Circular Dependencies
- **Rule:** Circular imports are strictly forbidden. Use dependency injection or the Event Bus to decouple modules.

---
*Locked as of Phase 30.1*

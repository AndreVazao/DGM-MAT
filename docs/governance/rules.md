# Ecosystem Governance Rules

## 1. CORE SUPREMACY
The **DGM-MAT Core** is the absolute sovereign of the ecosystem.
- Only Core can orchestrate tasks.
- Only Core can modify the global state of the Semantic Memory Graph.
- Only Core can approve agent evolution or capability changes.
- Satellites are strictly passive (awaiting commands) or reactive (responding to signals).

## 2. NO RUNTIME CODE (PHASE 2 & 3)
During the initialization and binding phases:
- NO implementation code is allowed (e.g., Python, JavaScript, Go).
- NO server frameworks (FastAPI, Express, etc.).
- NO UI components or library installations.
- All repositories must remain purely architectural placeholders.

## 3. EVENT FIDELITY
Every interaction must be documentable as an event. Any interaction that cannot be traced back to the Core Event Bus is a violation of the ecosystem architecture.

## 4. AGENT ISOLATION
Agents are not permitted to share memory or context directly. All context transfer must happen through Core-managed events.

# DGM-MAT Cockpit Convergence Plan

## Current State Audit
- **Infrastructure**: PySide6 framework with a multi-tab layout.
- **Widgets**: 13 widgets exist, but many are currently simple labels or placeholders (`DashboardWidget`, `LogsWidget`).
- **Data Flow**: One-way from Runtime to Cockpit via WebSockets (Events & Logs).
- **Control**: No interactive controls for agents, tasks, or ecosystem management are currently implemented in the UI.

## Gaps in Operator UX
1. **Interactive Controls**: Users cannot yet trigger ecosystem scans, start/stop agents, or approve tasks from the UI.
2. **Ecosystem Visualization**: The `KnowledgeGraphWidget` and `MeshMonitorWidget` lack real-time topology rendering.
3. **Approval Center**: No dedicated space for `ApprovalManager` interactions (required for Phase 21+ governance).
4. **Adaptive UI**: The UI does not yet reflect the "Cognitive OS" nature (e.g., suggesting strategies or highlighting risks).

## Convergence Objectives

### 1. Sidebar & Global Navigation
Implement a fixed sidebar for rapid switching between:
- **Ecosystem Explorer** (Registry & Drift)
- **Live Operations** (Events & Logs)
- **Agent Monitor** (State & Lifecycle)
- **Approval Center** (Governance & Safety)
- **Memory Explorer** (Knowledge Fabric)

### 2. Live Topology & Graphs
Integrate `networkx` and `PySide6` graphics view to render:
- **Ecosystem Graph**: Repositories and their dependencies.
- **Agent Mesh**: Active agents and their current tasks/communication.
- **Knowledge Graph**: Semantic nodes and relationships.

### 3. Integrated Controls
Add control panels to widgets:
- **Agent Widget**: Start/Stop/Spawn agents.
- **Ecosystem Widget**: Trigger materialization/fix-drift.
- **Governance Widget**: Manual overrides and threshold adjustments.

### 4. Inline Approvals
Implement a pop-up or dedicated tab for "Human-in-the-loop" approval of:
- Code generation/refactoring requests.
- High-priority task execution.
- External ingestion requests.

## Roadmap
- **Short-term**: Unified sidebar, interactive agent controls.
- **Mid-term**: Real-time graph rendering for Knowledge/Ecosystem.
- **Long-term**: Operational search integration and AI-driven UI suggestions.

# DGM-MAT Core Architecture

## PURPOSE
The DGM-MAT Core serves as the central orchestrator for the entire multi-agent ecosystem. It manages the lifecycle of agents, the flow of events, and the integrity of the semantic memory graph.

## SYSTEM BOUNDARIES
- **Inside Core**: Orchestration logic, event bus management, governance, security, and global state.
- **Outside Core**: UI execution, external provider implementations, specific asset storage, and deployment targets.

## CORE RESPONSIBILITIES
1. **Event Bus Management**: Routing all ecosystem communication.
2. **Agent Governance**: Overseeing agent contracts and permissions.
3. **Memory Coordination**: Managing the Semantic Memory Graph.
4. **Task Orchestration**: Sequencing operations across satellites.

## INTERACTION MODEL
All satellites interact with the Core via standardized events. No satellite is permitted to bypass the Core for orchestration or inter-satellite communication.

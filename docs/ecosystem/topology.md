# Ecosystem Topology

## 1. HUB AND SPOKE MODEL
The DGM-MAT ecosystem follows a strict hub-and-spoke model where:
- **HUB**: DGM-MAT (Core)
- **SPOKES**: All Satellites (Mobile, Plugins, Labs, Connectors, Providers, Assets, Deploy)

## 2. DEPENDENCY DIRECTION
Dependencies flow **inward** toward the Core:
`Satellite -> Core Contracts -> Core Event Bus`

The Core is aware of satellite interfaces but is independent of their implementations.

## 3. FORBIDDEN INTERACTIONS
- `Satellite A <-> Satellite B`: NEVER PERMITTED.
- `Satellite -> External Internet`: Must go through `DGM-MAT-Connectors` or `DGM-MAT-Providers`.
- `Satellite -> Direct Database`: NEVER PERMITTED. Must use Core Memory events.

## 4. REPOSITORY RELATIONS
| Repo | Relation to Core | Dependency |
|------|------------------|------------|
| Mobile | UI Spoke | Core Event Bus |
| Plugins | Extension Spoke | Core Contract API |
| Labs | Experimental Spoke | Core Sandbox |
| Connectors | Integration Spoke | Core Event Bus |
| Providers | AI Spoke | Core Event Bus |
| Assets | Data Spoke | Core Storage Protocol |
| Deploy | Infra Spoke | Core State |

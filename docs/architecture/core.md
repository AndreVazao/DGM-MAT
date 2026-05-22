# DGM-MAT Core Architecture

## SYSTEM TYPE

Event-driven multi-agent orchestration platform.

## LAYERS

### 1. Governance Layer
- Overseer Agent
- Evolution Governor
- Security Sovereign
- Memory Sovereign

### 2. Domain Layer
- Repo Intelligence
- Conversation Intelligence
- Asset Intelligence
- Ecosystem Intelligence

### 3. Execution Layer
- Agent Runtime
- Task Scheduler
- Worker Pools

### 4. Infrastructure Layer
- Event Bus (Redis Streams / NATS)
- Database Layer (PostgreSQL)
- Vector DB (Qdrant)
- Graph DB (Neo4j)

## RULES

- No agent can directly mutate another agent state
- All communication must go through Event Bus
- Memory is immutable, only append
- Evolution requires governance approval

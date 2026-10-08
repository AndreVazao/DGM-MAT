# DGM-MAT Digital Organization Architecture

## Identity

**DGM-MAT = DevOps God Mode Multi-Agent Tool**

DGM-MAT is not designed as a loose collection of autonomous scripts. It is the
operating system of a governed digital engineering organization.

The organization contains:

- HQ / central orchestration
- departments
- specialized AI agents ("digital employees")
- missions and tasks
- internal communication
- shared workspaces
- evidence and provenance
- institutional/project/agent memory
- quality and independent verification
- DevOps and deployment
- controlled agent evolution
- a human owner/director approval boundary

## Core principle

> **Agents are governed employees, not free-roaming scripts.**

Every consequential action must be attributable to a mission, task, agent,
department, evidence trail and policy boundary.

The system must optimize for:

**stability > features**

**reality > assumptions**

**manual control > destructive automation**

## Organizational model

### HQ

HQ owns:

- mission intake
- strategic prioritization
- orchestration
- dependency management
- governance
- approval routing
- evidence requirements
- cross-department coordination
- final integration
- institutional memory synchronization

### Engineering

Initial specialist families:

- Python
- JavaScript / TypeScript
- Backend
- Frontend
- Database
- Architecture

### Quality

Independent from implementation workers:

- syntax validation
- import/dependency validation
- unit tests
- integration tests
- regression tests
- API/UI verification
- performance checks
- security checks

### Bug Hunters

Specialists for:

- syntax
- indentation
- imports
- runtime failures
- API failures
- dependency conflicts
- configuration errors
- race/concurrency issues
- duplicated implementations
- architectural inconsistencies
- overengineering

### DevOps

Owns:

- Git
- GitHub
- Actions
- builds
- packaging
- deployment
- environment validation
- release gates
- rollback

### Research

Owns:

- web research
- technical documentation
- upstream projects
- benchmarks
- standards
- alternatives and feasibility analysis

### Conversation Intelligence

Owns the recovery pipeline:

`CONVERSATIONS -> CONTEXT -> CODE -> PROJECT LINKING -> AUDIT -> IMPLEMENTATION`

It must preserve context with recovered code and maintain provenance across
providers.

### AI Provider Liaison

Provider-specific workers may interface with:

- ChatGPT
- Claude
- Gemini
- Grok
- DeepSeek
- future providers

Provider-specific behavior stays behind adapters. The organization consumes
normalized artifacts, evidence and reports rather than provider-specific
assumptions.

## Internal communication

Agents communicate through an internal message contract containing:

- sender
- recipient
- subject
- body
- mission/task correlation
- priority
- evidence
- response requirement
- timestamp

Communication must be inspectable and auditable.

## Task model

A task is a first-class object with:

- mission
- owner department
- assigned agent
- requirements
- dependencies
- inputs
- outputs
- evidence
- approval requirement
- status
- retry policy
- timestamps

Workers do not independently redefine the mission while executing a task.

## Shared workspace

Canonical logical workspace:

`DGM-MAT-WORKSPACE/`

- `missions/`
- `tasks/`
- `departments/`
- `projects/`
- `conversations/`
- `artifacts/`
- `decisions/`
- `reports/`
- `tests/`
- `releases/`
- `memory/`
- `inbox/`
- `outbox/`
- `evidence/`
- `agent_profiles/`
- `evolution/`

Each project receives:

- `context/`
- `recovered/`
- `source/`
- `architecture/`
- `tests/`
- `reports/`
- `decisions/`
- `artifacts/`
- `.dgm/`

Workspace initialization is non-destructive.

## Ownership

Departments own responsibilities, not the whole filesystem.

Examples:

- Python owns Python implementation work.
- Frontend owns frontend implementation.
- DevOps owns deployment infrastructure.
- Architecture owns contracts and structural decisions.
- QA can inspect broadly but should not silently rewrite product code.
- Bug Hunters propose/validate fixes independently.
- Conversation Intelligence owns recovered evidence and provenance.

Cross-boundary changes require explicit task ownership and review.

## Evidence and provenance

Important claims must carry evidence.

Recovered code must retain:

- provider
- conversation identity
- message/source location
- extraction time
- project relationship
- original artifact fingerprint
- later corrections
- implementation destination

Invariant:

> **Context travels with code.**

## Memory

AndreOS / `andreos-memory` remains the persistent institutional memory source
of truth.

DGM-MAT adds three operational scopes:

1. institutional memory
2. project memory
3. agent memory

Operational state can be reconstructed from durable records after interruption.

## Agent evolution

Agents may improve, but not through unrestricted self-modification.

Evolution follows:

`LESSON -> PROPOSAL -> TEST -> EVALUATION -> APPROVAL/PROMOTION -> NEW VERSION`

Each agent keeps:

- identity
- role
- skills
- responsibilities
- permissions
- version
- performance
- lessons
- evaluation history

Promotion must be evidence-based.

## Human boundary

The human owner/director remains the final authority for:

- credentials/secrets
- destructive operations
- irreversible deletion
- destructive migrations
- production releases when policy requires
- financial/external commitments
- unresolved consequential ambiguity

The cockpit should surface these as concise approval requests rather than
forcing the owner to perform routine engineering work.

## Foundation implemented in v1

The first organization package provides:

- `AgentRegistry`
- `InternalMessageBus`
- `OrganizationTaskManager`
- `OrganizationWorkspace`
- canonical domain models for agents, departments, tasks, messages, evidence
  and evolution proposals

These components are deliberately decoupled from execution. The next layers
will connect them to the existing DGM-MAT Mission Engine, Event Bus,
Execution Fabric, Cockpit, AndreOS memory and provider adapters.

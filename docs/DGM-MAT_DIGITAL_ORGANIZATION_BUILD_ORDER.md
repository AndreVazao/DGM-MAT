# DGM-MAT Digital Organization Build Order

## Objective

Turn DGM-MAT into a functioning digital engineering organization without
creating a fragile swarm of agents.

## Phase 1 — Organization Kernel

Status: **started**

Implemented:

- agent/department models
- agent registry
- internal message bus
- task lifecycle manager
- shared workspace contract
- organization tests

## Phase 2 — Runtime Integration

Next:

1. connect organization tasks to existing Mission Engine;
2. emit organization events through the existing Event Bus;
3. connect task state to Execution Fabric;
4. expose organization state through the API;
5. persist durable state;
6. synchronize institutional records with AndreOS memory.

## Phase 3 — Governance

Implement:

- ownership matrix
- permission evaluation
- approval categories
- evidence requirements
- cross-department change requests
- release gates

## Phase 4 — Worker Lifecycle

Implement:

- worker registration
- worker heartbeat
- assignment
- execution
- timeout
- retry
- failure
- quarantine
- recovery
- shutdown

## Phase 5 — Pilot Departments

Do not spawn dozens of workers.

Pilot with:

1. HQ / Orchestrator
2. Python Engineering
3. QA + Bug Hunting
4. Conversation Intelligence
5. AI Provider Liaison
6. DevOps

These six areas validate the organization model against the most important
DGM-MAT workloads.

## Phase 6 — Conversation Intelligence Fleet

Add provider-specific workers and browser/scroll workers behind a normalized
contract.

The recovery lifecycle remains:

`RAW -> CONTEXTUALIZED -> CANDIDATE -> CONSOLIDATED -> IMPLEMENTED`

## Phase 7 — Project Task Forces

For complex projects, HQ assembles temporary multidisciplinary teams.

Example:

- project lead
- domain specialist
- Python
- frontend
- database
- research
- QA
- security
- DevOps

The task force is archived and its lessons returned to organizational memory.

## Phase 8 — Evaluation and Evolution

Measure:

- task success
- regression rate
- bug escape rate
- review score
- human correction rate
- evidence quality
- efficiency
- reliability

Promote improved worker versions only after evaluation.

## Phase 9 — Scale

Only after the kernel is stable:

- additional languages
- additional AI providers
- specialized domain departments
- autonomous project assembly
- distributed workers
- richer cockpit
- cross-device operation

## Non-negotiable rule

Do not optimize for the number of agents.

Optimize for:

**correct work + evidence + coordination + recoverability + controlled autonomy.**

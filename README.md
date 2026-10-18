# DGM-MAT

DGM-MAT is the sovereign engineering intelligence and runtime of the DevOps God Mode ecosystem. **The brain is primary. The Headquarters/cockpit is a read-only projection of what the brain is actually doing.**

## Authority and architecture boundaries

- **DGM-MAT brain:** owns reasoning, decisions, research, memory retrieval, task execution, agent lifecycle, approvals, runtime state, testing and controlled self-improvement.
- **Headquarters / cockpit:** visualizes verified runtime events, status and agent activity. It must not decide, orchestrate, authorize, or control the brain. Characters and animations are consequences of real activity, never the source of it.
- **Research laboratory:** receives third-party repositories only through an explicit, approved import for inspection, licensing/security review, tests and selective code/script reuse. No automatic cloning of satellite, private or unrelated repositories into the DGM-MAT workspace.
- **Persistent memory/archive:** preserves source provenance, conversations, decisions, context and supersession history; local retrieval is preferred over revisiting external AI websites.
- **AndreOS memory:** canonical cross-project memory and repository governance record: [AndreVazao/andreos-memory](https://github.com/AndreVazao/andreos-memory), local operational copy `C:\\AndreOS-Memory`.

## Current responsibilities

- repository/workspace intelligence and evidence-first audits;
- architecture and dependency analysis;
- multi-agent engineering and controlled execution;
- runtime health, event truth, diagnosis and repair;
- research and validated reuse from isolated lab material;
- conversation ingestion, searchable memory and provenance;
- controlled self-improvement with validation and approval boundaries.

## Operating principle

`OBSERVE -> AUDIT -> CLASSIFY -> PLAN -> APPROVE WHEN REQUIRED -> APPLY -> VALIDATE -> RECORD`

Audits are read-only. Moving, renaming, deleting, regrouping repositories, changing remotes, committing, pushing, cloning external code, or triggering workflows must never happen implicitly. Preserve unmerged work and user changes before cleanup.

## Repository intelligence

The evidence-first portfolio auditor lives under `core/repository_intelligence/` and should inspect local Git state, remotes, metadata, manifests, README purpose, dependencies, protected paths and risks before recommending a change.

Canonical development workspace: `C:\\ProgramasGodMode`.

`DGM-MAT-FULL-MIRROR` is explicitly protected and must remain untouched.

## Self-repair

Controlled self-repair lives under `core/self_healing/self_repair_engine.py`. Diagnosis is separate from mutation. Safe self-tests may run automatically; destructive or authority-changing operations remain approval-gated.

## Governance API

The runtime exposes self/workspace audit and repair-plan/apply endpoints under `/governance/`. These APIs belong to the brain. A cockpit may display their verified outputs, but must not become a second authority or silently trigger privileged actions.

## External code reuse

`DGM-MAT-Labs` is the designated external-code laboratory. Imports must be explicit and reviewed; never clone private or satellite repositories automatically. The default flow is:

`APPROVED IMPORT -> ISOLATE -> STUDY -> REVIEW LICENSE/SECURITY -> TEST -> EXTRACT CONCEPT -> ADAPT -> VALIDATE -> PRODUCT`

Do not execute untrusted code by default. Whole-repository copying is not the default.

## Conversation archive direction

Audit the current persistence implementation before adding a second one. Target a local-first searchable archive that preserves original exports and normalizes conversation/message records with provider, source IDs, timestamps, role, content and provenance. SQLite with full-text search is the initial candidate, not an assumption that should override an existing proven implementation. Keep summaries, decisions, project links and supersession metadata separate from source messages. Retrieve local records first; contact external AI websites only when needed.

## Satellite and product boundaries

- `DGM-Cockpit-Frontend`: presentation-only cockpit.
- `DGM-MAT-Mobile`: lightweight remote chat/cockpit; PC brain remains the execution authority.
- `DGM-Contracts`: public shared contracts only.
- `DGM-MAT-Deploy`: minimal node discovery/rendezvous; not an execution plane or conversation store.
- `DGM-MAT-Agents`: standalone agents only while the migration boundary remains validated.
- `DGM-MCP` and `DGM-HUB`: separate projects, not silently merged into the core.
- Keep only satellites with a verified purpose and consumer. Do not add dependencies merely because a repository exists.

The live repository inventory, retention recommendations and consolidation gate are maintained in [the canonical memory governance record](https://github.com/AndreVazao/andreos-memory/blob/main/AndreOS/02_PROJETOS/DGM-MAT/REPOSITORY_GOVERNANCE_AND_CONSOLIDATION_2026-10-18.md).

## Development policy

- stability > features;
- reality > assumptions;
- manual control > destructive automation;
- evidence before restructuring;
- preserve history and unmerged work;
- small validated changes;
- record meaningful decisions in `andreos-memory`;
- prefer local validation and do not add/run GitHub Actions workflows without a specific approved need.

## Primary mission

Recover and organize conversation memory and documentation before non-urgent engineering work. Always distinguish user requests, AI proposals, current decisions, superseded solutions and verified reality. Preserve provenance and temporal evolution; never let legacy/superseded material silently govern current work.

Historical mission reference: [DGM-MAT_PRIMARY_MISSION_AND_EVOLVING_TRUTH_2026-10-10.md](docs/DGM-MAT_PRIMARY_MISSION_AND_EVOLVING_TRUTH_2026-10-10.md). Do not bulk-delete historical documentation: inventory, classify, link successors and preserve backups first.

# DGM-MAT Conversation Recovery & Project Assembly Protocol

Status: NORMATIVE
Date: 2026-10-08
Authority: DGM-MAT + AndreOS persistent memory

## 1. Mission

The unit of recovery is not a code block. It is:

CONVERSATION + CONTEXT + CODE + RELATIONSHIPS + PROJECT + REPOSITORY + DECISIONS

DGM-MAT must be able to recover why code was created, what another AI corrected, where the code belongs, what has been tested, and what still needs to be done.

## 2. Provider discovery

Primary providers:
- ChatGPT
- Grok
- Claude / Claude Code
- Gemini
- DeepSeek

Acquisition priority: browser/local access, without paid provider APIs.

Provider-specific browser adapters must expose a common ConversationRecord and must isolate DOM, URL, pagination, export and UI differences.

## 3. Phase A — inventory

LIST -> IDENTIFY -> INDEX

Before changing anything, inventory every discoverable conversation:
- provider
- provider conversation ID
- current title
- URL/location
- dates
- message count when available
- project hints
- technologies/languages
- acquisition method
- last scan
- state

No automatic rename/grouping happens before inventory.

## 4. Phase B — context vault

Every conversation gets durable context storage.

Logical path:
CONVERSATIONS/<provider>/<conversation-id>/

Recommended records:
- CONVERSATION.md
- METADATA.json
- MESSAGES.jsonl
- CODE_ARTIFACTS.jsonl
- RELATIONSHIPS.json
- PROJECT_LINK.json
- DECISIONS.md
- OPEN_ITEMS.md
- AUDIT.md

The vault is the bridge between browser history and engineering work.

## 5. Phase C — relationship graph

DGM-MAT links conversations across the same or different providers.

Example:
ChatGPT -> initial implementation
DeepSeek -> correction/review of that implementation

Relationship types:
- same project
- same feature
- predecessor/successor
- correction
- alternative implementation
- review
- debugging
- continuation
- research -> implementation
- implementation -> repair
- provider-A -> provider-B correction
- conflicting proposals

Every relationship needs evidence and confidence. Similar titles alone are not sufficient.

## 6. Phase D — project threads

Cluster related conversations into a canonical project thread.

Each thread stores:
- canonical project name
- aliases
- providers involved
- related conversations
- objective
- architecture hints
- repository hints
- unresolved questions
- implementation state
- confidence

## 7. Phase E — rename/group

After clustering, DGM-MAT proposes or performs conversation renaming so the thread is obvious.

Example:
VAZAO EVSE — Charger Control — Design
VAZAO EVSE — Charger Control — Debug/Repair
VAZAO EVSE — Charger Control — DeepSeek Review

If a provider cannot be safely renamed automatically, record the recommended title and ask the user instead of guessing.

## 8. Phase F — recover scripts from real conversations

Do not depend only on exports.

When required, DGM-MAT opens the real browser conversation and:
1. navigates to the relevant history;
2. scrolls through loaded messages;
3. detects message boundaries;
4. captures code plus surrounding explanation;
5. identifies filename/path markers;
6. preserves turn/message provenance;
7. preserves revision order;
8. detects later corrections;
9. deduplicates already captured content.

Every artifact retains provider, conversation ID, turn/message ID when available, timestamp, URL, language, filename/path, fingerprint, surrounding context and extraction time.

A code block without context is incomplete evidence.

## 9. Phase G — staging

Recovered material is staged before touching a product repository.

Logical staging:
C:\ProgramasGodMode\<PROJECT>\recovered\

Lifecycle:
RAW -> CONTEXTUALIZED -> CANDIDATE -> CONSOLIDATED -> IMPLEMENTED

Original recovered artifacts remain traceable until validation.

## 10. Phase H — repository discovery

For each project thread check:
1. known local project directory;
2. local Git repository;
3. Git remotes;
4. user's GitHub repositories;
5. aliases/related repositories;
6. legacy/reference sources;
7. create a new repository only when evidence says it is genuinely new.

Classify as product, unfinished product, duplicate, satellite/module, legacy, research/reference, upstream/clone or new project.

DGM-MAT-FULL-MIRROR is immutable and never a writable target.

## 11. Phase I — project TREE

Before assembly generate:
<PROJECT>_TREE.txt

It must capture:
- root
- directories/files
- file purpose where known
- entry points
- imports/dependencies
- tests
- configuration
- APIs
- frontend/backend boundaries
- agents/services
- missing expected files
- duplicate candidates
- suspicious files
- source provenance

Regenerate after meaningful structural changes.

## 12. Phase J — assembly

For each recovered artifact determine:
- problem solved
- whether the functionality already exists
- whether it is an alternative
- owning module
- correct target file
- required imports/contracts
- required configuration
- required tests

Never paste code merely because the filename looks compatible. Placement must follow responsibility, contracts, imports, runtime flow, tests and architecture.

## 13. Phase K — consolidation

When several AIs implemented the same feature:

COLLECT -> COMPARE -> UNDERSTAND -> SELECT -> CONSOLIDATE -> TEST

Compare correctness, context fit, architecture, simplicity, dependencies, security, testability, compatibility, provenance and later corrections.

Goal: one coherent implementation, not a pile of AI variants.

This incorporates the established Script Comparator / Consolidator concept.

## 14. Phase L — real program map

After assembly, map actual:
UI -> API -> services -> agents -> tools -> storage -> external systems

and where applicable:
input -> processing -> state -> output

The map must describe actual code. Missing links become findings.

## 15. Phase M — engineering loop

AUDIT -> PLAN -> APPROVAL WHEN REQUIRED -> APPLY -> TEST -> REPAIR -> VALIDATE

Checks include syntax, imports, contracts, dependencies, tests, builds, runtime health, APIs, configuration, duplicates, dead code, overengineering, security, incomplete modules and architecture/code divergence.

## 16. Phase N — persistent memory

Canonical memory:
Local: C:\AndreOS-Memory
GitHub: AndreVazao/andreos-memory
Branch: main

Loop:
SYNC -> READ MEMORY -> WORK -> VALIDATE -> DOCUMENT -> COMMIT -> PUSH -> CONFIRM SYNC

Every meaningful transition records:
- discovery
- linked conversations
- project selected
- repository selected
- files changed
- tests
- remaining work
- human input required
- exact next action

A decision that exists only inside a chat is not persistent.

## 17. Recovery after interruption

After crash, browser loss, network loss or restart:
1. recover node identity;
2. sync memory;
3. load mission/state;
4. find last completed checkpoint;
5. verify repository state;
6. verify conversation-vault state;
7. resume from the first incomplete phase;
8. never repeat a destructive action only because the previous run stopped.

Every phase must have an idempotent checkpoint.

## 18. Human boundary

Automatic:
- read
- index
- analyze
- compare
- extract
- tree generation
- tests
- non-destructive audits
- prepare changes

Approval:
- credentials/secrets
- irreversible deletion
- destructive migration
- consequential project ambiguity
- publication/release
- financial/external commitments
- security-sensitive changes
- decisions evidence cannot resolve safely

## 19. Final invariant

DGM-MAT must always be able to answer:

What were we trying to build?
Which conversations contributed?
What did each AI contribute?
Which code is authoritative?
Where does it live?
Which repository contains it?
What has been tested?
What is missing?
What must DGM-MAT do next?

If it cannot answer these from durable state, context recovery is not finished.

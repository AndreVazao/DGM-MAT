# DGM-MAT Conversation Recovery & Project Assembly Protocol

**Status:** normative operating procedure  
**Date:** 2026-10-08  
**Authority:** DGM-MAT + AndreOS persistent memory

## 1. Purpose

DGM-MAT must recover the user's real development history from the AI conversations that produced it, preserve the context around that history, and turn fragmented AI-generated work into coherent, testable software projects.

The unit of recovery is:

**conversation + context + code + relationships + project + repository state + decisions**

The final objective is that neither the user nor DGM-MAT loses why something was created, where it belongs, what was tried, what was corrected, or what still needs to be done.

## 2. Provider discovery — browser first, paid APIs not required

DGM-MAT must support the user's working providers through browser-based/local collection first:

1. ChatGPT
2. Grok
3. Claude / Claude Code
4. Gemini
5. DeepSeek

The preferred acquisition model is browser/local access without paid provider APIs.

Provider adapters must isolate provider-specific details. The core must consume a normalized ConversationRecord.

For each provider, DGM-MAT should discover, where the account/browser permits it:

- conversation list;
- conversation identifier;
- title;
- date/time;
- participants/provider;
- URL/location;
- visible conversation messages;
- attachments and code blocks where accessible;
- scroll/load state;
- rename capability where safely available;
- grouping/project/folder capability where the provider exposes it.

The system must never assume that a provider exposes the same DOM, URL structure, export format, pagination, or rename/grouping controls as another provider.

## 3. Phase A — inventory every conversation

First operation:

**LIST → IDENTIFY → INDEX**

DGM-MAT creates an inventory before changing anything.

Minimum record:

- provider;
- provider conversation ID;
- current title;
- URL;
- first/last observed date;
- message count if obtainable;
- project hints;
- technologies/languages;
- extracted entities;
- conversation state;
- acquisition method;
- last scan timestamp.

No conversation is renamed or reorganized before it has an inventory record.

## 4. Phase B — create a context vault for every conversation

Each conversation receives its own durable context record.

Suggested logical structure:

CONVERSATIONS/<provider>/<conversation-id>/

Recommended artifacts:

- CONVERSATION.md — normalized readable context;
- METADATA.json — provider/id/title/timestamps/source;
- MESSAGES.jsonl — normalized messages when available;
- CODE_ARTIFACTS.jsonl — extracted code/provenance index;
- RELATIONSHIPS.json — links to other conversations;
- PROJECT_LINK.json — current project hypothesis and confidence;
- DECISIONS.md — decisions found in the conversation;
- OPEN_ITEMS.md — unfinished work/questions;
- AUDIT.md — extraction/audit status.

The vault is the durable bridge between browser conversations and the engineering workspace.

## 5. Phase C — relate conversations across providers

DGM-MAT must build a conversation relationship graph.

Example:

ChatGPT conversation A
→ produced initial charger controller

DeepSeek conversation B
→ corrected the controller training/logic

These are not two independent projects. They are two evidence sources for the same engineering thread.

Relationships may be:

- same project;
- same feature;
- predecessor/successor;
- correction;
- alternative implementation;
- review;
- debugging;
- continuation;
- design → implementation;
- implementation → repair;
- research → implementation;
- provider A → provider B correction;
- conflicting proposals.

Relationships must retain evidence and confidence. Do not merge conversations merely because their titles look similar.

## 6. Phase D — project/thread clustering

After relationships are known, DGM-MAT creates logical project threads.

A project thread is a collection of conversations that contribute to the same real-world program or subsystem.

The thread receives:

- canonical project name;
- aliases;
- providers involved;
- related conversations;
- current objective;
- known architecture;
- known repository;
- unresolved questions;
- implementation state;
- confidence.

This is the point where conversation titles can be normalized.

## 7. Phase E — rename conversations to expose the thread

Only after clustering should DGM-MAT propose or perform conversation renaming.

Canonical naming should make the project/thread immediately recognizable, for example:

VAZAO EVSE — Charger Control — CP/Load Management — Design
VAZAO EVSE — Charger Control — CP/Load Management — Debug/Repair
VAZAO EVSE — Charger Control — CP/Load Management — DeepSeek Review

The exact provider-specific rename operation must be performed only through a supported browser/UI adapter.

If a provider cannot safely rename automatically, DGM-MAT records the recommended title and asks for human action rather than guessing.

## 8. Phase F — recover code by scrolling the real conversations

Code extraction must not depend exclusively on exports.

When only the browser conversation is available, DGM-MAT must be able to:

1. open the conversation;
2. navigate through the conversation;
3. scroll upward/downward as required;
4. detect loaded message boundaries;
5. capture code blocks and surrounding explanatory text;
6. identify file paths and filenames;
7. preserve the message/turn that produced each artifact;
8. preserve the order of revisions;
9. detect code that was corrected later;
10. avoid duplicating already captured content.

The extracted artifact must retain provenance:

- provider;
- conversation ID;
- message/turn identifier when available;
- timestamp when available;
- source URL;
- detected language;
- filename/path;
- code fingerprint;
- surrounding context;
- extraction timestamp.

A code block without its surrounding reasoning is incomplete evidence.

## 9. Phase G — organize recovered material by project

Recovered material must be staged first, never written blindly into a production repository.

Logical staging:

C:\ProgramasGodMode\<PROJECT>\recovered\

Then classify:

**RAW → CONTEXTUALIZED → CANDIDATE → CONSOLIDATED → IMPLEMENTED**

The original recovered artifact remains traceable until validation is complete.

## 10. Phase H — discover the real repository

For each project thread DGM-MAT checks, in order:

1. known local project directory;
2. local Git repository;
3. configured Git remotes;
4. GitHub repositories belonging to the user;
5. related repository names/aliases;
6. archived/reference repositories;
7. only then, creation of a new repository if the evidence supports that this is genuinely a new project.

DGM-MAT must distinguish:

- existing product;
- unfinished product;
- duplicate implementation;
- satellite/module;
- legacy;
- research/reference;
- clone/upstream;
- new project.

DGM-MAT-FULL-MIRROR remains immutable and is never used as a normal writable target.

## 11. Phase I — generate the project TREE

Before assembly, DGM-MAT writes:

<PROJECT>_TREE.txt

The tree is an evidence snapshot, not a decorative diagram.

It should contain:

- repository root;
- directories;
- files;
- file purpose where known;
- detected entry points;
- imports/dependencies;
- tests;
- configuration;
- APIs;
- frontend/backend boundaries;
- agents/services;
- missing expected files;
- duplicate candidates;
- suspicious files;
- source provenance where a file originated from recovered conversations.

The tree must be regenerated after meaningful structural changes.

## 12. Phase J — assemble the program

DGM-MAT now stops treating scripts as isolated snippets.

For each recovered artifact it determines:

- what problem it solves;
- whether the functionality already exists;
- whether it is an alternative implementation;
- which module owns the responsibility;
- which file should contain it;
- which imports/contracts are required;
- what configuration it needs;
- what tests should cover it.

Then it assembles the program into the actual architecture.

Rule:

**Never paste code merely because a filename looks compatible.**

Placement must be justified by responsibility, imports, contracts, runtime flow, tests and surrounding architecture.

## 13. Phase K — consolidate competing AI implementations

When multiple providers produced the same feature:

**COLLECT → COMPARE → UNDERSTAND → SELECT → CONSOLIDATE → TEST**

DGM-MAT must compare:

- correctness;
- context fit;
- architectural fit;
- simplicity;
- dependency cost;
- security;
- testability;
- compatibility with existing code;
- provenance;
- known corrections from later conversations.

The goal is one coherent implementation, not a collection of AI variants.

This reuses the established Script Comparator / Consolidator concept inside DGM-MAT.

## 14. Phase L — build the program map

After code placement DGM-MAT creates/updates an architectural map:

**UI → API → services → agents → tools → storage → external systems**

and, where relevant:

**input → processing → state → output**

The map must reflect the actual code, not an imagined architecture.

Missing links become findings.

## 15. Phase M — audit, test, repair

Only after context and assembly are coherent does the normal DGM-MAT engineering loop take over:

**AUDIT → PLAN → APPROVAL (when required) → APPLY → TEST → REPAIR → VALIDATE**

Checks include:

- syntax;
- imports;
- type/contract mismatches;
- dependency availability;
- tests;
- build;
- runtime health;
- API health;
- configuration;
- duplicate implementations;
- dead code;
- overengineering;
- security;
- incomplete modules;
- architecture/code divergence.

## 16. Phase N — persistent memory and synchronization

Every meaningful state transition must be recorded in the canonical AndreOS memory:

- local: C:\AndreOS-Memory
- GitHub: AndreVazao/andreos-memory
- branch: main

The persistent loop is:

**SYNC → READ MEMORY → WORK → VALIDATE → DOCUMENT → COMMIT → PUSH → CONFIRM SYNC**

At minimum, DGM-MAT records:

- what it discovered;
- what conversations were linked;
- what project was selected;
- what repository was selected;
- what files were created/changed;
- what tests passed/failed;
- what remains;
- what requires human input;
- the next exact action.

A decision that exists only inside an AI chat is not considered persistent.

## 17. Recovery after interruption

If DGM-MAT stops, crashes, loses the browser session, loses the network, or restarts:

1. recover node identity;
2. sync persistent memory;
3. load the active mission/state;
4. locate the last completed checkpoint;
5. verify repository state;
6. verify conversation-vault state;
7. resume from the first incomplete phase;
8. never repeat destructive operations merely because the previous run ended unexpectedly.

Every phase therefore needs an idempotent checkpoint.

## 18. Human interruption boundary

DGM-MAT should continue automatically for:

- reading;
- indexing;
- analysis;
- comparison;
- extraction;
- tree generation;
- testing;
- non-destructive audits;
- preparation of changes.

Human approval is required when the action involves:

- credentials/secrets;
- irreversible deletion;
- destructive migration;
- ambiguous project identity with meaningful consequences;
- publication/release;
- financial or external commitments;
- security-sensitive changes;
- a decision the evidence cannot resolve safely.

## 19. Final invariant

The system must always be able to answer:

**What were we trying to build?**
**Which conversations contributed to it?**
**What did each AI contribute?**
**Which code is authoritative?**
**Where does that code live?**
**What repository contains it?**
**What has been tested?**
**What is still missing?**
**What should DGM-MAT do next?**

If it cannot answer these questions from its own durable state, the context-recovery system is not finished.

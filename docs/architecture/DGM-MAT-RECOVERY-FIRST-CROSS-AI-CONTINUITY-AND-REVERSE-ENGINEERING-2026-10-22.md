# DGM-MAT — Recovery-First Development, Cross-AI Continuity and Reverse-Engineering Department

**Status:** required architecture and build-order contract; end-to-end runtime implementation is pending.  
**Date:** 2026-10-22  
**Branch:** `audit/programming-department-readiness-2026-10-22-synced`

## Mission and priority

The primary job of DGM-MAT is to recover the user's existing development work and intent before starting a fresh implementation. The success criterion is the desired working program, not the amount of code generated, number of agents, or number of AI conversations.

The default order is:

1. discover and preserve authorized local conversation histories, exports, project files, scripts, attachments, repositories and backups;
2. classify conversations and artifacts by project/context, detect duplicates and related versions, and propose meaningful project/folder names;
3. recover code, requirements, decisions, dependencies and execution instructions with source provenance;
4. inspect any existing program whose original conversation is missing, infer its behavior from evidence, and create a recoverable technical brief;
5. reconcile recovered context with the actual repository and local files;
6. continue development using the most suitable available AI/provider and trustworthy web documentation;
7. integrate the smallest safe change, validate it independently, and continue until the agreed acceptance criteria are evidenced.

Do not start a greenfield rewrite merely because the conversation is missing or a first search fails. Search authorized sources systematically, record coverage and limitations, and ask for an export only when required access is genuinely unavailable.

## 1. Local-first conversation and artifact recovery

Search authorized locations and sources, subject to their actual available interfaces and permissions: user-provided exports, locally saved conversations, browser-accessible history, project directories, downloads, backups, Git repositories, attachments and code fragments. Never claim access to a provider's private history or deleted conversation unless the relevant source is actually accessible.

For every import:
- preserve the raw original and source metadata before normalization;
- retain provider, conversation/title/ID/URL where available, timestamps, speaker roles, message order, attachments, hashes and capture coverage/limitations;
- distinguish direct user requirements/decisions from AI suggestions, generated code, assumptions and observed test/runtime evidence;
- deduplicate safely without discarding distinct versions or context;
- link extracted code and decisions to their original conversation/message/file;
- keep deleted/unavailable/partially captured histories explicitly marked as such.

Normalize related conversations into project-specific indexes and briefs. For example, conversations about the same program should be grouped under one proposed project name, while retaining source identifiers and an index that can trace every item back to its original. Renaming or moving files/folders must be staged and reversible: preserve the source, preview the proposed plan, detect collisions, verify copies/checksums, and do not perform broad destructive cleanup without approval.

## 2. Recovering a program when its conversation is gone

A missing conversation is not a reason to abandon an existing program. Inspect the codebase and artifacts as a reverse-documentation task:
- identify file types, entry points, modules, UI, configuration, dependencies, build scripts and data stores;
- inspect README/docs, package manifests, Git history/branches/tags, commit messages, tests, logs and existing release artifacts;
- use static inspection first; run unknown code only in an appropriately isolated, authorized environment;
- determine what the program demonstrably does, what is inferred, what is broken, and what remains unknown;
- create a recovered project brief with architecture map, launch/build steps, dependency inventory, current revision, known behavior, test evidence, risks and next smallest safe action;
- compare it with related recovered conversations or other projects before changing anything.

Do not invent the missing user's intent. If several plausible directions would materially change the program, show the evidence and ask one focused question. Otherwise continue with reversible, low-risk work and clearly mark assumptions.

## 3. Cross-AI continuation and web research

DGM-MAT should have a provider-neutral AI liaison and research workflow, using only providers, browser sessions, connectors, APIs and accounts that are actually available and authorized. It must not depend on one AI vendor.

For each blocked or incomplete development task:
1. package a concise, source-linked context bundle: user goal and acceptance criteria, current code/revision, decisions and rejected options, what was tried, exact errors, tests/evidence, constraints and one concrete question;
2. select a suitable available provider based on capability, cost/free-tier status, context size, tool access, latency and current availability;
3. request an answer or a bounded implementation/research step;
4. record the provider, model/service where known, date, prompt/context bundle version, output and limitations;
5. evaluate the answer against source code, official documentation, license terms, tests and independent review; never treat an AI answer as proof by itself;
6. if the provider refuses, reaches a quota, lacks a capability, gives an incomplete answer or cannot resolve the issue, record the exact blocker and route the same task/context to another suitable available provider;
7. reconcile conflicting answers, preserve alternatives, and update the decision ledger only when the evidence or user decision justifies it;
8. return results to the project workspace and continue the development loop rather than leaving the user to manually restart the investigation.

Web research should prefer official documentation, upstream repositories, release notes, issue trackers and reproducible evidence; community discussions may supplement but not replace authoritative sources. Browser automation must use authorized sessions and respect access controls, provider rules, privacy and rate limits. Do not bypass paywalls, CAPTCHAs, authentication, quotas or safety controls. A provider barrier triggers a legitimate fallback, not circumvention. Never transmit secrets, private source code or personal conversation data to an external provider without the applicable permission and data-scope approval.

## 4. From recovered snippets to a coherent program

Before assembling recovered code:
- inspect the destination file, imports, symbols, callers, interfaces, tests and current version;
- identify whether the snippet is complete, a patch, an obsolete alternative, pseudocode or unverified output;
- merge into the correct original file/symbol, preserving unrelated functionality, encoding, formatting conventions and public interfaces;
- detect duplicates and incompatible versions; explain meaningful conflicts instead of silently concatenating them;
- keep a minimal diff and avoid new dependencies/abstractions unless justified;
- retain a backup/recovery point and provenance for each material contribution;
- run the smallest relevant tests first, then broader checks as resources allow;
- require independent QA before marking work verified.

A generated patch, successful API response, planning record or AI claim does not prove that a program was changed or works. Use truthful states such as planned, blocked, not implemented, running, failed and verified, with evidence attached to the actual run/revision.

## 5. Future Reverse Engineering department/tooling

A dedicated Reverse Engineering department is a later phase, not a prerequisite for the recovery-first workflow. First inventory existing open-source reverse-engineering repositories and the user's earlier reverse-engineering project; assess maturity, maintenance, Windows compatibility, dependencies, hardware cost, security, license and fit for a concrete DGM-MAT use case.

Potential approved capabilities may include:
- static analysis and symbol/file-format inspection;
- dependency and binary metadata analysis;
- debugging and profiling of software the user is authorized to inspect;
- interoperability analysis and documented API/protocol integration;
- extraction/reuse of components from appropriately licensed open-source projects where the license permits it;
- wrapping an existing tool as a bounded agent/service and adapting it through a documented interface rather than copying large chunks of its internals.

Before adopting a tool, record upstream URL, exact revision/release, license, attribution/notice obligations, dependencies, installation source, security posture, supported formats, input/output contract, sandbox requirements and tests. Prefer reusing the upstream tool through CLI/API/plugin boundaries when that is simpler and safer than transplanting code. When code reuse is permitted, preserve license notices and verify license compatibility with the destination project. Do not copy proprietary source code or bypass technical protections; inspect only software and artifacts the user is authorized to analyze. Keep binary analysis isolated and read-only by default, with explicit approval before modifying target files or running potentially unsafe samples.

The department must expose a narrow, permission-checked tool contract to other departments, with resource limits, audit logs, reproducible inputs/outputs and independent validation. It must not gain unrestricted authority to rewrite DGM-MAT or arbitrary programs.

## 6. Suggested acceptance gates

### Gate A — Recovery inventory
A read-only report enumerates discovered sources, coverage, gaps, duplicates and candidate project groupings without modifying originals.

### Gate B — Safe organization
A proposed folder/name plan is reviewed, collisions are resolved, originals are recoverable, and copy/hash verification passes before any approved move/rename.

### Gate C — Recovered project brief
For a project with missing conversation history, the brief identifies entry points, dependencies, build/run instructions, known behavior and evidence-backed gaps, with unknowns clearly labelled.

### Gate D — Cross-AI handoff
A blocked task can be handed to another authorized provider with the same versioned context bundle, without losing decisions, secrets boundaries or provenance. Provider failure is logged and fallback is tested.

### Gate E — Working patch
A bounded change is applied to the correct existing files, minimal diff reviewed, configured tests executed, independent QA recorded and durable evidence linked to the exact source revision/run.

### Gate F — Reverse-engineering pilot
Only after Gates A–E are operational, one selected open-source tool is evaluated for a specific use case, license and security reviewed, integrated behind a bounded interface, and tested without destructive changes to target artifacts.

## Truth boundary

This document is a specification, not proof that local conversation discovery, provider browser automation, cross-AI fallback, deleted-conversation recovery or a Reverse Engineering department is already operational. Implement incrementally on the audit branch, inspect existing modules/callers before adding new systems, test locally where possible, and keep the main branch and the single-open-PR policy unchanged until review gates are satisfied.

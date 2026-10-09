# DGM-MAT Operating Model

## Mission

DGM-MAT is the user's autonomous engineering counterpart. Its job is not merely to run DevOps commands. It must understand the user's programming work, recover useful code from AI conversations, understand the context that produced that code, assemble coherent programs, test them, find defects, simplify over-engineering, and finish incomplete projects.

## Core loop

CONVERSATIONS -> CONTEXT -> CODE EXTRACTION -> PROJECT LINKING -> CODE AUDIT -> CONSOLIDATION -> IMPLEMENTATION PLAN -> APPROVAL WHEN REQUIRED -> APPLY -> TEST -> REPAIR -> VALIDATE -> MEMORY -> RE-AUDIT

## Conversation sources

DGM-MAT must be provider-agnostic and support:

- ChatGPT
- Claude / Claude Code
- Grok
- DeepSeek
- Gemini
- Copilot
- Telescope-collected agent/MCP activity
- future providers through adapters

The stable internal representation is ConversationRecord. Provider-specific ingestion must never leak provider-specific formats into the rest of DGM-MAT.

## Code intelligence

For each imported conversation DGM-MAT must:

1. identify the project/family;
2. suggest a useful conversation title;
3. extract code blocks and FILE markers;
4. preserve provider and conversation provenance;
5. validate syntax where possible;
6. compare code with the surrounding context;
7. detect duplicate candidates;
8. identify possible over-engineering and unnecessary dependency density;
9. identify candidate target files;
10. build an evidence-backed implementation plan.

Current foundation:
- `core/conversation_intelligence/`
- `POST /governance/conversations/analyze`

## Consolidation rule

Repeated code is not copied blindly. DGM-MAT groups equivalent candidates, compares provenance/context, selects the strongest implementation, and only then proposes consolidation.

The target is one correct implementation, not a pile of AI-generated variants.

## Repository repair

After conversation intelligence, DGM-MAT uses repository intelligence and development/execution services to:

- audit almost-complete projects;
- detect missing pieces;
- detect broken imports and syntax errors;
- compare architecture against actual code;
- implement missing pieces in the correct repository/file;
- run tests/builds/health checks;
- repair failures in bounded loops;
- stop and ask the user when credentials, irreversible decisions, ambiguity or risky structural changes are required.

## Human interface

The mobile cockpit is the user's conversation surface. DGM-MAT should behave as if the user were present at the PC: it continues working autonomously and only interrupts when a real decision/input is required.

Examples of user intervention:
- credential required;
- login approval;
- ambiguous architecture choice;
- destructive/irreversible operation;
- budget or external service decision;
- final acceptance of a structural reorganization.

Secrets must be entered through the controlled cockpit/vault path and must never be stored in Vercel rendezvous records or conversation logs.

## Vercel rendezvous

Vercel is the discovery/control-plane rendezvous point. The home PC and mobile cockpit do not need manually entered IP addresses.

Current service:
- Vercel project: `dgm-mat-rendezvous`
- endpoint: `/api/rendezvous`
- private Vercel Blob registry
- short-lived node presence records
- shared enrollment secret stored locally and as a sensitive Vercel environment variable

Vercel is not the execution plane. DGM-MAT remains the execution authority on the authorized PC.

## Telescope

Microsoft Project Telescope is installed on the home Windows PC. It is used as a local-first observability layer for AI coding agents and MCP traffic. Its built-in collectors cover Claude Code and Copilot JSONL plus MCP proxy activity. DGM-MAT treats Telescope as an observation source, not as the project brain.

Because Telescope is experimental, DGM-MAT keeps its own provider-neutral conversation model so provider/Telescope format changes do not break the core system.

## Autonomy boundary

DGM-MAT may automatically observe, analyze, test and prepare changes. Mutating actions are governed by risk and approval policy.

The principle remains:

**stability > features**
**reality > assumptions**
**manual control > destructive automation**

The end state is autonomous engineering with human interruption only where the human is genuinely required.


## Mandatory conversation-to-program sequence

The normative procedure is defined in docs/DGM-MAT_CONVERSATION_RECOVERY_AND_PROJECT_ASSEMBLY.md.

1. LIST all conversations across ChatGPT, Grok, Claude, Gemini and DeepSeek through browser/local adapters.
2. CREATE a durable context vault for every conversation.
3. RELATE conversations across the same or different providers.
4. CLUSTER related conversations into canonical project threads.
5. RENAME/GROUP conversations only after evidence-backed clustering.
6. RECOVER scripts by scrolling real conversations when exports are insufficient, preserving context and provenance.
7. STAGE recovered artifacts by project before modifying product repositories.
8. DISCOVER/VERIFY the local and GitHub repository, or create a new repository only when justified.
9. GENERATE <PROJECT>_TREE.txt as an evidence-based structural snapshot.
10. ASSEMBLE code into the correct files/modules according to responsibility and architecture.
11. CONSOLIDATE competing AI implementations into one coherent implementation.
12. MAP the actual program architecture.
13. AUDIT.
14. TEST and REPAIR.
15. VALIDATE.
16. PERSIST memory and synchronize with AndreOS/andreos-memory.
17. RESUME safely from the last idempotent checkpoint after interruption.

**Invariant: context travels with code.** A recovered script without its originating reasoning, provenance, project relationship and later corrections is incomplete engineering evidence.

## Mobile Cockpit Implementation Update — 2026-10-08

The mobile cockpit requirement is now implemented as a DGM-MAT-owned conversation surface.

- UI repository: AndreVazao/DGM-MAT-Mobile
- Vercel UI project: dgm-mat-mobile
- Runtime API: DGM-MAT /mobile/*
- Private transport: Tailscale
- Discovery: dgm-mat-rendezvous
- Durable thread state: DGM-MAT runtime storage
- Persistent engineering memory: AndreOS/andreos-memory

The Vercel mobile shell discovers the current PC endpoint through the minimal public discovery path. Normal conversation content travels directly to the authorized DGM-MAT PC once the Tailscale HTTPS bridge is enabled.

The user experience must remain continuous across mobile and PC: same thread, same context, same intent and same execution authority.


## Binding clarification — company model, free collaborators and self-improvement (2026-10-09)

See normative charter: `docs/DGM-MAT_ENTERPRISE_AUTONOMY_AND_ZERO_COST_CHARTER_2026-10-09.md`. DGM-MAT is a digital company with HQ, departments and owned specialist roles, not a single external chatbot. Local/internal capability comes first. Claude Code Free, ChatGPT and other legitimate free browser tools can act as temporary specialist collaborators; their useful output must be independently reviewed and converted into persistent reusable lessons. Capability Acquisition/Recruitment must be able to discover, sandbox, test and promote free tools or create justified internal agents. Self-improvement is required but governed by verified backups, isolated changes, tests, independent review and controlled promotion. Paid adapters may exist for future use, but execution remains FREE-ONLY / PAID-DENY unless the user specifically authorizes a financial action. Browser AI, independent active agents and the full self-improvement loop must not be claimed complete until verified end-to-end.

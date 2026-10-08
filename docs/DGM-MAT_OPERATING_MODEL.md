# DGM-MAT Operating Model

## Mission

DGM-MAT is the user's autonomous engineering counterpart. Its job is not merely to run DevOps commands. It must understand the user's programming work, recover useful code from AI conversations, understand the context that produced that code, assemble coherent programs, test them, find defects, simplify over-engineering, and finish incomplete projects.

## Core loop

CONVERSATIONS -> CONTEXT -> CODE EXTRACTION -> PROJECT LINKING -> CODE AUDIT -> CONSOLIDATION -> IMPLEMENTATION PLAN -> APPROVAL WHEN REQUIRED -> APPLY -> TEST -> REPAIR -> VALIDATE -> MEMORY -> RE-AUDIT

## Conversation sources

DGM-MAT must be provider-agnostic and support ChatGPT, Claude / Claude Code, Grok, DeepSeek, Gemini, Copilot, Telescope-collected agent/MCP activity, and future providers through adapters.

The stable internal representation is ConversationRecord. Provider-specific ingestion must never leak provider-specific formats into the rest of DGM-MAT.

## Code intelligence

For each imported conversation DGM-MAT must identify the project/family, suggest a useful conversation title, extract code blocks and FILE markers, preserve provenance, validate syntax where possible, compare code with surrounding context, detect duplicate candidates, identify possible over-engineering and unnecessary dependency density, identify candidate target files, and build an evidence-backed implementation plan.

Current foundation:
- `core/conversation_intelligence/`
- `POST /governance/conversations/analyze`

## Consolidation rule

Repeated code is not copied blindly. DGM-MAT groups equivalent candidates, compares provenance/context, selects the strongest implementation, and only then proposes consolidation. The target is one correct implementation, not a pile of AI-generated variants.

## Repository repair

After conversation intelligence, DGM-MAT uses repository intelligence and development/execution services to audit almost-complete projects, detect missing pieces, detect broken imports and syntax errors, compare architecture against actual code, implement missing pieces in the correct repository/file, run tests/builds/health checks, repair failures in bounded loops, and stop when credentials, irreversible decisions, ambiguity or risky structural changes require the user.

## Human interface

The mobile cockpit is the user's conversation surface. DGM-MAT should behave as if the user were present at the PC: it continues working autonomously and only interrupts when a real decision/input is required.

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

**stability > features**
**reality > assumptions**
**manual control > destructive automation**

The end state is autonomous engineering with human interruption only where the human is genuinely required.

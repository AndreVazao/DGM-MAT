# Path: C:\\ProgramasGodMode\\DGM-MAT\\docs\\DGM-MAT_ENTERPRISE_AUTONOMY_AND_ZERO_COST_CHARTER_2026-10-09.md

# DGM-MAT — Enterprise Autonomy and Zero-Cost Charter
Date: 2026-10-09
Status: normative architecture direction; some execution layers remain incomplete

## 1. Company model

DGM-MAT is a digital company, not a single chatbot and not merely a launcher for external models. It has HQ/orchestration, departments, specialist employees (agents), tasks/missions, internal communication, shared workspace, evidence, quality control and institutional/project/agent memory.

Each defined function should have a clear specialist role/agent contract, ownership boundary, skills, permissions, supervisor, version, evaluation history and persistent lessons. Agents are not considered active merely because a roster entry exists: operational status must be backed by a real execution path and tests.

Departments can include HQ, Engineering, Frontend, Backend, Data/Database, QA, Bug Hunters, Security, DevOps/Release, Research, Conversation Intelligence, Memory/Knowledge, Provider Liaison, Browser Automation, Finance/Cost Governance and Capability Acquisition/Recruitment. The roster may grow as justified by real workload.

## 2. Internal-first resource hierarchy

1. Internal DGM-MAT logic, existing code, tests, project documentation, persistent memory, installed tools and reusable local modules.
2. Local models such as Ollama when health, memory and hardware checks say the PC can handle the task.
3. Existing authorized browser sessions for legitimate free modes of ChatGPT, Claude Code Free, Gemini, Grok, DeepSeek or other providers, only when a real adapter/agent integration exists and policy/terms permit it.
4. Another verified free provider with remaining capacity.
5. Defer and persist the task, evidence, attempted approaches, missing capability, next step and resume condition.

Never treat a successful call as proof of free billing. Unknown pricing, quotas, reset conditions or billing mode mean BLOCK. Reaching a free limit means wait until a trustworthy reset, switch to another verified free route, or ask the user for help. It never triggers a paid fallback.

## 3. External AI as a temporary employee/consultant

Claude Code Free, ChatGPT and other available free AI tools can serve as external specialist collaborators. DGM-MAT remains the coordinator and owner of institutional memory. It should give the external helper a bounded task packet (goal, project context, relevant files, attempted steps, constraints, evidence, expected output and validation criteria), receive the result, independently review/test it, and record reusable lessons and provenance.

Do not assume an external AI has a supported automation API. Prefer a legitimate user-authorized browser session or supported integration. Never bypass logins, CAPTCHAs, anti-bot controls, provider terms, account limits or free-tier restrictions. Browser session credentials/cookies remain local and secret. External providers receive only the minimum context needed.

## 4. Capability acquisition and recruitment department

DGM-MAT must have an open but governed capability/recruitment function. When a task exposes a missing skill, it should:
REQUEST -> SEARCH INTERNAL CAPABILITIES/TOOLS/PROJECTS/LABS -> ASSESS -> SNAPSHOT -> SANDBOX -> ADAPT -> TEST -> INDEPENDENT REVIEW -> PROMOTE -> REGISTER -> ACTIVATE.

It may create a new internal agent when a recurring function needs clear ownership, or recruit/adapt a free existing tool/agent if licensing, security, quality and cost are acceptable. Sources are not automatically trusted or activated. Labs and source repositories are discovery/reuse zones, not runtime dependencies. Never modify DGM-MAT-FULL-MIRROR.

## 5. Self-improvement / self-development department

DGM-MAT is expected to improve its own code and architecture, using internal agents first and free external collaborators (including ChatGPT and Claude Code Free) where helpful. The self-improvement loop is:
OBSERVE -> FORMULATE EVIDENCE-BACKED CHANGE -> BACKUP + SHA-256 -> ISOLATED BRANCH/SANDBOX -> IMPLEMENT -> TEST -> INDEPENDENT QA/SECURITY REVIEW -> DIFF/REGRESSION CHECK -> PROMOTE/COMMIT -> UPDATE MEMORY -> EVALUATE LESSONS.

It must not blindly overwrite itself, change its own permissions to evade policy, remove audit records, or mark unexecuted work complete. Existing file changes require verified backups. Risky/destructive/irreversible changes require human approval. If no free helper or sufficient evidence exists, it waits or asks for specific help.

## 6. Financial authorization model

Tool availability and payment authorization are separate concepts:
- Tools and provider adapters may be registered for future use.
- Paid capability can be documented and tested with mocks without activating paid execution.
- Default state is FREE-ONLY / PAID-DENY.
- No API spend, premium subscription, paid model fallback, credit consumption or upgrade unless the user explicitly authorizes that specific financial action after seeing the cost/limit.
- A configuration flag alone is not enough: the actual execution boundary must enforce policy and tests must prove forbidden requests never invoke adapters.
- If quota/cost checks or persistent reservations fail, fail closed.

## 7. Learning without repeated questions

After useful external help, preserve in the appropriate memory scopes:
- institutional lesson and reusable procedure;
- project-specific facts and decisions;
- agent-specific skills, limitations and quality history;
- provider/session provenance without secrets;
- attempted approaches, errors, solution, tests and conditions where it works;
- whether the result was independently validated.

Before asking the user or another AI to repeat work, search this memory and the workspace first. Never save passwords, session cookies, API keys or private authentication material.

## 8. Truthful maturity reporting

Architecture intention is not proof of implementation. Report each capability as one of:
- SPECIFIED
- IMPLEMENTED
- TESTED
- INTEGRATED
- VERIFIED IN LIVE WORKFLOW

At this checkpoint, the organizational model, deterministic roster/delegation foundations, help-seeking recommendation and zero-cost provider preflight exist. Browser-based multi-provider collaboration, true independent active specialists, durable task delegation, and the complete self-improving/recruitment loop still require implementation and end-to-end evidence. Do not claim them complete prematurely.

## 9. Current mandatory next sequence

1. Keep paid provider execution denied by default and preserve the zero-cost gate.
2. Define the common contract for internal specialist agents and the external-AI liaison.
3. Implement a task packet + result ingestion + independent validation + persistent learning flow for Claude Code Free / browser collaborators without assuming API access.
4. Connect HQ mission routing to real durable agent execution and departmental ownership.
5. Implement capability requests, candidate assessment, sandbox, tests, promotion and agent registration.
6. Implement self-improvement as a controlled, reversible engineering workflow.
7. Prove each layer with negative cost tests, integration tests and observable evidence before enabling it.

Safety: API/HTTP/WebSocket remote exposure remains separately blocked until global authentication/authorization and client migration are complete.

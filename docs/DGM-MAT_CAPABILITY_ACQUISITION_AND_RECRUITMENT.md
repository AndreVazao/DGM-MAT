# DGM-MAT Capability Acquisition, Skill Forge and Open Recruitment

## Purpose

DGM-MAT must not have a permanently closed list of workers.

When HQ discovers that a mission requires a capability that the current
workforce does not possess, it can open a **Capability Request** and search
approved source zones for an existing implementation, skill, tool or project
that can supply the missing capability.

This is the digital equivalent of recruitment plus acquisition of know-how.

## The correct model

- **Agent** = a digital employee with responsibility and identity.
- **Skill** = reusable know-how.
- **Module** = adapted, tested software capability owned by DGM-MAT.
- **Tool** = executable integration with an external/local system.
- **Source** = where the capability was discovered.
- **Department** = organizational home of the worker.
- **Task** = a concrete piece of work performed by the worker.

A source does not automatically become a module.

## Acquisition pipeline

`REQUEST -> DISCOVER -> ASSESS -> SNAPSHOT -> SANDBOX -> ADAPT -> TEST -> REVIEW -> PROMOTE -> REGISTER -> ACTIVATE`

### REQUEST

HQ identifies a missing capability. The system creates a Capability Request
containing the mission, reason, required skills, risk and requester.

### DISCOVER

The system searches:

1. already installed DGM-MAT capabilities;
2. local projects;
3. DGM-MAT-Labs;
4. other `*-skills-lab` repositories;
5. other approved local repositories;
6. GitHub sources;
7. external sources when allowed.

The discovery layer only inventories candidates.

### ASSESS

Each candidate receives capability match, provenance, license/source metadata,
adaptation cost, safety/risk, dependencies, maintenance condition and expected
benefit.

### SNAPSHOT

The source is copied into a DGM-MAT staging area. The source remains untouched.

**Labs are laboratories and reuse sources, not runtime dependencies.**

### SANDBOX

Untrusted or experimental code is isolated before execution. A sandbox worker
determines what the candidate actually does rather than trusting README claims.

### ADAPT

DGM-MAT creates an adapter/module around the useful capability.

The useful part is adapted to DGM-MAT contracts:

- task interface;
- tool interface;
- evidence/provenance;
- permissions;
- logging;
- error reporting;
- lifecycle;
- tests.

### TEST

The adapted capability is tested independently.

The original source is never treated as proof that the adaptation works.

### REVIEW

QA/Bug Hunters and, when necessary, Security review the candidate.

### PROMOTE

Only a validated adaptation becomes a DGM-MAT-owned module. Its provenance
remains attached to the module.

### REGISTER

The capability is registered in the Capability Registry. If it requires a
dedicated worker, HQ creates a Recruitment Order.

### ACTIVATE

The new worker receives identity, department, role, skills, permissions,
supervisor, memory scope and tasks, then becomes a normal DGM-MAT employee.

## Open recruitment

The organization deliberately contains an open recruitment zone.

HQ can create new worker definitions when:

- a capability is repeatedly needed;
- no existing worker owns it;
- a candidate module has been validated;
- the responsibility boundary is clear.

It must not create workers simply because more agents seem useful.

### Example

User:

> "DGM-MAT, I want voice cloning locally on this PC."

HQ:

1. creates `CapabilityRequest(voice_cloning)`;
2. searches local and GitHub sources;
3. discovers existing voice-related projects/skills;
4. compares them;
5. snapshots the best candidates;
6. adapts the useful implementation to DGM-MAT;
7. tests it;
8. creates a `voice-engineer` or `voice-service` worker if justified;
9. registers the worker;
10. assigns the implementation mission.

The human approval gate is triggered where the operation requires credentials,
external commitments, high-risk execution or another protected action.

## Existing-project reuse

This architecture is specifically designed to exploit the existing portfolio.

Known local skill laboratories include sources around:

- browser automation;
- OpenAI;
- Anthropic;
- Gemini;
- Google Cloud;
- Cloudflare;
- Vercel;
- HeyGen;
- Android/mobile;
- Ollama/local AI;
- Praison;
- Ruflo;
- Smol AI.

There are also existing project repositories containing potentially useful
specialized implementations.

DGM-MAT should **discover and evaluate** these sources rather than blindly
importing them.

## DGM-MAT reconstruction strategy

`DGM-MAT-FULL-MIRROR` remains archaeology only.

The active DGM-MAT is the reconstruction.

The rebuild process is:

1. preserve current reality;
2. map existing architecture;
3. identify reusable components;
4. identify obsolete/duplicated components;
5. promote only validated components;
6. integrate behind clear contracts;
7. test;
8. record provenance;
9. synchronize memory.

This prevents the new organization from inheriting the old architecture's
accidental coupling.

## Important rule

> **DGM-MAT can hire a capability, but it must not blindly hire the source.**

The source is evidence.

The adapted module is the product.

The worker is the employee.

The registry is the organizational record.

The tests are the proof.

The provenance is the history.

The human approval boundary remains the final authority for consequential
actions.


## Binding clarification — recruitment and self-development (2026-10-09)

This department is a permanent core capability, not a one-off feature: identify missing skills, reuse internal assets, discover free external tools/agents, sandbox, adapt, test, independently review, promote and register a specialist employee when justified. It also owns the controlled path for creating or improving DGM-MAT's own agents/modules. No source or new agent is trusted merely because it exists; no paid API/subscription/credits may be activated by recruitment. See `docs/DGM-MAT_ENTERPRISE_AUTONOMY_AND_ZERO_COST_CHARTER_2026-10-09.md`.

# Office Roster Profile Reconciliation — 2026-11-06

Related issue: #248
Related self-evolution objective: #245
Branch: fix/office-roster-profile-reconciliation-2026-11-06

## Finding

bootstrap_registry() creates agent:bug-hunter with an empty skill/permission
profile. OFFICE_AGENTS declares a richer profile for the same agent ID.
bootstrap_full_office() previously skipped all existing IDs, silently losing
the richer skill and responsibility declarations.

This prevented deterministic delegation from seeing the declared bug-hunting
skills. The base agent's empty permissions also remain a separate fail-closed
constraint.

## Change

AgentRegistry.reconcile_agent_profile() now merges only non-privileged,
declarative profile information:
- skills and responsibilities are additive and case-insensitively deduplicated;
- the canonical declared role can update the descriptive role field;
- missing supervisor and non-default memory scope can be filled;
- missing metadata keys can be added without overwriting existing values.

It deliberately does NOT merge permissions, status, performance, lessons,
creation time, or existing metadata values. Permissions remain governed by a
separate explicit grant. Runtime status and operator metadata survive
reconciliation.

bootstrap_full_office() now calls this reconciliation method for each declared
office agent. It remains idempotent and preserves unknown agents.

## What this does not solve

- AVAILABLE is still not proof that WorkerRuntime has a handler registered.
- DelegationEngine still needs a readiness contract bound to a registered
  handler or verified external adapter.
- The base QA/research profiles still need real skill/handler definitions.
- No permissions are widened to make tasks assignable.
- No worker is automatically activated.

These remaining issues stay tracked in #248.

## Validation

tests/organization/test_roster_reconciliation.py covers richer duplicate
profile merging, preservation of operator status/permissions/metadata,
idempotence, department conflict rejection and registration of new profiles.
CI and PC acceptance must be reported separately.

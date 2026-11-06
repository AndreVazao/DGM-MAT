# Engineering Team Planner v1 — implementation checkpoint

Date: 2026-11-06
Issue: #245
Branch: feat/internal-engineering-team-planner-v1

## Scope

This increment introduces a deterministic, planning-only engineering team
decomposer. It reuses the existing core/development/language_catalog.py and
core/organization/models.Task; it does not add another agent registry,
mission store, scheduler, executor, or memory database.

## Behavior

- Groups recognized changed paths by canonical language profile.
- Rejects absolute paths, Windows drive paths, traversal, unknown extensions,
  and ambiguous C/C++ headers from implementation assignment.
- Produces deterministic task IDs from mission/stage/key using SHA-256.
- Builds optional research -> language implementation subtasks -> integration
  review -> independent bug-hunt and QA tasks.
- Adds an independent security review for high/critical risk.
- Every task is marked planning_only=true, execution_authorized=false,
  toolchain_status=not_probed.
- Implementation proposals require a later approval bound to an exact diff
  and request the sandbox-write permission.
- Does not assign agents, run tools, apply patches, contact providers, or
  claim validation.

## Explicit limitation

This is the first internal team-planning primitive, not an operational
multi-agent coding workforce. The current organization registry and task
manager are in-memory, and the existing worker runtime only dispatches
explicitly registered local handlers. A real coding pilot still needs a
durable task/run boundary, verified isolated worktree, allowlisted patch
operations, trusted test evidence, independent QA execution, and restart
reconciliation.

## Validation status

Tests are authored in tests/organization/test_engineering_team_planner.py.
They must pass in CI and then on the actual Windows installation. No local
PC test or end-to-end coding task is claimed by this GitHub-only increment.

## Next gate

1. Validate this planner and the focused organization regressions.
2. Compare planned task ownership against the actual registered office roster.
3. Implement one deterministic internal worker adapter for a non-mutating task.
4. Only then add the first real patch worker behind the existing approval,
   worktree and evidence boundaries.

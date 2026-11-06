# Execution-Aware Delegation Gate — 2026-11-06

Related issue: #248
Related self-evolution objective: #245
Branch: fix/delegation-requires-registered-worker-2026-11-06

## Problem

AgentStatus.AVAILABLE and a matching role/skill profile do not prove that a
local worker handler exists. Delegation previously considered only status,
department, skills, permissions and dependencies. It could assign work to an
agent for which WorkerRuntime had no registered handler; dispatch would then
fail later with a missing-handler error.

## Change

WorkerRuntime now exposes:
- has_handler(agent_id)
- registered_agents()

DelegationEngine now requires the actual WorkerRuntime instance and excludes
agents without an explicitly registered handler before scoring candidates.
Existing status, department, skill, permission and dependency checks remain
in force.

A future remote adapter (e.g. a governed FCC/Codex/Claude wrapper) can become
eligible by registering a bounded handler through the same explicit boundary.
No implicit provider is activated.

## Maturity boundary

This proves only HANDLER_REGISTERED plus a declared capability match. The
declaration is not a test result. It does not prove:
- configuration or authentication;
- endpoint reachability;
- health under load;
- task-specific capability;
- successful task execution;
- restart recovery of an external provider session.

Those remain separate readiness states and acceptance tests. A handler
registration must never be reported as READY or TASK_VALIDATED by itself.

## Tests

The office delegation regression now supplies an explicit WorkerRuntime and
proves:
- a matching registered handler with matching declared capabilities can receive a task;
- an AVAILABLE role without a handler cannot receive a task;
- offline and unauthorized agents remain excluded;
- dependency gates remain active;
- WorkerRuntime reports its registered handler inventory.

No permissions are widened and no role is auto-activated.

The legacy MissionEngine registration of QAIntakeWorker under agent:bug-hunter
is now declared as qa-intake only. It therefore cannot be selected for
reproduction/fault-isolation tasks merely because a handler exists.

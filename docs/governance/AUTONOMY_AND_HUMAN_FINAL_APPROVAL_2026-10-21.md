# DGM-MAT Governance: Autonomy and Human Final Approval

Status: implementation contract, 2026-10-21

## Operating principle

The CEO may continuously investigate, propose, prepare and carry out routine improvements within already granted policy, budget, permissions and safety boundaries. A human approval request must not freeze unrelated missions or departments.

## Autonomous by default

Unless a policy explicitly classifies an action as critical, the CEO may:
- identify weak or degraded departments and investigate the cause;
- recruit, create, configure and retire specialist agents within approved limits;
- distribute work and coordinate departments;
- prepare and apply routine, reversible improvements;
- run tests and report evidence of the result.

Every change remains subject to existing access controls, resource limits, audit logging, backups/reversibility and the rule to investigate before changing. "Autonomous" is not permission to bypass security, erase evidence, spend unapproved money, expose credentials, or make irreversible changes.

## Human final approval required

A proposal must be marked critical when it entails a major architecture/platform change, a structural reorganisation affecting multiple departments, a major technology migration, a change to security/trust boundaries, or an irreversible/high-blast-radius change. Classification must be recorded with a rationale; it must not depend only on an agent's self-description.

Creating or hiring an agent is not, by itself, a human approval trigger. If its actual plan crosses one of the critical boundaries above, the critical plan needs approval even if the task title says "hire agent" or "improve department".

## Two-stage approval flow

1. The CEO convenes the relevant department meeting and collects evidence, alternatives, risks, estimated resource impact, rollback plan and success criteria.
2. The CEO can prepare the implementation plan and tests while other unrelated work continues.
3. For a critical plan, the CEO endorses the proposal and submits a human approval request. It appears as a persistent notification/modal in the PC cockpit and, later, the mobile cockpit.
4. The notification must show: what is weak or changing, why it matters, proposed actions, affected departments, cost/resource estimate, risks, reversibility/backup, test plan, and what will happen if declined.
5. André can approve, reject, or request changes. The choice, identity, timestamp and rationale are persisted.
6. Approval permits only the exact reviewed plan/version. If the plan changes materially after approval, approval expires and must be requested again.
7. After approval, the CEO authorises execution through the governed action runner. The runner verifies the approved plan/version, executes bounded steps, records results, and reports success/failure. Approval is never itself an unrestricted shell command.

## While waiting

- The critical action remains blocked at its execution boundary.
- Preparation, analysis, documentation, non-conflicting tests and unrelated department missions continue.
- The notification remains pending across restart and appears again in the cockpit until acted upon.
- A timeout must never silently become approval.
- Rejecting a proposal closes that version; a materially revised proposal may be resubmitted.
- If the cockpit is offline, the request stays durable and queued; the system must not treat missing UI delivery as approval.

## Implementation status

The current governance-meeting PR introduces durable meeting records and an initial two-stage approval state. It does not yet implement the cockpit popup, cross-device push delivery, approval-bound execution dispatch, or end-to-end runtime tests. Those are explicit follow-up work and must not be represented as completed.

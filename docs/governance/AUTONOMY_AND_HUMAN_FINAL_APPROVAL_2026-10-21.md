# DGM-MAT Governance: Autonomy and Human Final Approval

Status: implementation contract, 2026-10-21

## Operating principle

The CEO and every department must keep working and improving continuously within their granted authority. Human approval gates apply to the specific action or plan that needs approval, never as a reason to pause unrelated missions, departments, research or preparation.

The long-term goal is progressive autonomy: the CEO adapts to André's established preferences and decisions, and can take more decisions independently when a reliable, auditable pattern has been demonstrated and explicitly falls within delegated boundaries. The system must not make André a permanent bottleneck.

## Autonomous by default

Unless a policy explicitly classifies an action as critical, the CEO and departments may:
- identify weak or degraded departments and investigate the cause;
- recruit, create, configure and retire specialist agents within approved limits;
- distribute work and coordinate departments;
- prepare and apply routine, reversible improvements;
- run tests and report evidence of the result;
- improve their own workflows and propose further improvements, while respecting shared interfaces and security boundaries.

The CEO coordinates cross-department work and endorses decisions within the authority granted to it. Departments retain autonomy for work inside their own remit; they should not need CEO or owner approval for every ordinary task.

Every change remains subject to access controls, resource limits, audit logging, backups/reversibility and the rule to investigate before changing. "Autonomous" is not permission to bypass security, erase evidence, spend unapproved money, expose credentials, or make irreversible changes.

## Progressive trust and delegated decision authority

The CEO should learn from André's approvals, rejections, requested changes, stated reasons and the verified outcomes of decisions. The purpose is to reduce repetitive approval requests for genuinely equivalent, low-risk decisions.

Trust must be evidence-based and scoped, not a single opaque confidence score:
- Record the decision category, context, affected scope, risk level, André's choice and rationale when available.
- Compare new cases against prior decisions by substance and risk, not merely by matching task titles or keywords.
- Promote a decision category to autonomous handling only when there is sufficient repeated evidence of consistent outcomes and the authority policy explicitly allows delegation for that category.
- Start with narrow scope and reversible actions; expand scope gradually only when results support it.
- Keep a clear audit trail explaining why a decision was handled autonomously and which prior decisions/policy boundaries supported it.
- Learn from rejections and corrections as well as approvals. An approval for one department, environment, budget or risk level does not automatically generalise to another.
- Treat changed circumstances, novel risks, conflicting examples or materially different plans as reasons to lower confidence and reassess.
- André must be able to inspect, correct, narrow or revoke a delegation. Never silently infer unlimited authority from repeated approvals.
- Confidence alone must never override an explicit human-approval requirement, security rule, legal constraint, budget limit or protected boundary.

Suggested maturity levels:
1. **Unfamiliar:** investigate and prepare; request approval if outside current authority.
2. **Observed pattern:** use previous decisions as guidance but keep the existing approval gate.
3. **Consistent and verified:** autonomously handle equivalent cases only inside a documented, delegated scope.
4. **Exception or drift:** pause only the affected action, explain what differs and escalate when the difference crosses a protected boundary.

## Progressive-trust implementation boundary

The initial policy engine is implemented in `core/governance/progressive_trust.py` with a separate persistent store. It records owner-attributed feedback, evaluates an exact category/scope against an existing owner-granted delegation, requires a configurable number of verified reversible successes, and resets the success run after rejection/correction/revocation. Delegations are restricted to low/medium risk and cannot remove mandatory protected boundaries. Owner-only API routes create/revoke delegations and record feedback; a read-only evaluation route returns a decision result without permitting execution.

This is deliberately not automatic self-promotion: repeated approvals alone never create a delegation. An explicit owner-granted scope is required. The feedback endpoint trusts only the authenticated owner identity and is intended for verified results; UI integration must not mark a result verified until the outcome has actually been checked. The policy engine is not yet wired into the CEO's live decision scheduler/action runner, and the cockpit does not yet surface the approval/feedback/delegation controls.

## Human final approval required

A proposal must be marked critical when it entails a major architecture/platform change, a structural reorganisation affecting multiple departments, a major technology migration, a change to security/trust boundaries, or an irreversible/high-blast-radius change. Classification must be recorded with a rationale; it must not depend only on an agent's self-description.

Creating or hiring an agent is not, by itself, a human approval trigger. If its actual plan crosses one of the critical boundaries above, the critical plan needs approval even if the task title says "hire agent" or "improve department".

Explicitly protected structural changes remain subject to André's approval even if similar changes were approved before, unless André has specifically delegated that exact decision category and scope through a recorded policy change. The CEO may recommend such a delegation but cannot grant it to itself.

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
- The blocked task must not hold a department-wide lock or prevent unrelated work from being scheduled.

## Privileged governance API credentials

The CEO approval, owner final-approval, and owner progressive-trust endpoints require a separate server-verified credential in the `X-DGM-Governance-Credential` header. Configure two distinct random secrets of at least 32 characters as `DGM_GOVERNANCE_CEO_TOKEN` and `DGM_GOVERNANCE_OWNER_TOKEN`. If either secret is missing, too short, or equal to the other, privileged governance routes fail closed with HTTP 503. An invalid or missing credential is denied; a session's `client_id`, subject, username, request-body actor, or claimed role never establishes CEO/owner authority.

These secrets must remain outside source control, frontend bundles, URLs, request bodies, logs, and browser local storage. The generic local session bearer remains required by the outer API middleware in addition to the dedicated governance header. The current cockpit does not yet provide a secure credential-entry/approval flow, and the CEO scheduler does not yet inject its privileged credential; therefore this change secures the API boundary but does not claim the full approval workflow is end-to-end operational.

## Implementation status

The current governance-meeting PR introduces durable meeting records, a pending-approval listing endpoint for cockpit polling, conservative content-based critical-plan signals in addition to meeting-type classification, and a SHA-256 digest binding CEO/owner approval to the reviewed proposal, action plan and recorded evidence. New evidence added after a decision invalidates that decision and its approvals. A separate progressive-trust policy module and owner-controlled API are also included. Focused governance tests passed in GitHub Actions on Linux and Windows (Python 3.12): https://github.com/AndreVazao/DGM-MAT/actions/runs/39846286623. This is focused validation, not a full-repository or live-PC integration test. The PR does not yet implement the cockpit popup, cross-device push delivery, approval-bound execution dispatch, live CEO scheduler integration, UI feedback capture, or end-to-end runtime tests. After both approval gates succeed, the registry now reports `approved_execution_not_implemented` rather than implying the action is ready to run; no governed action runner is currently wired to execute the approved plan. These gaps remain follow-up work and must not be represented as completed.

# Path: C:\\ProgramasGodMode\\DGM-MAT\\docs\\architecture\\HELP_SEEKING_ZERO_COST_POLICY.md
# DGM-MAT — Help-Seeking and Zero-Cost-by-Default Policy

Date: 2026-10-09
Status: deterministic policy primitive implemented; MissionEngine failure-path integration is tested. Global provider/spending enforcement is not yet implemented.

## Core invariant

DGM-MAT does not need to know everything. It must recognize uncertainty, use evidence, find the appropriate help path and ask a precise question when blocked. It must never disguise an unverified guess as a result.

**Free by default. Evidence before claims. Ask when blocked. Never spend without explicit authorization.**

## Decision order

1. Reject an empty/missing mission goal by asking the user for the intended outcome.
2. If a material decision or authorization belongs to the user, ask one focused question.
3. If the bounded attempt budget has been reached, stop retrying and report a truthful BLOCKED/PARTIAL state with evidence.
4. If a suitable internal specialist is available, delegate with relevant context before reaching for external services.
5. If a safe local/free option exists, investigate it and record evidence.
6. If only a potentially paid option is known, stop before execution and request cost-specific authorization.
7. If unknowns remain, inspect persistent memory, code, tests and official documentation without paid calls.
8. Proceed only within existing permissions and verify the result before claiming completion.

## Help request contract

A routed help request should include, where available:
- desired goal and acceptance criteria;
- verified facts, clearly separated from unknowns;
- steps already attempted;
- relevant error messages, test results and evidence;
- known local/free options and constraints;
- the exact question or action needed from the recipient.

Do not repeat work already evidenced in memory or task history. Route to the smallest suitable specialist group rather than broadcasting indiscriminately.

## Spending gate

A future execution adapter may proceed with spending only when all three are independently true:
- explicit human approval exists;
- exact cost/limit is known;
- the operation is within the approved limit.

Approval to spend is not itself approval to execute an unrelated action. Credentials must not be exposed in help requests or logs. Free-tier availability and quota must be verified rather than assumed. When no safe/free path exists, leave the task BLOCKED/PARTIAL and explain the exact decision needed.

## Implemented primitive

- core/organization/help_seeking.py
  - HelpContext: mission facts, unknowns, attempts, evidence, free options, specialist availability and approval state.
  - HelpSeekingPolicy.decide: deterministic fail-closed next-step choice.
  - HelpSeekingPolicy.build_request: evidence-led request formatting.
  - HelpSeekingPolicy.may_spend: strict three-condition spending gate.
- Tests: tests/organization/test_help_seeking.py.

## Current limitation / next gate

MissionEngine's failure handler now records a persisted `RECOMMENDATION_ONLY` help-seeking record in mission metadata: action, reason, next step, evidence-rich request and `spending_allowed=false`. It preserves the mission's honest `FAILED` state and does not dispatch a message, retry, invoke a provider or spend money. Focused integration tests and the full repository suite passed after this change.

This is not yet a global enforcement boundary. Provider adapters are not all gated by this policy, recommendations are not yet routed to live specialist workers, and there is no end-to-end guarantee across every spend-capable code path. Next work: route recommendations to durable task/help queues; integrate cost/approval preflight at the provider execution boundary; persist attempts and evidence; enforce retry limits/quarantine; and test that paid adapters are never invoked without explicit approval, verified cost and an approved limit. Do not claim platform-wide protection until those gates are implemented and verified.

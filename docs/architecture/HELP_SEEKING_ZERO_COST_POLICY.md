# Path: C:\\ProgramasGodMode\\DGM-MAT\\docs\\architecture\\HELP_SEEKING_ZERO_COST_POLICY.md
# DGM-MAT — Help-Seeking and Zero-Cost-by-Default Policy

Date: 2026-10-09
Status: first deterministic policy primitive implemented and unit-tested; not yet wired into Mission Engine/provider execution.

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

This is a policy primitive, not yet a global enforcement boundary. It does not call providers, send messages, or alter Mission Engine status. Next work must integrate it into Mission Engine and provider routing, persist decisions and evidence, enforce bounded retries/quarantine, and add end-to-end tests proving that a paid path is never invoked without the explicit cost-specific gate. Do not claim the DGM-MAT as a whole is already protected by this policy until that integration is completed and verified.

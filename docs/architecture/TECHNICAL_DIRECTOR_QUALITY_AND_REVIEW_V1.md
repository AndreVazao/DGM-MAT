# Technical director: quality and peer-review policy

## Purpose

The DGM-MAT technical director must decide whether a code change is measurably safer/better than its baseline, request independent review, and escalate unresolved technical disputes to evidence-based research.

## Deterministic quality gate

`assess_code_change` compares immutable baseline and candidate Git revisions using host-collected evidence. It checks:
- no previously passing check regresses;
- no baseline check silently disappears;
- all candidate checks pass;
- diff whitespace and compilation checks pass;
- changed files stay within the declared scope;
- every changed path has declared test evidence;
- critical findings do not increase and high findings do not increase.

The gate returns BLOCKED, NEEDS_FIXES, or ACCEPT_FOR_PEER_REVIEW plus a SHA-256 digest of the evidence. Passing means only that measured gates passed; it is not a proof of correctness or security.

## Sequential peer review

The policy accepts only Codex and Claude Code as the initial local providers. The author cannot review its own output. Reviews happen one at a time:
1. author submits a candidate and evidence;
2. objective gates run before AI review;
3. a distinct provider reviews the diff and evidence;
4. REQUEST_CHANGES returns the task to the author;
5. UNRESOLVED/blocked findings are escalated to the next independent provider;
6. after the local reviewers are exhausted, the director emits WEB_RESEARCH_REQUIRED with a concrete question.

An APPROVE outcome permits only transition to operator approval. It does not approve the change, enable writes, merge, or deploy.

## Web research boundary

This increment produces a bounded research question only. It does not silently browse, treat search snippets as truth, or call external AI services. A future host adapter must collect source URLs, publication dates, quoted evidence, and provider provenance, then return findings for the director to assess. Research cannot override failed tests or grant execution authority.

## Explicit non-capabilities

This increment is a deterministic policy/state machine. It does not launch Codex/Claude, execute code, collect Git diffs, run tests, or make real provider calls. Those operations require separately tested host adapters, isolation, receipts, and task-specific approval.

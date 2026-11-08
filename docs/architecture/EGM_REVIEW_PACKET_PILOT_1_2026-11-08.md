# EGM review packet contract — pilot 1

- Date: 2026-11-08
- Branch: feat/egm-review-packet-contract-2026-11-08
- Scope: read-only contract and deterministic tests
- Upstream method: https://github.com/google/elephant-goldfish-model

## What was implemented

`core/organization/design_review.py` adds a small, dependency-free contract for preparing bounded design-review packets and validating recorded reviewer results.

- `DesignBrief`: problem, outcome, constraints, acceptance criteria, evidence locators and optional existing mission/task identifiers.
- `ReviewerPacket`: one reviewer identity per packet, shared bounded brief and explicit forbidden-context policy.
- `ReviewFinding`: severity, evidence, impact, recommendation and confidence.
- `ReviewerResult`: result linked to review/reviewer and a runtime context identifier.
- `build_reviewer_packets`: requires 2–5 unique reviewer IDs.
- `validate_independent_results`: rejects missing/mismatched reviewers and shared runtime context IDs; distinct IDs alone are only structurally valid, not proof of independence.
- `result_to_dict`: creates a JSON-ready snapshot suitable for a future existing task receipt.

## Security and authority limits

This is a contract/builder only. It does not instantiate model sessions, call providers, dispatch tasks, read conversations, execute tools, mutate files, approve changes or persist records.

The validator defaults to `independent=false`. It only returns `independent=true` when reviewer identities match, runtime context IDs are distinct, and the caller explicitly supplies a runtime isolation attestation. That attestation must come from a provider/runtime adapter that can prove the contexts are fresh and do not share prior conversation or reviewer outputs. A boolean supplied by an untrusted model response is not acceptable evidence.

Reviewer packets deliberately omit author conversation, chain-of-thought, author recommendation, other reviewers' outputs and all credentials/session secrets. Only the explicit DesignBrief is included.

The module does not create a new queue or database. A future integration must use the existing OrganizationTaskManager, MissionEngine and durable receipt path. It must not add a parallel execution plane.

## Current limitations / next gate

- No runtime provider adapter exists in this pilot.
- No API, APK or PC dashboard route is added.
- No automatic invocation or approval is enabled.
- No task lifecycle or production configuration is changed.
- A follow-up must prove fresh context creation in the actual agent runtime before any review can be labelled independent.
- The first live pilot must be read-only and operate on a low-risk design brief, with at least two truly isolated reviewers and a persisted task-linked receipt.

## Tests

`tests/organization/test_design_review.py` covers reviewer-count/identity constraints, bounded packet shape, forbidden context fields, distinct-context enforcement, explicit runtime-attestation gating, identity mismatch, finding validation and JSON-ready result snapshots.

These tests are authored in this branch; CI execution is required before the pilot can be considered validated.

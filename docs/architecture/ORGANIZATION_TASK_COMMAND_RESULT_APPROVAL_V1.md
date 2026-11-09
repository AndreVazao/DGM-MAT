# Organization task command, result and approval API v1

**Status:** implementation candidate; awaiting focused CI and Windows build evidence  
**Scope:** the three currently registered read-only repository specialists only.

## Contract

The local runtime exposes a bounded, authenticated lifecycle:

| Operation | Route | Scope |
|---|---|---|
| Issue a typed order and attempt dispatch | `POST /runtime/organization/tasks` | operator |
| Resume an assigned task that remained queued | `POST /runtime/organization/tasks/{task_id}/dispatch` | operator |
| Read status, result, receipt and digest | `GET /runtime/organization/tasks/{task_id}` | local-client |
| Request review of an exact result | `POST /runtime/organization/tasks/{task_id}/approval` | operator |
| Approve/reject the exact reviewed result | `POST /runtime/organization/tasks/{task_id}/decision` | operator |

## Order boundary

The caller may select only one of three typed operations:

- `repository_inventory`
- `python_source_analysis`
- `python_test_inventory`

The request accepts a host-owned repository identifier, not a path, shell command, script, executable, free-form prompt, or permission list. The worker registration resolves the identifier through `DGM_READ_ONLY_WORKSPACE_ROOT` and `DGM_READ_ONLY_REPOSITORIES`. If that host allowlist or a compatible worker is absent, delegation is blocked and no task code runs.

## Result receipt

A successful dispatch must return a worker message ID, structured result and `durable_receipt=true`. The existing OrganizationTaskManager persists the result in the shared SQLite task store. A later GET reads that stored record and computes a canonical JSON SHA-256 digest. A queued task can be resumed; the deterministic message identity in the read-only orchestrator prevents duplicate work after a completed receipt. A worker-level refusal is also persisted with its receipt but leaves the task in `BLOCKED`; blocked results cannot enter the approval route.

## Approval binding

The approval request stores an envelope containing task ID, mission ID, operation kind, repository ID, assigned agent, worker message ID, exact structured result and result digest. The operator decision must repeat the same digest. The authenticated operator identity and rejection rationale are preserved in the durable approval audit and exposed on subsequent task reads. Before accepting it, the API re-reads the durable task and verifies the digest, message ID and approval envelope. Stale or substituted results are rejected. Approval/rejection is persisted through the existing durable approval queue and can be read back from the task endpoint.

This approval is an explicit review decision for a read-only worker result. It is **not** permission to edit files, approve a coding patch, merge a PR, deploy software, or execute a command.

## Safety and current limits

- No shell or executable is accepted from the request.
- No external provider or paid fallback is contacted.
- No code mutation, worktree write, Codex/Claude invocation, commit, merge or deployment is enabled by these routes.
- Operator routes use the existing local session authentication inventory; result reads use the local-client scope.
- A missing worker, missing host allowlist, stale digest, missing receipt, duplicate decision or invalid task ID fails closed.
- This API proves the DGM-MAT order/result/review loop for the fixed read-only specialists only. A separate controlled coding executor and patch-digest promotion gate remain required before claiming end-to-end coding-agent autonomy.

## Acceptance tests

The focused API tests exercise command dispatch, result retrieval, durable receipt fields, exact digest review, stale-digest rejection, decision persistence, queued dispatch resumption and rejection of arbitrary task kinds/invalid repository IDs. Security tests assert the operator/local-client route scopes. CI results are recorded in the associated pull request; this document alone is not execution evidence.

# DGM-MAT readiness checkpoint — 2026-11-05

## Executive status

DGM-MAT is **not yet ready for unattended autonomous development**. Browser conversation recovery has a merged evidence-based improvement. A native Windows backup-first executor now exists in draft PR #220 and passes hosted Windows and focused CI, but it is not merged, not locally accepted on the operator's Windows 10 PC, and not integrated into MissionEngine. Runtime must remain SAFE.

## Verified GitHub changes

### PR #216 — merged

- Merge commit: `31608ebba5d83f14d978204d147f6f2c136380ad`.
- Adds bounded top-loading attempts before the extension scans the visible conversation window.
- Captures `top_load_steps` and `top_load_limit_reached` in the API schema, immutable archive and response.
- A top-loading limit marks the capture truncated.
- Does **not** claim full history: `history_start_reached=false`, `oldest_boundary=unknown`, `full_history_verified=false` until provider-specific positive evidence exists.
- Focused PR Validation #243: success.
- Chrome Extension Validation #79: success, including JavaScript syntax, manifest validation, pip-audit, Bandit, API regressions and extension packaging.
- Artifact: `DGM-MAT-Chrome-Conversation-Recovery`, ID `13427659768`.
- SHA-256: `5946ad06c12e918cce32e8f46cec838719fe95ba9f6c356ab74fecde2853ca83`.
- Artifact expiry: 2026-11-19.
- Live acceptance against authenticated ChatGPT, Gemini and Grok sessions remains outstanding (#208); provider-confirmed oldest-history and deterministic multi-window fixtures remain outstanding (#215).

### PR #222 — draft virtualized-history capture fixtures

- Clean replacement for PR #221; branch `test/browser-virtualized-history-clean-2026-11-05`, one commit and five files.
- Adds seven deterministic Node fixtures against the actual content script, covering ChatGPT/Gemini/Grok selectors, virtualized older windows, overlap/duplicates, chronological ordering, unknown oldest boundary, hard limits, identical text-only turns without stable IDs, and DOM mismatch fail-closed behavior.
- The content script merges overlapping windows by stable message IDs and marks ambiguous ordering/identity as truncated.
- API archives `sequence_order_conflict` and `oldest_boundary_evidence`. A positive oldest-boundary claim is accepted only when evidence is in the provider-specific allowlist; production allowlist is intentionally empty. All current providers remain `partial_or_unknown` until real provider markers are verified.
- Fresh CI on exact PR head `d9bae549a49bdf7dd4f5cc4c4f894e49a492d6f9`: Chrome Extension Validation #103 **success**; Focused PR Validation #354 **success**.
- Artifact: `DGM-MAT-Chrome-Conversation-Recovery`, ID `13435428666`, SHA-256 `2e54d055b82d0eec1be73974ec3428fe0e79f9a10d30c8817e7dc03665c208f5`, expires 2026-11-19.
- PR #221 closed without merge to keep the branch history small; source branch retained for audit.
- Live authenticated ChatGPT/Gemini/Grok acceptance remains outstanding (#208). No real provider oldest-history marker has been confirmed (#215).

### Backup-first executor — draft PR #220

- PR #214 was closed without merge; its original path-based executor remains retained for audit.
- PR #217 remains a separate draft containing the POSIX dirfd prototype; Windows mutation in that branch fails closed.
- PR #219 was closed without merge because its 78-commit history was unnecessarily large. Its source branch remains retained for audit.
- Clean replacement: [PR #220](https://github.com/AndreVazao/DGM-MAT/pull/220), branch `fix/backup-first-executor-win32-clean-2026-11-05`. The PR contains six files and three commits (one implementation commit plus two merge-base synchronization commits).
- Implementation commit: `aa51f100c5145f83e7ea651076c44abeac068a7f`; synchronization commit: `6bd69227baafacaa37255c0654c0cd9a91e9ca41`.
- Fresh CI on the implementation commit: Windows Guard #71 passed (38 passed, 8 POSIX-only tests skipped by policy); Focused PR Validation #328 passed.
- After synchronization with current main, Windows Guard #73 and Focused PR Validation #330 both passed on exact head `db18012f3d2d094a8dc3ed14b7b680b8025b93d1` (38 passed, 8 POSIX-only tests skipped). PR #220 remains draft and mergeable, but is not accepted locally.
- Windows is the only active mutation backend. Existing targets are opened with exclusive share semantics and write-through; new targets use atomic `FILE_CREATE`. Handles remain pinned during backup, write and verification. Hard-linked targets, reparse points and 8.3 aliases are rejected.
- Backup-root directories are created relative to pinned no-follow handles. Backup and manifest files use exclusive handles. The manifest records `prepared` before mutation and `applied` after byte verification. Rollback checks repository identity, target identity, hard-link count, operation/backup consistency, current hash and rollback availability.
- POSIX apply and rollback explicitly fail closed. The unsafe POSIX mutation implementation has been removed because portable POSIX replace/delete cannot exclude uncoordinated writers.
- Snyk reports exactly `You have used your limit of private tests`. The scan did not run; this is neither a vulnerability report nor a clean scan. No paid quota was purchased and the scanner was not disabled.
- CodeRabbit's free OSS review limit has been reached. No fresh independent review of #220 has completed.
- Remaining executor gates: independent review when available; review inherited backup-root ACL and Windows namespace durability limits; local Windows 10 acceptance. Keep #220 draft and do not merge yet.

## Verified remaining implementation gaps

### Mission execution (#212)

- `core/development/implementation_engine.py` remains a placeholder: it backs up `.env` and returns `IN_PROGRESS`.
- `DevelopmentEngine.process_request` dispatches an implementation event but does not apply a patch or validate the result.
- The backup-first executor is not integrated into mission execution.
- No end-to-end temporary Git repository test yet proves patch, registered tests, checkpoint/resume, rollback and PR-ready output.
- No arbitrary shell, OS elevation, writes outside a validated worktree or automatic merge may be introduced.
- Integration remains blocked until PR #220 is reviewed, merged after all gates, and accepted on the local Windows 10 PC.

### Free-tier AI consultation (#211)

- Controlled ChatGPT/Gemini/Grok consultation through the normal authenticated browser UI is not implemented.
- It must remain a separate, explicit opt-in workflow, with minimal redacted prompts, local provenance, rate limits and AI responses stored only as untrusted proposals.

### Conversation recovery (#208, #215)

- The extension is packaged and CI-validated, but it has not been paired with the operator's local Chrome session in this checkpoint.
- No live conversation has been captured in this session.
- Never read cookies, tokens, passwords, browser authentication storage or hidden provider APIs.
- A visible snapshot is not proof of full historical coverage.

## Runtime safety state

The main-branch configuration remains:

- `execution_mode=SAFE`
- SAFE permissions: `read`, `test`
- `approval_required=true`
- `auto_merge_enabled=false`

Do not promote the runtime mode merely by changing configuration. Real write capability must exist, be integrated, tested and recoverable first.

## Next gates, in order

1. Obtain an independent security review when CodeRabbit's review quota resets; separately resolve the Snyk private-test quota or obtain equivalent coverage without hiding the check.
2. Review backup-root ACL inheritance and document the limits of write-through/file flushes for sudden power loss; do not claim unverified namespace durability.
3. Perform local Windows 10 acceptance for #220: create/replace, backup, rollback, prepared-state recovery and concurrent-writer rejection.
4. Complete live authenticated UI acceptance for #222 on ChatGPT, Gemini and Grok; provider-specific oldest-history markers remain disabled until real evidence is stable and reviewed.
5. Only after the executor gates, integrate it into MissionEngine under issue #212: structured plans, allowlisted paths, isolated worktrees, fixed validator registry, checkpoints, guarded rollback and reviewable PR output.
6. Add a temporary-Git-repository E2E test, including negative tests for traversal, symlinks, secrets, arbitrary shell and rollback conflicts.
7. Implement separate free-tier AI consultation (#211), with explicit opt-in and no paid API use.
8. Build the Windows executable from validated main, preserve the local dirty checkout, then perform one controlled installation/health/worker/persistence smoke test.
9. Only after the local runtime passes, enable bounded autonomous work in isolated worktrees. Keep approval for irreversible or high-impact actions and keep auto-merge disabled.

## Local-PC and quota boundary

No local PC installation, executable replacement, process cleanup, Chrome pairing or live conversation capture was performed in this checkpoint. Desktop Commander was not used. The local dirty working tree and existing executable copies must remain preserved until a validated new Windows build is ready.

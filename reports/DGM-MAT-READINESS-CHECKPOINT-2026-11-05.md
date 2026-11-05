# DGM-MAT readiness checkpoint — 2026-11-05

## Executive status

DGM-MAT is **not yet ready for unattended autonomous development**. The current main branch has a validated improvement to browser conversation recovery, but mission execution still lacks a connected, race-resistant patch path. The runtime must remain SAFE until that gap is closed.

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

### PR #214 — blocked, do not merge

- Branch: `fix/backup-first-executor-rebased-2026-11-05`.
- Earlier focused validation #239 passed for the previous implementation; it does not validate the latest changes.
- Latest code head: `9108381e16507d2258fa8abf64fe19c0ab53a865`.
- The latest implementation uses POSIX `O_DIRECTORY | O_NOFOLLOW` directory-handle traversal and basename-relative atomic rename; original bytes are read from the pinned directory handle, the external backup is verified from those bytes, and rollback uses the same guarded path.
- A deterministic regression swaps the visible parent path to an outside symlink after opening the directory handle and asserts that the outside target remains unchanged.
- Windows mutations explicitly fail closed before backup or write because a native Windows handle backend is not yet implemented.
- **Validation gap:** no CI run has yet been observed for the latest head. Do not treat earlier #239 as evidence for this implementation.
- **Residual threat-model limit:** POSIX handle anchoring addresses parent-path symlink substitution, but does not claim containment if a hostile same-user process physically relocates the already-open directory outside the worktree. This needs independent review or a stricter operational boundary.
- The Snyk status is an external integration error, not a vulnerability result; no clean Snyk result is claimed.
- Do not merge until current-head tests pass, the residual filesystem threat model is accepted or further hardened, and the supported Windows runtime has an appropriate native backend or remains explicitly unavailable.

### PR #207 — closed as superseded

- Closed without merge; its branch was not deleted.
- PR #214 is the current-main replacement and remains blocked by the security gate above.

## Verified remaining implementation gaps

### Mission execution (#212)

- `core/development/implementation_engine.py` is still a placeholder: it backs up `.env` and returns `IN_PROGRESS`.
- `DevelopmentEngine.process_request` dispatches an implementation event but does not apply a patch or validate the result.
- The backup-first executor is not integrated into mission execution.
- No end-to-end temporary Git repository test yet proves patch, registered tests, checkpoint/resume, rollback and PR-ready output.
- No arbitrary shell, OS elevation, writes outside a validated worktree or automatic merge may be introduced.

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

1. Resolve the Windows TOCTOU defect in PR #214; prove the fix with concurrent-swap tests.
2. Re-run focused validation and independent security checks; do not suppress or misreport the Snyk integration error.
3. Integrate the verified executor into the mission engine under issue #212: structured plans, allowlisted paths, isolated worktrees, fixed validator registry, checkpoints, guarded rollback and reviewable PR output.
4. Add a temporary-Git-repository E2E test, including negative tests for traversal, symlinks, secrets, arbitrary shell and rollback conflicts.
5. Finish provider-specific virtualized-history fixtures and live local acceptance for ChatGPT, Gemini and Grok.
6. Implement separate free-tier AI consultation (#211), with explicit opt-in and no paid API use.
7. Build the Windows executable from validated main, preserve the local dirty checkout, then perform one controlled installation/health/worker/persistence smoke test.
8. Only after the local runtime passes, enable bounded autonomous work in isolated worktrees. Keep approval for irreversible or high-impact actions and keep auto-merge disabled.

## Local-PC and quota boundary

No local PC installation, executable replacement, process cleanup, Chrome pairing or live conversation capture was performed in this checkpoint. Desktop Commander was not used. The local dirty working tree and existing executable copies must remain preserved until a validated new Windows build is ready.

# DGM-MAT — Code Recovery, File Assembly and Simplicity Gate

**Status:** operating contract / design gate; not yet wired into the mission runtime.  
**Date:** 2026-10-22  
**Branch:** `audit/programming-department-readiness-2026-10-22-synced`

## Objective

Recover useful code and decisions from the user's conversations across ChatGPT, Claude, Gemini, Grok, Perplexity and other sources; reconstruct the intended project state; integrate only the necessary code into the actual original files; and keep the result simple, secure, testable and functional.

The goal is working software, not the largest patch, the most abstractions, or the most files.

## 1. Recover conversations with provenance

1. Use only conversations, exports, files or connectors the user has authorized and that the runtime can actually access. Never imply that an inaccessible AI account or private conversation has been searched.
2. Preserve source metadata where available: platform, conversation/export identifier, timestamp, message author, message order, project/repository, referenced file and exact excerpt or artifact digest.
3. Classify each item as one of:
   - **User requirement/decision** — explicit user instruction or approval.
   - **AI proposal** — suggestion only; not approved merely because an AI wrote it.
   - **Observed fact/evidence** — code, logs, tests, command output or repository state with source and time.
   - **Superseded/contradicted** — retained for history but not treated as current truth.
   - **Unverified** — missing source, incomplete snippet or not independently checked.
4. Keep the original excerpt/file unchanged in the recovery record. Record any extracted code separately and link it to the source; do not silently rewrite history.
5. Resolve conflicts using explicit user decisions and newer verified repository/runtime evidence. If a material conflict remains unresolved, ask the user rather than inventing a decision.
6. Never treat credentials, tokens, personal secrets or private data found in exports as ordinary code to reproduce. Redact secrets from reports and use approved secret storage.

## 2. Reconstruct before editing

For each recovery mission, create a small inventory containing:
- requested behavior and acceptance criteria;
- source conversation/artifact and confidence;
- target repository, branch, exact destination file and relevant symbol/function;
- whether the source is a complete file, patch, snippet or pseudocode;
- dependencies, imports, callers and compatibility assumptions;
- unresolved conflicts and required tests.

Inspect the actual current destination file and its callers before editing. A snippet is not a replacement for the original file. Do not overwrite an original with a fragment simply because the fragment looks newer.

## 3. Assemble files by minimal patch

- Prefer a narrow patch to the original file over creating a parallel implementation.
- Place recovered functions/classes at the correct scope; merge imports without duplicates; preserve existing public names, signatures, configuration behavior, encoding and line endings where practical.
- Before adding a new helper/module, search for an existing function or service that already performs the job. Extend it when safe; do not create a second competing source of truth.
- Reconcile conflicting snippets against the current file, tests, callers and dated source evidence. Do not blindly concatenate fragments or accept code solely because it appeared in an AI answer.
- Keep unrelated formatting, renames, refactors and documentation churn out of a functional fix.
- Preserve a recoverable diff/commit before destructive cleanup. Never delete legacy code until callers, dynamic loading, configuration references and compatibility tests have been checked.
- Apply changes only within the mission's declared path allowlist. Any additional path requires a recorded reason and owner approval.

## 4. Mandatory overengineering / simplicity check

Before implementation and again before marking a task complete, ask:

1. **Necessity:** Which explicit acceptance criterion requires each changed file, abstraction, dependency and service?
2. **Reuse:** Can an existing module, API or dependency safely solve this without duplication?
3. **Smallest sufficient change:** Can the same behavior be achieved with fewer files, branches, settings, moving parts or runtime processes?
4. **Security:** Does the change reduce risk without adding unnecessary privilege, network exposure, secret copies or destructive automation?
5. **Compatibility:** Have existing callers, stored data, configuration, public interfaces and startup paths been considered?
6. **Proof:** What focused test demonstrates the requested behavior? What regression/security test protects the boundary?
7. **Removal:** Is any new code unused, duplicated, speculative or unconnected? If yes, do not add it yet.
8. **Evidence:** Is each claim labelled as proposed, implemented, test-passed, independently reviewed or runtime-verified? Never upgrade a status without evidence.

A change is not approved merely because it passes a checklist. The review must explain each new dependency and duplicated capability; unexplained additions block the patch. Unrelated files are out of scope. Untested changes require review and cannot be reported as verified.

The deterministic helper `core/development/change_scope_review.py` provides an initial machine-checkable scope check. It detects undeclared paths, unsafe paths, missing scope/outcome, untested changed paths, unjustified new dependencies and overlapping capabilities. It is a review aid, not an AI design judge or security certification. It is not yet wired into mission execution.

## 5. Merge and validation sequence

1. Establish a clean baseline and record repository, branch, base commit and working-tree state.
2. Inventory sources and map fragments to current files.
3. Agree on scope and acceptance criteria before editing.
4. Prepare the smallest patch; inspect the complete diff for accidental deletions, duplicate code, secrets and unrelated changes.
5. Run focused tests, then relevant regression tests; record exact commands, exit codes and artifact paths.
6. Have an independent reviewer examine behavior, security and unnecessary complexity. The implementer cannot self-certify independent QA.
7. Check for stale source revisions, conflicts, changed callers and generated files.
8. Report what was changed, what was tested, what failed, what remains unverified and the exact branch/commit.
9. Keep the branch unmerged until evidence and repository policy permit it. Never claim runtime success from code review or a GitHub commit alone.

## 6. Required recovery record

Each recovered unit should minimally record:

- `source_id`, `platform`, `conversation_or_export_ref`, `message_or_file_ref`, `author_role`, `captured_at`;
- `classification` (user decision / AI proposal / observed evidence / superseded / unverified);
- `project`, `repository`, `branch`, `source_revision` where known;
- `target_path`, `target_symbol`, `integration_method` (insert / patch / replace-full-file / reject);
- `reason`, `conflicts`, `tests`, `verification_status`.

Do not add a new database or service just to store these fields if an existing memory/task store can safely hold them. First identify the existing source of truth and extend it minimally.

## Acceptance criteria

A recovery/assembly mission is complete only when:
- source provenance and user-approved intent are distinguishable from AI suggestions;
- every integrated fragment is mapped to a target and reconciled against the original file;
- the diff contains only justified changes;
- duplicate capabilities and dependencies have been reviewed;
- focused tests and independent QA have recorded results;
- unresolved limitations are explicit;
- the system does not claim success when files were merely planned, generated or copied.

**Current implementation boundary:** this document and the scope-review helper define the intended process. Conversation ingestion, fragment assembly, provenance persistence, and runtime enforcement are not yet implemented end-to-end.

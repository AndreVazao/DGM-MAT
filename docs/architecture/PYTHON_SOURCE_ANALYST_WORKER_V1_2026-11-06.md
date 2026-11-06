# Python Source Analyst Worker v1

Date: 2026-11-06
Issue: #245
Depends on: PR #250 (handler capability-aware delegation)

## Purpose

Introduces the first language-specific engineering specialist. It performs bounded,
read-only Python source analysis using the standard-library AST parser. It does not
execute modules, import project code, invoke a shell, contact an AI provider, or
modify repository files.

## Request boundary

The message body is strict JSON with exactly:
- schema_version: 1
- operation: analyze_python_repository
- repository_id: an identifier configured by the host

The sender, recipient, mission and correlation IDs are checked. The request cannot
supply paths, commands, output locations, or resource limits. Repository roots are
resolved and checked against a host-owned allowed root at construction and dispatch.

## Analysis

- Walks only non-symlink directories and skips common secret/dependency/cache folders.
- Reads bounded UTF-8 Python source files only; sensitive filenames are excluded.
- Parses with ast.parse; it never calls exec, eval, compile, importlib, subprocess or a shell.
- Reports syntax diagnostics, import names, function/class counts and a deterministic
  source digest; it never returns source text.
- Enforces file count, per-file byte, aggregate byte, directory-entry and traversal-depth budgets. Reads at most the remaining per-file/aggregate allowance plus one byte, so oversized files are not loaded wholesale.

## Maturity boundary

The worker is a deterministic syntax/structure analyst, not an AI reviewer. AST parsing
does not prove runtime correctness, security, behavior, test coverage or type correctness.
It is not registered or auto-activated by this increment. Host registration must remain
explicit and require the capability-aware WorkerRuntime contract.

## Validation

Focused tests cover AST metrics, syntax errors, secret/dependency exclusion, no source
disclosure, no mutation, identity gates, strict request schema, allowlist containment and
resource limits. CI results and Windows acceptance must be recorded separately.

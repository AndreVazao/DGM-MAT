# Repository Cartographer Worker v1 — implementation checkpoint

Date: 2026-11-06
Issue: #245
Branch: feat/internal-repository-cartographer-worker-v1

## Scope

Adds the first bounded internal worker that performs a real local task without
Codex, Claude, a model, a browser provider, or a shell command.

The worker reuses core/repository_intelligence/snapshot.py and the existing
Message / WorkerRuntime contracts. It inventories only repository roots
explicitly allowlisted by the host.

## Request contract

The message body must be JSON with exactly:
- schema_version: 1
- operation: inventory_repository
- repository_id: stable host-configured identifier

The sender must be allowlisted (default: agent:hq-orchestrator), and mission
and correlation IDs are required. The message cannot supply a filesystem path,
command, output destination, or resource limit.

## Safety properties

- Read-only directory/file metadata inventory.
- No file contents are read.
- No symlink traversal by the underlying snapshot utility.
- Repository root is resolved and checked to remain inside the host allowlist
  at configuration time and revalidated on every dispatch. The snapshot
  utility also enforces containment after its own canonical path resolution.
- Recipient identity is checked by the worker in addition to WorkerRuntime inbox routing.
- Fixed operation only; no shell, subprocess, network, provider or AI call.
- Bounded depth, entries, request bytes and response sample.
- Sensitive filenames are counted but excluded from the returned sample.
- Structured blocked outcomes do not expose exception messages or filesystem paths.
- The handler is explicitly registered by the host through the existing
  MissionEngine/WorkerRuntime boundary; it is not auto-activated.

## Maturity boundary

This is a real deterministic internal worker for repository metadata, not an
AI coding agent. It proves the local handler path can do bounded useful work
without external coding agents. It does not edit source, generate patches,
run tests, or validate code correctness.

## Validation

Focused tests cover valid inventory, no content leakage, no file mutation,
invalid schemas/operations, sender/recipient allowlisting, missing correlation, request
size, initial, dispatch-time and scanner-boundary repository-root containment, and resource bounds. CI and Windows acceptance
must be reported separately. No local PC acceptance is claimed in this GitHub
increment.

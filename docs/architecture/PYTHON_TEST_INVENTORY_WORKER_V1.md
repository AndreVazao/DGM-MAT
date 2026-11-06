# Python Test Inventory Worker v1

The Python Test Inventory Worker is a deterministic, read-only specialist for
understanding the shape of Python test suites.

## Scope

- Scans only Python files inside directories named `tests`.
- Parses source with the standard-library AST parser; it never imports or executes tests.
- Counts test functions, async tests, test classes, fixture decorators and parametrize
  decorators; identifies pytest/unittest imports.
- Reports syntax diagnostics and a deterministic inventory digest.
- Returns metadata only, never source text.

## Safety and limits

- Host-owned repository ID allowlist; request bodies cannot supply filesystem paths.
- Sender, recipient, mission and correlation IDs are required.
- Skips symlinks, hidden directories and common dependency/build/cache directories.
- Enforces file count, per-file and aggregate byte budgets.
- Does not run pytest/unittest, invoke a shell, access the network or modify files.

## Maturity boundary

This is test-suite inventory, not test execution, coverage measurement, assertion
quality scoring or proof that a test validates production behavior. A high test count
does not imply quality. The worker is registered only through the same explicit
operator workspace allowlist as the Cartographer and Python Source Analyst.

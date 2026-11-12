# Cockpit mission capability feedback

## Problem

A mission can be correctly persisted as `WAITING_FOR_CAPABILITY` when the
intent router cannot find a registered executor. The chat console previously
reported only that the mission had been registered and then stopped polling,
leaving the operator with no explanation of why nothing happened.

## Change

The cockpit now renders a clear blocker message when it receives
`WAITING_FOR_CAPABILITY`. The message includes the mission ID and backend
reason, states explicitly that no action was executed, and explains that a
compatible executor must be registered before retrying.

The status is not converted to a terminal mission state. The mission checkpoint
remains recoverable and unchanged; the UI simply stops waiting and reports the
actual blocker.

## Provider launch distinction

The cockpit regression test also protects the distinction between:
- `abre o chatgpt`: submit a mission that opens the fixed provider home page
  after the mission's normal operator approval;
- `consulta o chatgpt: ...`: use the separate provider consultation workflow,
  which is transported by the paired browser extension.

Opening a provider page must never silently send a prompt.

## Validation

Focused tests cover the WAITING_FOR_CAPABILITY feedback and the command-console
routing boundary. Full focused CI and Windows build remain required before merge.

# Mission-linked browser consultations

## Problem

The cockpit consultation dialog could load a durable mission checkpoint and
show its redacted goal/context, but enqueue still used the active chat thread
as `task_ref`. The provider response was therefore persisted as a mobile
thread consultation rather than attached to the mission checkpoint.

## Change

After a successful `mission-context` response, the dialog remembers the
validated `mission_<8 hex>` ID. Enqueue then uses that mission ID as the
consultation `task_ref`. The existing result API stores the response hash and
provider/status receipt in that mission's durable metadata, explicitly marked
as an unverified external proposal.

If the operator edits the mission ID after loading, the binding is invalidated
and the operator must reload the checkpoint. Ordinary consultations that do
not load a mission continue to use `mobile-thread:<thread_id>`.

## Safety

- Loading context and generating a preview do not contact a provider.
- The exact redacted prompt digest must match at enqueue.
- Free-tier capacity attestation, allowlist, explicit approval and paired
  browser-extension transport remain required.
- Responses remain untrusted proposals; this change does not auto-apply them.
- A changed mission ID cannot silently reuse the previously loaded checkpoint.

## Validation

Focused cockpit tests verify both normal thread linkage and durable mission
linkage, including invalidation after changing the mission ID.

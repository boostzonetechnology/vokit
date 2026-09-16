# ADR-009 — Agency clone of an agent onto another owned customer

**Status:** Accepted  
**Date:** 2026-09-16  
**SRS refs:** AG3-005, TPL-002, Q-016, AGT-001  
**Jira:** VKT-063 (clone path), owner override of AG3-005  

---

## Context

AG3-005 (Should) says clone stays inside the same agency **and** the same customer.
Agencies need to copy a working agent onto another of their customers without
rebuilding persona, voice, tools, or call-handling from scratch.

Q-016 remains: Customer is a child scope inside the Agency tenant database. There
is no per-customer database and no cross-agency customer move in V1.

Super Admin clone already copies an agent onto any customer as an independent
Draft. Agency clone previously 404’d when `customer_id` differed from the source.

## Decision

Agency clone is the same `CloneAgent` use case as Super Admin, with a stricter
authorization path:

- Clone the **agent**, not the customer.
- Source agent must belong to the session tenant.
- Target `customer_id` is optional. Omit (or same id) copies onto the source
  customer (existing behavior).
- If provided, the target customer must belong to the **same agency tenant**.
  Missing or foreign customers resolve to non-disclosing **404**.
- Super Admin may still clone onto any customer (including another agency).
- The clone is a new `agent_id`, status `draft`, no published version, unlocked.
- Config is copied. Knowledge attachments and phone numbers are **not** copied
  (TPL-002 independence).
- `default_transfer_id` is cleared when the **customer** changes (destinations
  are customer-owned even inside the same tenant DB).
- After clone, the agency edits the draft with the existing configure PATCH.
  Agency clone does not accept greeting / `system_prompt` at clone time.

This does **not** change physical tenancy. The browser still cannot select a
database.

## Consequences

Positive:

- Same-agency reuse without a second clone engine.
- Fail-closed across agencies; Q-016 unchanged.

Trade-offs:

- AG3-005 “same customer” is owner-overridden for agency clone.
- A clone onto another customer will not keep the source transfer destination.

## Rollback

Revert the agency `CloneAgent` branch. Existing same-customer clone with an empty
body remains the compatible default.

## Change rule

Do not allow agency clone onto another tenant. Do not copy knowledge or numbers
on clone without a new ADR. Do not implement cross-agency customer reassignment
(Q-016).

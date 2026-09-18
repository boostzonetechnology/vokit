# ADR-011 — Plan entitlements and mid-cycle change

**Status:** Accepted  
**Date:** 2026-09-18  
**SRS refs:** PLAN-001, PLAN-005, PLAN-007, SA3-004, Q-004  
**Jira:** VKT-036 (backend entitlements), VKT-039 (plan change)

---

## Context

Plans attach only to customers (Q-004). Super Admin owns the catalog; agencies cannot create plans. `PlanVersion` already snapshots price/minutes and becomes immutable after `used_at` (PLAN-001). Subscriptions live on the tenant DB and point at a version id. Invoice lines already store `amount_minor` at purchase time.

PLAN-005 limits (agents, numbers, concurrency, recordings, integrations) were not on `PlanVersion`. First assign rejected a second subscription (`subscription_exists`). Mid-cycle upgrade/downgrade and PLAN-007 proration were undefined until the owner specified them.

## Decision

Entitlements live on **`PlanVersion`**, not `Plan`. A later version never rewrites invoices or commission snapshots for an earlier version.

`max_agents`, `max_phone_numbers`, `max_concurrency`: `0` means unlimited. `recording_allowed` defaults true. Empty `allowed_integrations` means every `ProviderKind`. Existing rows keep those defaults so current customers are not locked.

Enforcement is **per customer** from the active subscription’s version, on platform and agency APIs. Agent cap counts `AgentStatus.ACTIVE` only. Create/clone/template, publish, resume, and platform status→active fail at the cap. Pause/archive drop the count; activate again only under the cap.

**Upgrade** (higher `price_minor`): Super Admin or agency opens an upgrade invoice. Credit is unused time in the calendar month from `period_started_at`:

`credit = floor(current_price_minor * remaining_seconds / period_seconds)`  
`total = max(0, new_price_minor - credit)`

`due_at` is created_at + 1 day. Version switches only after payment (or in-process `$0` paid). Unpaid past due → VOID; stay on the old version; a new change creates a new invoice. Paid upgrade restarts `period_started_at`. Unused minutes are not clawed back.

**Downgrade** (lower `price_minor`, or same price with any tighter cap/recording/integrations): schedule at current period end. Block scheduling until ACTIVE agents and assigned numbers fit the target. No customer self-cancel. No auto-renew in this decision.

Same price with no tighter entitlements applies immediately without an invoice.

Flow (what runs today): [`docs/flows/plans/PLAN-CREATE-ASSIGN-CAPS.md`](../flows/plans/PLAN-CREATE-ASSIGN-CAPS.md)

## Consequences

Positive:

- Ledger history stays the price of the version that was purchased.
- Caps are one source of truth for both portals.
- Upgrade money is a new invoice, not a rewrite.

Trade-offs:

- Cycle remains monthly (already hardcoded).
- Feature flags are recording + integration allowlist, not a generic flag catalog.
- Frontend plan screens must be updated later to send the new fields.

## Rollback

Stop writing entitlement and pending-change fields. Defaults remain unlimited/allow-all. VOID upgrade invoices stay VOID. Do not rewrite historical invoice lines.

## Change rule

Do not let agencies create plans. Do not mutate a used `PlanVersion`. Do not apply an unpaid upgrade. Do not cancel a live subscription in this slice.

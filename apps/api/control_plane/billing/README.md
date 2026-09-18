# Billing

Plans attach only to customers (Q-004). Money is integer USD minor units. Plan versions become immutable after a subscription uses them (PLAN-001).

Entitlements live on `PlanVersion`: `max_agents`, `max_phone_numbers`, `max_concurrency` (`0` = unlimited), `recording_allowed` (default true), `allowed_integrations` (empty = all providers). Limits apply per customer from the active version. Agent cap counts `ACTIVE` only.

First assign remains `POST .../customers/{id}/subscription`. Mid-cycle change is `POST .../subscription/change`. Upgrade (higher price) opens an invoice with unused-time credit and applies after pay. Downgrade is scheduled at period end and is blocked while extras exceed the target caps. See `docs/flows/plans/PLAN-CREATE-ASSIGN-CAPS.md` and ADR-011.

Payment processors are a port. Stripe and Braintree adapters verify HMAC, then normalize to a Vokit event. Settlement is keyed by `(processor, event_id)` so a repeated sandbox webhook cannot pay an invoice twice.

Tenant DBs own subscriptions, invoices, lines, payments, and minute lots. Super Admin reads invoices from the control-plane index and privileged tenant traversal — never a cross-tenant JOIN.

Commission ledger writes start in Phase 7. Tax, promo, and pass-through lines default to not commissionable.

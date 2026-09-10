# Billing

Plans attach only to customers (Q-004). Money is integer USD minor units. Plan versions become immutable after a subscription uses them (PLAN-001).

Payment processors are a port. Stripe and Braintree adapters verify HMAC, then normalize to a Vokit event. Settlement is keyed by `(processor, event_id)` so a repeated sandbox webhook cannot pay an invoice twice.

Tenant DBs own subscriptions, invoices, lines, payments, and minute lots. Super Admin reads invoices from the control-plane index and privileged tenant traversal — never a cross-tenant JOIN.

Commission ledger writes start in Phase 7. Tax, promo, and pass-through lines default to not commissionable.

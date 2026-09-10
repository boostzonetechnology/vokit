# Vokit Financial Integrity Skill

## When to use
Use for invoices, payments, subscriptions, minutes, top-ups, commission, wallet, ledger, refunds, disputes, chargebacks and payouts.

## Procedure
1. Map the requirement to the financial source of truth.
2. Define immutable records and derived projections.
3. Define exact state transitions.
4. Define idempotency keys and unique constraints.
5. Define transaction boundaries and concurrency controls.
6. Define retry/reconciliation behavior for provider success/local failure and duplicate/out-of-order events.
7. Preserve commission rate/rule snapshots.
8. Verify hold and availability calculations use authoritative timestamps and explicit timezone semantics.
9. Verify payout reservation cannot exceed available funds under concurrent requests.
10. Test refund during hold, refund after availability, chargeback after payout, commission-rate changes, duplicate payment webhooks and accidental payout marking.
11. Reconcile payment -> invoice -> commission -> wallet -> payout references.

## Hard rule
Never fix a financial discrepancy by editing historical truth. Create an auditable corrective entry/workflow.

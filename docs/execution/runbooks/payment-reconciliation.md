# Payment reconciliation

1. Contain: do not replay unsigned webhooks; do not edit ledger rows.
2. Identify processor + `event_id` + invoice_id. Duplicate events must return `duplicate: true`.
3. Run `python manage.py reconcile_finance`.
4. Compare invoice paid total to commission earned for that payment. Snapshot rate must match the payment-time rate, not the current agency rate.
5. If the processor captured and Vokit has no payment row, replay **only** the signed original payload.
6. Verify dashboard `gross_revenue_minor` / agency `customer_mrr_minor` equals paid invoices (not UI math).

Evidence: `test_duplicate_stripe_webhook_settles_once`, Appendix C, staging sandbox E2E.

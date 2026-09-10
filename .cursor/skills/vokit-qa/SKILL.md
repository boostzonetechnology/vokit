# Vokit QA & Adversarial Testing Skill

## When to use
Use for feature completion, bug fixes, release candidates, security-sensitive changes and regression analysis.

## Procedure
1. Identify requirement IDs and acceptance criteria.
2. Build a state-transition test matrix.
3. Build a role/tenant authorization matrix.
4. Test happy path, invalid input, unauthorized access, duplicate requests, retries, concurrency, timeout, provider failure and recovery.
5. Test browser/API manipulation independently of UI restrictions.
6. Test observability assertions for critical failures.
7. Test migration compatibility and rollback assumptions for schema changes.
8. For realtime features, test routing and terminal call states.
9. Record reproducible defects with impact, evidence, root cause and regression test.

## Mandatory adversarial cases
- Agency A attempts Customer/Agent/Call/Wallet access from Agency B.
- Customer attempts another customer's resource IDs.
- Client removes/changes permission flags and submits directly.
- Duplicate payment/provider webhook.
- Concurrent payout requests exceeding available funds.
- Refund/chargeback at every commission state.
- Expired KYC with available wallet.
- Suspended agency attempts API creation.
- Webhook signature missing/invalid/replayed.
- Malicious URL/file upload.
- Tool invocation not on agent allowlist.
- Knowledge retrieval with unauthorized tenant scope.

## Exit criterion
All critical acceptance criteria pass and no open critical/high security or financial defects remain without explicit risk acceptance.

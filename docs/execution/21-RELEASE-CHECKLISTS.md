# Vokit Release Checklists

Use on every merge to the release branch and every production deploy. HIGH changes use the full list.

## A. Before merge

- [ ] SRS requirement IDs in PR
- [ ] No conflict with Decided questions or accepted ADRs
- [ ] Tests added (domain/app/API as applicable)
- [ ] Security review if HIGH
- [ ] Tenant isolation tests if tenant-owned
- [ ] Migration safety (expand-only)
- [ ] Observability added
- [ ] Rollback plan written
- [ ] Runbook/ADR updated if HIGH
- [ ] Frozen telephony paths unchanged or dual-compatible
- [ ] No secrets in repo

## B. Engineering / QA (SRS §31.2)

- [ ] Commission/wallet state-machine tests
- [ ] Tenant isolation authorization tests
- [ ] Payment webhook + payout reservation idempotency tests
- [ ] Security review: auth, RBAC, secrets, webhooks, uploads, payments
- [ ] Provider sandbox E2E for numbers and calls (when those modules ship)
- [ ] Backup/restore test evidence for primary stores
- [ ] Dashboards/alerts for payment, payout, calling, integrations
- [ ] Runbooks listed in deployment ops

## C. Functional (SRS §31.1) — required for V1 GA, incremental earlier

- [ ] Super Admin creates agency + commission + invite
- [ ] External KYC status blocks payout until Verified; agency cannot self-verify
- [ ] Agency creates customer only when allowed
- [ ] Customer assigned plan and pays Vokit
- [ ] Eligible payment → exactly one commission + 15-day availability
- [ ] Held funds not withdrawable
- [ ] Available funds reserved once, atomically
- [ ] Proof private; receipt on Paid
- [ ] Suspended agency cannot create customers via API
- [ ] Overrides audited
- [ ] Number + published agent + inbound call + call record
- [ ] Customer portal scoped
- [ ] Webhooks tenant-scoped and signed
- [ ] Refund/chargeback does not rewrite history
- [ ] Roles block KYC/payout/commission/cross-tenant/customer-agent abuse

## D. After deploy

- [ ] Auth works on all three portals
- [ ] Tenant DB routing works
- [ ] One agency/customer workflow
- [ ] One production-like call
- [ ] Recording artifact authorization
- [ ] Payment/webhook processing
- [ ] Queues draining
- [ ] No cross-tenant access in canary probes
- [ ] Error/latency/saturation normal

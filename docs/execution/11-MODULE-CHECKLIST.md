# Vokit Module Checklist

Use this as the definition of done for each bounded context. A module is not complete when CRUD exists.

## Global checks (every module)

- [ ] SRS IDs listed
- [ ] Bounded context and data ownership explicit
- [ ] Decided questions / ADRs respected
- [ ] Domain state machine centralized
- [ ] Application service is the transaction boundary
- [ ] Repository does not leak other tenants
- [ ] API does not expose ORM entities
- [ ] Idempotency/reconciliation where retryable
- [ ] Correlation ID on requests/jobs
- [ ] Structured logs without secrets
- [ ] Metrics for success/failure/latency
- [ ] Tenant isolation tests (if tenant-owned)
- [ ] Authorization tests
- [ ] Migration + rollback notes
- [ ] Runbook touch if HIGH
- [ ] Task report filled

## Identity & Access

- [ ] Email unique globally
- [ ] Platform users cannot be tenant members
- [ ] One tenant membership only
- [ ] Distinct platform/agency/customer permission namespaces
- [ ] Invite lifecycle Invited/Active/Disabled
- [ ] Disable revokes sessions
- [x] Sensitive permissions explicit (KYC, payout, wallet adjust, commission, impersonation)
- [ ] CSRF + secure cookies

## Tenancy & Provisioning

- [ ] Immutable tenant_id + database_id
- [ ] Registry has host/port/TLS/secret-ref/status/schema/health
- [ ] Provisioning saga resumable
- [ ] Tenant not Active until DB verified
- [ ] Router fail closed
- [ ] No client-selected DB
- [ ] Tenant-safe pools
- [ ] Workers reconstruct routing
- [x] Canary tenant migrations
- [x] Backup/restore one tenant without touching another
- [ ] Customer remains under Agency; no per-customer DB (Q-016)
- [ ] Do **not** ship cross-agency customer reassignment in initial V1

## Customers

- [ ] customer_id global index
- [ ] Exactly one current agency
- [ ] Ban-index check on create
- [ ] Customer status machine
- [ ] Portal permissions default deny agent edit
- [ ] Customer rows live only in the owning Agency DB (Q-016)

## Billing

- [ ] Plan versions immutable once used
- [ ] USD minor units
- [ ] Processor port + Stripe and Braintree adapters
- [ ] Webhook signature + event-id dedup
- [ ] Minutes lots + drain order
- [ ] Grace on hard-stop
- [ ] Tax/promo/pass-through not commissionable by default

## Commission / Wallet / Payout

- [ ] Ledger insert-only
- [ ] Per-entry 15-day hold
- [ ] Rate and eligible_base snapshot
- [ ] Atomic payout reservation
- [ ] Proof private; receipt generated on Paid
- [ ] Negative balance path
- [ ] Reconciliation job payment→invoice→commission→payout

## KYC

- [ ] KycProvider port + adapter; API keys as secret refs only
- [ ] Provider-hosted start/resume session
- [ ] Signed webhook + event-id dedup
- [ ] Status mapped to SRS §6.3
- [ ] Payout gated on Verified; unknown status fail closed
- [ ] No KYC document bytes stored as SoT
- [ ] Super Admin status + override (KYC-007), no file inbox
- [x] Status changes audited; payloads redacted

## Risk

- [x] Risk status independent of account status
- [x] Verification docs + masked card last-four
- [x] Reject over-exposed card images
- [x] Chargeback auto-freeze + agent shutdown
- [x] Permanent ban across agencies
- [x] Commission reversal order
- [x] Agency cannot override

## Agents / Templates / Knowledge

- [x] Draft cannot take production traffic
- [x] Publish preflight
- [x] Template clone is independent
- [x] Instruction precedence
- [x] Knowledge isolation including Qdrant payload
- [x] Tool allowlist
- [x] No secrets in prompts/transcripts

## Telephony

- [x] Platform inventory
- [x] 10-minute reservation
- [x] Customer billed on assign
- [x] One active routing target
- [x] Provider adapter + reconcile orphans
- [x] E.164 storage

## Calls / Voice

- [x] Existing internal telephony paths implemented
- [x] Admission deterministic and observed
- [x] continue_call minutes/grace
- [x] Transfer via Django
- [x] Voicemail both directions
- [x] Usage attributed to one customer
- [x] No slow DB in audio loop

## Recordings

- [x] Metadata only in app DB
- [x] Object namespace tenant/call/artifact
- [x] Checksum + async verify
- [x] Signed short-lived access
- [x] Retention + legal hold
- [x] Orphan detection
- [x] Recording negative matrix green

## Integrations / Webhooks

- [x] Per-customer connections
- [x] Encrypted secret refs
- [x] Django tool gateway
- [x] Signed outbound webhooks
- [x] Delivery log without secrets
- [x] Bounded retry + DLQ

## Notifications / Audit / Settings

- [x] In-app + email
- [x] Mandatory notices not user-disableable
- [x] Audit immutable
- [x] Settings centralized (hold days, limits, flags)

## Portals / reporting

- [x] Dashboards from ledger/projections (not UI math)
- [x] Period + timezone filters
- [x] Platform/agency/customer Must screens
- [x] Responsive agency/customer nav

## Hardening (Phase 17)

- [x] Isolation / finance / voice / recording matrices catalogued and executable
- [x] Security review recorded
- [x] Capacity worksheet filed (no speculative scale-out)
- [x] Core portal accessibility pass (landmarks, labels, focus, skip link)

## Production gate (Phase 19)

- [x] Independent live flags fail closed (`calling_live`, `billing_live`, `recordings_live`)
- [x] Production boot requires distinct telephony/recording tokens, CORS/CSRF, MySQL+TLS
- [x] Go/no-go evaluator cannot be greened by `VOKIT_LAUNCH_GO` alone
- [x] Lab readiness + post-deploy smoke commands
- [ ] Live inbound/outbound/payment/restore/legal attestations (No-Go)

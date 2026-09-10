# Vokit Development Roadmap

Implementation sequence. Do not start Phase 1 until the owner says **proceed** and Gate 0 ADRs are accepted.

## Phase 0 — Decision lock

- Accept/amend ADR-001, 002, 003, 004, 005 — **Accepted 2026-09-10**
- Confirm Agency physical tenancy and customer-under-agency (Q-016)
- Confirm external KYC (Q-015)
- Owner said proceed; Phase 1 started. **Complete 2026-09-10**

## Phase 1 — Foundation

- Create `apps/api` skeleton, settings split, CI lint/test
- Shared kernel: correlation ID middleware, structured logging, money/phone/time types
- Secret-ref pattern (no plaintext in models)
- Health/ready endpoints
- Compose: MySQL + Redis local

**Exit:** empty API boots, CI green, no tenant routing yet. **Complete 2026-09-10**

## Phase 2 — Identity

- Users, credentials, sessions, CSRF
- Platform vs tenant membership (Q-001)
- Roles/permissions namespaces
- Invitations
- Three React app shells that can log in and render 401/403

**Exit:** platform user and a tenant user can authenticate; disable revokes session. **Complete 2026-09-10**

## Phase 3 — Tenant data plane

- `tenants` + `tenant_databases` registry
- Provisioning saga (create DB, schema, verify, mark ready)
- Fail-closed router + tenant-safe pools
- Tenant migration runner (canary, lock, bounded concurrency)
- Isolation test harness (two local tenant DBs)

**Exit:** forged tenant_id cannot switch DB; missing mapping denies. **Complete 2026-09-10**

## Phase 4 — Agency & customer lifecycle

- Agency state machine + capabilities
- Customer index + tenant customer rows
- Super Admin create agency / create customer **under that agency**
- Agency create customer when allowed
- No cross-agency customer move
- Ban-index hook (empty keys OK, API in place)

**Exit:** two agencies cannot see each other’s customers via API. **Complete 2026-09-10**

## Phase 5 — KYC (external)

- KycProvider port + adapter
- Platform API-key secret refs
- Agency start/resume provider session
- Signed webhook → mapped status
- Super Admin status + override
- Payout eligibility from Verified only

**Exit:** payout API rejects Unverified; no KYC files in Vokit object storage. **Complete 2026-09-10**

## Phase 6 — Billing

- Plans/versions
- Subscriptions, invoices, lines
- PaymentProcessor port + Stripe + Braintree webhooks
- Minute lots + top-ups
- Customer billing portal
- Super Admin invoice/payment views

**Exit:** sandbox payment settles once under duplicate webhook. **Complete 2026-09-10**

## Phase 7 — Commission, wallet, payout

- Commission from captured eligible cash
- Hold job
- Ledger + projected buckets
- Payout request/approve/proof/paid/receipt
- Reconciliation job

**Exit:** Appendix C examples 1–5 pass as automated tests. **Complete 2026-09-10**

## Phase 8 — Risk

- Risk statuses
- Verification + card-image mask check
- Chargeback consumer → freeze, agent disable, commission reverse
- Permanent ban + re-onboard block

**Exit:** chargeback fixture disables agents and writes compensating ledger. **Complete 2026-09-10**

## Phase 9 — Agents, templates, knowledge

- Agent builder domain + versions
- Templates clone
- Instruction merge
- Knowledge ingest + Qdrant write path
- Publish preflight
- Test/training session APIs

**Exit:** unpublished agent is not routable. **Complete 2026-09-10**

## Phase 10 — Numbers

- Inventory in control plane
- Search/purchase adapter
- 10-minute reservation
- Assign + customer charge
- Release + reconcile

**Exit:** second agency cannot take a reserved number. **Complete 2026-09-10**

## Phase 11 — Voice control APIs

- Implement frozen Pipecat paths
- DID resolve / admission
- continue_call minutes/grace
- Tool invoke stub
- Call metadata + usage ledger

**Exit:** Pipecat bootstrap against Django succeeds in lab. **Complete 2026-09-10**

## Phase 12 — Media completion

- Inbound + outbound E2E with existing Edge/Asterisk
- Transfer destinations including queue/SIP client (ADR if Edge must change)
- Inbound/outbound voicemail

**Exit:** one inbound and one outbound production-like call recorded in metadata. **Complete 2026-09-10**

## Phase 13 — Recording plane

- Ingest workflow
- Signed access
- Retention/legal hold
- Orphan reconcilers

**Exit:** recording negative matrix green. **Complete 2026-09-10**

## Phase 14 — Integrations & webhooks

- Per-customer OAuth/webhook connections
- Native CRM/accounting adapters
- Outbound signed webhooks + replay
- Django tool gateway wired to Pipecat

**Exit:** customer A cannot use customer B connection. **Complete 2026-09-10**

## Phase 15 — Notifications, audit, settings

- In-app + email templates
- Mandatory notices
- Immutable audit search
- Platform settings (hold days, flags, providers)

**Exit:** mandatory notices cannot be disabled; audit append-only. **Complete 2026-09-10**

## Phase 16 — Portal completion

- All Must screens in feature matrix
- Dashboards from ledger/projections
- Responsive agency/customer monitoring

**Exit:** all Must screens in the feature matrix. **Complete 2026-09-10**

## Phase 17 — Hardening

- Full isolation + finance + voice + recording matrices
- Security review
- Load/capacity worksheet
- Accessibility pass on core flows

**Exit:** matrices executable; security review recorded; capacity worksheet filed; core portal a11y pass. **Complete 2026-09-10**

## Phase 18 — Staging / canary

- Provider sandbox E2E
- Backup/restore of control + one tenant
- Canary tenant migration
- Runbooks

**Exit:** sandbox journey + restore drill automated; canary-only migrate; runbooks filed. **Complete 2026-09-10**

## Phase 19 — Production

- Follow [`20-PRODUCTION-DEPLOYMENT.md`](20-PRODUCTION-DEPLOYMENT.md)
- Post-deploy go/no-go: [`23-FINAL-PRODUCTION-CHECKLIST.md`](23-FINAL-PRODUCTION-CHECKLIST.md)
- Executable gate: `check_production_readiness` / `post_deploy_smoke`
- Independent live flags; production boot fail-closed
- Evidence pack: [`26-PHASE-19-EVIDENCE.md`](26-PHASE-19-EVIDENCE.md)

**Exit:** production gate is executable and cannot be greened by a config flag.
Live launch remains **No-Go** until dated attestations exist. **Gate complete 2026-09-10**

## Phase 20 — Scale

- Measure: routing, pools, call concurrency, ingest, queues, hotspot tenants
- Add capacity only with ADR
- Do not extract services speculatively

## Parallelism rules

Safe after Phase 3: frontend shells track each backend slice.  
Unsafe in parallel with Phase 3: any feature that opens a tenant DB.  
Voice UI may proceed in mock form, but media integration waits for Phase 11.

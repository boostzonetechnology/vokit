# Vokit Complete Execution Plan

From empty application code to production, post-deploy operations, and scale.

**Do not implement until the product owner says proceed.**

## 0. Current architecture map

```text
TODAY (Phases 0–19 gate 2026-09-10; live launch No-Go)
─────
docs/          SRS + OPEN-QUESTIONS + Accepted ADRs 001–006
.cursor/       rules + skills
apps/api       Django modular monolith through production go/no-go gate
apps/web-*     Must screens + WCAG landmarks/labels/focus
packages/pipecat-voice     realtime media peer (WS /sip/media)
packages/vokit-sip-edge    Rust SIP B2BUA + HTTP control (unchanged {to})
deploy/asterisk            inbound/outbound + SIP-client lab extensions

NEXT
────
Attach dated live attestations for a production GO
Phase 20 scale only after a live GO
```

### Domain map

| Bounded context | Plane | Owns |
|---|---|---|
| Identity & Access | Control | Platform users, tenant users identity index, sessions, RBAC namespaces |
| Tenancy & Provisioning | Control | Agency tenant registry, DB endpoints, schema version, lifecycle |
| Customers | Tenant + Control index | Customer profile/ops in Agency DB; global customer index + ban list in control |
| Billing & Payments | Tenant + Control projections | Customer invoices/payments/minutes in Agency DB; processor events/idempotency in control |
| Commission / Wallet / Payout | Tenant + Control projections | Agency ledger in Agency DB; payout ops queue visible to Super Admin |
| KYC / Risk | Control + KYC provider | Agency KYC status/refs via external provider; customer payment-risk + fraud index stay in Vokit |
| Agents / Templates / Knowledge | Mixed | Global templates/knowledge in control; tenant agents/knowledge in Agency DB |
| Telephony inventory | Control | Platform-owned numbers; assignment pointers copied to tenant |
| Calls / Usage / Artifacts | Tenant + Recording plane | Call metadata/usage in Agency DB; raw audio on recording server |
| Integrations / Webhooks | Tenant | Per-customer connections; secrets as references |
| Notifications | Mixed | Templates in control; deliveries per recipient |
| Audit / Compliance | Control | Immutable events that survive tenant DB loss |
| Voice runtime | Media plane | Asterisk, SIP Edge, Pipecat — no business SoT |

### Data-ownership map

| Data | Physical home |
|---|---|
| Users, membership, roles | Control plane (identity). Membership binds one user to one Agency **or** one Customer (Q-001) |
| Tenant DB registry + secret refs | Control plane |
| Plans / plan versions | Control plane |
| Phone-number inventory | Control plane |
| Audit, fraud/ban index, KYC status + provider refs | Control plane (no KYC document vault) |
| KYC API keys | Secret manager / encrypted secret refs only |
| Agency profile, capabilities, wallet, payouts | Agency tenant DB |
| Customers, agents, calls, usage, invoices, integrations | Agency tenant DB of the owning Agency (Q-016: customer stays under that agency) |
| Raw recordings / voicemail audio | Recording data plane |
| Knowledge vectors | Qdrant with tenant/customer/agent payload isolation |

### Runtime / deployment map

```text
Browser (React portals)
    │ HTTPS /api/v1
    ▼
Django API  ── control-plane MySQL
    │         ── tenant registry ── TLS ── Agency MySQL (remote OK)
    │         ── Redis/queue
    │         ── payment processors (Stripe, Braintree)
    │         ── KYC provider (API keys + webhooks)
    │         ── email
    │
    ├── internal telephony APIs ── Pipecat
    │                                ▲ WS μ-law /sip/media
    │                                │
    │                         vokit-sip-edge ◄── Asterisk ◄── PSTN
    │
    └── signed short-lived access ── Recording server ── object storage
```

## 1. Method (mandatory order)

For every non-trivial feature:

1. Requirements and invariant analysis (SRS IDs)
2. Architecture / bounded context
3. ADR if HIGH impact
4. Data model / ERD
5. Domain policies / state machines
6. Application / use-case services
7. Repository and provider adapter interfaces
8. Infrastructure implementation
9. Migrations (control-plane and/or tenant)
10. API contracts
11. React implementation
12. Realtime integration if needed
13. Tests including tenant-negative matrix
14. Observability
15. Deployment / runbook
16. Post-deploy verification definition

Do not jump to CRUD.

## 2. Phase plan

| Phase | Name | Outcome | Depends on | Status |
|---|---|---|---|---|
| 0 | Decision lock | ADRs accepted; proceed given | Owner | Complete 2026-09-10 |
| 1 | Foundation | Repo skeleton, CI, observability, secrets pattern | 0 | Complete 2026-09-10 |
| 2 | Control plane + identity | Users, sessions, RBAC namespaces, invitations | 1 | Complete 2026-09-10 |
| 3 | Tenant data plane | Registry, provisioning saga, router, tenant migrations | 2 | Complete 2026-09-10 |
| 4 | Agency + customer lifecycle | Agency/customer state machines, Super Admin + portal shells | 3 | Complete 2026-09-10 |
| 5 | KYC | External KYC provider adapter, webhooks, status gate | 4 | Complete 2026-09-10 |
| 6 | Billing | Plans, subscriptions, invoices, Stripe+Braintree, minutes | 4 | Complete 2026-09-10 |
| 7 | Commission / wallet / payout | Ledger, holds, reservation, proof/receipt | 6 | Complete 2026-09-10 |
| 8 | Payment risk | Verification, chargeback freeze, ban index | 6–7 | Complete 2026-09-10 |
| 9 | Agents / templates / knowledge | Builder, clone semantics, scoped retrieval | 4 | Complete 2026-09-10 |
| 10 | Numbers | Platform inventory, 10-min reserve, customer billing | 6, 9 | Complete 2026-09-10 |
| 11 | Voice control APIs | DID resolve, bootstrap/events/end/transfer, admission | 9–10 | Complete 2026-09-10 |
| 12 | Media contract completion | Inbound/outbound, voicemail, queues/SIP transfer | 11 | Complete 2026-09-10 |
| 13 | Recording plane | Ingest, signed access, retention, orphans | 11 | Complete 2026-09-10 |
| 14 | Integrations / webhooks | Per-customer connections, Django tool gateway | 9, 11 | Complete 2026-09-10 |
| 15 | Notifications / audit / settings | In-app + email, immutable audit, platform settings | 4+ | Complete 2026-09-10 |
| 16 | Portal completion | All Must UI flows for three portals | 5–15 | Complete 2026-09-10 |
| 17 | Hardening | Isolation, finance, voice, recording matrices; security review | 16 | Complete 2026-09-10 |
| 18 | Staging / canary | Provider sandbox E2E, backup restore, runbooks | 17 | Complete 2026-09-10 |
| 19 | Production launch | Gated rollout + post-deploy verification | 18 | Gate complete 2026-09-10; live No-Go |
| 20 | Post-deploy + scale | Operations, capacity, measured extraction only | 19 | Not started |

Detailed stories live in [`13-DEVELOPMENT-ROADMAP.md`](13-DEVELOPMENT-ROADMAP.md).

## 3. Recommended engineering stack (ADR-004 Accepted 2026-09-10)

These are **engineering defaults**, not product-rule changes. Confirm in Gate 0.

| Concern | Recommended default | Why |
|---|---|---|
| API | Django 5 + Django REST Framework | Matches product direction; mature RBAC/admin/ORM |
| Workers | Celery + Redis | Resumable tenant jobs, webhooks, ingest, holds |
| Control DB | MySQL 8 | Product direction |
| Tenant DB | MySQL 8, one DB per Agency | ADR-001 |
| Cache / broker | Redis | Sessions optional, queues, short-lived locks |
| Frontend | React + TypeScript + Vite, three apps | Q-007; portal isolation |
| Auth | Server-issued HttpOnly session cookies + CSRF | SRS SEC-006/007; SPA-friendly same-site |
| IDs | UUID v7 (time-sortable) | Cross-DB identity, no enumerable IDs |
| Money | Integer minor units, USD | NFR-011, Q-005 |
| Phone | E.164 + display | NFR-012 |
| Time | UTC storage | NFR-010 |
| API version | `/api/v1/` public; `/internal/telephony/v1/` private | Existing Pipecat paths |
| Knowledge vectors | Qdrant | Existing Pipecat path |
| Hosting | Linux services bound to `0.0.0.0:$PORT` | Render-compatible; ephemeral disk |

If the owner rejects a default, record the alternative in ADR-004 **before** coding.

## 4. Critical design that must not be buried in code

### 4.1 Membership vs physical tenant

Q-001: a person belongs to one logical tenant (Agency **or** Customer).  
ADR-001: the physical database tenant is the Agency.

Therefore:

- Agency users route to that Agency DB.
- Customer users resolve `customer_id → current_agency_id` from the **control-plane customer index**, then route to that Agency DB.
- Platform users have no tenant membership and use only control-plane data plus explicit privileged traversal.

### 4.2 Customer stays under Agency (Q-016)

Customer is a child scope inside the Agency tenant DB. Do not create a customer database. Do not implement cross-agency customer reassignment in the initial V1 build.

If Q-006 is later scheduled, it is a HIGH saga (not `UPDATE agency_id`) and needs its own implementation ADR at that time.

### 4.3 Agency KYC is external (Q-015)

Vokit does not store KYC document bytes or run a Super Admin file-review inbox. A KYC provider supplies API keys (secret refs). Vokit starts/resumes the provider flow, consumes signed webhooks, maps status to SRS §6.3, and gates payouts on Verified.

Customer payment-risk verification remains a separate Vokit module.

### 4.4 Minutes, not a prepaid money wallet (Q-003)

Store and drain **minute entitlements**: included → top-up → overage if the plan allows.  
Money lives on invoices/payments.  
Hard-stop plans get a configured grace period, then the call ends.

### 4.5 Voice path

Django remains SoT for agents, admission, billing, tools, and call records.  
Pipecat calls Django for tools (Q-009).  
Existing internal paths must be implemented, not renamed:

- `POST /internal/telephony/v1/voice-session/bootstrap/`
- `POST /internal/telephony/v1/voice-session/events/`
- `POST /internal/telephony/v1/voice-session/end/`
- `POST /internal/telephony/v1/voice-session/transfer/`
- `GET  /internal/telephony/v1/voice-session/transfer/status/`
- training-session bootstrap/propose/confirm/end

Asterisk/SIP Edge HTTP `{to}` stays unchanged (ADR-006). Django hunts queues and maps SIP clients to numeric extensions.

## 5. Quality bar (every phase)

Critical work requires:

- SRS requirement IDs
- Domain + application tests
- Authorization tests
- Tenant isolation negative tests
- Idempotency/retry tests
- Observability (correlation ID, structured logs, metrics)
- Migration and rollback notes
- Runbook updates for HIGH changes

Minimum tenant and recording negative matrices are in [`17-QA-TESTING-PLAN.md`](17-QA-TESTING-PLAN.md), `MASTER-CURSOR-BOOTSTRAP.md`, and SRS §31.

## 6. Production and scale rule

The V1 system is a **modular monolith** plus existing voice packages plus a recording service.

Do not extract new services, add replicas/shards, or multiply tenant DB hosts until you can name:

- measured bottleneck
- capacity impact
- failure mode
- rollout
- ADR

Tenant scale analysis must include active tenants, connections, pool size, concurrent calls, recording ingest, storage growth, queues, webhooks, provider quotas, and hotspot tenants.

## 7. Required task report

Every non-trivial Cursor task ends with:

- Requirement IDs
- Files inspected
- Current vs proposed architecture
- Affected bounded contexts
- Data ownership
- Tenant-routing implications
- API/event contract
- Failure modes
- Retry/idempotency
- Security/privacy impact
- Tests added/run
- Migration impact
- Observability
- Deployment order
- Rollback
- Residual risks

## 8. Current execution position

Phases 0–19 (gate) are complete. Live production is **No-Go** until dated
attestations exist (`26-PHASE-19-EVIDENCE.md`). Phase 20 (scale) waits for a live GO.
Do not skip to service extraction.

# Vokit System Architecture

**Status:** Working architecture for V1. ADRs 001–004 remain Proposed until Gate 0.  
**Product SoT:** SRS v1.0  
**Related:** ADR-001–005, OPEN-QUESTIONS Q-001–Q-016

## 1. Architectural style

Vokit V1 is a **domain-driven modular monolith** (Django) plus three existing/adjacent runtime planes:

| Plane | Components | Responsibility |
|---|---|---|
| Control plane | Django + control-plane MySQL | Identity, tenant registry, plans, number inventory, audit, fraud index, privileged indexes |
| Tenant data plane | One MySQL per Agency | Agency business data and child customer scope (Q-016: customer stays here) |
| Recording data plane | Recording service + object storage | Raw audio / voicemail bytes |
| Media plane | Asterisk, vokit-sip-edge, Pipecat | Realtime signaling and audio |
| Presentation | Three React apps | Presentation and client state only |

Extract additional services only after a measured bottleneck and an ADR.

## 2. Logical vs physical tenancy

```text
LOGICAL (SRS §3)
Platform → Agency → Customer → Agent

PHYSICAL (ADR-001)
Control-plane DB
   └── Tenant registry
         └── Agency A MySQL  (customers, agents, calls, invoices, wallet)
         └── Agency B MySQL
Recording objects: tenant/{tenant_id}/calls/{call_id}/artifacts/{artifact_id}
```

Customer is **never** the default physical database tenant. If that changes, redesign the registry, routing, migrations, backups, authorization, and ops model in a new ADR. Do not patch it.

## 3. Request authorization stack

Every protected command/query evaluates, in order:

1. Authenticated identity
2. Platform role **or** tenant membership (never both for the same user — Q-001)
3. Tenant scope (`tenant_id` / Agency)
4. Customer scope when the resource is customer-owned
5. Resource ownership
6. Capability / entitlement / KYC / risk gates

Never trust `tenant_id`, `agency_id`, `customer_id`, role, or permission from the client.

Foreign resources return non-disclosing not-found.

## 4. Tenant routing

```text
Authenticate
  → resolve membership from control plane
  → if platform user: control plane only, unless explicit privileged traversal
  → if agency member: tenant_id = that agency
  → if customer member: tenant_id = customer.current_agency_id from control-plane index
  → load TenantDatabaseRegistry row
  → reject if missing / suspended / unhealthy / credentials missing
  → open TLS connection from tenant-safe pool
  → bind repository to that connection
  → never reuse the connection for another tenant_id
```

Workers carry `tenant_id`, `customer_id` when applicable, actor, `correlation_id`, and job/event ID. They reconstruct routing from the registry. They never serialize raw DB credentials into jobs.

## 5. Bounded contexts

| Context | Module (target) | Key invariants |
|---|---|---|
| Identity & Access | `identity` | One membership; distinct RBAC namespaces; session revoke on disable |
| Tenancy | `tenancy` | Immutable `tenant_id` + `database_id`; fail closed |
| Customers | `customers` | Exactly one current agency; historical finance frozen to original agency |
| Billing | `billing` | Minutes entitlements; invoices/payments immutable after settlement |
| Commission | `commission` | Per-entry hold; snapshots; compensating entries only |
| KYC | `kyc` | External provider adapter; status + secret refs; payout gated on Verified |
| Risk | `risk` | Chargeback freeze; cross-agency ban index |
| Agents | `agents` | Draft→publish validation; customer-owned |
| Knowledge | `knowledge` | Scope isolation; Django write / Pipecat retrieve |
| Telephony | `telephony` | Platform inventory; 10-minute reservation |
| Calls | `calls` | Usage attribution; artifact metadata only |
| Integrations | `integrations` | Per-customer connections; Django tool gateway |
| Webhooks | `webhooks` | Signed, idempotent, tenant-scoped |
| Notifications | `notifications` | In-app + email; mandatory notices |
| Audit | `audit` | Immutable; no secrets |
| Voice adapter | `voice_runtime` | Internal telephony contract only |
| Recording adapter | `recordings` | Signed access after authorization |

## 6. Layering

```text
React portals
    ↓ HTTP
API (views, serializers, error mapping, pagination)
    ↓
Application (use cases, transactions, auth context)
    ↓
Domain (invariants, state machines, value objects)
    ↓
Infrastructure (ORM repos, Stripe/Braintree adapters, telephony adapters, queue, storage)
```

Forbidden:

- Business workflows living only on ORM models
- Domain importing Stripe/Braintree/HubSpot SDKs
- Controllers calculating commission or choosing a tenant DB
- React deciding authorization, price, or entitlements

## 7. Voice architecture

```text
PSTN
  → Asterisk
  → vokit-sip-edge (SIP + RTP μ-law + HTTP control)
  → Pipecat WS /sip/media
       → STT / LLM / TTS
       → Django bootstrap / heartbeat events / end
       → Django tool gateway (CRM, webhook, transfer)
Django hangup/transfer commands go to SIP Edge, not into the audio loop.
```

Call identity on every hop after admission:

- `vokit_call_id`
- `provider_call_id` / `edge_call_id`
- `tenant_id`
- `customer_id`
- `agent_id`
- `correlation_id`

No runtime component infers tenancy from a caller-controlled header.

Admission (before production media) must resolve tenant/customer/agent, publish state, DID routing, minute/overage/grace eligibility, recording/disclosure policy, and runtime providers.

## 8. Recording architecture

```text
Call completes
  → recording available (provider or media plane)
  → async fetch/receive
  → checksum verify
  → store object on recording plane
  → persist metadata on tenant call record
  → ready + event

Playback:
  authenticate → authorize tenant+customer+call+artifact
  → mint short-lived single-purpose token
  → recording server validates
  → stream
  → audit
```

Never authorize by `artifact_id` alone. Never return a permanent URL.

## 9. KYC and payment architecture

Agency KYC talks to a **KycProvider** port (Q-015 / ADR-005). Platform stores API-key secret refs. Status is mapped from signed provider webhooks. Payouts fail closed unless status is Verified.

Payments talk to a **PaymentProcessor** port.

Adapters: Stripe, Braintree.

Inbound webhooks:

1. Verify signature
2. Validate event ID
3. Deduplicate
4. Persist receipt
5. Apply side effects idempotently
6. Dead-letter poison messages

Vokit does not store raw PAN/CVV. Card-image verification allows last-four only and rejects over-exposed images.

## 10. Integration architecture

```text
Pipecat tool call
  → Django tool gateway
  → customer-owned IntegrationConnection
  → CRM / signed webhook / automation
  → sanitized result back to Pipecat
```

Agency connections are not shared across customers (Q-010).

## 11. Observability

Every HTTP request and job has a correlation/trace ID.

Structured logs include timestamp, severity, service/module, event name, correlation ID, tenant_id only when safe, resource IDs, outcome/latency.

Never log secrets, raw audio, transcripts, full payment credentials, or KYC document contents.

P0/P1 alerts: tenant isolation breach, wrong-tenant routing, financial inconsistency, call routing outage, recording exposure, widespread payment/webhook failure.

## 12. Scale envelope

Horizontal scale of API/workers first. Bounded connection pools per **active** tenant, not one permanent pool multiplied by all tenants.

Before adding hosts, replicas, or services, complete the capacity worksheet in the production-readiness skill and write an ADR.

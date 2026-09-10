# Vokit API Contracts

**SoT:** SRS §30, SEC-*, WH-*, existing Pipecat client  
**Auth:** server-side only; never trust client tenant identifiers

## 1. Surfaces

| Surface | Base path | Audience | Auth |
|---|---|---|---|
| Portal / public API | `/api/v1/` | React portals + future partners | Session cookie + CSRF |
| Internal telephony | `/internal/telephony/v1/` | Pipecat, SIP Edge helpers | Shared service token |
| Internal recording | `/internal/recordings/v1/` | Recording plane | Service mTLS/token |
| Provider webhooks | `/webhooks/{processor}/v1/` | Stripe, Braintree, telephony | Signature verify first |
| Recording access | Recording server, not Django static | Browsers after authorize | Short-lived signed token |

Version externally consumed contracts. Additive changes preferred.

## 2. Envelope

Success:

```json
{
  "data": {},
  "meta": {
    "request_id": "01J…",
    "page": { "next": null, "limit": 50 }
  }
}
```

Error:

```json
{
  "error": {
    "code": "tenant_not_found",
    "message": "Resource not found.",
    "details": {}
  },
  "meta": { "request_id": "01J…" }
}
```

Rules:

- Stable machine-readable `error.code`
- Non-disclosing not-found for foreign tenants
- Sensitive fields omitted or masked by role
- Pagination required on lists; hard max page size
- Idempotency-Key header required for payment-adjacent, number purchase, payout, and other irreversible POSTs

## 3. Portal API modules (logical resources)

All paths below are `/api/v1/...`. Scope is implied by session, not by client-supplied tenant.

### Platform (Super Admin)

| Method | Resource | SRS |
|---|---|---|
| GET | `/platform/dashboard` | SA1-*, RPT-* — period (`today`/`7d`/`30d`/`mtd`/`custom` + since/until), timezone, optional `agency_id`; money from ledger/invoices |
| GET/POST | `/platform/agencies` | SA2-* |
| POST | `/platform/agencies/{id}/status` | SA2-004 |
| POST | `/platform/agencies/{id}/commission` | SA2-003, BR-001 |
| POST | `/platform/agencies/{id}/capabilities` | SA2-005 |
| POST | `/platform/agencies/{id}/reassign-customer` | **Not in initial V1** (Q-016) |
| GET/POST | `/platform/customers` | SA3-* |
| POST | `/platform/customers/{id}/minutes-adjustment` | SA3-003 |
| GET | `/platform/kyc/cases` | SA4-* status/aging, not document preview |
| POST | `/platform/kyc/cases/{id}/override` | KYC-007 freeze/override |
| POST | `/webhooks/kyc/{provider}/v1/` | Signed provider events (Q-015) |
| GET/POST | `/platform/agents` | SA5-* |
| GET/POST | `/platform/templates` | SA6-* |
| GET/POST | `/platform/instructions` | SA7-* |
| GET/POST | `/platform/knowledge` | SA8-* |
| GET/POST | `/platform/phone-numbers` | SA9-*, Q-002 |
| GET/POST | `/platform/plans` | SA11-*, PLAN-* |
| GET | `/platform/payments` `/invoices` `/disputes` | SA12-* |
| GET/POST | `/platform/payouts` | SA13-* |
| POST | `/platform/payouts/{id}/proof` | SA13-004, BR-009 |
| POST | `/platform/payouts/{id}/mark-paid` | SA13-005, BR-010 |
| GET | `/platform/calls` | SA14-* |
| GET | `/platform/audit-events` | SA17-* — search only; no PATCH/DELETE |
| GET/PATCH | `/platform/settings` | SA19-* — secrets masked; reason required |
| POST | `/platform/settings/flags` | SA19-004 agency feature flags |
| GET/POST | `/platform/notification-templates` | SA16-001 |
| GET | `/platform/notification-deliveries` | SA16-002 |
| POST | `/platform/announcements` | SA16-003 |
| GET | `/platform/notifications` | NOT-001 in-app inbox |
| GET/POST | `/platform/users` `/roles` | SA18-* |

### Agency

| Method | Resource | SRS |
|---|---|---|
| GET | `/agency/dashboard` | AG1-* — session tenant only |
| GET/POST | `/agency/customers` | AG2-* |
| GET/POST | `/agency/agents` | AG3-* |
| POST | `/agency/agents/{id}/publish` | AGT-002 |
| GET/POST | `/agency/phone-numbers/search` `reservations` `assignments` | AG4-*, Q-002 |
| GET | `/agency/calls` | AG5-* |
| GET/POST | `/agency/calls/{id}/artifacts` `/access` `/hold` `/delete` | CALL-003–005, ADR-002 |
| GET/POST | `/agency/transfers` | AG6-*, XFER-* |
| GET/POST | `/agency/knowledge` | AG7-* |
| GET/POST | `/agency/integrations` | AG8-* — **customer-owned connections only** |
| GET/POST | `/agency/webhooks` | AG9-* |
| GET | `/agency/plans` `/customer-invoices` | AG10-* |
| GET/POST | `/agency/wallet` `/payouts` | AG11-*, WAL-* |
| GET | `/agency/kyc` | AG12-002 status + payout gate |
| POST | `/agency/kyc/session` | Start/resume external KYC (Q-015) |
| GET/POST | `/agency/team` | AG13-* |
| GET | `/agency/notifications` | NOT-001 |
| GET/PUT | `/agency/notification-preferences` | AG14-001 — mandatory events locked |

Agency cannot change Vokit payment destination (AG10-003).  
Agency cannot approve payouts or view payout proof.

### Customer

| Method | Resource | SRS |
|---|---|---|
| GET | `/customer/dashboard` | CU1-* — session customer only |
| GET | `/customer/agents` | CU2-* — session customer only |
| PATCH | `/customer/agents/{id}` | Only if agency granted |
| GET | `/customer/calls` | CU3-* |
| POST | `/customer/calls/{id}/artifacts/{artifact_id}/access` | CALL-003, ADR-002 |
| GET | `/customer/usage` | CU4-* |
| POST | `/customer/usage/top-ups` | CU4-003 |
| GET/POST | `/customer/invoices` `/payments` `/payment-methods` | CU5-* |
| GET/PATCH | `/customer/knowledge` | CU6-* |
| GET/POST | `/customer/integrations` | CU7-* if enabled |
| GET/POST | `/customer/team` | CU8-* |
| GET | `/customer/notifications` | CU1-002 / NOT-001 |
| GET/PUT | `/customer/notification-preferences` | CU8-002 — mandatory events locked |

## 4. Internal telephony contract (frozen unless ADR)

Pipecat already calls these paths. Django V1 **must implement them**.

| Method | Path | Purpose |
|---|---|---|
| POST | `/internal/telephony/v1/voice-session/bootstrap/` | Resolve DID/session; return agent, providers, transfer spec, compliance — **no secrets in prompts** |
| POST | `/internal/telephony/v1/voice-session/events/` | Heartbeat / transcript / lifecycle events |
| POST | `/internal/telephony/v1/voice-session/end/` | Terminal reconcile |
| POST | `/internal/telephony/v1/voice-session/transfer/` | Start transfer via Edge |
| GET | `/internal/telephony/v1/voice-session/transfer/status/` | Poll until terminal |
| POST | `/internal/telephony/v1/training-session/bootstrap/` | Browser simulator |
| POST | `/internal/telephony/v1/training-session/propose/` | Training proposal |
| POST | `/internal/telephony/v1/training-session/confirm/` | Confirm |
| POST | `/internal/telephony/v1/training-session/end/` | End training |

Auth header: `X-Vokit-Internal-Token`.

Bootstrap must fail closed if tenant/agent/minutes/risk/admission fails.

Additional **new** internal endpoints required by SRS, added without breaking the above:

| Method | Path | Purpose |
|---|---|---|
| POST | `/internal/telephony/v1/did/resolve/` | Asterisk/admission `routable` decision |
| POST | `/internal/telephony/v1/tools/invoke/` | Q-009 Django tool gateway |
| POST | `/internal/telephony/v1/voice-session/continue/` | Mid-call minutes/grace/overage decision |
| POST | `/internal/telephony/v1/voice-session/voicemail/` | Inbound mailbox / outbound leave (metadata only; audio is Phase 13) |
| POST | `/internal/recordings/v1/ingest/` | Artifact available callback |
| POST | `/internal/recordings/v1/access/validate/` | Recording plane consumes a single-use grant |

SIP Edge HTTP (`POST /v1/calls`, `DELETE /v1/calls/:id`, transfer) remains Edge-owned. Django is the client.

## 5. Outbound webhooks (SRS §30.2)

Envelope:

```json
{
  "event_id": "…",
  "event_type": "call.completed",
  "event_version": "1",
  "occurred_at": "2026-09-10T00:00:00Z",
  "agency_id": "…",
  "customer_id": "…",
  "object_id": "…",
  "data": {},
  "delivery_id": "…"
}
```

- Tenant-specific signing secret, rotatable
- Unique `event_id` + `delivery_id`
- Bounded retry/backoff
- No secret-bearing payloads
- Replay is an authorized action

Event names stay as listed in SRS §30.2.

## 6. Inbound provider webhooks

Order is mandatory: signature → event ID → dedup → persist → side effects.

Processors: Stripe and Braintree. Normalize to domain events (`payment.captured`, `dispute.created`, …) before commission/risk logic.

KYC provider webhooks use the same verify → event ID → dedup → persist → map-status order. Do not persist document images from the payload.

## 7. Recording access contract

`POST /api/v1/{scope}/calls/{call_id}/artifacts/{artifact_id}/access`

Returns `{ "token": "…", "expires_at": "…", "url": "https://recording…/stream?token=" }`  
TTL short; single-purpose; bind tenant, customer, call, artifact, actor.  
Recording server validates signature/expiry/replay policy.

## 8. Error codes (initial set)

`unauthenticated`, `forbidden`, `not_found`, `validation_error`, `idempotency_conflict`, `tenant_unavailable`, `capability_disabled`, `kyc_required`, `insufficient_minutes`, `plan_hard_stop`, `payout_ineligible`, `reservation_expired`, `processor_rejected`, `conflict_state`, `rate_limited`.

Do not leak whether a foreign ID exists.

## 9. Compatibility rule

Releasing Django must not silently break Pipecat/SIP Edge/Asterisk contracts. Media-path changes need compatibility tests and rollback.

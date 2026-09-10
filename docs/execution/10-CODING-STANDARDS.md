# Vokit Coding Standards

## 1. Languages

| Area | Standard |
|---|---|
| Django API | Python 3.12+, type hints on public functions |
| React | TypeScript `strict` |
| Pipecat | Existing Python package conventions |
| SIP Edge | Existing Rust conventions |

## 2. Architecture rules

- Domain has no Django views, no React, no provider SDKs.
- Application services orchestrate one use case and one transaction.
- Infrastructure implements ports.
- API maps HTTP ↔ application DTOs.
- React maps application DTOs ↔ UI state.

New cross-context coupling must go through an application service, domain event, or explicit interface.

## 3. Naming

- Use cases: `CreateAgency`, `ReservePhoneNumber`, `RequestPayout`
- Commands/queries explicit
- Events: SRS catalog names (`invoice.paid`)
- Feature flags and permissions: stable snake_case codes

## 4. Data and money

- UUID v7 strings in APIs
- Money: integer minor units + `USD`
- Phones: E.164
- Time: UTC in storage and API; convert in UI
- No binary floats for money or billable seconds aggregation that becomes money

## 5. Errors

Raise domain errors with stable codes. Map once at the API boundary. Do not leak stack traces, DSNs, or existence of foreign tenants.

## 6. Concurrency and idempotency

- `Idempotency-Key` on irreversible POSTs
- Processor `event_id` unique
- Payout reservation uses row locks / compare-and-set in the **tenant** DB transaction
- Tenant migration lock is per tenant

## 7. Logging

Required fields: timestamp, severity, module, event, correlation_id, outcome, latency.  
Optional: tenant_id when authorized for ops.  
Forbidden: secrets, raw audio, transcripts, PAN, KYC images, payout proof bytes.

## 8. Testing

See [`17-QA-TESTING-PLAN.md`](17-QA-TESTING-PLAN.md). No module merges without the applicable negative tests.

## 9. Frontend

- No `any` without justification
- Server state in Query; no global tenant store used as auth
- Accessibility on core forms
- Do not commit `.env`

## 10. Git hygiene

- Do not commit secrets, dumps, recordings, or KYC fixtures with real PII
- Do not amend pushed commits
- Commit only when asked

## 11. Render / Linux notes

- Bind HTTP to `0.0.0.0:$PORT`
- Treat local disk as ephemeral
- Paths are case-sensitive in production

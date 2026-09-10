# Vokit Final Production Checklist

Go / No-Go for V1 launch. Every item needs **evidence** (test output, screenshot of dashboard, ticket, restore log). A config flag alone is not evidence.

## 1. Governance

- [x] SRS v1.0 is still the product SoT
- [x] Q-001–Q-016 still Decided and implemented as decided
- [x] ADR-001–005 Accepted
- [x] Agency KYC is provider-backed; no Vokit document vault
- [x] Customers exist only under their Agency (no reassignment shipped)
- [x] No unresolved HIGH open question that changes tenancy, ERD, billing, voice, or recordings
- [ ] Legal/compliance signed launched jurisdictions

## 2. Functional evidence (SRS §31.1)

Attach links/IDs for a recorded staging or canary run of every bullet in Release Checklist C.

## 3. Engineering evidence (SRS §31.2)

- [x] CI/lab: isolation, finance, sandbox E2E, memory restore, security review, runbooks
- [ ] Live: dated restore drill + alert screenshot (`26-PHASE-19-EVIDENCE.md`)

## 4. Isolation evidence

- [ ] Tenant negative matrix executed on production-like data
- [ ] Recording negative matrix executed
- [ ] Ban-index does not leak reason to agency

## 5. Live-path evidence

- [ ] Inbound call → correct agent → call row → usage
- [ ] Outbound call → authorized caller ID
- [ ] Transfer (E.164 and queue or SIP client as shipped)
- [ ] Voicemail inbound or outbound path
- [ ] Recording play via short-lived token
- [ ] Tool/CRM or webhook action without secret leakage
- [ ] Payment → one commission → hold
- [ ] Payout request → proof → Paid → receipt visible, proof not

## 6. Operations evidence

- [ ] Backup restore of control plane
- [ ] Backup restore of one tenant DB
- [ ] Worker replay/idempotency
- [ ] On-call knows P0 isolation/finance/voice/recording actions
- [ ] Rollback performed once in staging

## 7. Scale readiness (launch-day, not “infinite scale”)

- [ ] Connection pool caps documented
- [ ] Max concurrent calls documented
- [ ] Hotspot-tenant plan (noisy neighbor)
- [ ] Recording ingest bandwidth estimate
- [ ] Provider quota headroom

## 8. Sign-off

| Role | Name | Go/No-Go | Date | Evidence pack |
|---|---|---|---|---|
| Product Owner | | | | |
| Engineering Lead | | | | |
| QA Lead | | | | |
| Finance / Operations | | | | |
| Compliance / Legal | | | | |

No-Go if any P0 control is untested, any accepted ADR is violated, or recordings/finance/tenancy lack negative-test evidence.

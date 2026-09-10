# ADR-005 — External Agency KYC Provider

Status: Accepted  
Date: 2026-09-10  
Accepted: 2026-09-10 (owner proceed)

## Context

SRS §6, KYC-001–008, SA4 and AG12 define agency KYC as a first-class Vokit workflow with document upload and Super Admin review. OPEN-QUESTIONS previously deferred the KYC vendor and treated manual review as the V1 path.

The product owner has now decided that **agency KYC is handled externally**. The KYC provider supplies API keys. Vokit must not become the primary KYC document vault or reviewer workbench.

This does **not** remove SRS payout gating: an agency still cannot request payout unless KYC status is Verified (KYC-001, BR-011).

This ADR covers **agency KYC only**. Customer payment-risk verification (government ID + masked card last-four, chargeback freeze) remains the SRS risk module unless a later decision delegates that to the same provider.

## Decision

1. Integrate KYC through a **provider port/adapter**. Do not couple the domain to a specific vendor SDK.
2. Store provider **API keys as encrypted secret references** in the control plane (platform settings). Never put keys in React, tenant DBs, logs, or agent prompts.
3. Agency users start or resume KYC through the provider-hosted flow (redirect/hosted session). Vokit does not collect or store KYC document bytes as the system of record.
4. Vokit persists only:
   - mapped KYC status (SRS §6.3 states);
   - provider account/session/inquiry references;
   - last provider event ID;
   - non-sensitive reason codes if the provider supplies them;
   - timestamps and audit of status changes.
5. Inbound provider webhooks: verify signature → validate event ID → deduplicate → map to domain status → notify → audit.
6. Super Admin sees KYC **status** and may freeze/override capabilities (KYC-007). Super Admin does not review raw KYC files inside Vokit.
7. Agency portal shows status, provider-required next step, and payout restriction until Verified (AG12-002, AG12-004).
8. If the provider later exposes document access, treat it as highly restricted, auditable, and never available to support/customer views (KYC-002). Prefer leaving documents at the provider.

## Non-goals

- Building an in-app KYC document review queue as the primary V1 path.
- Choosing the commercial KYC vendor name inside domain code.
- Replacing customer payment-card verification / chargeback rules.

## Consequences

Positive:

- Vokit avoids storing high-sensitivity identity documents.
- Provider can change without rewriting payout/ledger rules.
- Matches “API keys from the KYC provider.”

Trade-offs:

- Payout eligibility depends on provider availability; fail closed for payouts if status is unknown.
- Super Admin KPI “KYC queue” becomes provider-status aging, not an internal document inbox.
- SRS SA4 evidence-review screens are satisfied by status/override + provider console, not by Vokit file preview.

## Security

- Secret-ref only for API keys; rotation supported.
- Webhook signature required before parse.
- Never log raw provider payloads that contain document images or full identity numbers.
- Fail closed: missing/unknown KYC status is not Verified.

## Required follow-up

Accepted at Gate 0 proceed. Name the vendor only in environment/secrets, not in the domain model.

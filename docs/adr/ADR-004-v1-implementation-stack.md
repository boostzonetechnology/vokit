# ADR-004 — V1 Implementation Stack Defaults

Status: Accepted  
Date: 2026-09-10  
Accepted: 2026-09-10 (owner proceed)

## Context

`docs/OPEN-QUESTIONS.md` defers Django package choices, folder structure, primary-key style, API envelope, queue product, and hosting details. Implementation cannot start without locking these **engineering** defaults. None of the options below change SRS business rules.

## Decision

1. Django 5 + Django REST Framework for the modular-monolith API.
2. Celery + Redis for asynchronous work.
3. MySQL 8 for control-plane and each Agency tenant database.
4. React + TypeScript + Vite for three separate portal apps.
5. Cookie session authentication with CSRF for browser portals; service tokens for internal telephony and recording.
6. UUID v7 primary keys.
7. Integer minor units for money; USD only.
8. Public API prefix `/api/v1/`; keep existing `/internal/telephony/v1/` paths used by Pipecat.
9. Qdrant remains the knowledge vector store; Django writes, Pipecat retrieves.
10. Object storage for payout proof and recording objects; vendor chosen at deploy time without leaking into the domain. Agency KYC documents stay at the external KYC provider (ADR-005).

## Consequences

Positive:

- Matches decided product direction (Django + MySQL + React).
- Preserves existing voice contracts.
- Keeps domain logic testable without provider SDKs.

Trade-offs:

- Three frontend apps increase some shared-UI cost; this is accepted to keep Super Admin, Agency, and Customer security surfaces separate.
- Celery/Redis becomes a production dependency and must be observed.

## Non-goals

- Choosing a specific cloud object-storage brand as a domain concept.
- Choosing Stripe vs Braintree SDKs inside domain code.
- Extracting microservices in V1.

## Required follow-up

Accepted at Gate 0 proceed. Amend this ADR before changing the stack defaults.

---
name: vokit-implement-feature
description: Implement a Vokit roadmap slice using SRS IDs, architecture-first method, tenant/finance/voice safety, and the required task report. Use when building a feature, module, or vertical slice after Gate 0 proceed.
---

# Implement Vokit Feature

## When
After the owner has said proceed and the slice's phase prerequisites exist.

## Steps
1. Read matching SRS IDs from `docs/execution/12-FEATURE-MATRIX.md`.
2. Read Decided answers and ADRs that touch tenancy, money, recordings, or voice.
3. Fill the architecture-review template (requirement IDs, current/proposed architecture, ownership, routing, contracts, failure/retry, security, observability, migration, rollback, tests, scale).
4. Stop if a HIGH decision is missing — write/update an ADR instead of coding.
5. Implement in order: domain → application → ports → infrastructure → migrations → API → tests → observability → React if needed → runbook.
6. Add the applicable negative tests from `docs/execution/17-QA-TESTING-PLAN.md`.
7. End with the Required Task Report.

## Reject
Tenant isolation weakening, business rules in React, provider types in domain, mutable finance, raw recordings in Django/static, unbounded per-tenant connections, renaming frozen `/internal/telephony/v1/` paths without an ADR, in-app agency KYC document vaults (Q-015), per-customer databases or cross-agency customer moves in the initial build (Q-016).

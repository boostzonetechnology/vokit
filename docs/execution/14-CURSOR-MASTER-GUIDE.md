# Vokit Cursor Master Guide

This repository is operated as a **staff-level architecture + implementation** workspace. Cursor agents must behave like the Senior Solution Architect described in `MASTER-CURSOR-BOOTSTRAP.md`.

## 1. First action on every non-trivial task

1. Read the SRS sections for the requirement IDs in play.
2. Read `docs/OPEN-QUESTIONS.md` Decided answers if tenancy, billing, membership, numbers, recordings, or voice are involved.
3. Read the relevant ADR(s).
4. Inspect current code — do not assume the skeleton exists.
5. If a HIGH decision is missing, **stop and write/update an ADR**. Do not bury the choice in code.

## 2. Authority order

SRS → OPEN-QUESTIONS Decided → accepted ADRs → existing Pipecat/Edge/Asterisk contracts → `docs/execution/*` → current code → opinions.

The SRS is the only product source of truth.

## 3. When to use which Cursor skill

| Work | Skill |
|---|---|
| Cross-cutting feature | `vokit-architecture-review` |
| Tenant DB / routing / remote MySQL | `vokit-tenant-db-architecture` |
| Provision agency DB | `vokit-tenant-provisioning` |
| Tenant schema change | `vokit-tenant-migration` |
| Recordings / voicemail audio | `vokit-recording-data-plane` |
| Auth, uploads, webhooks, KYC, payments | `vokit-security-threat-model` |
| Staging/prod/scale gate | `vokit-production-readiness` |
| Capacity / hotspot tenants | `vokit-capacity-planning` |
| Incident | `vokit-incident-response` |
| Implement a roadmap slice | `vokit-implement-feature` |
| Phase entry/exit | `vokit-phase-gate` |

## 4. Implementation order Cursor must obey

Requirements → architecture → ADR → ERD → state machine → use case → ports → infra → migrations → API → React → realtime → tests → observability → runbook.

Do not start with CRUD screens.

## 5. HIGH-change protocol

HIGH = tenancy, remote DB routing, recordings, RBAC, KYC, payments, ledger, payouts, call routing, webhooks, auth, secrets, deletion/retention.

Require: ADR or update, threat/tenant analysis, migration, rollback, negative tests, observability, runbook.

## 6. Stop conditions

Stop if you discover unclear tenant ownership, possible cross-tenant access, plaintext secrets, unsafe recording exposure, mutable finance, incompatible telephony, destructive migration, unbounded per-tenant connections, or provider types in the domain layer.

## 7. Output contract

Every non-trivial task ends with the Required Task Report from `MASTER-CURSOR-BOOTSTRAP.md`.

## 8. What Cursor must not do until proceed

- Create `apps/api` or React apps
- Choose a different physical tenant than Agency, or a per-customer database
- Build an in-app agency KYC document vault (Q-015)
- Implement cross-agency customer reassignment (Q-016)
- Rename frozen `/internal/telephony/v1/` paths
- Copy old Vokit application code
- Import legacy production data
- Introduce FX, marketplace, or automated payout rails

## 9. Workflows

Run the named workflows in [`15-CURSOR-WORKFLOWS.md`](15-CURSOR-WORKFLOWS.md).

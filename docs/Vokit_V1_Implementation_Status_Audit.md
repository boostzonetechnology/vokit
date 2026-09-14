# Vokit V1 Implementation Status Audit

Generated from:
- Vokit SRS
- Vokit V1 Jira Sprint Plan
- Current Backend Codebase
- Current Frontend Codebase
- Tests
- ADRs
- Known Gaps

Audit Scope:
VKT-001 through VKT-151

Sources:
- Vokit SRS
- Vokit V1 Jira Sprint Plan
- Current Backend Codebase
- Current Frontend Codebase
- Tests
- ADRs
- Known Gaps

Audit Type:
Full Implementation Baseline / Backend + Frontend Gap Analysis

Important:
This report reflects repository evidence at the time of the audit.
No implementation changes were made during this audit.

**Audit date:** 2026-09-12 (updated with frontend re-audit)

## Final Project Status (Executive)

```text
Total Jira Tasks: 151

COMPLETE: 55
PARTIAL: 89
NOT_IMPLEMENTED: 7
BLOCKED: 0
NEEDS_MANUAL_REVIEW: 0
```

```text
Complete by task count: 36.4%
Partial by task count: 58.9%
Remaining by task count (PARTIAL+NOT_IMPLEMENTED+BLOCKED+NMR): 63.6%
```

```text
Total Story Points (XLS): 698
Completed Story Points: 254
Partial Story Points: 421
Not Implemented Story Points: 23
Remaining Story Points (non-COMPLETE): 444
```

**Verdict:** Backend domain remains largely ahead of a greenfield Jira start. After the **frontend code pull**, many Super Admin UI gaps closed (agencies create/notes, KYC review, payout review, plans/billing/calls/settings/users/audit/notifications). Remaining work concentrates on **agency/customer portal depth**, invite accept UI, async knowledge, billing notification dispatch, privacy export, transfer rules, webhook replay, agent simulator, and **live production attestations**.

**Frontend re-audit (2026-09-12):** Platform portal uses dedicated feature screens via `renderPlatformScreen.tsx`; only `risk` remains generic. Agency/customer portals still lean on `productScreens.tsx`. Frontend automated tests are missing.

## Status Legend


| Status              | Meaning                                                                                             |
| ------------------- | --------------------------------------------------------------------------------------------------- |
| COMPLETE            | Jira Definition of Done satisfied by repository evidence (including ADR-superseded DoD where noted) |
| PARTIAL             | Meaningful implementation exists; specific gaps listed per task                                     |
| NOT_IMPLEMENTED     | Required functionality not found                                                                    |
| BLOCKED             | Cannot proceed due to missing dependency (none identified in this audit)                            |
| NEEDS_MANUAL_REVIEW | Evidence insufficient (none identified)                                                             |
| N/A                 | Category not applicable to this task                                                                |


---



## Status Changes After Frontend Audit

Compared to the pre-frontend-pull audit baseline (including the mid-day agency re-check).

### VKT-019

**Previous:** PARTIAL

**Current:** COMPLETE

**Reason:** PlatformAgencyCreateScreen now collects MySQL username/password (+ optional host/port) and POSTs database payload.

**Evidence:**

- packages/web-ui/src/features/agencies/PlatformAgencyCreateScreen.tsx — Database step
- packages/web-ui/src/features/agencies/hooks/useCreatePlatformAgency.ts — POST /api/v1/platform/agencies with database{}
- packages/web-ui/src/features/agencies/renderAgencyRoutes.tsx — /agencies/new

### VKT-020

**Previous:** PARTIAL

**Current:** COMPLETE

**Reason:** PlatformAgencyDetailScreen provides profile/commission/status/capabilities/financial/resources/notes tabs wired to APIs.

**Evidence:**

- packages/web-ui/src/features/agencies/PlatformAgencyDetailScreen.tsx
- packages/web-ui/src/features/agencies/hooks/usePlatformAgencyDetail.ts

### VKT-023

**Previous:** PARTIAL

**Current:** COMPLETE

**Reason:** Notes tab now lists/creates notes via platform agencies notes API (risk_flag supported).

**Evidence:**

- packages/web-ui/src/features/agencies/PlatformAgencyDetailScreen.tsx — notes tab
- packages/web-ui/src/features/agencies/hooks/usePlatformAgencyDetail.ts — GET/POST .../notes

### VKT-030

**Previous:** PARTIAL

**Current:** COMPLETE

**Reason:** PlatformKycScreen implements SA KYC case queue with filters and case selection (ADR-005 status queue).

**Evidence:**

- packages/web-ui/src/features/kyc/PlatformKycScreen.tsx
- packages/web-ui/src/features/kyc/hooks/usePlatformKyc.ts — GET /api/v1/platform/kyc/cases

### VKT-032

**Previous:** PARTIAL

**Current:** COMPLETE

**Reason:** KYC override UI exposes Verify / Reject / More information (+ freeze/unfreeze) via override API.

**Evidence:**

- packages/web-ui/src/features/kyc/PlatformKycScreen.tsx — decision actions
- packages/web-ui/src/features/kyc/types.ts — DECISION_STATUSES
- packages/web-ui/src/features/kyc/hooks/usePlatformKyc.ts — POST .../override

### VKT-035

**Previous:** PARTIAL

**Current:** COMPLETE

**Reason:** PlatformPlansScreen provides dedicated plan catalog UI (replaces generic table).

**Evidence:**

- packages/web-ui/src/features/plans/PlatformPlansScreen.tsx
- packages/web-ui/src/features/plans/hooks/usePlatformPlans.ts

### VKT-036

**Previous:** PARTIAL

**Current:** COMPLETE

**Reason:** Platform plans screen supports plan/version management against billing APIs.

**Evidence:**

- packages/web-ui/src/features/plans/PlatformPlansScreen.tsx
- packages/web-ui/src/features/plans/hooks/usePlatformPlans.ts

### VKT-049

**Previous:** PARTIAL

**Current:** COMPLETE

**Reason:** PlatformBillingScreen covers payments/invoices/disputes with real platform APIs.

**Evidence:**

- packages/web-ui/src/features/billing/PlatformBillingScreen.tsx
- packages/web-ui/src/features/billing/hooks/usePlatformBilling.ts

### VKT-053

**Previous:** PARTIAL

**Current:** COMPLETE

**Reason:** PlatformPayoutsScreen implements queue, approve/reject/freeze/process, mark-paid, proof upload/view, receipt metadata.

**Evidence:**

- packages/web-ui/src/features/payouts/PlatformPayoutsScreen.tsx
- packages/web-ui/src/features/payouts/hooks/usePlatformPayouts.ts
- packages/web-ui/src/features/payouts/types.ts — PAYOUT_ACTIONS

### VKT-071

**Previous:** PARTIAL

**Current:** COMPLETE

**Reason:** PlatformInstructionsScreen manages global/platform instructions via API.

**Evidence:**

- packages/web-ui/src/features/instructions/PlatformInstructionsScreen.tsx
- packages/web-ui/src/features/instructions/hooks/usePlatformInstructions.ts

### VKT-072

**Previous:** PARTIAL

**Current:** COMPLETE

**Reason:** PlatformKnowledgeScreen provides global knowledge source management UI.

**Evidence:**

- packages/web-ui/src/features/knowledge/PlatformKnowledgeScreen.tsx
- packages/web-ui/src/features/knowledge/hooks/usePlatformKnowledge.ts

### VKT-075

**Previous:** PARTIAL

**Current:** COMPLETE

**Reason:** PlatformTemplatesScreen provides template catalog management UI.

**Evidence:**

- packages/web-ui/src/features/templates/PlatformTemplatesScreen.tsx
- packages/web-ui/src/features/templates/hooks/usePlatformTemplates.ts

### VKT-079

**Previous:** PARTIAL

**Current:** COMPLETE

**Reason:** Agency NumbersScreen search + PlatformNumbersScreen inventory; agency search/reserve/assign wired.

**Evidence:**

- packages/web-ui/src/productScreens.tsx — NumbersScreen search/reserve/assign
- packages/web-ui/src/features/numbers/PlatformNumbersScreen.tsx

### VKT-100

**Previous:** PARTIAL

**Current:** COMPLETE

**Reason:** PlatformCallsScreen provides dedicated SA call monitoring list/detail.

**Evidence:**

- packages/web-ui/src/features/calls/PlatformCallsScreen.tsx
- packages/web-ui/src/features/calls/hooks/usePlatformCalls.ts

### VKT-112

**Previous:** PARTIAL

**Current:** COMPLETE

**Reason:** PlatformUsersScreen covers users, invite, roles/RBAC matrix, sensitive permissions.

**Evidence:**

- packages/web-ui/src/features/users/PlatformUsersScreen.tsx
- packages/web-ui/src/features/users/hooks/usePlatformUsers.ts

### VKT-114

**Previous:** PARTIAL

**Current:** COMPLETE

**Reason:** PlatformNotificationsScreen administers templates, deliveries, announcements, inbox.

**Evidence:**

- packages/web-ui/src/features/notifications/PlatformNotificationsScreen.tsx
- packages/web-ui/src/features/notifications/hooks/usePlatformNotifications.ts

### VKT-115

**Previous:** PARTIAL

**Current:** COMPLETE

**Reason:** PlatformIntegrationsScreen shows provider registry and tenant connection visibility.

**Evidence:**

- packages/web-ui/src/features/integrations/PlatformIntegrationsScreen.tsx
- packages/web-ui/src/features/integrations/hooks/usePlatformIntegrations.ts

### VKT-117

**Previous:** PARTIAL

**Current:** COMPLETE

**Reason:** PlatformTransfersScreen provides transfer directory/monitoring/diagnostics.

**Evidence:**

- packages/web-ui/src/features/transfers/PlatformTransfersScreen.tsx
- packages/web-ui/src/features/transfers/hooks/usePlatformTransfers.ts

### VKT-118

**Previous:** PARTIAL

**Current:** COMPLETE

**Reason:** PlatformAuditScreen provides filtered search + detail panel.

**Evidence:**

- packages/web-ui/src/features/audit/PlatformAuditScreen.tsx
- packages/web-ui/src/features/audit/hooks/usePlatformAudit.ts

### VKT-120

**Previous:** PARTIAL

**Current:** COMPLETE

**Reason:** PlatformSettingsScreen edits platform settings/flags via API.

**Evidence:**

- packages/web-ui/src/features/settings/PlatformSettingsScreen.tsx
- packages/web-ui/src/features/settings/hooks/usePlatformSettings.ts

**Net COMPLETE upgrades this pass:** 20 (VKT-019, VKT-020, VKT-023, VKT-030, VKT-032, VKT-035, VKT-036, VKT-049, VKT-053, VKT-071, VKT-072, VKT-075, VKT-079, VKT-100, VKT-112, VKT-114, VKT-115, VKT-117, VKT-118, VKT-120)

---
## Frontend Audit Findings

### Architecture (current)

- Shared UI package: `packages/web-ui` (React + TypeScript + Vite + React Router `BrowserRouter`)
- Thin portals: `apps/web-platform`, `apps/web-agency`, `apps/web-customer` mount `PortalApp`
- Platform routes: dedicated feature screens via `features/platform/renderPlatformScreen.tsx` (code-split)
- Agency/Customer product routes: mostly lab-style screens in `productScreens.tsx` (except dashboards)
- Auth: `LoginScreen` + session via `getPortalMe` / CSRF cookie client in `api.ts`
- **Only generic SA module left:** `risk` (`platformModules.ts` → `PlatformResourceScreen`)
- Dead code: `screens.tsx` is **not imported** (contains unwired customer top-up / richer helpers)

### Key discoveries

1. **Super Admin UI largely replaced generic tables** for agencies, customers, KYC, payouts, plans, billing, calls, knowledge, templates, instructions, numbers, transfers, integrations, notifications, audit, users, settings.
2. **Agency create DB credentials** and **agency notes** are now fully wired (were open gaps earlier today).
3. **SA payout review + KYC override actions** are fully wired to real APIs.
4. **Agency/Customer portals remain thinner** than Super Admin — many routes still use `productScreens.tsx` list/forms.
5. **Invite acceptance UI still missing** (API exists).
6. **Agency customer detail tabs still missing** (platform customer detail exists but does not satisfy agency DoD).
7. **Customer pay invoice + top-up** not on active routes (top-up only in dead `screens.tsx`).
8. **Webhook delivery/replay UI missing**; transfer rules UI missing; agent simulator UI missing.
9. **Frontend automated tests: MISSING** (no vitest/RTL/Playwright in `packages/web-ui`).
10. Presence of UI ≠ production readiness (lab adapters, live attestations still open — VKT-148–151).

### Frontend tests

```text
Frontend implementation (platform SA modules): largely COMPLETE for dedicated screens
Frontend implementation (agency/customer product UX): PARTIAL
Frontend tests: MISSING
```

---
## Master Task-by-Task Table

The master matrix below is intentionally **compact** so it remains readable in the editor preview.
For each VKT ID, open the matching **Detailed Task Record** for SRS traceability, evidence paths, missing work, dependencies, and remaining work.


| VKT ID  | Sprint   | Epic               | Task                                                 | Pri  | Pts | Overall         | Backend         | UI              | Infra           | Tests           |
| ------- | -------- | ------------------ | ---------------------------------------------------- | ---- | --- | --------------- | --------------- | --------------- | --------------- | --------------- |
| VKT-001 | Sprint 1 | Foundation         | Baseline implementation traceability                 | Must | 2   | PARTIAL         | PARTIAL         | N/A             | N/A             | PARTIAL         |
| VKT-002 | Sprint 1 | Foundation         | Define tenant ownership model                        | Must | 5   | COMPLETE        | COMPLETE        | N/A             | COMPLETE        | COMPLETE        |
| VKT-003 | Sprint 1 | Foundation         | Create core identity and tenancy tables              | Must | 5   | PARTIAL         | PARTIAL         | N/A             | N/A             | PARTIAL         |
| VKT-004 | Sprint 1 | Foundation         | Create commercial and financial tables               | Must | 8   | PARTIAL         | PARTIAL         | N/A             | N/A             | COMPLETE        |
| VKT-005 | Sprint 1 | Foundation         | Create AI/telephony/integration tables               | Must | 8   | PARTIAL         | PARTIAL         | N/A             | N/A             | PARTIAL         |
| VKT-006 | Sprint 1 | Foundation         | Create notification and audit tables                 | Must | 3   | COMPLETE        | COMPLETE        | N/A             | N/A             | COMPLETE        |
| VKT-007 | Sprint 1 | Foundation         | Implement secure authentication/session foundation   | Must | 5   | PARTIAL         | PARTIAL         | PARTIAL         | N/A             | PARTIAL         |
| VKT-008 | Sprint 1 | Foundation         | Implement server-side RBAC and tenant guards         | Must | 8   | COMPLETE        | COMPLETE        | N/A             | N/A             | COMPLETE        |
| VKT-009 | Sprint 1 | Foundation         | Implement input validation and security middleware   | Must | 5   | PARTIAL         | PARTIAL         | N/A             | PARTIAL         | PARTIAL         |
| VKT-010 | Sprint 1 | Foundation         | Implement server-side secret management              | Must | 3   | PARTIAL         | PARTIAL         | N/A             | PARTIAL         | COMPLETE        |
| VKT-011 | Sprint 1 | Foundation         | Define versioned API conventions and error contract  | Must | 3   | COMPLETE        | COMPLETE        | COMPLETE        | N/A             | COMPLETE        |
| VKT-012 | Sprint 1 | Foundation         | Implement internal domain-event contract             | Must | 3   | PARTIAL         | PARTIAL         | N/A             | N/A             | PARTIAL         |
| VKT-013 | Sprint 1 | Foundation         | Implement canonical money, UTC and E.164 handling    | Must | 3   | COMPLETE        | COMPLETE        | N/A             | N/A             | COMPLETE        |
| VKT-014 | Sprint 1 | Foundation         | Implement secure file upload abstraction             | Must | 3   | PARTIAL         | PARTIAL         | N/A             | PARTIAL         | PARTIAL         |
| VKT-015 | Sprint 1 | Foundation         | Create production-like staging environment and CI... | Must | 5   | PARTIAL         | PARTIAL         | N/A             | PARTIAL         | PARTIAL         |
| VKT-016 | Sprint 2 | Portal Shell       | Build Super Admin application shell                  | Must | 3   | COMPLETE        | N/A             | COMPLETE        | N/A             | N/A             |
| VKT-017 | Sprint 2 | Dashboard          | Build Super Admin dashboard                          | Must | 5   | PARTIAL         | PARTIAL         | PARTIAL         | N/A             | PARTIAL         |
| VKT-018 | Sprint 2 | Agencies           | Build agency directory with search/filter/status ... | Must | 3   | COMPLETE        | COMPLETE        | COMPLETE        | N/A             | COMPLETE        |
| VKT-019 | Sprint 2 | Agencies | Build Create Agency form | Must | 5 | COMPLETE | COMPLETE | COMPLETE | COMPLETE | COMPLETE |
| VKT-020 | Sprint 2 | Agencies | Build agency profile/detail and resource tabs | Must | 5 | COMPLETE | COMPLETE | COMPLETE | N/A | PARTIAL |
| VKT-021 | Sprint 2 | Agencies           | Implement commission rate/effective-date UI and s... | Must | 3   | PARTIAL         | PARTIAL         | COMPLETE        | N/A             | COMPLETE        |
| VKT-022 | Sprint 2 | Agencies           | Implement agency status and capability overrides     | Must | 5   | COMPLETE        | COMPLETE        | COMPLETE        | N/A             | COMPLETE        |
| VKT-023 | Sprint 2 | Agencies | Build internal notes/risk flags | Must | 2 | COMPLETE | COMPLETE | COMPLETE | N/A | COMPLETE |
| VKT-024 | Sprint 2 | Onboarding | Build agency-owner invitation acceptance | Must | 3 | PARTIAL | COMPLETE | NOT_IMPLEMENTED | N/A | PARTIAL |
| VKT-025 | Sprint 2 | KYC                | Build KYC business identity form                     | Must | 3   | COMPLETE        | COMPLETE        | N/A             | COMPLETE        | COMPLETE        |
| VKT-026 | Sprint 2 | KYC                | Build owner/controller information form              | Must | 3   | COMPLETE        | COMPLETE        | N/A             | COMPLETE        | COMPLETE        |
| VKT-027 | Sprint 2 | KYC                | Build identity/business/address evidence upload      | Must | 5   | COMPLETE        | COMPLETE        | N/A             | COMPLETE        | COMPLETE        |
| VKT-028 | Sprint 2 | KYC                | Build payout details capture                         | Must | 3   | NOT_IMPLEMENTED | NOT_IMPLEMENTED | NOT_IMPLEMENTED | N/A             | NOT_IMPLEMENTED |
| VKT-029 | Sprint 2 | KYC                | Build declarations and KYC submission                | Must | 3   | COMPLETE        | COMPLETE        | N/A             | COMPLETE        | COMPLETE        |
| VKT-030 | Sprint 2 | KYC | Build KYC review queue | Must | 3 | COMPLETE | COMPLETE | COMPLETE | COMPLETE | COMPLETE |
| VKT-031 | Sprint 2 | KYC                | Build secure evidence review and notes               | Must | 3   | COMPLETE        | COMPLETE        | N/A             | COMPLETE        | COMPLETE        |
| VKT-032 | Sprint 2 | KYC | Implement Verify / Reject / More Information | Must | 5 | COMPLETE | COMPLETE | COMPLETE | COMPLETE | COMPLETE |
| VKT-033 | Sprint 2 | Onboarding         | Implement status/capability gates centrally          | Must | 5   | PARTIAL         | PARTIAL         | N/A             | N/A             | PARTIAL         |
| VKT-034 | Sprint 2 | Notifications      | Implement onboarding/KYC notification triggers       | Must | 3   | PARTIAL         | PARTIAL         | N/A             | N/A             | PARTIAL         |
| VKT-035 | Sprint 3 | Plans | Build plan catalog list | Must | 3 | COMPLETE | COMPLETE | COMPLETE | N/A | PARTIAL |
| VKT-036 | Sprint 3 | Plans | Implement plan CRUD/versioning and entitlements | Must | 5 | COMPLETE | COMPLETE | COMPLETE | N/A | PARTIAL |
| VKT-037 | Sprint 3 | Customers          | Build global customer directory                      | Must | 3   | PARTIAL         | COMPLETE        | PARTIAL         | N/A             | PARTIAL         |
| VKT-038 | Sprint 3 | Customers          | Implement Super Admin customer creation              | Must | 5   | PARTIAL         | COMPLETE        | PARTIAL         | N/A             | PARTIAL         |
| VKT-039 | Sprint 3 | Customers          | Implement customer plan assignment, ledger-backed... | Must | 5   | PARTIAL         | PARTIAL         | PARTIAL         | N/A             | PARTIAL         |
| VKT-040 | Sprint 3 | Customers          | Build Agency customer list and create flow           | Must | 5   | COMPLETE        | COMPLETE        | COMPLETE        | N/A             | COMPLETE        |
| VKT-041 | Sprint 3 | Customers | Build agency customer detail | Must | 3 | NOT_IMPLEMENTED | PARTIAL | NOT_IMPLEMENTED | N/A | PARTIAL |
| VKT-042 | Sprint 3 | Onboarding         | Implement customer owner/admin invitation            | Must | 3   | COMPLETE        | COMPLETE        | N/A             | N/A             | COMPLETE        |
| VKT-043 | Sprint 3 | Billing            | Implement customer subscription and invoice lifec... | Must | 8   | PARTIAL         | PARTIAL         | PARTIAL         | N/A             | PARTIAL         |
| VKT-044 | Sprint 3 | Billing            | Implement hosted/tokenized payment integration bo... | Must | 8   | PARTIAL         | PARTIAL         | N/A             | PARTIAL         | PARTIAL         |
| VKT-045 | Sprint 3 | Billing            | Implement payment webhook handling                   | Must | 5   | COMPLETE        | COMPLETE        | N/A             | COMPLETE        | COMPLETE        |
| VKT-046 | Sprint 3 | Commission         | Implement commissionable revenue calculation         | Must | 5   | COMPLETE        | COMPLETE        | N/A             | N/A             | COMPLETE        |
| VKT-047 | Sprint 3 | Commission         | Implement independent commission holds               | Must | 5   | PARTIAL         | PARTIAL         | N/A             | N/A             | COMPLETE        |
| VKT-048 | Sprint 3 | Wallet             | Implement ledger entries and balance derivation      | Must | 8   | COMPLETE        | COMPLETE        | N/A             | N/A             | COMPLETE        |
| VKT-049 | Sprint 3 | Billing | Build Super Admin payments/invoices/reconciliatio... | Must | 5 | COMPLETE | COMPLETE | COMPLETE | N/A | PARTIAL |
| VKT-050 | Sprint 3 | Wallet/Payouts     | Build agency wallet and bucket visibility            | Must | 3   | COMPLETE        | COMPLETE        | COMPLETE        | N/A             | PARTIAL         |
| VKT-051 | Sprint 3 | Wallet/Payouts | Build Agency wallet summary and ledger | Must | 3 | PARTIAL | COMPLETE | PARTIAL | N/A | PARTIAL |
| VKT-052 | Sprint 3 | Wallet/Payouts     | Implement payout request validation and reservation  | Must | 5   | COMPLETE        | COMPLETE        | N/A             | N/A             | COMPLETE        |
| VKT-053 | Sprint 3 | Wallet/Payouts | Build payout review queue and detail | Must | 5 | COMPLETE | COMPLETE | COMPLETE | N/A | PARTIAL |
| VKT-054 | Sprint 3 | Wallet/Payouts     | Implement private proof upload and Paid transition   | Must | 5   | COMPLETE        | COMPLETE        | N/A             | N/A             | COMPLETE        |
| VKT-055 | Sprint 3 | Wallet/Payouts     | Generate agency-visible payout receipt               | Must | 3   | COMPLETE        | COMPLETE        | N/A             | N/A             | COMPLETE        |
| VKT-056 | Sprint 3 | Wallet/Payouts | Build agency payout history and receipt access | Must | 3 | PARTIAL | COMPLETE | PARTIAL | N/A | PARTIAL |
| VKT-057 | Sprint 3 | Billing/Commission | Implement commission reversal rules                  | Must | 8   | PARTIAL         | PARTIAL         | N/A             | PARTIAL         | COMPLETE        |
| VKT-058 | Sprint 3 | Risk               | Implement confirmed chargeback customer freeze an... | Must | 8   | COMPLETE        | COMPLETE        | N/A             | COMPLETE        | COMPLETE        |
| VKT-059 | Sprint 3 | Risk               | Implement agency fraud/risk actions                  | Must | 5   | PARTIAL         | PARTIAL         | PARTIAL         | N/A             | PARTIAL         |
| VKT-060 | Sprint 3 | Notifications      | Implement billing/wallet notification triggers       | Must | 3   | NOT_IMPLEMENTED | NOT_IMPLEMENTED | N/A             | N/A             | NOT_IMPLEMENTED |
| VKT-061 | Sprint 4 | Agents             | Build global agent directory and diagnostics entry   | Must | 3   | PARTIAL         | COMPLETE        | PARTIAL         | N/A             | PARTIAL         |
| VKT-062 | Sprint 4 | Agents             | Implement Super Admin agent lifecycle actions        | Must | 5   | PARTIAL         | PARTIAL         | PARTIAL         | N/A             | PARTIAL         |
| VKT-063 | Sprint 4 | Agents             | Build agency agent directory and creation entry      | Must | 3   | PARTIAL         | COMPLETE        | PARTIAL         | N/A             | PARTIAL         |
| VKT-064 | Sprint 4 | Agents             | Build Identity stage                                 | Must | 2   | PARTIAL         | PARTIAL         | PARTIAL         | N/A             | PARTIAL         |
| VKT-065 | Sprint 4 | Agents             | Build Voice & Language stage                         | Must | 3   | PARTIAL         | PARTIAL         | PARTIAL         | N/A             | PARTIAL         |
| VKT-066 | Sprint 4 | Agents             | Build Persona/Instructions stage                     | Must | 5   | PARTIAL         | PARTIAL         | PARTIAL         | N/A             | PARTIAL         |
| VKT-067 | Sprint 4 | Agents             | Build Knowledge attachment stage                     | Must | 3   | PARTIAL         | PARTIAL         | PARTIAL         | N/A             | PARTIAL         |
| VKT-068 | Sprint 4 | Agents             | Build Call Handling stage                            | Must | 3   | PARTIAL         | PARTIAL         | PARTIAL         | N/A             | PARTIAL         |
| VKT-069 | Sprint 4 | Agents             | Build Tools/Actions stage                            | Must | 3   | PARTIAL         | PARTIAL         | PARTIAL         | N/A             | PARTIAL         |
| VKT-070 | Sprint 4 | Instructions       | Implement deterministic instruction inheritance/r... | Must | 5   | COMPLETE        | COMPLETE        | N/A             | N/A             | COMPLETE        |
| VKT-071 | Sprint 4 | Instructions | Build global and template instruction management | Must | 3 | COMPLETE | COMPLETE | COMPLETE | N/A | PARTIAL |
| VKT-072 | Sprint 4 | Knowledge | Build global knowledge source management | Must | 3 | COMPLETE | COMPLETE | COMPLETE | N/A | PARTIAL |
| VKT-073 | Sprint 4 | Knowledge          | Build agency-wide and customer-specific knowledge... | Must | 5   | PARTIAL         | PARTIAL         | PARTIAL         | N/A             | PARTIAL         |
| VKT-074 | Sprint 4 | Knowledge          | Implement knowledge processing states and failure... | Must | 5   | NOT_IMPLEMENTED | NOT_IMPLEMENTED | N/A             | NOT_IMPLEMENTED | NOT_IMPLEMENTED |
| VKT-075 | Sprint 4 | Templates | Build template catalog management UI | Must | 3 | COMPLETE | COMPLETE | COMPLETE | N/A | PARTIAL |
| VKT-076 | Sprint 4 | Templates          | Implement template metadata, visibility and versi... | Must | 5   | PARTIAL         | PARTIAL         | PARTIAL         | N/A             | PARTIAL         |
| VKT-077 | Sprint 4 | Templates          | Implement independent editable template installation | Must | 3   | COMPLETE        | COMPLETE        | N/A             | N/A             | COMPLETE        |
| VKT-078 | Sprint 4 | Telephony          | Implement telephony provider abstraction             | Must | 5   | COMPLETE        | COMPLETE        | N/A             | PARTIAL         | PARTIAL         |
| VKT-079 | Sprint 4 | Phone Numbers | Build phone number search UI | Must | 3 | COMPLETE | COMPLETE | COMPLETE | PARTIAL | PARTIAL |
| VKT-080 | Sprint 4 | Phone Numbers      | Implement number purchase, assignment, release an... | Must | 8   | PARTIAL         | PARTIAL         | PARTIAL         | PARTIAL         | PARTIAL         |
| VKT-081 | Sprint 4 | Telephony          | Implement idempotent number purchase reconciliation  | Must | 3   | PARTIAL         | PARTIAL         | N/A             | PARTIAL         | PARTIAL         |
| VKT-082 | Sprint 4 | Transfers          | Build transfer destination/team management           | Must | 3   | PARTIAL         | PARTIAL         | PARTIAL         | N/A             | PARTIAL         |
| VKT-083 | Sprint 4 | Transfers          | Build transfer rules                                 | Must | 3   | NOT_IMPLEMENTED | NOT_IMPLEMENTED | NOT_IMPLEMENTED | N/A             | NOT_IMPLEMENTED |
| VKT-084 | Sprint 4 | Agents             | Build integration/action mapping stage               | Must | 3   | NOT_IMPLEMENTED | PARTIAL         | NOT_IMPLEMENTED | N/A             | PARTIAL         |
| VKT-085 | Sprint 4 | Agents             | Build Transfers, Phone Number and Compliance stages  | Must | 5   | PARTIAL         | PARTIAL         | PARTIAL         | N/A             | PARTIAL         |
| VKT-086 | Sprint 4 | Integrations       | Implement integration ownership/OAuth/credential ... | Must | 5   | PARTIAL         | PARTIAL         | N/A             | PARTIAL         | PARTIAL         |
| VKT-087 | Sprint 4 | Integrations       | Build integrations UI                                | Must | 5   | PARTIAL         | PARTIAL         | PARTIAL         | N/A             | PARTIAL         |
| VKT-088 | Sprint 4 | Integrations       | Implement normalized action execution                | Must | 8   | COMPLETE        | COMPLETE        | N/A             | PARTIAL         | COMPLETE        |
| VKT-089 | Sprint 4 | Webhooks           | Build webhook endpoint management                    | Must | 5   | PARTIAL         | COMPLETE        | PARTIAL         | N/A             | PARTIAL         |
| VKT-090 | Sprint 4 | Webhooks           | Implement signed webhook delivery                    | Must | 8   | COMPLETE        | COMPLETE        | N/A             | COMPLETE        | COMPLETE        |
| VKT-091 | Sprint 5 | Agents | Build browser/simulator test screen | Must | 5 | PARTIAL | PARTIAL | NOT_IMPLEMENTED | N/A | PARTIAL |
| VKT-092 | Sprint 5 | Agents             | Implement agent publish validation                   | Must | 5   | COMPLETE        | COMPLETE        | N/A             | N/A             | COMPLETE        |
| VKT-093 | Sprint 5 | Agents             | Build publish, activate, pause and clone actions     | Must | 3   | PARTIAL         | PARTIAL         | PARTIAL         | N/A             | PARTIAL         |
| VKT-094 | Sprint 5 | Calls              | Implement call ingestion and lifecycle persistence   | Must | 8   | COMPLETE        | COMPLETE        | N/A             | COMPLETE        | COMPLETE        |
| VKT-095 | Sprint 5 | Calls              | Implement inbound routing to assigned agent/fallback | Must | 8   | COMPLETE        | COMPLETE        | N/A             | COMPLETE        | COMPLETE        |
| VKT-096 | Sprint 5 | Calls              | Implement outbound calling/caller ID where enabled   | Must | 5   | PARTIAL         | PARTIAL         | N/A             | PARTIAL         | PARTIAL         |
| VKT-097 | Sprint 5 | Calls              | Implement billable usage and entitlement linkage     | Must | 8   | COMPLETE        | COMPLETE        | N/A             | N/A             | COMPLETE        |
| VKT-098 | Sprint 5 | Calls              | Implement recording/transcript/summary artifact s... | Must | 8   | COMPLETE        | COMPLETE        | N/A             | PARTIAL         | COMPLETE        |
| VKT-099 | Sprint 5 | Transfers          | Implement transfer execution and call linkage        | Must | 5   | PARTIAL         | COMPLETE        | N/A             | PARTIAL         | COMPLETE        |
| VKT-100 | Sprint 5 | Calls | Build Super Admin call monitoring | Must | 5 | COMPLETE | COMPLETE | COMPLETE | N/A | PARTIAL |
| VKT-101 | Sprint 5 | Calls              | Build agency call monitoring                         | Must | 3   | PARTIAL         | PARTIAL         | PARTIAL         | N/A             | PARTIAL         |
| VKT-102 | Sprint 5 | Portal Shell       | Build Customer Portal shell                          | Must | 3   | COMPLETE        | N/A             | COMPLETE        | N/A             | N/A             |
| VKT-103 | Sprint 5 | Dashboard          | Build Customer dashboard                             | Must | 5   | PARTIAL         | PARTIAL         | PARTIAL         | N/A             | PARTIAL         |
| VKT-104 | Sprint 5 | Agents             | Build customer agent monitoring                      | Must | 3   | PARTIAL         | PARTIAL         | PARTIAL         | N/A             | PARTIAL         |
| VKT-105 | Sprint 5 | Calls              | Build customer call history and artifacts            | Must | 5   | PARTIAL         | PARTIAL         | PARTIAL         | N/A             | PARTIAL         |
| VKT-106 | Sprint 5 | Usage | Build customer usage and top-up screen | Must | 5 | PARTIAL | COMPLETE | PARTIAL | N/A | PARTIAL |
| VKT-107 | Sprint 5 | Billing | Build customer invoices and payment UI | Must | 5 | PARTIAL | COMPLETE | PARTIAL | N/A | PARTIAL |
| VKT-108 | Sprint 5 | Knowledge          | Build customer knowledge view/edit where granted     | Must | 3   | PARTIAL         | PARTIAL         | PARTIAL         | N/A             | PARTIAL         |
| VKT-109 | Sprint 5 | Integrations       | Build customer integration visibility and permitt... | Must | 3   | PARTIAL         | PARTIAL         | PARTIAL         | N/A             | PARTIAL         |
| VKT-110 | Sprint 5 | Team/Settings      | Build customer team, notifications and profile se... | Must | 3   | PARTIAL         | PARTIAL         | PARTIAL         | N/A             | PARTIAL         |
| VKT-111 | Sprint 5 | Team/Settings      | Build agency team, notification and security sett... | Must | 5   | PARTIAL         | PARTIAL         | PARTIAL         | N/A             | PARTIAL         |
| VKT-112 | Sprint 5 | Users/Roles | Build Super Admin user and role management | Must | 5 | COMPLETE | COMPLETE | COMPLETE | N/A | PARTIAL |
| VKT-113 | Sprint 5 | Notifications      | Complete notification preference and template engine | Must | 5   | PARTIAL         | PARTIAL         | PARTIAL         | N/A             | PARTIAL         |
| VKT-114 | Sprint 5 | Notifications | Build Super Admin notification administration | Must | 3 | COMPLETE | COMPLETE | COMPLETE | N/A | PARTIAL |
| VKT-115 | Sprint 6 | Integrations | Build provider registry and tenant connection vis... | Must | 3 | COMPLETE | COMPLETE | COMPLETE | PARTIAL | PARTIAL |
| VKT-116 | Sprint 6 | Webhooks | Build webhook delivery log and replay UI | Must | 3 | PARTIAL | COMPLETE | NOT_IMPLEMENTED | N/A | PARTIAL |
| VKT-117 | Sprint 6 | Transfers | Build transfer monitoring | Must | 3 | COMPLETE | COMPLETE | COMPLETE | PARTIAL | PARTIAL |
| VKT-118 | Sprint 6 | Audit | Build immutable audit log search/detail | Must | 3 | COMPLETE | COMPLETE | COMPLETE | N/A | PARTIAL |
| VKT-119 | Sprint 6 | Overrides          | Implement Super Admin override workflow              | Must | 5   | PARTIAL         | PARTIAL         | PARTIAL         | N/A             | PARTIAL         |
| VKT-120 | Sprint 6 | Settings | Build platform settings UI | Must | 5 | COMPLETE | COMPLETE | COMPLETE | N/A | PARTIAL |
| VKT-121 | Sprint 6 | Settings           | Implement centralized configurable business rules    | Must | 5   | PARTIAL         | PARTIAL         | N/A             | N/A             | PARTIAL         |
| VKT-122 | Sprint 6 | Privacy            | Implement configurable retention and deletion-req... | Must | 5   | PARTIAL         | PARTIAL         | N/A             | PARTIAL         | PARTIAL         |
| VKT-123 | Sprint 6 | Privacy            | Implement authorized tenant data export              | Must | 3   | NOT_IMPLEMENTED | NOT_IMPLEMENTED | N/A             | NOT_IMPLEMENTED | NOT_IMPLEMENTED |
| VKT-124 | Sprint 6 | Reporting          | Build platform operational/financial reporting       | Must | 5   | PARTIAL         | PARTIAL         | PARTIAL         | N/A             | PARTIAL         |
| VKT-125 | Sprint 6 | Reporting          | Complete agency KPI/report data layer                | Must | 3   | PARTIAL         | PARTIAL         | PARTIAL         | N/A             | PARTIAL         |
| VKT-126 | Sprint 6 | Reporting          | Complete customer KPI/report data layer              | Must | 3   | PARTIAL         | PARTIAL         | PARTIAL         | N/A             | PARTIAL         |
| VKT-127 | Sprint 6 | Observability      | Implement structured logs, metrics, traces and co... | Must | 5   | PARTIAL         | PARTIAL         | N/A             | NOT_IMPLEMENTED | PARTIAL         |
| VKT-128 | Sprint 6 | Reliability        | Implement automated backups and recovery test        | Must | 3   | PARTIAL         | COMPLETE        | N/A             | PARTIAL         | COMPLETE        |
| VKT-129 | Sprint 6 | Automated Tests    | Automate commission/wallet/payout state transitio... | Must | 8   | COMPLETE        | COMPLETE        | N/A             | N/A             | COMPLETE        |
| VKT-130 | Sprint 6 | Automated Tests    | Automate cross-tenant authorization tests            | Must | 8   | COMPLETE        | COMPLETE        | N/A             | N/A             | COMPLETE        |
| VKT-131 | Sprint 6 | Automated Tests    | Automate payment/webhook/payout/number idempotenc... | Must | 8   | PARTIAL         | PARTIAL         | N/A             | N/A             | PARTIAL         |
| VKT-132 | Sprint 6 | Security           | Run security checks for auth/RBAC/secrets/webhook... | Must | 8   | PARTIAL         | PARTIAL         | N/A             | N/A             | PARTIAL         |
| VKT-133 | Sprint 7 | UI Completion      | Complete dashboard filter and drilldown behavior     | Must | 2   | PARTIAL         | PARTIAL         | PARTIAL         | N/A             | PARTIAL         |
| VKT-134 | Sprint 7 | UI Completion | Complete Super Admin screens and permission-aware... | Must | 5 | PARTIAL | PARTIAL | PARTIAL | N/A | N/A |
| VKT-135 | Sprint 7 | UI Completion      | Complete Agency portal screens and state/permissi... | Must | 5   | PARTIAL         | PARTIAL         | PARTIAL         | N/A             | N/A             |
| VKT-136 | Sprint 7 | UI Completion      | Complete Customer portal screens and customer-sco... | Must | 5   | PARTIAL         | PARTIAL         | PARTIAL         | N/A             | N/A             |
| VKT-137 | Sprint 7 | Edge Cases         | Verify payment and commission edge cases             | Must | 5   | PARTIAL         | PARTIAL         | N/A             | N/A             | PARTIAL         |
| VKT-138 | Sprint 7 | Edge Cases         | Verify payout and risk edge cases                    | Must | 5   | PARTIAL         | PARTIAL         | N/A             | N/A             | PARTIAL         |
| VKT-139 | Sprint 7 | Edge Cases         | Verify number/call/agent failure behavior            | Must | 5   | PARTIAL         | PARTIAL         | N/A             | N/A             | PARTIAL         |
| VKT-140 | Sprint 7 | Risk               | Run confirmed chargeback shutdown and re-onboardi... | Must | 8   | PARTIAL         | COMPLETE        | N/A             | N/A             | COMPLETE        |
| VKT-141 | Sprint 7 | E2E                | Run complete agency lifecycle acceptance test        | Must | 5   | PARTIAL         | PARTIAL         | PARTIAL         | N/A             | PARTIAL         |
| VKT-142 | Sprint 7 | E2E                | Run customer commercial flow acceptance test         | Must | 8   | PARTIAL         | PARTIAL         | PARTIAL         | N/A             | PARTIAL         |
| VKT-143 | Sprint 7 | E2E                | Run telephony production-path acceptance test        | Must | 8   | PARTIAL         | PARTIAL         | N/A             | PARTIAL         | PARTIAL         |
| VKT-144 | Sprint 7 | E2E                | Run tools, integration and human handoff acceptan... | Must | 5   | PARTIAL         | PARTIAL         | N/A             | PARTIAL         | PARTIAL         |
| VKT-145 | Sprint 7 | E2E                | Verify customer portal scope and permitted functions | Must | 5   | PARTIAL         | PARTIAL         | PARTIAL         | N/A             | PARTIAL         |
| VKT-146 | Sprint 7 | E2E                | Run payout request-to-receipt acceptance test        | Must | 8   | PARTIAL         | COMPLETE        | PARTIAL         | N/A             | COMPLETE        |
| VKT-147 | Sprint 7 | Release            | Execute requirement-by-requirement Must regression   | Must | 8   | PARTIAL         | PARTIAL         | N/A             | N/A             | PARTIAL         |
| VKT-148 | Sprint 7 | Release            | Verify SRS functional and engineering/QA release ... | Must | 5   | PARTIAL         | PARTIAL         | N/A             | PARTIAL         | PARTIAL         |
| VKT-149 | Sprint 7 | Release            | Prepare production configuration and operational ... | Must | 5   | PARTIAL         | PARTIAL         | N/A             | PARTIAL         | N/A             |
| VKT-150 | Sprint 7 | Release            | Deploy V1 and validate critical production paths     | Must | 5   | PARTIAL         | PARTIAL         | N/A             | NOT_IMPLEMENTED | PARTIAL         |
| VKT-151 | Sprint 7 | Release            | Close release with explicit V1 boundary              | Must | 2   | PARTIAL         | N/A             | N/A             | N/A             | N/A             |




### Quick status index

Same 151 tasks, grouped by overall status for scanning (after frontend re-audit):

**COMPLETE** (55)

VKT-002, VKT-006, VKT-011, VKT-013, VKT-016, VKT-018, VKT-019, VKT-020, VKT-022, VKT-023, VKT-025, VKT-026
VKT-027, VKT-029, VKT-030, VKT-031, VKT-032, VKT-035, VKT-036, VKT-040, VKT-042, VKT-045, VKT-046, VKT-048
VKT-049, VKT-050, VKT-052, VKT-053, VKT-054, VKT-055, VKT-058, VKT-070, VKT-071, VKT-072, VKT-075, VKT-077
VKT-078, VKT-079, VKT-088, VKT-090, VKT-092, VKT-094, VKT-095, VKT-097, VKT-098, VKT-100, VKT-102, VKT-112
VKT-114, VKT-115, VKT-117, VKT-118, VKT-120, VKT-129, VKT-130

**PARTIAL** (89)

VKT-001, VKT-003, VKT-004, VKT-005, VKT-007, VKT-008, VKT-009, VKT-010, VKT-012, VKT-014, VKT-015, VKT-017
VKT-021, VKT-024, VKT-033, VKT-034, VKT-037, VKT-038, VKT-039, VKT-043, VKT-044, VKT-047, VKT-051, VKT-056
VKT-057, VKT-059, VKT-061, VKT-062, VKT-063, VKT-064, VKT-065, VKT-066, VKT-067, VKT-068, VKT-069, VKT-073
VKT-076, VKT-080, VKT-081, VKT-082, VKT-085, VKT-086, VKT-087, VKT-089, VKT-091, VKT-093, VKT-096, VKT-099
VKT-101, VKT-103, VKT-104, VKT-105, VKT-106, VKT-107, VKT-108, VKT-109, VKT-110, VKT-111, VKT-113, VKT-116
VKT-119, VKT-121, VKT-122, VKT-124, VKT-125, VKT-126, VKT-127, VKT-128, VKT-131, VKT-132, VKT-133, VKT-134
VKT-135, VKT-136, VKT-137, VKT-138, VKT-139, VKT-140, VKT-141, VKT-142, VKT-143, VKT-144, VKT-145, VKT-146
VKT-147, VKT-148, VKT-149, VKT-150, VKT-151

**NOT_IMPLEMENTED** (7)

VKT-028, VKT-041, VKT-060, VKT-074, VKT-083, VKT-084, VKT-123

**BLOCKED** (0)

_None._

**NEEDS_MANUAL_REVIEW** (0)

_None._

## Detailed Task Records

Each of the following sections is an individual audit record. Do not collapse these when using this document as the implementation baseline.

# VKT-001 — Baseline implementation traceability



## Jira Definition

**Sprint:** Sprint 1  
**Portal / Layer:** Platform  
**Epic:** Foundation  
**Module:** Architecture  
**Priority:** Must  
**Story Points:** 2  
**Estimated Hours:** 3  
**Dependencies:** None  
**Dependency Category:** BLOCKING  
**Flow:** SRS -> Jira Epic/Task -> API -> UI -> QA acceptance criterion.  

### Definition of Done

Create the implementation traceability matrix from every SRS module, requirement ID, state machine, event and release gate to Jira epics/tasks. Treat SRS business rules and state machines as authoritative.

### SRS Traceability

- **SRS Traceability (from XLS):** SRS §Document Governance; §31
- **Business rules / state machines / events / acceptance / gates:** Interpreted only from the XLS SRS column and matching SRS sections; see SRS document for full text. Do not invent IDs beyond the XLS column.



### Current Implementation Status

**Overall:** PARTIAL

**Backend:** PARTIAL  
**UI:** N/A  
**Infrastructure/Integration:** N/A  
**Tests:** PARTIAL  

**Note:** Traceability exists fragmented; not a single maintained matrix before this audit.

### What Already Exists

- docs/execution/12-FEATURE-MATRIX.md maps SRS families to modules/phases
- XLS Full Task Register has SRS Traceability column for VKT-001..151
- This audit document begins formal task-level matrix



### What Is Missing

- Living matrix linking every SRS ID → Jira → API → UI → QA acceptance artifact in repo
- Automated requirement coverage dashboard



### What Is Partial

*N/A or covered under Missing/Exists.*

### Codebase Evidence

- docs/execution/12-FEATURE-MATRIX.md
- docs/Vokit_V1_7-Day_Jira_Sprint_Plan.xlsx — Full Task Register
- docs/Vokit_V1_Implementation_Status_Audit.md (this file)



### Dependency Verification

No Jira dependencies. Task can be evaluated independently.

### Acceptance / QA Coverage

Some automated tests exist; gaps remain relative to full DoD/acceptance (see Missing/Remaining).

### Required Remaining Work

- Maintain this audit as the SRS↔VKT↔code↔test matrix
- Optionally export CSV for Jira status sync



### Audit Conclusion

VKT-001 is **PARTIAL**. Keep existing evidence; finish only the listed remaining work.

---



# VKT-002 — Define tenant ownership model



## Jira Definition

**Sprint:** Sprint 1  
**Portal / Layer:** Platform  
**Epic:** Foundation  
**Module:** Domain model  
**Priority:** Must  
**Story Points:** 5  
**Estimated Hours:** 6  
**Dependencies:** None  
**Dependency Category:** BLOCKING  
**Flow:** Platform -> Agency -> Customer -> Agent; Financial transaction links platform/agency/customer.  

### Definition of Done

Define platform/agency/customer/agent/financial ownership relationships and enforce the rule that customer-owned objects retain both customer and agency ownership where required.

### SRS Traceability

- **SRS Traceability (from XLS):** TEN-001..006; §23
- **Business rules / state machines / events / acceptance / gates:** Interpreted only from the XLS SRS column and matching SRS sections; see SRS document for full text. Do not invent IDs beyond the XLS column.



### Current Implementation Status

**Overall:** COMPLETE

**Backend:** COMPLETE  
**UI:** N/A  
**Infrastructure/Integration:** COMPLETE  
**Tests:** COMPLETE  

### What Already Exists

- Platform→Agency→Customer→Agent ownership enforced server-side
- Customer objects carry tenant_id + customer_id
- Fail-closed tenant routing



### What Is Missing

*Nothing material missing relative to DoD (COMPLETE).* 

### What Is Partial

*N/A or covered under Missing/Exists.*

### Codebase Evidence

- apps/api/control_plane/tenancy/domain/policies.py — resolve_route_tenant_id, assert_tenant_is_routable
- apps/api/tenant/runtime/router.py — TenantRouter.connection_for_tenant
- apps/api/tenant/agents/domain.py — TenantAgent.tenant_id+customer_id
- apps/api/tests/test_tenant_routing.py



### Dependency Verification

No Jira dependencies. Task can be evaluated independently.

### Acceptance / QA Coverage

Automated tests covering the core DoD behaviors were found (see Evidence).

### Required Remaining Work

- None for DoD; keep regression tests green



### Audit Conclusion

VKT-002 is **COMPLETE** against repository evidence. **DO NOT REIMPLEMENT.** Only perform verification/QA if required for release.

---



# VKT-003 — Create core identity and tenancy tables



## Jira Definition

**Sprint:** Sprint 1  
**Portal / Layer:** Platform  
**Epic:** Foundation  
**Module:** Database  
**Priority:** Must  
**Story Points:** 5  
**Estimated Hours:** 7  
**Dependencies:** VKT-002  
**Dependency Category:** BLOCKING  
**Flow:** Create tenant -> assign owner -> assign scoped role -> persist status/ownership.  

### Definition of Done

Implement Agency, Customer, User and Role persistence with status fields and scope boundaries. Do not allow financial/KYC/audit records to be hard-deleted through normal flows.

### SRS Traceability

- **SRS Traceability (from XLS):** §23; TEN-001..006; RBAC-001..006
- **Business rules / state machines / events / acceptance / gates:** Interpreted only from the XLS SRS column and matching SRS sections; see SRS document for full text. Do not invent IDs beyond the XLS column.



### Current Implementation Status

**Overall:** PARTIAL

**Backend:** PARTIAL  
**UI:** N/A  
**Infrastructure/Integration:** N/A  
**Tests:** PARTIAL  

### What Already Exists

- Agency/Tenant, Customer, User, Membership models with status fields
- Financial/KYC/audit immutability guards on audit + ledger patterns



### What Is Missing

- Dedicated Role ORM table — roles are catalog in identity/domain/roles.py
- Explicit hard-delete prevention tests for all financial/KYC entity types



### What Is Partial

*N/A or covered under Missing/Exists.*

### Codebase Evidence

- apps/api/control_plane/tenancy/models.py — Tenant
- apps/api/control_plane/identity/models.py — User, Membership
- apps/api/control_plane/customers/models.py — CustomerIndex
- apps/api/control_plane/identity/domain/roles.py — PLATFORM/AGENCY/CUSTOMER_PERMISSIONS
- apps/api/control_plane/audit/models.py — AuditEvent.assert_immutable



### Dependency Verification

**Jira Dependencies:** VKT-002

**Dependency Status:**

- VKT-002 = COMPLETE

Dependencies are COMPLETE or do not block evaluating this task's own gaps.

### Acceptance / QA Coverage

Some automated tests exist; gaps remain relative to full DoD/acceptance (see Missing/Remaining).

### Required Remaining Work

- Document Role-as-catalog as intentional OR add Role table if product requires DB roles
- Add hard-delete denial tests for ledger/KYC/payment rows



### Audit Conclusion

VKT-003 is **PARTIAL**. Keep existing evidence; finish only the listed remaining work.

---



# VKT-004 — Create commercial and financial tables



## Jira Definition

**Sprint:** Sprint 1  
**Portal / Layer:** Platform  
**Epic:** Foundation  
**Module:** Database  
**Priority:** Must  
**Story Points:** 8  
**Estimated Hours:** 8  
**Dependencies:** VKT-002  
**Dependency Category:** BLOCKING  
**Flow:** Plan -> Subscription -> Invoice -> Payment -> Commission -> Ledger -> Payout.  

### Definition of Done

Implement Plan/version, Subscription, Invoice, Payment, CommissionEntry, WalletLedgerEntry, Payout and PayoutProof persistence with immutable/version-aware fields.

### SRS Traceability

- **SRS Traceability (from XLS):** PLAN-001..007; WAL-001..007; §23
- **Business rules / state machines / events / acceptance / gates:** Interpreted only from the XLS SRS column and matching SRS sections; see SRS document for full text. Do not invent IDs beyond the XLS column.



### Current Implementation Status

**Overall:** PARTIAL

**Backend:** PARTIAL  
**UI:** N/A  
**Infrastructure/Integration:** N/A  
**Tests:** COMPLETE  

**Note:** Architecture uses ledger-centric commission (SRS-aligned) rather than separate CommissionEntry entity.

### What Already Exists

- Plan, PlanVersion, Subscription, Invoice, Payment, LedgerEntry, Payout, PayoutProof models
- Commission captured as ledger entries with snapshots (not separate CommissionEntry table name)



### What Is Missing

- Named CommissionEntry table — commission is LedgerEntry kinds with snapshots
- Full immutability enforcement on all commercial tables beyond ledger/audit



### What Is Partial

*N/A or covered under Missing/Exists.*

### Codebase Evidence

- apps/api/control_plane/billing/models.py
- apps/api/control_plane/commission/models.py — LedgerEntry, Payout, PayoutProof
- apps/api/tests/test_appendix_c.py
- apps/api/tests/test_billing_domain.py



### Dependency Verification

**Jira Dependencies:** VKT-002

**Dependency Status:**

- VKT-002 = COMPLETE

Dependencies are COMPLETE or do not block evaluating this task's own gaps.

### Acceptance / QA Coverage

Automated tests covering the core DoD behaviors were found (see Evidence).

### Required Remaining Work

- Accept LedgerEntry as CommissionEntry SoT in docs/Jira OR rename for clarity
- Audit which commercial rows allow unsafe delete



### Audit Conclusion

VKT-004 is **PARTIAL**. Keep existing evidence; finish only the listed remaining work.

---



# VKT-005 — Create AI/telephony/integration tables



## Jira Definition

**Sprint:** Sprint 1  
**Portal / Layer:** Platform  
**Epic:** Foundation  
**Module:** Database  
**Priority:** Must  
**Story Points:** 8  
**Estimated Hours:** 8  
**Dependencies:** VKT-002  
**Dependency Category:** BLOCKING  
**Flow:** Customer -> Agent -> Number/Knowledge/Action/Integration -> Call/Artifacts.  

### Definition of Done

Implement Agent, AgentTemplate, KnowledgeSource, PhoneNumber, Call, CallArtifact, IntegrationConnection, AgentAction, WebhookEndpoint and WebhookDelivery persistence.

### SRS Traceability

- **SRS Traceability (from XLS):** §23; AGT-001..008; TEL-001..010; INT-001..008; WH-001..008
- **Business rules / state machines / events / acceptance / gates:** Interpreted only from the XLS SRS column and matching SRS sections; see SRS document for full text. Do not invent IDs beyond the XLS column.



### Current Implementation Status

**Overall:** PARTIAL

**Backend:** PARTIAL  
**UI:** N/A  
**Infrastructure/Integration:** N/A  
**Tests:** PARTIAL  

### What Already Exists

- Agent, templates, knowledge, PhoneNumber, Call indexes, IntegrationConnection, WebhookEndpoint/Delivery, recording artifacts



### What Is Missing

- AgentAction as first-class persistence table — actions are allowlisted tools + integration invoke path
- Full CallArtifact unified model naming vs recordings module split



### What Is Partial

*N/A or covered under Missing/Exists.*

### Codebase Evidence

- apps/api/control_plane/agents/models.py
- apps/api/control_plane/telephony/models.py
- apps/api/control_plane/integrations/models.py
- apps/api/control_plane/recordings/



### Dependency Verification

**Jira Dependencies:** VKT-002

**Dependency Status:**

- VKT-002 = COMPLETE

Dependencies are COMPLETE or do not block evaluating this task's own gaps.

### Acceptance / QA Coverage

Some automated tests exist; gaps remain relative to full DoD/acceptance (see Missing/Remaining).

### Required Remaining Work

- Map AgentAction DoD to tool allowlist + integration action categories in docs
- Confirm artifact persistence covers transcript/summary as required



### Audit Conclusion

VKT-005 is **PARTIAL**. Keep existing evidence; finish only the listed remaining work.

---



# VKT-006 — Create notification and audit tables



## Jira Definition

**Sprint:** Sprint 1  
**Portal / Layer:** Platform  
**Epic:** Foundation  
**Module:** Database  
**Priority:** Must  
**Story Points:** 3  
**Estimated Hours:** 5  
**Dependencies:** VKT-003  
**Dependency Category:** BLOCKING  
**Flow:** Business event -> notification/audit consumers; audit cannot be edited/deleted by ordinary UI.  

### Definition of Done

Implement Notification and immutable AuditEvent storage with actor, role, tenant, action, entity, timestamp, correlation/request ID and sensitive-field redaction.

### SRS Traceability

- **SRS Traceability (from XLS):** NOT-001..005; AUD-001..005
- **Business rules / state machines / events / acceptance / gates:** Interpreted only from the XLS SRS column and matching SRS sections; see SRS document for full text. Do not invent IDs beyond the XLS column.



### Current Implementation Status

**Overall:** COMPLETE

**Backend:** COMPLETE  
**UI:** N/A  
**Infrastructure/Integration:** N/A  
**Tests:** COMPLETE  

### What Already Exists

- InAppNotification, NotificationDelivery, NotificationTemplate
- Immutable AuditEvent append-only



### What Is Missing

*Nothing material missing relative to DoD (COMPLETE).* 

### What Is Partial

*N/A or covered under Missing/Exists.*

### Codebase Evidence

- apps/api/control_plane/notifications/models.py
- apps/api/control_plane/audit/models.py
- apps/api/tests/test_notifications_domain.py
- apps/api/tests/test_audit_domain.py



### Dependency Verification

**Jira Dependencies:** VKT-003

**Dependency Status:**

- VKT-003 = PARTIAL

Dependencies are COMPLETE or do not block evaluating this task's own gaps.

### Acceptance / QA Coverage

Automated tests covering the core DoD behaviors were found (see Evidence).

### Required Remaining Work

- None for table DoD



### Audit Conclusion

VKT-006 is **COMPLETE** against repository evidence. **DO NOT REIMPLEMENT.** Only perform verification/QA if required for release.

---



# VKT-007 — Implement secure authentication/session foundation



## Jira Definition

**Sprint:** Sprint 1  
**Portal / Layer:** Platform  
**Epic:** Foundation  
**Module:** Authentication  
**Priority:** Must  
**Story Points:** 5  
**Estimated Hours:** 8  
**Dependencies:** None  
**Dependency Category:** BLOCKING  
**Flow:** Login -> authenticated session -> scoped portal -> logout/disable invalidates session.  

### Definition of Done

Implement secure authentication for all three portals, secure session handling, logout, session invalidation and server-side authorization hooks. Support MFA capability for privileged roles where enabled.

### SRS Traceability

- **SRS Traceability (from XLS):** SEC-001, SEC-006, RBAC-007..008
- **Business rules / state machines / events / acceptance / gates:** Interpreted only from the XLS SRS column and matching SRS sections; see SRS document for full text. Do not invent IDs beyond the XLS column.



### Current Implementation Status

**Overall:** PARTIAL

**Backend:** PARTIAL  
**UI:** PARTIAL  
**Infrastructure/Integration:** N/A  
**Tests:** PARTIAL  

### What Already Exists

- Login/logout/session, CSRF endpoint, login rate limit, UserSession
- Login UI



### What Is Missing

- MFA enrollment/TOTP for privileged users (policy flag only)
- Invite acceptance UI (API exists separately)



### What Is Partial

*N/A or covered under Missing/Exists.*

### Codebase Evidence

- apps/api/control_plane/identity/api/views.py — LoginView, SessionView, CsrfView
- apps/api/control_plane/identity/infrastructure/rate_limit.py
- apps/api/control_plane/identity/domain/policies.py — assert_privileged_mfa
- packages/web-ui/src/features/auth/components/LoginScreen.tsx
- docs/execution/24-PHASE-17-SECURITY-REVIEW.md



### Dependency Verification

No Jira dependencies. Task can be evaluated independently.

### Acceptance / QA Coverage

Some automated tests exist; gaps remain relative to full DoD/acceptance (see Missing/Remaining).

### Required Remaining Work

- Implement MFA enrollment + challenge for privileged roles
- Keep CSRF/session hardening verified in staging



### Audit Conclusion

VKT-007 is **PARTIAL**. Keep existing evidence; finish only the listed remaining work.

---



# VKT-008 — Implement server-side RBAC and tenant guards



## Jira Definition

**Sprint:** Sprint 1  
**Portal / Layer:** Platform  
**Epic:** Foundation  
**Module:** Authorization  
**Priority:** Must  
**Story Points:** 8  
**Estimated Hours:** 8  
**Dependencies:** VKT-003, VKT-007  
**Dependency Category:** BLOCKING  
**Flow:** Request -> authenticate -> resolve scope -> authorize -> execute/deny.  

### Definition of Done

Every protected request must check role permissions and tenant ownership server-side. Agency roles cannot gain platform permissions; customer roles cannot gain agency permissions.

### SRS Traceability

- **SRS Traceability (from XLS):** TEN-001..005; SEC-002; RBAC-002..006
- **Business rules / state machines / events / acceptance / gates:** Interpreted only from the XLS SRS column and matching SRS sections; see SRS document for full text. Do not invent IDs beyond the XLS column.



### Current Implementation Status

**Overall:** COMPLETE

**Backend:** COMPLETE  
**UI:** N/A (FE integrates later via docs/flows/RBAC-ROLES-PERMISSIONS.md)  
**Infrastructure/Integration:** N/A  
**Tests:** COMPLETE  

### What Already Exists

- Distinct PLATFORM/AGENCY/CUSTOMER permission namespaces (DB-backed, ADR-007)
- Centralized `require_platform_perm` / `require_agency_perm` / `require_customer_perm` with `super_admin` bypass
- Tenant/customer scope binding from membership
- Dynamic roles + role_permissions + additive permission sync (command + API)
- Platform role CRUD APIs; agency/customer read-only role lists
- Negative tests: `apps/api/tests/test_rbac_api.py`



### What Is Missing

*None for VKT-008 DoD. Frontend role UI is deferred (flow doc only).*



### What Is Partial

*N/A*

### Codebase Evidence

- docs/adr/ADR-007-dynamic-rbac-roles-permissions.md
- apps/api/control_plane/identity/domain/permission_catalog.py
- apps/api/control_plane/identity/api/auth.py
- apps/api/control_plane/identity/api/rbac_views.py
- apps/api/tests/test_rbac_api.py
- docs/flows/RBAC-ROLES-PERMISSIONS.md



### Dependency Verification

**Jira Dependencies:** VKT-003, VKT-007

**Dependency Status:**

- VKT-003 = PARTIAL
- VKT-007 = PARTIAL

Remaining work may still depend on: VKT-003, VKT-007.

### Acceptance / QA Coverage

Automated RBAC + identity + regression suites cover permission checks, namespace isolation, sync additive behavior, and super_admin bypass.

### Required Remaining Work

*None for VKT-008.*

### Audit Conclusion

VKT-008 is **COMPLETE** (backend). Frontend catalog hardcoding removal is tracked via the flow doc, not this ticket’s DoD.

---



# VKT-009 — Implement input validation and security middleware



## Jira Definition

**Sprint:** Sprint 1  
**Portal / Layer:** Platform  
**Epic:** Foundation  
**Module:** Security  
**Priority:** Must  
**Story Points:** 5  
**Estimated Hours:** 7  
**Dependencies:** VKT-007, VKT-008  
**Dependency Category:** BLOCKING  
**Flow:** External input -> validation -> normalized domain value -> service; rejected input returns stable error.  

### Definition of Done

Normalize/validate URLs, phone numbers, webhook payloads and external inputs; add CSRF protection, rate limits and secure transport/session configuration.

### SRS Traceability

- **SRS Traceability (from XLS):** SEC-005..010
- **Business rules / state machines / events / acceptance / gates:** Interpreted only from the XLS SRS column and matching SRS sections; see SRS document for full text. Do not invent IDs beyond the XLS column.



### Current Implementation Status

**Overall:** PARTIAL

**Backend:** PARTIAL  
**UI:** N/A  
**Infrastructure/Integration:** PARTIAL  
**Tests:** PARTIAL  

### What Already Exists

- CSRF for state-changing browser APIs
- Login rate limiting
- Input validation at API serializers/views
- Production hardening settings



### What Is Missing

- Dedicated rate limits for payout, webhook replay, uploads as first-class middleware
- Malware scanning for uploads



### What Is Partial

*N/A or covered under Missing/Exists.*

### Codebase Evidence

- apps/api/config/settings/hardening.py
- apps/api/control_plane/identity/infrastructure/rate_limit.py
- apps/api/shared_kernel/http/exceptions.py — csrf_failure



### Dependency Verification

**Jira Dependencies:** VKT-007, VKT-008

**Dependency Status:**

- VKT-007 = PARTIAL
- VKT-008 = PARTIAL

Remaining work may still depend on: VKT-007, VKT-008.

### Acceptance / QA Coverage

Some automated tests exist; gaps remain relative to full DoD/acceptance (see Missing/Remaining).

### Required Remaining Work

- Add rate-limit policies for payout/upload/webhook-replay
- Document validation matrix per high-risk endpoint



### Audit Conclusion

VKT-009 is **PARTIAL**. Keep existing evidence; finish only the listed remaining work.

---



# VKT-010 — Implement server-side secret management



## Jira Definition

**Sprint:** Sprint 1  
**Portal / Layer:** Platform  
**Epic:** Foundation  
**Module:** Secrets  
**Priority:** Must  
**Story Points:** 3  
**Estimated Hours:** 5  
**Dependencies:** VKT-009  
**Dependency Category:** BLOCKING  
**Flow:** Credential entry -> encrypted secret reference -> provider adapter; never return secret.  

### Definition of Done

Store payment, telephony, AI, OAuth refresh and webhook signing secrets encrypted/secret-managed; never expose them to client code, prompts, transcripts or logs.

### SRS Traceability

- **SRS Traceability (from XLS):** SEC-003, SEC-015, INT-002
- **Business rules / state machines / events / acceptance / gates:** Interpreted only from the XLS SRS column and matching SRS sections; see SRS document for full text. Do not invent IDs beyond the XLS column.



### Current Implementation Status

**Overall:** PARTIAL

**Backend:** PARTIAL  
**UI:** N/A  
**Infrastructure/Integration:** PARTIAL  
**Tests:** COMPLETE  

### What Already Exists

- SecretRef type
- Encrypted tenant DB credential vault
- Webhook secret refs for billing/KYC



### What Is Missing

- Full external secret-manager backend (env/file vault pattern today)
- Provider API keys not all in a single rotated vault UI



### What Is Partial

*N/A or covered under Missing/Exists.*

### Codebase Evidence

- apps/api/shared_kernel/secrets.py — SecretRef
- apps/api/control_plane/tenancy/infrastructure/vault.py
- apps/api/tests/test_secret_ref.py
- docs/execution/runbooks/key-rotation.md



### Dependency Verification

**Jira Dependencies:** VKT-009

**Dependency Status:**

- VKT-009 = PARTIAL

Remaining work may still depend on: VKT-009.

### Acceptance / QA Coverage

Automated tests covering the core DoD behaviors were found (see Evidence).

### Required Remaining Work

- Decide production KMS/secret-manager adapter
- Ensure all provider secrets use SecretRef exclusively



### Audit Conclusion

VKT-010 is **PARTIAL**. Keep existing evidence; finish only the listed remaining work.

---



# VKT-011 — Define versioned API conventions and error contract



## Jira Definition

**Sprint:** Sprint 1  
**Portal / Layer:** Platform  
**Epic:** Foundation  
**Module:** API  
**Priority:** Must  
**Story Points:** 3  
**Estimated Hours:** 5  
**Dependencies:** VKT-008, VKT-009  
**Dependency Category:** BLOCKING  
**Flow:** UI/provider -> API -> validation/auth -> service -> structured response/error.  

### Definition of Done

Create consistent versioned API conventions, pagination, stable machine-readable errors, human-readable messages and request/correlation IDs.

### SRS Traceability

- **SRS Traceability (from XLS):** §30.1
- **Business rules / state machines / events / acceptance / gates:** Interpreted only from the XLS SRS column and matching SRS sections; see SRS document for full text. Do not invent IDs beyond the XLS column.



### Current Implementation Status

**Overall:** COMPLETE

**Backend:** COMPLETE  
**UI:** COMPLETE  
**Infrastructure/Integration:** N/A  
**Tests:** COMPLETE  

### What Already Exists

- /api/v1 prefix
- success/failure envelope
- correlation/request IDs
- Frontend api client consumes envelope



### What Is Missing

*Nothing material missing relative to DoD (COMPLETE).* 

### What Is Partial

*N/A or covered under Missing/Exists.*

### Codebase Evidence

- apps/api/config/urls.py
- apps/api/shared_kernel/http/envelope.py
- apps/api/shared_kernel/http/correlation.py
- packages/web-ui/src/api.ts
- apps/api/tests/test_correlation.py



### Dependency Verification

**Jira Dependencies:** VKT-008, VKT-009

**Dependency Status:**

- VKT-008 = PARTIAL
- VKT-009 = PARTIAL

Dependencies are COMPLETE or do not block evaluating this task's own gaps.

### Acceptance / QA Coverage

Automated tests covering the core DoD behaviors were found (see Evidence).

### Required Remaining Work

- None for DoD



### Audit Conclusion

VKT-011 is **COMPLETE** against repository evidence. **DO NOT REIMPLEMENT.** Only perform verification/QA if required for release.

---



# VKT-012 — Implement internal domain-event contract



## Jira Definition

**Sprint:** Sprint 1  
**Portal / Layer:** Platform  
**Epic:** Foundation  
**Module:** Events  
**Priority:** Must  
**Story Points:** 3  
**Estimated Hours:** 5  
**Dependencies:** VKT-006, VKT-011  
**Dependency Category:** BLOCKING  
**Flow:** Domain transaction -> event_id/event_type -> idempotent consumers.  

### Definition of Done

Define idempotent internal events mirroring lifecycle semantics used for notifications, audit, reporting and outbound webhook delivery.

### SRS Traceability

- **SRS Traceability (from XLS):** §30.2; Appendix B
- **Business rules / state machines / events / acceptance / gates:** Interpreted only from the XLS SRS column and matching SRS sections; see SRS document for full text. Do not invent IDs beyond the XLS column.



### Current Implementation Status

**Overall:** PARTIAL

**Backend:** PARTIAL  
**UI:** N/A  
**Infrastructure/Integration:** N/A  
**Tests:** PARTIAL  

### What Already Exists

- Per-module idempotency keys (payments, commission, KYC, risk events)
- Structured log events



### What Is Missing

- Unified internal domain-event bus / outbox
- Cross-module event contract catalog enforced in code



### What Is Partial

*N/A or covered under Missing/Exists.*

### Codebase Evidence

- apps/api/control_plane/billing — PaymentProcessorEvent
- apps/api/control_plane/commission — CommissionIdempotencyKey
- apps/api/control_plane/notifications/domain/types.py — EVENT_CATALOG



### Dependency Verification

**Jira Dependencies:** VKT-006, VKT-011

**Dependency Status:**

- VKT-006 = COMPLETE
- VKT-011 = COMPLETE

Dependencies are COMPLETE or do not block evaluating this task's own gaps.

### Acceptance / QA Coverage

Some automated tests exist; gaps remain relative to full DoD/acceptance (see Missing/Remaining).

### Required Remaining Work

- Either implement outbox/event bus or formally accept per-module idempotent events as V1 contract



### Audit Conclusion

VKT-012 is **PARTIAL**. Keep existing evidence; finish only the listed remaining work.

---



# VKT-013 — Implement canonical money, UTC and E.164 handling



## Jira Definition

**Sprint:** Sprint 1  
**Portal / Layer:** Platform  
**Epic:** Foundation  
**Module:** Time/money/phone  
**Priority:** Must  
**Story Points:** 3  
**Estimated Hours:** 4  
**Dependencies:** VKT-002, VKT-011  
**Dependency Category:** BLOCKING  
**Flow:** Input -> canonical representation -> storage -> tenant/user timezone display.  

### Definition of Done

Store monetary values in safe minor units/decimal with currency, timestamps in UTC, and phone numbers normalized to E.164 where applicable.

### SRS Traceability

- **SRS Traceability (from XLS):** NFR-010..012
- **Business rules / state machines / events / acceptance / gates:** Interpreted only from the XLS SRS column and matching SRS sections; see SRS document for full text. Do not invent IDs beyond the XLS column.



### Current Implementation Status

**Overall:** COMPLETE

**Backend:** COMPLETE  
**UI:** N/A  
**Infrastructure/Integration:** N/A  
**Tests:** COMPLETE  

### What Already Exists

- Money minor units USD-only
- UTC persistence conventions
- E.164 phone helpers



### What Is Missing

*Nothing material missing relative to DoD (COMPLETE).* 

### What Is Partial

*N/A or covered under Missing/Exists.*

### Codebase Evidence

- apps/api/shared_kernel/money.py
- apps/api/shared_kernel/phone.py (or tests/test_phone.py)
- apps/api/tests/test_money.py
- apps/api/tests/test_phone.py



### Dependency Verification

**Jira Dependencies:** VKT-002, VKT-011

**Dependency Status:**

- VKT-002 = COMPLETE
- VKT-011 = COMPLETE

Dependencies are COMPLETE or do not block evaluating this task's own gaps.

### Acceptance / QA Coverage

Automated tests covering the core DoD behaviors were found (see Evidence).

### Required Remaining Work

- None for DoD



### Audit Conclusion

VKT-013 is **COMPLETE** against repository evidence. **DO NOT REIMPLEMENT.** Only perform verification/QA if required for release.

---



# VKT-014 — Implement secure file upload abstraction



## Jira Definition

**Sprint:** Sprint 1  
**Portal / Layer:** Platform  
**Epic:** Foundation  
**Module:** File security  
**Priority:** Must  
**Story Points:** 3  
**Estimated Hours:** 5  
**Dependencies:** VKT-009, VKT-010  
**Dependency Category:** BLOCKING  
**Flow:** Upload -> validate -> private storage -> hash/ref -> processing state.  

### Definition of Done

Provide type/size policy, private storage references and malware scanning where infrastructure permits for KYC/knowledge files; separate internal KYC visibility.

### SRS Traceability

- **SRS Traceability (from XLS):** KYC-002, KYC-005, SEC-011, PRIV-002
- **Business rules / state machines / events / acceptance / gates:** Interpreted only from the XLS SRS column and matching SRS sections; see SRS document for full text. Do not invent IDs beyond the XLS column.
- **ADR / architecture note:** ADR-005 supersedes KYC document upload SoT



### Current Implementation Status

**Overall:** PARTIAL

**Backend:** PARTIAL  
**UI:** N/A  
**Infrastructure/Integration:** PARTIAL  
**Tests:** PARTIAL  

**Architecture deviation from original Jira task:** Yes — see ADR note above. Status judged against current accepted architecture, not obsolete Jira wording alone.

### What Already Exists

- object_ref pattern for payout proof (no bytes in DB)
- Recording metadata plane (ADR-002)



### What Is Missing

- Generic secure upload service with malware scan
- In-app KYC upload N/A under ADR-005



### What Is Partial

*N/A or covered under Missing/Exists.*

### Codebase Evidence

- apps/api/control_plane/commission/models.py — PayoutProof.object_ref
- docs/adr/ADR-002-recording-storage-separation.md
- docs/adr/ADR-005-external-kyc-provider.md



### Dependency Verification

**Jira Dependencies:** VKT-009, VKT-010

**Dependency Status:**

- VKT-009 = PARTIAL
- VKT-010 = PARTIAL

Remaining work may still depend on: VKT-009, VKT-010.

### Acceptance / QA Coverage

Some automated tests exist; gaps remain relative to full DoD/acceptance (see Missing/Remaining).

### Required Remaining Work

- Define upload abstraction for remaining file types (proof, risk verification images)
- Add content-type/size validation + scan where required



### Audit Conclusion

VKT-014 is **PARTIAL**. Keep existing evidence; finish only the listed remaining work.

---



# VKT-015 — Create production-like staging environment and CI checks



## Jira Definition

**Sprint:** Sprint 1  
**Portal / Layer:** Platform  
**Epic:** Foundation  
**Module:** Environment  
**Priority:** Must  
**Story Points:** 5  
**Estimated Hours:** 6  
**Dependencies:** VKT-010, VKT-011  
**Dependency Category:** BLOCKING  
**Flow:** Commit -> CI -> tests -> migration checks -> staging deployment.  

### Definition of Done

Create deployable staging configuration, database migration pipeline, automated test execution, secret injection and environment separation. Do not hard-code provider credentials.

### SRS Traceability

- **SRS Traceability (from XLS):** NFR-004..007
- **Business rules / state machines / events / acceptance / gates:** Interpreted only from the XLS SRS column and matching SRS sections; see SRS document for full text. Do not invent IDs beyond the XLS column.



### Current Implementation Status

**Overall:** PARTIAL

**Backend:** PARTIAL  
**UI:** N/A  
**Infrastructure/Integration:** PARTIAL  
**Tests:** PARTIAL  

### What Already Exists

- GitHub Actions api-ci
- docker-compose deploy
- In-process staging sandbox e2e test
- check_production_readiness --lab



### What Is Missing

- Distinct deployed staging environment with separate credentials
- External staging E2E against real hosts



### What Is Partial

*N/A or covered under Missing/Exists.*

### Codebase Evidence

- .github/workflows/api-ci.yml
- deploy/compose/docker-compose.yml
- apps/api/tests/test_staging_sandbox_e2e.py
- apps/api/control_plane/ops/management/commands/check_production_readiness.py



### Dependency Verification

**Jira Dependencies:** VKT-010, VKT-011

**Dependency Status:**

- VKT-010 = PARTIAL
- VKT-011 = COMPLETE

Remaining work may still depend on: VKT-010.

### Acceptance / QA Coverage

Some automated tests exist; gaps remain relative to full DoD/acceptance (see Missing/Remaining).

### Required Remaining Work

- Provision real staging stack
- Point CI optional job at staging smoke



### Audit Conclusion

VKT-015 is **PARTIAL**. Keep existing evidence; finish only the listed remaining work.

---



# VKT-016 — Build Super Admin application shell



## Jira Definition

**Sprint:** Sprint 2  
**Portal / Layer:** Super Admin  
**Epic:** Portal Shell  
**Module:** Layout & navigation  
**Priority:** Must  
**Story Points:** 3  
**Estimated Hours:** 5  
**Dependencies:** VKT-007, VKT-008  
**Dependency Category:** BLOCKING  
**Flow:** Login -> Super Admin shell -> authorized module -> scoped data.  

### Definition of Done

Create authenticated Super Admin layout, navigation, route guards, permission-aware menu visibility and shared list/detail/form patterns.

### SRS Traceability

- **SRS Traceability (from XLS):** §7; SEC-001..002
- **Business rules / state machines / events / acceptance / gates:** Interpreted only from the XLS SRS column and matching SRS sections; see SRS document for full text. Do not invent IDs beyond the XLS column.



### Current Implementation Status

**Overall:** COMPLETE

**Backend:** N/A  
**UI:** COMPLETE  
**Infrastructure/Integration:** N/A  
**Tests:** N/A  

### What Already Exists

- Platform portal AppShell, sidebar, hash routing, platform nav



### What Is Missing

*Nothing material missing relative to DoD (COMPLETE).* 

### What Is Partial

*N/A or covered under Missing/Exists.*

### Codebase Evidence

- packages/web-ui/src/components/layout/AppShell.tsx
- packages/web-ui/src/PortalApp.tsx portal=platform
- apps/web-platform/src/main.tsx
- packages/web-ui/src/components/layout/navGroups.ts



### Dependency Verification

**Jira Dependencies:** VKT-007, VKT-008

**Dependency Status:**

- VKT-007 = PARTIAL
- VKT-008 = PARTIAL

Dependencies are COMPLETE or do not block evaluating this task's own gaps.

### Acceptance / QA Coverage

Test applicability limited (N/A) or not separately scored.

### Required Remaining Work

- None for shell DoD



### Audit Conclusion

VKT-016 is **COMPLETE** against repository evidence. **DO NOT REIMPLEMENT.** Only perform verification/QA if required for release.

---



# VKT-017 — Build Super Admin dashboard



## Jira Definition

**Sprint:** Sprint 2  
**Portal / Layer:** Super Admin  
**Epic:** Dashboard  
**Module:** Dashboard screen  
**Priority:** Must  
**Story Points:** 5  
**Estimated Hours:** 7  
**Dependencies:** VKT-011, VKT-012, VKT-016  
**Dependency Category:** PARALLEL  
**Flow:** Filter period -> KPI cards -> click card -> filtered module view.  

### Definition of Done

Display agencies, customers, agents, numbers, calls, minutes, MRR, payments, commission liability, pending payouts and KYC queue; add financial summary, operational health and drilldown/date filters.

### SRS Traceability

- **SRS Traceability (from XLS):** SA1-001..005
- **Business rules / state machines / events / acceptance / gates:** Interpreted only from the XLS SRS column and matching SRS sections; see SRS document for full text. Do not invent IDs beyond the XLS column.



### Current Implementation Status

**Overall:** PARTIAL

**Backend:** PARTIAL  
**UI:** PARTIAL  
**Infrastructure/Integration:** N/A  
**Tests:** PARTIAL  

### What Already Exists

- PlatformDashboard with KPIs/charts
- Dashboard API



### What Is Missing

- True MRR/aging completeness
- Ops health integration on dashboard
- Full filter/drilldown (also VKT-133)



### What Is Partial

*N/A or covered under Missing/Exists.*

### Codebase Evidence

- packages/web-ui/src/features/dashboard/PlatformDashboard.tsx
- apps/api/control_plane/reporting/application/dashboard.py
- apps/api/tests/test_dashboard_api.py



### Dependency Verification

**Jira Dependencies:** VKT-011, VKT-012, VKT-016

**Dependency Status:**

- VKT-011 = COMPLETE
- VKT-012 = PARTIAL
- VKT-016 = COMPLETE

Remaining work may still depend on: VKT-012.

### Acceptance / QA Coverage

Some automated tests exist; gaps remain relative to full DoD/acceptance (see Missing/Remaining).

### Required Remaining Work

- Wire remaining financial KPIs and filters per SRS SA1



### Audit Conclusion

VKT-017 is **PARTIAL**. Keep existing evidence; finish only the listed remaining work.

---



# VKT-018 — Build agency directory with search/filter/status visibility



## Jira Definition

**Sprint:** Sprint 2  
**Portal / Layer:** Platform  
**Epic:** Agencies  
**Module:** Agencies  
**Priority:** Must  
**Story Points:** 3  
**Estimated Hours:** (see XLS)  
**Dependencies:** (see XLS)  

### Definition of Done

Build Super Admin agency directory with search/filter and status visibility.

### SRS Traceability

- **SRS Traceability (from XLS):** SA2 / agency directory requirements



### Current Implementation Status

**Overall:** COMPLETE

**Backend:** COMPLETE  
**UI:** COMPLETE  
**Infrastructure/Integration:** N/A  
**Tests:** COMPLETE  

**Re-verified 2026-09-12:** Earlier PARTIAL was based on stale SA2 gap notes. Code now has server filters and a working directory UI.

### What Already Exists

- `GET /api/v1/platform/agencies` with `status` and `name` query filters + pagination
- `PlatformAgenciesScreen` directory table with status badges and client-side search
- Tests: `apps/api/tests/test_sa2_agency_api.py` — `test_agency_list_filters_and_team_by_agency`



### What Is Missing

*Nothing material missing relative to DoD (COMPLETE).*

### What Is Partial

*N/A*

### Codebase Evidence

- `apps/api/control_plane/tenancy/api/agency_views.py` — `AgencyCollectionView.get` filters
- `packages/web-ui/src/features/agencies/PlatformAgenciesScreen.tsx` — directory + query filter
- `apps/api/tests/test_sa2_agency_api.py` — list filter test



### Dependency Verification

See XLS dependencies; core tenancy exists.

### Acceptance / QA Coverage

Automated list-filter test present; UI covered by platform agencies screen.

### Required Remaining Work

*None — treat as COMPLETE; only verify/QA if release requires re-attestation.*

### Audit Conclusion

VKT-018 is **COMPLETE** against repository evidence. **DO NOT REIMPLEMENT.** Only perform verification/QA if required for release.

---



# VKT-019 — Build Create Agency form

## Jira Definition

**Sprint:** Sprint 2  
**Portal / Layer:** Super Admin  
**Epic:** Agencies  
**Module:** Create agency screen  
**Priority:** Must  
**Story Points:** 5  
**Estimated Hours:** 6  
**Dependencies:** VKT-018, VKT-011  

### Definition of Done

Create agency identity, owner/contact details, default status, commission rate, currency/region and optional operating restrictions. Creation starts Invited/Onboarding according to flow and sends secure owner invitation.

### SRS Traceability

- **SRS Traceability (from XLS):** SA2-001; §6.1

### Current Implementation Status

**Overall:** COMPLETE

**Backend:** COMPLETE  
**UI:** COMPLETE  
**Infrastructure/Integration:** COMPLETE  
**Tests:** COMPLETE  

**Frontend re-audit (2026-09-12):** PlatformAgencyCreateScreen now collects MySQL username/password (+ optional host/port) and POSTs database payload.

### Backend — Existing Implementation

- Prior backend audit findings retained unless contradicted; see Backend Evidence / previous COMPLETE notes for domain services.

### Frontend/UI — Existing Implementation

- packages/web-ui/src/features/agencies/PlatformAgencyCreateScreen.tsx — Database step
- packages/web-ui/src/features/agencies/hooks/useCreatePlatformAgency.ts — POST /api/v1/platform/agencies with database{}
- packages/web-ui/src/features/agencies/renderAgencyRoutes.tsx — /agencies/new

### What Is Complete

- Overall status after frontend pull: **COMPLETE**
- Backend: COMPLETE; UI: COMPLETE

### What Is Partial

_N/A or minor residual notes only._

### What Is Missing

- _Nothing material missing relative to DoD (COMPLETE)._

### Backend Evidence

- See prior audit evidence for this VKT ID (domain/API/tests under `apps/api`).

### Frontend Evidence

- `packages/web-ui/src/features/agencies/PlatformAgencyCreateScreen.tsx` — Database step
- `packages/web-ui/src/features/agencies/hooks/useCreatePlatformAgency.ts` — POST /api/v1/platform/agencies with database{}
- `packages/web-ui/src/features/agencies/renderAgencyRoutes.tsx` — /agencies/new

### Test Evidence

- Backend tests: see `apps/api/tests/` (status **COMPLETE**).
- Frontend automated tests: **MISSING** (no vitest/RTL/Playwright under `packages/web-ui`).

### Dependency Verification

Jira dependencies: VKT-018, VKT-011

### Required Remaining Work

_None — treat as COMPLETE; only verify/QA if release requires re-attestation._

### Audit Conclusion

VKT-019 is **COMPLETE** after frontend re-audit. **DO NOT REIMPLEMENT.** Previous status was PARTIAL.

---
# VKT-020 — Build agency profile/detail and resource tabs

## Jira Definition

**Sprint:** Sprint 2  
**Portal / Layer:** Super Admin  
**Epic:** Agencies  
**Module:** Agency detail screen  
**Priority:** Must  
**Story Points:** 5  
**Estimated Hours:** 6  
**Dependencies:** VKT-018, VKT-019  

### Definition of Done

Show/edit legal/operating data subject to audit rules; expose customers, agents, numbers, calls, integrations, team, knowledge and financial overview.

### SRS Traceability

- **SRS Traceability (from XLS):** SA2-002, SA2-006, SA2-007

### Current Implementation Status

**Overall:** COMPLETE

**Backend:** COMPLETE  
**UI:** COMPLETE  
**Infrastructure/Integration:** N/A  
**Tests:** PARTIAL  

**Frontend re-audit (2026-09-12):** PlatformAgencyDetailScreen provides profile/commission/status/capabilities/financial/resources/notes tabs wired to APIs.

### Backend — Existing Implementation

- Prior backend audit findings retained unless contradicted; see Backend Evidence / previous COMPLETE notes for domain services.

### Frontend/UI — Existing Implementation

- packages/web-ui/src/features/agencies/PlatformAgencyDetailScreen.tsx
- packages/web-ui/src/features/agencies/hooks/usePlatformAgencyDetail.ts

### What Is Complete

- Overall status after frontend pull: **COMPLETE**
- Backend: COMPLETE; UI: COMPLETE

### What Is Partial

_N/A or minor residual notes only._

### What Is Missing

- Optional SA knowledge traversal under resources remains thin (SA2-007 nice-to-have).

### Backend Evidence

- See prior audit evidence for this VKT ID (domain/API/tests under `apps/api`).

### Frontend Evidence

- `packages/web-ui/src/features/agencies/PlatformAgencyDetailScreen.tsx`
- `packages/web-ui/src/features/agencies/hooks/usePlatformAgencyDetail.ts`

### Test Evidence

- Backend tests: see `apps/api/tests/` (status **PARTIAL**).
- Frontend automated tests: **MISSING** (no vitest/RTL/Playwright under `packages/web-ui`).

### Dependency Verification

Jira dependencies: VKT-018, VKT-019

### Required Remaining Work

- Optional SA knowledge traversal under resources remains thin (SA2-007 nice-to-have).

### Audit Conclusion

VKT-020 is **COMPLETE** after frontend re-audit. **DO NOT REIMPLEMENT.** Previous status was PARTIAL.

---
# VKT-021 — Implement commission rate/effective-date UI and service



## Jira Definition

**Sprint:** Sprint 2  
**Epic:** Agencies  

### Definition of Done

Commission rate change UI/service with effective-date behavior and historical snapshot safety.

### Current Implementation Status

**Overall:** PARTIAL

**Backend:** PARTIAL  
**UI:** COMPLETE  
**Infrastructure/Integration:** N/A  
**Tests:** COMPLETE  

**Re-verified 2026-09-12:** Rate change is audited and snaps on future accruals. Still no schedulable future effective-date input or rate-history API.

### What Already Exists

- `POST .../commission` via `SetCommissionRate` (sets `rate_effective_at=now`, writes `audit_events`)
- Ledger accruals snapshot `rate_bps_snapshot` (historical entries unchanged)
- Commission tab UI on `PlatformAgenciesScreen`
- Test: `test_platform_can_change_commission_rate`



### What Is Missing

- Future effective-date scheduling input/API
- Commission rate history table / GET past rates



### Codebase Evidence

- `apps/api/control_plane/tenancy/application/change_agency.py` — `SetCommissionRate`
- `apps/api/control_plane/commission/application/accrue.py` — rate snapshot
- `packages/web-ui/src/features/agencies/PlatformAgenciesScreen.tsx` — commission tab



### Required Remaining Work

- Add optional `effective_at` (future) + history query if product still requires SA2-003 scheduling



### Audit Conclusion

VKT-021 remains **PARTIAL** — immediate rate change COMPLETE; scheduled effective-date/history still missing.

---



# VKT-022 — Implement agency status and capability overrides



## Jira Definition

**Sprint:** Sprint 2  
**Epic:** Agencies  

### Definition of Done

Implement agency status transitions and capability override controls.

### Current Implementation Status

**Overall:** COMPLETE

**Backend:** COMPLETE  
**UI:** COMPLETE  
**Infrastructure/Integration:** N/A  
**Tests:** COMPLETE  

**Re-verified 2026-09-12:** Older gap list is stale. Status actions apply §24.1 default capability gates; status changes audited; capability PATCH preserves omitted flags; UI tabs exist; `create_agents` enforced for agency actors.

### What Already Exists

- `ChangeAgencyStatus` + `default_capabilities_for_status` / `merge_capability_gates`
- Status audited (`agency.status.changed`); suspend notifies
- `ChangeAgencyCapabilities` + UI; partial updates preserve untouched flags
- Tests for restrict gates, partial capabilities, create_agents block



### What Is Missing

*Nothing material for this DoD.* Residual runtime gate depth for `existing_customer_services` on voice path is tracked under **VKT-033**. Capability-change audit event is nice-to-have, not required to call overrides complete.

### Codebase Evidence

- `apps/api/control_plane/tenancy/domain/lifecycle.py` — status gates
- `apps/api/control_plane/tenancy/application/change_agency.py`
- `packages/web-ui/src/features/agencies/PlatformAgenciesScreen.tsx` — status/capabilities tabs
- `apps/api/tests/test_sa2_agency_api.py`



### Required Remaining Work

*None for VKT-022 DoD. See VKT-033 for remaining central gate coverage.*

### Audit Conclusion

VKT-022 is **COMPLETE** against repository evidence. **DO NOT REIMPLEMENT.**

---



# VKT-023 — Build internal notes/risk flags

## Jira Definition

**Sprint:** Sprint 2  
**Portal / Layer:** Super Admin  
**Epic:** Agencies  
**Module:** Risk/internal notes  
**Priority:** Must  
**Story Points:** 2  
**Estimated Hours:** 3  
**Dependencies:** VKT-020, VKT-006  

### Definition of Done

Allow platform-only internal notes and risk flags without exposing them to agency/customer users.

### SRS Traceability

- **SRS Traceability (from XLS):** SA2-008

### Current Implementation Status

**Overall:** COMPLETE

**Backend:** COMPLETE  
**UI:** COMPLETE  
**Infrastructure/Integration:** N/A  
**Tests:** COMPLETE  

**Frontend re-audit (2026-09-12):** Notes tab now lists/creates notes via platform agencies notes API (risk_flag supported).

### Backend — Existing Implementation

- Prior backend audit findings retained unless contradicted; see Backend Evidence / previous COMPLETE notes for domain services.

### Frontend/UI — Existing Implementation

- packages/web-ui/src/features/agencies/PlatformAgencyDetailScreen.tsx — notes tab
- packages/web-ui/src/features/agencies/hooks/usePlatformAgencyDetail.ts — GET/POST .../notes

### What Is Complete

- Overall status after frontend pull: **COMPLETE**
- Backend: COMPLETE; UI: COMPLETE

### What Is Partial

_N/A or minor residual notes only._

### What Is Missing

- _Nothing material missing relative to DoD (COMPLETE)._

### Backend Evidence

- See prior audit evidence for this VKT ID (domain/API/tests under `apps/api`).

### Frontend Evidence

- `packages/web-ui/src/features/agencies/PlatformAgencyDetailScreen.tsx` — notes tab
- `packages/web-ui/src/features/agencies/hooks/usePlatformAgencyDetail.ts` — GET/POST .../notes

### Test Evidence

- Backend tests: see `apps/api/tests/` (status **COMPLETE**).
- Frontend automated tests: **MISSING** (no vitest/RTL/Playwright under `packages/web-ui`).

### Dependency Verification

Jira dependencies: VKT-020, VKT-006

### Required Remaining Work

_None — treat as COMPLETE; only verify/QA if release requires re-attestation._

### Audit Conclusion

VKT-023 is **COMPLETE** after frontend re-audit. **DO NOT REIMPLEMENT.** Previous status was PARTIAL.

---
# VKT-024 — Build agency-owner invitation acceptance

## Jira Definition

**Sprint:** Sprint 2  
**Portal / Layer:** Agency  
**Epic:** Onboarding  
**Module:** Invitation acceptance screen  
**Priority:** Must  
**Story Points:** 3  
**Estimated Hours:** 5  
**Dependencies:** VKT-019, VKT-007  

### Definition of Done

Secure invited owner flow: accept invitation, create credentials, verify email and accept platform terms before portal access.

### SRS Traceability

- **SRS Traceability (from XLS):** §6.1

### Current Implementation Status

**Overall:** PARTIAL

**Backend:** COMPLETE  
**UI:** NOT_IMPLEMENTED  
**Infrastructure/Integration:** N/A  
**Tests:** PARTIAL  

**Frontend re-audit (2026-09-12):** Invite send exists; accept-invitation UI still absent after frontend pull.

### Backend — Existing Implementation

- Prior backend audit findings retained unless contradicted; see Backend Evidence / previous COMPLETE notes for domain services.

### Frontend/UI — Existing Implementation

- packages/web-ui/src/features/auth/components/LoginScreen.tsx — login only
- No accept-invite route in PortalApp / features/auth

### What Is Complete

- Overall status after frontend pull: **PARTIAL**
- Backend: COMPLETE; UI: NOT_IMPLEMENTED

### What Is Partial

- Build invitation acceptance page calling POST /api/v1/auth/invitations/accept

### What Is Missing

- Build invitation acceptance page calling POST /api/v1/auth/invitations/accept

### Backend Evidence

- See prior audit evidence for this VKT ID (domain/API/tests under `apps/api`).

### Frontend Evidence

- `packages/web-ui/src/features/auth/components/LoginScreen.tsx` — login only
- `No accept-invite route in PortalApp / features/auth`

### Test Evidence

- Backend tests: see `apps/api/tests/` (status **PARTIAL**).
- Frontend automated tests: **MISSING** (no vitest/RTL/Playwright under `packages/web-ui`).

### Dependency Verification

Jira dependencies: VKT-019, VKT-007

### Required Remaining Work

- Build invitation acceptance page calling POST /api/v1/auth/invitations/accept

### Audit Conclusion

VKT-024 remains **PARTIAL**. Invite send exists; accept-invitation UI still absent after frontend pull.

---
# VKT-025 — Build KYC business identity form



## Jira Definition

**Sprint:** Sprint 2  
**Portal / Layer:** Agency  
**Epic:** KYC  
**Module:** Business profile screen  
**Priority:** Must  
**Story Points:** 3  
**Estimated Hours:** 5  
**Dependencies:** VKT-014, VKT-024  
**Dependency Category:** BLOCKING  
**Flow:** KYC Not Started/Incomplete -> save -> Incomplete.  

### Definition of Done

Capture legal/trading name, entity type, registration/incorporation number where applicable, incorporation/operating countries and business address.

### SRS Traceability

- **SRS Traceability (from XLS):** §6.2; KYC-001..005
- **Business rules / state machines / events / acceptance / gates:** Interpreted only from the XLS SRS column and matching SRS sections; see SRS document for full text. Do not invent IDs beyond the XLS column.
- **ADR / architecture note:** ADR-005 — Architecture deviation from original Jira in-app form wording



### Current Implementation Status

**Overall:** COMPLETE

**Backend:** COMPLETE  
**UI:** N/A  
**Infrastructure/Integration:** COMPLETE  
**Tests:** COMPLETE  

**Note:** COMPLETE according to current architecture (external KYC).

**Architecture deviation from original Jira task:** Yes — see ADR note above. Status judged against current accepted architecture, not obsolete Jira wording alone.

### What Already Exists

- External hosted KYC session start — no in-app business identity form SoT



### What Is Missing

*Nothing material missing relative to DoD (COMPLETE).* 

### What Is Partial

*N/A or covered under Missing/Exists.*

### Codebase Evidence

- docs/adr/ADR-005-external-kyc-provider.md
- apps/api/providers/kyc/hosted.py — HostedKycAdapter
- apps/api/control_plane/kyc/application/start_session.py
- apps/api/tests/test_kyc_api.py — test_kyc_models_do_not_store_files



### Dependency Verification

**Jira Dependencies:** VKT-014, VKT-024

**Dependency Status:**

- VKT-014 = PARTIAL
- VKT-024 = PARTIAL

Dependencies are COMPLETE or do not block evaluating this task's own gaps.

### Acceptance / QA Coverage

Automated tests covering the core DoD behaviors were found (see Evidence).

### Required Remaining Work

- Do not rebuild in-app forms; verify provider session UX in agency portal



### Audit Conclusion

VKT-025 is **COMPLETE** against repository evidence. **DO NOT REIMPLEMENT.** Only perform verification/QA if required for release.

---



# VKT-026 — Build owner/controller information form



## Jira Definition

**Sprint:** Sprint 2  
**Portal / Layer:** Agency  
**Epic:** KYC  
**Module:** Owner/controller screen  
**Priority:** Must  
**Story Points:** 3  
**Estimated Hours:** 4  
**Dependencies:** VKT-025  
**Dependency Category:** BLOCKING  
**Flow:** KYC Incomplete -> owner/controller section -> save -> Incomplete.  

### Definition of Done

Capture required owner/controller information including full legal name, lawful/required DOB/nationality, residential address and ownership/control relationship.

### SRS Traceability

- **SRS Traceability (from XLS):** §6.2
- **Business rules / state machines / events / acceptance / gates:** Interpreted only from the XLS SRS column and matching SRS sections; see SRS document for full text. Do not invent IDs beyond the XLS column.
- **ADR / architecture note:** ADR-005



### Current Implementation Status

**Overall:** COMPLETE

**Backend:** COMPLETE  
**UI:** N/A  
**Infrastructure/Integration:** COMPLETE  
**Tests:** COMPLETE  

**Note:** COMPLETE via ADR-005; original Jira form superseded.

**Architecture deviation from original Jira task:** Yes — see ADR note above. Status judged against current accepted architecture, not obsolete Jira wording alone.

### What Already Exists

- Owner/controller data collected by external KYC provider



### What Is Missing

*Nothing material missing relative to DoD (COMPLETE).* 

### What Is Partial

*N/A or covered under Missing/Exists.*

### Codebase Evidence

- docs/adr/ADR-005-external-kyc-provider.md
- apps/api/control_plane/kyc/



### Dependency Verification

**Jira Dependencies:** VKT-025

**Dependency Status:**

- VKT-025 = COMPLETE

Dependencies are COMPLETE or do not block evaluating this task's own gaps.

### Acceptance / QA Coverage

Automated tests covering the core DoD behaviors were found (see Evidence).

### Required Remaining Work

- Do not rebuild in-app owner forms



### Audit Conclusion

VKT-026 is **COMPLETE** against repository evidence. **DO NOT REIMPLEMENT.** Only perform verification/QA if required for release.

---



# VKT-027 — Build identity/business/address evidence upload



## Jira Definition

**Sprint:** Sprint 2  
**Portal / Layer:** Agency  
**Epic:** KYC  
**Module:** Evidence upload screen  
**Priority:** Must  
**Story Points:** 5  
**Estimated Hours:** 6  
**Dependencies:** VKT-014, VKT-025  
**Dependency Category:** BLOCKING  
**Flow:** Upload -> validation/private storage -> evidence attached -> preserve prior version.  

### Definition of Done

Upload government ID, registration/incorporation evidence and proof of address where required; enforce secure file policy and preserve versions on resubmission.

### SRS Traceability

- **SRS Traceability (from XLS):** §6.2; KYC-002, KYC-005
- **Business rules / state machines / events / acceptance / gates:** Interpreted only from the XLS SRS column and matching SRS sections; see SRS document for full text. Do not invent IDs beyond the XLS column.
- **ADR / architecture note:** ADR-005



### Current Implementation Status

**Overall:** COMPLETE

**Backend:** COMPLETE  
**UI:** N/A  
**Infrastructure/Integration:** COMPLETE  
**Tests:** COMPLETE  

**Architecture deviation from original Jira task:** Yes — see ADR note above. Status judged against current accepted architecture, not obsolete Jira wording alone.

### What Already Exists

- Evidence upload at provider; Vokit stores no document bytes



### What Is Missing

*Nothing material missing relative to DoD (COMPLETE).* 

### What Is Partial

*N/A or covered under Missing/Exists.*

### Codebase Evidence

- docs/adr/ADR-005-external-kyc-provider.md
- apps/api/tests/test_kyc_api.py — test_no_kyc_document_upload_route



### Dependency Verification

**Jira Dependencies:** VKT-014, VKT-025

**Dependency Status:**

- VKT-014 = PARTIAL
- VKT-025 = COMPLETE

Dependencies are COMPLETE or do not block evaluating this task's own gaps.

### Acceptance / QA Coverage

Automated tests covering the core DoD behaviors were found (see Evidence).

### Required Remaining Work

- Do not rebuild evidence upload in Vokit



### Audit Conclusion

VKT-027 is **COMPLETE** against repository evidence. **DO NOT REIMPLEMENT.** Only perform verification/QA if required for release.

---



# VKT-028 — Build payout details capture



## Jira Definition

**Sprint:** Sprint 2  
**Portal / Layer:** Agency  
**Epic:** KYC  
**Module:** Payout details screen  
**Priority:** Must  
**Story Points:** 3  
**Estimated Hours:** 4  
**Dependencies:** VKT-025, VKT-014  
**Dependency Category:** BLOCKING  
**Flow:** KYC -> payout details -> verification_state -> unavailable until allowed.  

### Definition of Done

Capture beneficiary name, account identifier, bank/provider details, country and currency. Keep payout method unusable until verification rules are satisfied.

### SRS Traceability

- **SRS Traceability (from XLS):** §6.2; KYC-001
- **Business rules / state machines / events / acceptance / gates:** Interpreted only from the XLS SRS column and matching SRS sections; see SRS document for full text. Do not invent IDs beyond the XLS column.



### Current Implementation Status

**Overall:** NOT_IMPLEMENTED

**Backend:** NOT_IMPLEMENTED  
**UI:** NOT_IMPLEMENTED  
**Infrastructure/Integration:** N/A  
**Tests:** NOT_IMPLEMENTED  

**Note:** Payout request/reservation exists (VKT-052) but bank/details capture UI/API not found.

### What Already Exists

*None identified.*

### What Is Missing

- Agency payout bank/details capture form (method of payment destination)
- Persistence for payout destination details beyond KYC-gated request



### What Is Partial

*N/A or covered under Missing/Exists.*

### Codebase Evidence

- Unable to locate dedicated payout-details form/model in web-ui or agency APIs beyond payout request amount flow



### Dependency Verification

**Jira Dependencies:** VKT-025, VKT-014

**Dependency Status:**

- VKT-025 = COMPLETE
- VKT-014 = PARTIAL

Remaining work may still depend on: VKT-014.

### Acceptance / QA Coverage

Required tests for this DoD were not found or are insufficient.

### Required Remaining Work

- Define payout destination schema (SRS AG11)
- Build agency UI + API to capture/update payout details
- Gate editable fields by KYC status



### Audit Conclusion

VKT-028 is **NOT_IMPLEMENTED**. Build the Missing/Remaining items; do not assume adjacent features cover this DoD.

---



# VKT-029 — Build declarations and KYC submission



## Jira Definition

**Sprint:** Sprint 2  
**Portal / Layer:** Agency  
**Epic:** KYC  
**Module:** Declarations & submit  
**Priority:** Must  
**Story Points:** 3  
**Estimated Hours:** 4  
**Dependencies:** VKT-026, VKT-027, VKT-028  
**Dependency Category:** BLOCKING  
**Flow:** Incomplete -> declarations -> Submit -> Submitted -> Under Review.  

### Definition of Done

Capture accuracy/beneficial ownership declarations where applicable, platform terms, acceptable use and privacy/recording acknowledgements. Lock application on submission.

### SRS Traceability

- **SRS Traceability (from XLS):** §6.1; KYC-003..004
- **Business rules / state machines / events / acceptance / gates:** Interpreted only from the XLS SRS column and matching SRS sections; see SRS document for full text. Do not invent IDs beyond the XLS column.
- **ADR / architecture note:** ADR-005



### Current Implementation Status

**Overall:** COMPLETE

**Backend:** COMPLETE  
**UI:** N/A  
**Infrastructure/Integration:** COMPLETE  
**Tests:** COMPLETE  

**Architecture deviation from original Jira task:** Yes — see ADR note above. Status judged against current accepted architecture, not obsolete Jira wording alone.

### What Already Exists

- Declarations/submission handled in provider-hosted KYC flow



### What Is Missing

*Nothing material missing relative to DoD (COMPLETE).* 

### What Is Partial

*N/A or covered under Missing/Exists.*

### Codebase Evidence

- docs/adr/ADR-005-external-kyc-provider.md
- apps/api/control_plane/kyc/application/start_session.py



### Dependency Verification

**Jira Dependencies:** VKT-026, VKT-027, VKT-028

**Dependency Status:**

- VKT-026 = COMPLETE
- VKT-027 = COMPLETE
- VKT-028 = NOT_IMPLEMENTED

Dependencies are COMPLETE or do not block evaluating this task's own gaps.

### Acceptance / QA Coverage

Automated tests covering the core DoD behaviors were found (see Evidence).

### Required Remaining Work

- None in-app; validate provider checklist covers declarations



### Audit Conclusion

VKT-029 is **COMPLETE** against repository evidence. **DO NOT REIMPLEMENT.** Only perform verification/QA if required for release.

---



# VKT-030 — Build KYC review queue

## Jira Definition

**Sprint:** Sprint 2  
**Portal / Layer:** Super Admin  
**Epic:** KYC  
**Module:** KYC queue screen  
**Priority:** Must  
**Story Points:** 3  
**Estimated Hours:** 5  
**Dependencies:** VKT-029, VKT-016  

### Definition of Done

Filter KYC applications by status, age, country, agency and risk flags; expose only to authorized KYC/platform roles.

### SRS Traceability

- **SRS Traceability (from XLS):** SA4-001; KYC-002

### Current Implementation Status

**Overall:** COMPLETE

**Backend:** COMPLETE  
**UI:** COMPLETE  
**Infrastructure/Integration:** COMPLETE  
**Tests:** COMPLETE  

**Frontend re-audit (2026-09-12):** PlatformKycScreen implements SA KYC case queue with filters and case selection (ADR-005 status queue).

### Backend — Existing Implementation

- Prior backend audit findings retained unless contradicted; see Backend Evidence / previous COMPLETE notes for domain services.

### Frontend/UI — Existing Implementation

- packages/web-ui/src/features/kyc/PlatformKycScreen.tsx
- packages/web-ui/src/features/kyc/hooks/usePlatformKyc.ts — GET /api/v1/platform/kyc/cases

### What Is Complete

- Overall status after frontend pull: **COMPLETE**
- Backend: COMPLETE; UI: COMPLETE

### What Is Partial

_N/A or minor residual notes only._

### What Is Missing

- _Nothing material missing relative to DoD (COMPLETE)._

### Backend Evidence

- See prior audit evidence for this VKT ID (domain/API/tests under `apps/api`).

### Frontend Evidence

- `packages/web-ui/src/features/kyc/PlatformKycScreen.tsx`
- `packages/web-ui/src/features/kyc/hooks/usePlatformKyc.ts` — GET /api/v1/platform/kyc/cases

### Test Evidence

- Backend tests: see `apps/api/tests/` (status **COMPLETE**).
- Frontend automated tests: **MISSING** (no vitest/RTL/Playwright under `packages/web-ui`).

### Dependency Verification

Jira dependencies: VKT-029, VKT-016

### Required Remaining Work

_None — treat as COMPLETE; only verify/QA if release requires re-attestation._

### Audit Conclusion

VKT-030 is **COMPLETE** after frontend re-audit. **DO NOT REIMPLEMENT.** Previous status was PARTIAL.

---
# VKT-031 — Build secure evidence review and notes



## Jira Definition

**Sprint:** Sprint 2  
**Portal / Layer:** Super Admin  
**Epic:** KYC  
**Module:** KYC review detail  
**Priority:** Must  
**Story Points:** 3  
**Estimated Hours:** 5  
**Dependencies:** VKT-030  
**Dependency Category:** BLOCKING  
**Flow:** Queue -> review -> inspect evidence -> internal/external notes.  

### Definition of Done

Securely inspect submitted information/documents; support internal reviewer notes and agency-visible request notes without exposing internal notes.

### SRS Traceability

- **SRS Traceability (from XLS):** SA4-002; KYC-002..003
- **Business rules / state machines / events / acceptance / gates:** Interpreted only from the XLS SRS column and matching SRS sections; see SRS document for full text. Do not invent IDs beyond the XLS column.
- **ADR / architecture note:** ADR-005



### Current Implementation Status

**Overall:** COMPLETE

**Backend:** COMPLETE  
**UI:** N/A  
**Infrastructure/Integration:** COMPLETE  
**Tests:** COMPLETE  

**Architecture deviation from original Jira task:** Yes — see ADR note above. Status judged against current accepted architecture, not obsolete Jira wording alone.

### What Already Exists

- Evidence review out-of-band at provider; SA override without file vault



### What Is Missing

*Nothing material missing relative to DoD (COMPLETE).* 

### What Is Partial

*N/A or covered under Missing/Exists.*

### Codebase Evidence

- docs/adr/ADR-005-external-kyc-provider.md §Decision 6
- apps/api/control_plane/kyc/application/override_case.py



### Dependency Verification

**Jira Dependencies:** VKT-030

**Dependency Status:**

- VKT-030 = PARTIAL

Dependencies are COMPLETE or do not block evaluating this task's own gaps.

### Acceptance / QA Coverage

Automated tests covering the core DoD behaviors were found (see Evidence).

### Required Remaining Work

- Do not build in-app evidence viewer as SoT



### Audit Conclusion

VKT-031 is **COMPLETE** against repository evidence. **DO NOT REIMPLEMENT.** Only perform verification/QA if required for release.

---



# VKT-032 — Implement Verify / Reject / More Information

## Jira Definition

**Sprint:** Sprint 2  
**Portal / Layer:** Super Admin  
**Epic:** KYC  
**Module:** KYC decision actions  
**Priority:** Must  
**Story Points:** 5  
**Estimated Hours:** 6  
**Dependencies:** VKT-031, VKT-006, VKT-012  

### Definition of Done

Implement state machine transitions and structured reason codes plus optional notes. Preserve prior evidence/audit history on resubmission.

### SRS Traceability

- **SRS Traceability (from XLS):** SA4-003..005; §6.3; KYC-003..006

### Current Implementation Status

**Overall:** COMPLETE

**Backend:** COMPLETE  
**UI:** COMPLETE  
**Infrastructure/Integration:** COMPLETE  
**Tests:** COMPLETE  

**Frontend re-audit (2026-09-12):** KYC override UI exposes Verify / Reject / More information (+ freeze/unfreeze) via override API.

### Backend — Existing Implementation

- Prior backend audit findings retained unless contradicted; see Backend Evidence / previous COMPLETE notes for domain services.

### Frontend/UI — Existing Implementation

- packages/web-ui/src/features/kyc/PlatformKycScreen.tsx — decision actions
- packages/web-ui/src/features/kyc/types.ts — DECISION_STATUSES
- packages/web-ui/src/features/kyc/hooks/usePlatformKyc.ts — POST .../override

### What Is Complete

- Overall status after frontend pull: **COMPLETE**
- Backend: COMPLETE; UI: COMPLETE

### What Is Partial

_N/A or minor residual notes only._

### What Is Missing

- _Nothing material missing relative to DoD (COMPLETE)._

### Backend Evidence

- See prior audit evidence for this VKT ID (domain/API/tests under `apps/api`).

### Frontend Evidence

- `packages/web-ui/src/features/kyc/PlatformKycScreen.tsx` — decision actions
- `packages/web-ui/src/features/kyc/types.ts` — DECISION_STATUSES
- `packages/web-ui/src/features/kyc/hooks/usePlatformKyc.ts` — POST .../override

### Test Evidence

- Backend tests: see `apps/api/tests/` (status **COMPLETE**).
- Frontend automated tests: **MISSING** (no vitest/RTL/Playwright under `packages/web-ui`).

### Dependency Verification

Jira dependencies: VKT-031, VKT-006, VKT-012

### Required Remaining Work

_None — treat as COMPLETE; only verify/QA if release requires re-attestation._

### Audit Conclusion

VKT-032 is **COMPLETE** after frontend re-audit. **DO NOT REIMPLEMENT.** Previous status was PARTIAL.

---
# VKT-033 — Implement status/capability gates centrally



## Jira Definition

**Sprint:** Sprint 2  

### Definition of Done

Central enforcement of agency status/capability gates on protected actions.

### Current Implementation Status

**Overall:** PARTIAL

**Backend:** PARTIAL  
**UI:** N/A  
**Infrastructure/Integration:** N/A  
**Tests:** PARTIAL  

**Re-verified 2026-09-12:** Many gates are now real: create customers, purchase numbers, create agents (agency actor), payout KYC+capability, customer mutate when `existing_customer_services` false. Still not proven on inbound/voice/runtime path for `existing_customer_services`.

### What Already Exists

- `assert_agency_may_create_customer`, `assert_agency_may_purchase_numbers`, `assert_agency_may_mutate_customer`
- `create_agents` checked in risk/create agent path for non-privileged
- Status-driven default capability merges on restrict/under_review/suspend



### What Is Missing

- Enforce `existing_customer_services` (and related) on call/DID/agent runtime traffic paths
- Confirm publish/outbound paths honor the same central helpers



### Codebase Evidence

- `apps/api/control_plane/tenancy/domain/lifecycle.py`
- `apps/api/control_plane/risk/application/create_agent.py` — create_agents gate
- `apps/api/control_plane/customers/application/change_customer.py` — mutate gate
- Telephony session path: no `existing_customer_services` usage found under `control_plane/telephony`



### Required Remaining Work

- Add runtime admission checks for disabled existing customer services
- Extend negative tests for voice/number/agent publish paths



### Audit Conclusion

VKT-033 remains **PARTIAL** — substantially improved; voice/runtime coverage still open.

---



# VKT-034 — Implement onboarding/KYC notification triggers



## Jira Definition

**Sprint:** Sprint 2  

### Current Implementation Status

**Overall:** PARTIAL

**Backend:** PARTIAL  
**UI:** N/A  
**Tests:** PARTIAL  

**Re-verified 2026-09-12:** Invitation + KYC notify hooks exist; agency suspend notifies via status path. Full onboarding event matrix still incomplete vs catalog.

### What Already Exists

- `deliver_invitation` on agency create
- `kyc_notify` on KYC webhook/override
- Suspend status triggers notification



### What Is Missing

- Remaining onboarding lifecycle notifications (e.g. invited→active, capability restriction notices) if required by NOT catalog



### Codebase Evidence

- `apps/api/control_plane/notifications/application/hooks.py`
- `apps/api/control_plane/tenancy/application/change_agency.py` — suspend → `kyc_notify`



### Required Remaining Work

- Map EVENT_CATALOG onboarding events to lifecycle hooks and add tests



### Audit Conclusion

VKT-034 remains **PARTIAL**.

---



# VKT-035 — Build plan catalog list

## Jira Definition

**Sprint:** Sprint 3  
**Portal / Layer:** Super Admin  
**Epic:** Plans  
**Module:** Plan list screen  
**Priority:** Must  
**Story Points:** 3  
**Estimated Hours:** 4  
**Dependencies:** VKT-004, VKT-016  

### Definition of Done

List plans and versions with status and commercial terms; expose versioned immutable terms once used by active subscriptions.

### SRS Traceability

- **SRS Traceability (from XLS):** SA11-001..004; PLAN-001

### Current Implementation Status

**Overall:** COMPLETE

**Backend:** COMPLETE  
**UI:** COMPLETE  
**Infrastructure/Integration:** N/A  
**Tests:** PARTIAL  

**Frontend re-audit (2026-09-12):** PlatformPlansScreen provides dedicated plan catalog UI (replaces generic table).

### Backend — Existing Implementation

- Prior backend audit findings retained unless contradicted; see Backend Evidence / previous COMPLETE notes for domain services.

### Frontend/UI — Existing Implementation

- packages/web-ui/src/features/plans/PlatformPlansScreen.tsx
- packages/web-ui/src/features/plans/hooks/usePlatformPlans.ts

### What Is Complete

- Overall status after frontend pull: **COMPLETE**
- Backend: COMPLETE; UI: COMPLETE

### What Is Partial

_N/A or minor residual notes only._

### What Is Missing

- _Nothing material missing relative to DoD (COMPLETE)._

### Backend Evidence

- See prior audit evidence for this VKT ID (domain/API/tests under `apps/api`).

### Frontend Evidence

- `packages/web-ui/src/features/plans/PlatformPlansScreen.tsx`
- `packages/web-ui/src/features/plans/hooks/usePlatformPlans.ts`

### Test Evidence

- Backend tests: see `apps/api/tests/` (status **PARTIAL**).
- Frontend automated tests: **MISSING** (no vitest/RTL/Playwright under `packages/web-ui`).

### Dependency Verification

Jira dependencies: VKT-004, VKT-016

### Required Remaining Work

_None — treat as COMPLETE; only verify/QA if release requires re-attestation._

### Audit Conclusion

VKT-035 is **COMPLETE** after frontend re-audit. **DO NOT REIMPLEMENT.** Previous status was PARTIAL.

---
# VKT-036 — Implement plan CRUD/versioning and entitlements

## Jira Definition

**Sprint:** Sprint 3  
**Portal / Layer:** Super Admin  
**Epic:** Plans  
**Module:** Plan create/edit/version screen  
**Priority:** Must  
**Story Points:** 5  
**Estimated Hours:** 7  
**Dependencies:** VKT-035, VKT-004  

### Definition of Done

Configure price, billing cycle, included minutes, top-ups, overage/hard stop, agent/number/concurrency limits and feature flags. Preserve version used by active subscriptions.

### SRS Traceability

- **SRS Traceability (from XLS):** PLAN-001..007

### Current Implementation Status

**Overall:** COMPLETE

**Backend:** COMPLETE  
**UI:** COMPLETE  
**Infrastructure/Integration:** N/A  
**Tests:** PARTIAL  

**Frontend re-audit (2026-09-12):** Platform plans screen supports plan/version management against billing APIs.

### Backend — Existing Implementation

- Prior backend audit findings retained unless contradicted; see Backend Evidence / previous COMPLETE notes for domain services.

### Frontend/UI — Existing Implementation

- packages/web-ui/src/features/plans/PlatformPlansScreen.tsx
- packages/web-ui/src/features/plans/hooks/usePlatformPlans.ts

### What Is Complete

- Overall status after frontend pull: **COMPLETE**
- Backend: COMPLETE; UI: COMPLETE

### What Is Partial

_N/A or minor residual notes only._

### What Is Missing

- Some entitlement edge UX may remain thin; core CRUD/versioning UI present.

### Backend Evidence

- See prior audit evidence for this VKT ID (domain/API/tests under `apps/api`).

### Frontend Evidence

- `packages/web-ui/src/features/plans/PlatformPlansScreen.tsx`
- `packages/web-ui/src/features/plans/hooks/usePlatformPlans.ts`

### Test Evidence

- Backend tests: see `apps/api/tests/` (status **PARTIAL**).
- Frontend automated tests: **MISSING** (no vitest/RTL/Playwright under `packages/web-ui`).

### Dependency Verification

Jira dependencies: VKT-035, VKT-004

### Required Remaining Work

- Some entitlement edge UX may remain thin; core CRUD/versioning UI present.

### Audit Conclusion

VKT-036 is **COMPLETE** after frontend re-audit. **DO NOT REIMPLEMENT.** Previous status was PARTIAL.

---
# VKT-037 — Build global customer directory



## Jira Definition

**Sprint:** Sprint 3  
**Portal / Layer:** Super Admin  
**Epic:** Customers  
**Module:** Customer directory screen  
**Priority:** Must  
**Story Points:** 3  
**Estimated Hours:** 4  
**Dependencies:** VKT-003, VKT-016  
**Dependency Category:** PARALLEL  
**Flow:** Customers -> filters -> customer detail.  

### Definition of Done

Search/filter customers by agency, status, plan, balance and activity; maintain tenant ownership.

### SRS Traceability

- **SRS Traceability (from XLS):** SA3-001
- **Business rules / state machines / events / acceptance / gates:** Interpreted only from the XLS SRS column and matching SRS sections; see SRS document for full text. Do not invent IDs beyond the XLS column.



### Current Implementation Status

**Overall:** PARTIAL

**Backend:** COMPLETE  
**UI:** PARTIAL  
**Infrastructure/Integration:** N/A  
**Tests:** PARTIAL  

### What Already Exists

- Global customer directory API + PlatformCustomersScreen



### What Is Missing

- Advanced filters/search completeness vs SRS SA3



### What Is Partial

*N/A or covered under Missing/Exists.*

### Codebase Evidence

- packages/web-ui/src/features/customers/PlatformCustomersScreen.tsx
- apps/api/control_plane/customers/api/views.py
- apps/api/tests/test_sa3_customer_api.py



### Dependency Verification

**Jira Dependencies:** VKT-003, VKT-016

**Dependency Status:**

- VKT-003 = PARTIAL
- VKT-016 = COMPLETE

Remaining work may still depend on: VKT-003.

### Acceptance / QA Coverage

Some automated tests exist; gaps remain relative to full DoD/acceptance (see Missing/Remaining).

### Required Remaining Work

- Polish directory filters; link to agency scope



### Audit Conclusion

VKT-037 is **PARTIAL**. Keep existing evidence; finish only the listed remaining work.

---



# VKT-038 — Implement Super Admin customer creation



## Jira Definition

**Sprint:** Sprint 3  
**Portal / Layer:** Super Admin  
**Epic:** Customers  
**Module:** Create/manage customer screen  
**Priority:** Must  
**Story Points:** 5  
**Estimated Hours:** 6  
**Dependencies:** VKT-033, VKT-037  
**Dependency Category:** BLOCKING  
**Flow:** Agency -> create customer -> risk check -> customer Invited/Active per policy.  

### Definition of Done

Create customer under any agency and capture identity/service/commercial controls. Enforce permanently-banned/re-onboarding checks where applicable.

### SRS Traceability

- **SRS Traceability (from XLS):** SA3-002; §24; risk/chargeback rules
- **Business rules / state machines / events / acceptance / gates:** Interpreted only from the XLS SRS column and matching SRS sections; see SRS document for full text. Do not invent IDs beyond the XLS column.



### Current Implementation Status

**Overall:** PARTIAL

**Backend:** COMPLETE  
**UI:** PARTIAL  
**Infrastructure/Integration:** N/A  
**Tests:** PARTIAL  

### What Already Exists

- Super Admin customer create → Invited



### What Is Missing

- Full create wizard fields if SRS requires more than current form



### What Is Partial

*N/A or covered under Missing/Exists.*

### Codebase Evidence

- apps/api/control_plane/customers/application/create_customer.py
- packages/web-ui/src/features/customers/



### Dependency Verification

**Jira Dependencies:** VKT-033, VKT-037

**Dependency Status:**

- VKT-033 = PARTIAL
- VKT-037 = PARTIAL

Remaining work may still depend on: VKT-033, VKT-037.

### Acceptance / QA Coverage

Some automated tests exist; gaps remain relative to full DoD/acceptance (see Missing/Remaining).

### Required Remaining Work

- Align create form with SA3 field set; ban-index checks UX



### Audit Conclusion

VKT-038 is **PARTIAL**. Keep existing evidence; finish only the listed remaining work.

---



# VKT-039 — Implement customer plan assignment, ledger-backed balance adjustment and suspension



## Jira Definition

**Sprint:** Sprint 3  
**Portal / Layer:** Super Admin  
**Epic:** Customers  
**Module:** Customer plan/balance/suspension actions  
**Priority:** Must  
**Story Points:** 5  
**Estimated Hours:** 7  
**Dependencies:** VKT-036, VKT-004, VKT-006, VKT-038  
**Dependency Category:** BLOCKING  
**Flow:** Customer -> action -> policy/permission -> ledger/status -> audit.  

### Definition of Done

Assign/change plan with effective date; adjust minute/monetary balance only through ledger-backed entries; suspend customer independently when authorized.

### SRS Traceability

- **SRS Traceability (from XLS):** SA3-003..005; BR-020
- **Business rules / state machines / events / acceptance / gates:** Interpreted only from the XLS SRS column and matching SRS sections; see SRS document for full text. Do not invent IDs beyond the XLS column.



### Current Implementation Status

**Overall:** PARTIAL

**Backend:** PARTIAL  
**UI:** PARTIAL  
**Infrastructure/Integration:** N/A  
**Tests:** PARTIAL  

### What Already Exists

- Assign subscription, suspend/status, minutes adjust APIs
- Platform customer tabs for balance/plan/status



### What Is Missing

- Mid-cycle plan change/proration (SA3 known gap deferred)
- Impersonation (Should/deferred)



### What Is Partial

*N/A or covered under Missing/Exists.*

### Codebase Evidence

- apps/api/control_plane/billing/application/assign_subscription.py
- apps/api/control_plane/billing/application/adjust_minutes.py
- docs/known-gaps/SA3-CUSTOMERS-BACKEND-GAPS.md



### Dependency Verification

**Jira Dependencies:** VKT-036, VKT-004, VKT-006, VKT-038

**Dependency Status:**

- VKT-036 = PARTIAL
- VKT-004 = PARTIAL
- VKT-006 = COMPLETE
- VKT-038 = PARTIAL

Remaining work may still depend on: VKT-036, VKT-004, VKT-038.

### Acceptance / QA Coverage

Some automated tests exist; gaps remain relative to full DoD/acceptance (see Missing/Remaining).

### Required Remaining Work

- Implement plan change when owner un-defers; keep ledger-backed adjustments audited



### Audit Conclusion

VKT-039 is **PARTIAL**. Keep existing evidence; finish only the listed remaining work.

---



# VKT-040 — Build Agency customer list and create flow



## Jira Definition

**Sprint:** Sprint 3  

### Definition of Done

Agency portal customer list and create flow.

### Current Implementation Status

**Overall:** COMPLETE

**Backend:** COMPLETE  
**UI:** COMPLETE  
**Infrastructure/Integration:** N/A  
**Tests:** COMPLETE  

**Re-verified 2026-09-12:** Agency customer collection API + `CustomersScreen` list/create (with contact fields) satisfy list+create DoD. Detail tabs remain VKT-041.

### What Already Exists

- `AgencyCustomerCollectionView` create/list with capability gates
- Agency `CustomersScreen` create form + table
- Tests under `test_agency_customer_api.py` / SA3 suites



### What Is Missing

*None for list+create DoD.* Customer detail is **VKT-041**.

### Codebase Evidence

- `apps/api/control_plane/customers/api/views.py` — agency customer collection
- `packages/web-ui/src/productScreens.tsx` — `CustomersScreen`
- Capability gate via `assert_agency_may_create_customer`



### Required Remaining Work

*None for VKT-040. Build detail under VKT-041.*

### Audit Conclusion

VKT-040 is **COMPLETE**. **DO NOT REIMPLEMENT** list/create.

---



# VKT-041 — Build agency customer detail

## Jira Definition

**Sprint:** Sprint 3  
**Portal / Layer:** Agency  
**Epic:** Customers  
**Module:** Customer detail/resources screen  
**Priority:** Must  
**Story Points:** 3  
**Estimated Hours:** 5  
**Dependencies:** VKT-040, VKT-008  

### Definition of Done

Show customer profile, service status, plan, agents, numbers, calls, knowledge, integrations, invoices and usage within agency scope.

### SRS Traceability

- **SRS Traceability (from XLS):** AG2-003..005

### Current Implementation Status

**Overall:** NOT_IMPLEMENTED

**Backend:** PARTIAL  
**UI:** NOT_IMPLEMENTED  
**Infrastructure/Integration:** N/A  
**Tests:** PARTIAL  

**Frontend re-audit (2026-09-12):** Platform customer detail exists, but AGENCY portal customer detail/tabs still missing (Jira is agency customer detail).

### Backend — Existing Implementation

- Prior backend audit findings retained unless contradicted; see Backend Evidence / previous COMPLETE notes for domain services.

### Frontend/UI — Existing Implementation

- packages/web-ui/src/productScreens.tsx — CustomersScreen list/create only for agency
- packages/web-ui/src/features/customers/PlatformCustomerDetailScreen.tsx — platform only

### What Is Complete

- Overall status after frontend pull: **NOT_IMPLEMENTED**
- Backend: PARTIAL; UI: NOT_IMPLEMENTED

### What Is Partial

_N/A or minor residual notes only._

### What Is Missing

- Agency portal customer detail with resource tabs

### Backend Evidence

- See prior audit evidence for this VKT ID (domain/API/tests under `apps/api`).

### Frontend Evidence

- `packages/web-ui/src/productScreens.tsx` — CustomersScreen list/create only for agency
- `packages/web-ui/src/features/customers/PlatformCustomerDetailScreen.tsx` — platform only

### Test Evidence

- Backend tests: see `apps/api/tests/` (status **PARTIAL**).
- Frontend automated tests: **MISSING** (no vitest/RTL/Playwright under `packages/web-ui`).

### Dependency Verification

Jira dependencies: VKT-040, VKT-008

### Required Remaining Work

- Agency portal customer detail with resource tabs

### Audit Conclusion

VKT-041 remains **NOT_IMPLEMENTED**. Platform customer detail exists, but AGENCY portal customer detail/tabs still missing (Jira is agency customer detail).

---
# VKT-042 — Implement customer owner/admin invitation



## Jira Definition

**Sprint:** Sprint 3  
**Portal / Layer:** Customer  
**Epic:** Onboarding  
**Module:** Customer invitation/activation  
**Priority:** Must  
**Story Points:** 3  
**Estimated Hours:** 4  
**Dependencies:** VKT-040, VKT-034, VKT-007  
**Dependency Category:** BLOCKING  
**Flow:** Agency creates/invites -> customer accepts -> credentials -> portal.  

### Definition of Done

Customer invitation email links to credential creation/activation; customer status supports Invited -> Active according to platform flow.

### SRS Traceability

- **SRS Traceability (from XLS):** AG2-002; CU8-001; §24.2
- **Business rules / state machines / events / acceptance / gates:** Interpreted only from the XLS SRS column and matching SRS sections; see SRS document for full text. Do not invent IDs beyond the XLS column.



### Current Implementation Status

**Overall:** COMPLETE

**Backend:** COMPLETE  
**UI:** N/A  
**Infrastructure/Integration:** N/A  
**Tests:** COMPLETE  

### What Already Exists

- Customer invitation Invited → accept → Active



### What Is Missing

*Nothing material missing relative to DoD (COMPLETE).* 

### What Is Partial

*N/A or covered under Missing/Exists.*

### Codebase Evidence

- apps/api/control_plane/customers/application/create_customer.py — INVITED
- apps/api/control_plane/identity/application/accept_invitation.py — ActivateCustomerOnInviteAccept
- apps/api/control_plane/customers/application/change_customer.py



### Dependency Verification

**Jira Dependencies:** VKT-040, VKT-034, VKT-007

**Dependency Status:**

- VKT-040 = PARTIAL
- VKT-034 = PARTIAL
- VKT-007 = PARTIAL

Dependencies are COMPLETE or do not block evaluating this task's own gaps.

### Acceptance / QA Coverage

Automated tests covering the core DoD behaviors were found (see Evidence).

### Required Remaining Work

- UI for accept is VKT-024; backend invitation lifecycle COMPLETE



### Audit Conclusion

VKT-042 is **COMPLETE** against repository evidence. **DO NOT REIMPLEMENT.** Only perform verification/QA if required for release.

---



# VKT-043 — Implement customer subscription and invoice lifecycle



## Jira Definition

**Sprint:** Sprint 3  
**Portal / Layer:** Platform  
**Epic:** Billing  
**Module:** Subscription/invoice domain service  
**Priority:** Must  
**Story Points:** 8  
**Estimated Hours:** 8  
**Dependencies:** VKT-036, VKT-038, VKT-004  
**Dependency Category:** BLOCKING  
**Flow:** Customer -> plan -> subscription -> invoice -> payment.  

### Definition of Done

Create customer subscription referencing plan version; create invoices with amount/currency/status/processor reference; support open/paid/failed/refunded states.

### SRS Traceability

- **SRS Traceability (from XLS):** §10.1..10.3; CU5-001
- **Business rules / state machines / events / acceptance / gates:** Interpreted only from the XLS SRS column and matching SRS sections; see SRS document for full text. Do not invent IDs beyond the XLS column.



### Current Implementation Status

**Overall:** PARTIAL

**Backend:** PARTIAL  
**UI:** PARTIAL  
**Infrastructure/Integration:** N/A  
**Tests:** PARTIAL  

### What Already Exists

- Subscription assign, invoices, pay invoice intent, settle grants lots



### What Is Missing

- Full invoice state-machine UI
- Some commercial auto-transitions (Payment Due/Restricted) per SA3 gaps



### What Is Partial

*N/A or covered under Missing/Exists.*

### Codebase Evidence

- apps/api/control_plane/billing/application/assign_subscription.py
- apps/api/control_plane/billing/application/pay_invoice.py
- apps/api/control_plane/billing/application/settle_payment.py



### Dependency Verification

**Jira Dependencies:** VKT-036, VKT-038, VKT-004

**Dependency Status:**

- VKT-036 = PARTIAL
- VKT-038 = PARTIAL
- VKT-004 = PARTIAL

Remaining work may still depend on: VKT-036, VKT-038, VKT-004.

### Acceptance / QA Coverage

Some automated tests exist; gaps remain relative to full DoD/acceptance (see Missing/Remaining).

### Required Remaining Work

- Close deferred commercial status automation; complete invoice UX



### Audit Conclusion

VKT-043 is **PARTIAL**. Keep existing evidence; finish only the listed remaining work.

---



# VKT-044 — Implement hosted/tokenized payment integration boundary



## Jira Definition

**Sprint:** Sprint 3  
**Portal / Layer:** Platform  
**Epic:** Billing  
**Module:** Payment processor adapter  
**Priority:** Must  
**Story Points:** 8  
**Estimated Hours:** 8  
**Dependencies:** VKT-043, VKT-010  
**Dependency Category:** BLOCKING  
**Flow:** Invoice -> processor -> success/failure -> Payment record.  

### Definition of Done

Integrate payment processor through adapter/hosted fields where possible; never store raw card security codes. Handle processor success/failure references.

### SRS Traceability

- **SRS Traceability (from XLS):** BR-002; SEC-004; §10.3
- **Business rules / state machines / events / acceptance / gates:** Interpreted only from the XLS SRS column and matching SRS sections; see SRS document for full text. Do not invent IDs beyond the XLS column.



### Current Implementation Status

**Overall:** PARTIAL

**Backend:** PARTIAL  
**UI:** N/A  
**Infrastructure/Integration:** PARTIAL  
**Tests:** PARTIAL  

**Note:** Lab/sandbox boundary exists; not production-processor-complete.

### What Already Exists

- PaymentProcessor port + Stripe/Braintree adapters
- Checkout intent path



### What Is Missing

- Vendor-native hosted fields/SDK signature schemes
- Production Stripe/Braintree SDK integration



### What Is Partial

*N/A or covered under Missing/Exists.*

### Codebase Evidence

- apps/api/providers/billing/stripe.py
- apps/api/providers/billing/braintree.py
- apps/api/control_plane/billing/infrastructure/container.py



### Dependency Verification

**Jira Dependencies:** VKT-043, VKT-010

**Dependency Status:**

- VKT-043 = PARTIAL
- VKT-010 = PARTIAL

Remaining work may still depend on: VKT-043, VKT-010.

### Acceptance / QA Coverage

Some automated tests exist; gaps remain relative to full DoD/acceptance (see Missing/Remaining).

### Required Remaining Work

- Replace sandbox HMAC adapters with production processor verification + hosted fields



### Audit Conclusion

VKT-044 is **PARTIAL**. Keep existing evidence; finish only the listed remaining work.

---



# VKT-045 — Implement payment webhook handling



## Jira Definition

**Sprint:** Sprint 3  
**Portal / Layer:** Platform  
**Epic:** Billing  
**Module:** Payment webhook idempotency/reconciliation  
**Priority:** Must  
**Story Points:** 5  
**Estimated Hours:** 7  
**Dependencies:** VKT-044, VKT-012  
**Dependency Category:** BLOCKING  
**Flow:** Provider event -> signature validation -> idempotency -> payment state -> downstream event.  

### Definition of Done

Process payment events idempotently using provider event ID/idempotency key; repeated webhook cannot double-settle invoice or create duplicate commission.

### SRS Traceability

- **SRS Traceability (from XLS):** §28; §30; NFR-005
- **Business rules / state machines / events / acceptance / gates:** Interpreted only from the XLS SRS column and matching SRS sections; see SRS document for full text. Do not invent IDs beyond the XLS column.



### Current Implementation Status

**Overall:** COMPLETE

**Backend:** COMPLETE  
**UI:** N/A  
**Infrastructure/Integration:** COMPLETE  
**Tests:** COMPLETE  

### What Already Exists

- Webhook verify + event-id dedup + settle → commission



### What Is Missing

*Nothing material missing relative to DoD (COMPLETE).* 

### What Is Partial

*N/A or covered under Missing/Exists.*

### Codebase Evidence

- apps/api/control_plane/billing/api/views.py — PaymentWebhookView
- apps/api/control_plane/billing/application/settle_payment.py
- apps/api/tests/test_billing_api.py — webhook dedup/forged sig



### Dependency Verification

**Jira Dependencies:** VKT-044, VKT-012

**Dependency Status:**

- VKT-044 = PARTIAL
- VKT-012 = PARTIAL

Dependencies are COMPLETE or do not block evaluating this task's own gaps.

### Acceptance / QA Coverage

Automated tests covering the core DoD behaviors were found (see Evidence).

### Required Remaining Work

- Upgrade signature scheme with VKT-044 production adapters; DoD for handling COMPLETE in lab



### Audit Conclusion

VKT-045 is **COMPLETE** against repository evidence. **DO NOT REIMPLEMENT.** Only perform verification/QA if required for release.

---



# VKT-046 — Implement commissionable revenue calculation



## Jira Definition

**Sprint:** Sprint 3  
**Portal / Layer:** Platform  
**Epic:** Commission  
**Module:** Commission calculation service  
**Priority:** Must  
**Story Points:** 5  
**Estimated Hours:** 7  
**Dependencies:** VKT-021, VKT-045  
**Dependency Category:** BLOCKING  
**Flow:** Paid payment -> eligible line items -> snapshot rate -> commission amount.  

### Definition of Done

Calculate commission only for eligible net revenue using the agency rate/rule snapshot. Exclude tax/promotional/goodwill defaults and apply configurable pass-through rules.

### SRS Traceability

- **SRS Traceability (from XLS):** BR-003; BR-018; §10.4
- **Business rules / state machines / events / acceptance / gates:** Interpreted only from the XLS SRS column and matching SRS sections; see SRS document for full text. Do not invent IDs beyond the XLS column.



### Current Implementation Status

**Overall:** COMPLETE

**Backend:** COMPLETE  
**UI:** N/A  
**Infrastructure/Integration:** N/A  
**Tests:** COMPLETE  

### What Already Exists

- eligible_base_from_lines + commission_amount + rate snapshot



### What Is Missing

*Nothing material missing relative to DoD (COMPLETE).* 

### What Is Partial

*N/A or covered under Missing/Exists.*

### Codebase Evidence

- apps/api/control_plane/commission/application/accrue.py
- apps/api/control_plane/commission/domain/policies.py
- apps/api/tests/test_appendix_c.py



### Dependency Verification

**Jira Dependencies:** VKT-021, VKT-045

**Dependency Status:**

- VKT-021 = PARTIAL
- VKT-045 = COMPLETE

Dependencies are COMPLETE or do not block evaluating this task's own gaps.

### Acceptance / QA Coverage

Automated tests covering the core DoD behaviors were found (see Evidence).

### Required Remaining Work

- None for calculation DoD



### Audit Conclusion

VKT-046 is **COMPLETE** against repository evidence. **DO NOT REIMPLEMENT.** Only perform verification/QA if required for release.

---



# VKT-047 — Implement independent commission holds



## Jira Definition

**Sprint:** Sprint 3  
**Portal / Layer:** Platform  
**Epic:** Commission  
**Module:** 15-day hold scheduler/state transition  
**Priority:** Must  
**Story Points:** 5  
**Estimated Hours:** 6  
**Dependencies:** VKT-046, VKT-004  
**Dependency Category:** BLOCKING  
**Flow:** Commission created On Hold -> date reached/no block -> Available; otherwise remain blocked.  

### Definition of Done

Create one commission entry per qualifying payment with earned_at and available_at = qualifying settlement + 15 days. Held funds remain unavailable; freezes/reversals override release.

### SRS Traceability

- **SRS Traceability (from XLS):** BR-004..006; WAL-001, WAL-006
- **Business rules / state machines / events / acceptance / gates:** Interpreted only from the XLS SRS column and matching SRS sections; see SRS document for full text. Do not invent IDs beyond the XLS column.



### Current Implementation Status

**Overall:** PARTIAL

**Backend:** PARTIAL  
**UI:** N/A  
**Infrastructure/Integration:** N/A  
**Tests:** COMPLETE  

### What Already Exists

- HOLD_DAYS=15, available_at, ReleaseHolds job, wallet projection



### What Is Missing

- Webhook settle path always uses configurable platform_settings hold_days



### What Is Partial

*N/A or covered under Missing/Exists.*

### Codebase Evidence

- apps/api/control_plane/commission/domain/types.py — HOLD_DAYS
- apps/api/control_plane/commission/application/release_holds.py
- apps/api/control_plane/billing/infrastructure/container.py — settle wiring gap
- apps/api/tests/test_settings_domain.py — test_hold_days_are_bounded_and_used



### Dependency Verification

**Jira Dependencies:** VKT-046, VKT-004

**Dependency Status:**

- VKT-046 = COMPLETE
- VKT-004 = PARTIAL

Remaining work may still depend on: VKT-004.

### Acceptance / QA Coverage

Automated tests covering the core DoD behaviors were found (see Evidence).

### Required Remaining Work

- Pass platform_settings().hold_days() into AccrueCommission from settle_payment container



### Audit Conclusion

VKT-047 is **PARTIAL**. Keep existing evidence; finish only the listed remaining work.

---



# VKT-048 — Implement ledger entries and balance derivation



## Jira Definition

**Sprint:** Sprint 3  
**Portal / Layer:** Platform  
**Epic:** Wallet  
**Module:** Immutable wallet ledger service  
**Priority:** Must  
**Story Points:** 8  
**Estimated Hours:** 8  
**Dependencies:** VKT-004, VKT-046  
**Dependency Category:** BLOCKING  
**Flow:** Financial event -> immutable ledger entry -> reproducible wallet buckets.  

### Definition of Done

Implement Commission Earned, Hold Released, Reversal, Manual Credit/Debit, Payout Reserved/Paid, Rejected/Cancelled and Freeze semantics. Cached balance cannot be authoritative.

### SRS Traceability

- **SRS Traceability (from XLS):** BR-020; §11.1..11.2; WAL-001..007
- **Business rules / state machines / events / acceptance / gates:** Interpreted only from the XLS SRS column and matching SRS sections; see SRS document for full text. Do not invent IDs beyond the XLS column.



### Current Implementation Status

**Overall:** COMPLETE

**Backend:** COMPLETE  
**UI:** N/A  
**Infrastructure/Integration:** N/A  
**Tests:** COMPLETE  

### What Already Exists

- Insert-only ledger; balances derived via project_wallet



### What Is Missing

*Nothing material missing relative to DoD (COMPLETE).* 

### What Is Partial

*N/A or covered under Missing/Exists.*

### Codebase Evidence

- apps/api/control_plane/commission/infrastructure/repositories.py — DjangoLedgerRepository.append
- apps/api/control_plane/commission/domain/wallet.py — project_wallet
- apps/api/tests/test_commission_api.py
- apps/api/tests/test_appendix_c.py



### Dependency Verification

**Jira Dependencies:** VKT-004, VKT-046

**Dependency Status:**

- VKT-004 = PARTIAL
- VKT-046 = COMPLETE

Dependencies are COMPLETE or do not block evaluating this task's own gaps.

### Acceptance / QA Coverage

Automated tests covering the core DoD behaviors were found (see Evidence).

### Required Remaining Work

- None for ledger DoD



### Audit Conclusion

VKT-048 is **COMPLETE** against repository evidence. **DO NOT REIMPLEMENT.** Only perform verification/QA if required for release.

---



# VKT-049 — Build Super Admin payments/invoices/reconciliation UI

## Jira Definition

**Sprint:** Sprint 3  
**Portal / Layer:** Super Admin  
**Epic:** Billing  
**Module:** Payments/invoices screen  
**Priority:** Must  
**Story Points:** 5  
**Estimated Hours:** 6  
**Dependencies:** VKT-043, VKT-044, VKT-048  

### Definition of Done

View customer payments, processor state/allocation, invoices, refunds, disputes/chargebacks and ledger-backed manual adjustments with reason.

### SRS Traceability

- **SRS Traceability (from XLS):** SA12-001..005

### Current Implementation Status

**Overall:** COMPLETE

**Backend:** COMPLETE  
**UI:** COMPLETE  
**Infrastructure/Integration:** N/A  
**Tests:** PARTIAL  

**Frontend re-audit (2026-09-12):** PlatformBillingScreen covers payments/invoices/disputes with real platform APIs.

### Backend — Existing Implementation

- Prior backend audit findings retained unless contradicted; see Backend Evidence / previous COMPLETE notes for domain services.

### Frontend/UI — Existing Implementation

- packages/web-ui/src/features/billing/PlatformBillingScreen.tsx
- packages/web-ui/src/features/billing/hooks/usePlatformBilling.ts

### What Is Complete

- Overall status after frontend pull: **COMPLETE**
- Backend: COMPLETE; UI: COMPLETE

### What Is Partial

_N/A or minor residual notes only._

### What Is Missing

- _Nothing material missing relative to DoD (COMPLETE)._

### Backend Evidence

- See prior audit evidence for this VKT ID (domain/API/tests under `apps/api`).

### Frontend Evidence

- `packages/web-ui/src/features/billing/PlatformBillingScreen.tsx`
- `packages/web-ui/src/features/billing/hooks/usePlatformBilling.ts`

### Test Evidence

- Backend tests: see `apps/api/tests/` (status **PARTIAL**).
- Frontend automated tests: **MISSING** (no vitest/RTL/Playwright under `packages/web-ui`).

### Dependency Verification

Jira dependencies: VKT-043, VKT-044, VKT-048

### Required Remaining Work

_None — treat as COMPLETE; only verify/QA if release requires re-attestation._

### Audit Conclusion

VKT-049 is **COMPLETE** after frontend re-audit. **DO NOT REIMPLEMENT.** Previous status was PARTIAL.

---
# VKT-050 — Build agency wallet and bucket visibility



## Jira Definition

**Sprint:** Sprint 3  

### Definition of Done

Show agency wallet buckets (held/available/reserved/paid visibility).

### Current Implementation Status

**Overall:** COMPLETE

**Backend:** COMPLETE  
**UI:** COMPLETE  
**Infrastructure/Integration:** N/A  
**Tests:** PARTIAL  

**Re-verified 2026-09-12:** SA agency Financial tab shows available/held/pending withdrawal/lifetime paid from wallet API; agency portal has Wallet screen + payout request.

### What Already Exists

- `GET /api/v1/platform/agencies/{id}/wallet` and agency wallet endpoint
- `project_wallet` buckets
- SA Financial tab MetricCards for buckets
- Agency `#/wallet` / PaymentsScreen wallet path



### What Is Missing

*None material for bucket visibility DoD.* Deeper ledger browse is VKT-051.

### Codebase Evidence

- `packages/web-ui/src/features/agencies/PlatformAgenciesScreen.tsx` — financial tab buckets
- `packages/web-ui/src/features/agencies/hooks/usePlatformAgencies.ts` — wallet load
- `apps/api/control_plane/commission/domain/wallet.py` — `project_wallet`



### Required Remaining Work

*None for VKT-050.*

### Audit Conclusion

VKT-050 is **COMPLETE**. **DO NOT REIMPLEMENT.**

---



# VKT-051 — Build Agency wallet summary and ledger

## Jira Definition

**Sprint:** Sprint 3  
**Portal / Layer:** Agency  
**Epic:** Wallet/Payouts  
**Module:** Wallet screen  
**Priority:** Must  
**Story Points:** 3  
**Estimated Hours:** 5  
**Dependencies:** VKT-048, VKT-041  

### Definition of Done

Show held/available/frozen/pending withdrawal/lifetime paid plus every earning, reversal, adjustment, hold release and payout.

### SRS Traceability

- **SRS Traceability (from XLS):** AG11-001..002

### Current Implementation Status

**Overall:** PARTIAL

**Backend:** COMPLETE  
**UI:** PARTIAL  
**Infrastructure/Integration:** N/A  
**Tests:** PARTIAL  

**Frontend re-audit (2026-09-12):** Agency wallet route exists but ledger line-item UI still thin; SA wallet buckets are on payouts screen.

### Backend — Existing Implementation

- Prior backend audit findings retained unless contradicted; see Backend Evidence / previous COMPLETE notes for domain services.

### Frontend/UI — Existing Implementation

- packages/web-ui/src/productScreens.tsx — PaymentsScreen /wallet
- packages/web-ui/src/features/payouts/PlatformPayoutsScreen.tsx — SA wallet buckets

### What Is Complete

- Overall status after frontend pull: **PARTIAL**
- Backend: COMPLETE; UI: PARTIAL

### What Is Partial

- Agency ledger entry browser with held/available breakdown

### What Is Missing

- Agency ledger entry browser with held/available breakdown

### Backend Evidence

- See prior audit evidence for this VKT ID (domain/API/tests under `apps/api`).

### Frontend Evidence

- `packages/web-ui/src/productScreens.tsx` — PaymentsScreen /wallet
- `packages/web-ui/src/features/payouts/PlatformPayoutsScreen.tsx` — SA wallet buckets

### Test Evidence

- Backend tests: see `apps/api/tests/` (status **PARTIAL**).
- Frontend automated tests: **MISSING** (no vitest/RTL/Playwright under `packages/web-ui`).

### Dependency Verification

Jira dependencies: VKT-048, VKT-041

### Required Remaining Work

- Agency ledger entry browser with held/available breakdown

### Audit Conclusion

VKT-051 remains **PARTIAL**. Agency wallet route exists but ledger line-item UI still thin; SA wallet buckets are on payouts screen.

---
# VKT-052 — Implement payout request validation and reservation



## Jira Definition

**Sprint:** Sprint 3  
**Portal / Layer:** Agency  
**Epic:** Wallet/Payouts  
**Module:** Withdraw screen  
**Priority:** Must  
**Story Points:** 5  
**Estimated Hours:** 7  
**Dependencies:** VKT-032, VKT-048, VKT-051  
**Dependency Category:** BLOCKING  
**Flow:** Wallet -> Withdraw -> validations -> amount -> atomic reserve -> Requested.  

### Definition of Done

Validate KYC Verified, agency status, payout capability, payout method and available balance. Atomically reserve requested amount from Available to Withdrawal Pending.

### SRS Traceability

- **SRS Traceability (from XLS):** §11.3; WAL-002; KYC-001
- **Business rules / state machines / events / acceptance / gates:** Interpreted only from the XLS SRS column and matching SRS sections; see SRS document for full text. Do not invent IDs beyond the XLS column.



### Current Implementation Status

**Overall:** COMPLETE

**Backend:** COMPLETE  
**UI:** N/A  
**Infrastructure/Integration:** N/A  
**Tests:** COMPLETE  

### What Already Exists

- RequestAgencyPayout with atomic select_for_update reserve + KYC gate + idempotency



### What Is Missing

*Nothing material missing relative to DoD (COMPLETE).* 

### What Is Partial

*N/A or covered under Missing/Exists.*

### Codebase Evidence

- apps/api/control_plane/commission/application/payout.py — RequestAgencyPayout
- apps/api/tests/test_commission_api.py — concurrent reserve



### Dependency Verification

**Jira Dependencies:** VKT-032, VKT-048, VKT-051

**Dependency Status:**

- VKT-032 = PARTIAL
- VKT-048 = COMPLETE
- VKT-051 = PARTIAL

Dependencies are COMPLETE or do not block evaluating this task's own gaps.

### Acceptance / QA Coverage

Automated tests covering the core DoD behaviors were found (see Evidence).

### Required Remaining Work

- None for reservation DoD; UI is separate tasks



### Audit Conclusion

VKT-052 is **COMPLETE** against repository evidence. **DO NOT REIMPLEMENT.** Only perform verification/QA if required for release.

---



# VKT-053 — Build payout review queue and detail

## Jira Definition

**Sprint:** Sprint 3  
**Portal / Layer:** Super Admin  
**Epic:** Wallet/Payouts  
**Module:** Payout queue/detail screen  
**Priority:** Must  
**Story Points:** 5  
**Estimated Hours:** 6  
**Dependencies:** VKT-052, VKT-016  

### Definition of Done

Review requested payouts and risk/compliance context; support approve, reject, freeze and process transitions.

### SRS Traceability

- **SRS Traceability (from XLS):** SA13-002..003; §11.3; §24.5

### Current Implementation Status

**Overall:** COMPLETE

**Backend:** COMPLETE  
**UI:** COMPLETE  
**Infrastructure/Integration:** N/A  
**Tests:** PARTIAL  

**Frontend re-audit (2026-09-12):** PlatformPayoutsScreen implements queue, approve/reject/freeze/process, mark-paid, proof upload/view, receipt metadata.

### Backend — Existing Implementation

- Prior backend audit findings retained unless contradicted; see Backend Evidence / previous COMPLETE notes for domain services.

### Frontend/UI — Existing Implementation

- packages/web-ui/src/features/payouts/PlatformPayoutsScreen.tsx
- packages/web-ui/src/features/payouts/hooks/usePlatformPayouts.ts
- packages/web-ui/src/features/payouts/types.ts — PAYOUT_ACTIONS

### What Is Complete

- Overall status after frontend pull: **COMPLETE**
- Backend: COMPLETE; UI: COMPLETE

### What Is Partial

_N/A or minor residual notes only._

### What Is Missing

- _Nothing material missing relative to DoD (COMPLETE)._

### Backend Evidence

- See prior audit evidence for this VKT ID (domain/API/tests under `apps/api`).

### Frontend Evidence

- `packages/web-ui/src/features/payouts/PlatformPayoutsScreen.tsx`
- `packages/web-ui/src/features/payouts/hooks/usePlatformPayouts.ts`
- `packages/web-ui/src/features/payouts/types.ts` — PAYOUT_ACTIONS

### Test Evidence

- Backend tests: see `apps/api/tests/` (status **PARTIAL**).
- Frontend automated tests: **MISSING** (no vitest/RTL/Playwright under `packages/web-ui`).

### Dependency Verification

Jira dependencies: VKT-052, VKT-016

### Required Remaining Work

_None — treat as COMPLETE; only verify/QA if release requires re-attestation._

### Audit Conclusion

VKT-053 is **COMPLETE** after frontend re-audit. **DO NOT REIMPLEMENT.** Previous status was PARTIAL.

---
# VKT-054 — Implement private proof upload and Paid transition



## Jira Definition

**Sprint:** Sprint 3  
**Portal / Layer:** Super Admin  
**Epic:** Wallet/Payouts  
**Module:** Payout proof + mark paid  
**Priority:** Must  
**Story Points:** 5  
**Estimated Hours:** 6  
**Dependencies:** VKT-053, VKT-014, VKT-006  
**Dependency Category:** BLOCKING  
**Flow:** Processing -> private proof -> transaction ref -> Paid.  

### Definition of Done

Upload private internal payout proof, enter non-sensitive transaction reference, enforce proof-required setting when configured, then mark Paid.

### SRS Traceability

- **SRS Traceability (from XLS):** SA13-004..005; BR-009..010
- **Business rules / state machines / events / acceptance / gates:** Interpreted only from the XLS SRS column and matching SRS sections; see SRS document for full text. Do not invent IDs beyond the XLS column.



### Current Implementation Status

**Overall:** COMPLETE

**Backend:** COMPLETE  
**UI:** N/A  
**Infrastructure/Integration:** N/A  
**Tests:** COMPLETE  

### What Already Exists

- UploadPayoutProof + mark_paid requires proof; agency cannot GET proof



### What Is Missing

*Nothing material missing relative to DoD (COMPLETE).* 

### What Is Partial

*N/A or covered under Missing/Exists.*

### Codebase Evidence

- apps/api/control_plane/commission/application/payout.py — UploadPayoutProof, DecidePayout
- apps/api/control_plane/commission/api/views.py — AgencyPayoutProofView 404
- apps/api/tests/test_commission_api.py — proof ACL / mark-paid without proof



### Dependency Verification

**Jira Dependencies:** VKT-053, VKT-014, VKT-006

**Dependency Status:**

- VKT-053 = PARTIAL
- VKT-014 = PARTIAL
- VKT-006 = COMPLETE

Dependencies are COMPLETE or do not block evaluating this task's own gaps.

### Acceptance / QA Coverage

Automated tests covering the core DoD behaviors were found (see Evidence).

### Required Remaining Work

- UI for proof upload is part of VKT-053 polish



### Audit Conclusion

VKT-054 is **COMPLETE** against repository evidence. **DO NOT REIMPLEMENT.** Only perform verification/QA if required for release.

---



# VKT-055 — Generate agency-visible payout receipt



## Jira Definition

**Sprint:** Sprint 3  
**Portal / Layer:** Platform  
**Epic:** Wallet/Payouts  
**Module:** Payout receipt generator  
**Priority:** Must  
**Story Points:** 3  
**Estimated Hours:** 5  
**Dependencies:** VKT-054, VKT-012  
**Dependency Category:** BLOCKING  
**Flow:** Mark Paid -> finalize ledger -> receipt -> agency notification.  

### Definition of Done

Generate receipt number, agency name, request ID, amount/currency, masked method, request/paid dates, Paid status, masked/non-sensitive reference and issuer details.

### SRS Traceability

- **SRS Traceability (from XLS):** §11.4; BR-010
- **Business rules / state machines / events / acceptance / gates:** Interpreted only from the XLS SRS column and matching SRS sections; see SRS document for full text. Do not invent IDs beyond the XLS column.



### Current Implementation Status

**Overall:** COMPLETE

**Backend:** COMPLETE  
**UI:** N/A  
**Infrastructure/Integration:** N/A  
**Tests:** COMPLETE  

### What Already Exists

- receipt_number on Paid + agency receipt payload



### What Is Missing

*Nothing material missing relative to DoD (COMPLETE).* 

### What Is Partial

*N/A or covered under Missing/Exists.*

### Codebase Evidence

- apps/api/control_plane/commission/api/views.py — AgencyPayoutReceiptView, _receipt_payload
- apps/api/control_plane/commission/application/payout.py — mark_paid generates receipt



### Dependency Verification

**Jira Dependencies:** VKT-054, VKT-012

**Dependency Status:**

- VKT-054 = COMPLETE
- VKT-012 = PARTIAL

Dependencies are COMPLETE or do not block evaluating this task's own gaps.

### Acceptance / QA Coverage

Automated tests covering the core DoD behaviors were found (see Evidence).

### Required Remaining Work

- None for generation DoD



### Audit Conclusion

VKT-055 is **COMPLETE** against repository evidence. **DO NOT REIMPLEMENT.** Only perform verification/QA if required for release.

---



# VKT-056 — Build agency payout history and receipt access

## Jira Definition

**Sprint:** Sprint 3  
**Portal / Layer:** Agency  
**Epic:** Wallet/Payouts  
**Module:** Payout history/receipt screen  
**Priority:** Must  
**Story Points:** 3  
**Estimated Hours:** 4  
**Dependencies:** VKT-055, VKT-008  

### Definition of Done

Agency can view/download generated receipts but cannot access private admin proof.

### SRS Traceability

- **SRS Traceability (from XLS):** AG11-005; BR-009

### Current Implementation Status

**Overall:** PARTIAL

**Backend:** COMPLETE  
**UI:** PARTIAL  
**Infrastructure/Integration:** N/A  
**Tests:** PARTIAL  

**Frontend re-audit (2026-09-12):** Agency payout history list exists; dedicated receipt viewer still not wired to receipt API.

### Backend — Existing Implementation

- Prior backend audit findings retained unless contradicted; see Backend Evidence / previous COMPLETE notes for domain services.

### Frontend/UI — Existing Implementation

- packages/web-ui/src/productScreens.tsx — PayoutsScreen list + request
- SA receipt tab on PlatformPayoutsScreen is platform-scoped

### What Is Complete

- Overall status after frontend pull: **PARTIAL**
- Backend: COMPLETE; UI: PARTIAL

### What Is Partial

- Agency receipt view via GET /api/v1/agency/payouts/{id}/receipt

### What Is Missing

- Agency receipt view via GET /api/v1/agency/payouts/{id}/receipt

### Backend Evidence

- See prior audit evidence for this VKT ID (domain/API/tests under `apps/api`).

### Frontend Evidence

- `packages/web-ui/src/productScreens.tsx` — PayoutsScreen list + request
- `SA receipt tab on PlatformPayoutsScreen is platform-scoped`

### Test Evidence

- Backend tests: see `apps/api/tests/` (status **PARTIAL**).
- Frontend automated tests: **MISSING** (no vitest/RTL/Playwright under `packages/web-ui`).

### Dependency Verification

Jira dependencies: VKT-055, VKT-008

### Required Remaining Work

- Agency receipt view via GET /api/v1/agency/payouts/{id}/receipt

### Audit Conclusion

VKT-056 remains **PARTIAL**. Agency payout history list exists; dedicated receipt viewer still not wired to receipt API.

---
# VKT-057 — Implement commission reversal rules



## Jira Definition

**Sprint:** Sprint 3  
**Portal / Layer:** Platform  
**Epic:** Billing/Commission  
**Module:** Refund/chargeback reversal service  
**Priority:** Must  
**Story Points:** 8  
**Estimated Hours:** 8  
**Dependencies:** VKT-048, VKT-045, VKT-046  
**Dependency Category:** BLOCKING  
**Flow:** Refund/chargeback -> locate original commission -> state-specific reversal -> ledger/audit/event.  

### Definition of Done

Refund during hold reverses held commission; refund after availability debits available; pending payout may be reduced/cancelled/recalculated; paid commission creates negative balance/recovery from future earnings. Never rewrite history.

### SRS Traceability

- **SRS Traceability (from XLS):** BR-017; §28; Appendix C
- **Business rules / state machines / events / acceptance / gates:** Interpreted only from the XLS SRS column and matching SRS sections; see SRS document for full text. Do not invent IDs beyond the XLS column.



### Current Implementation Status

**Overall:** PARTIAL

**Backend:** PARTIAL  
**UI:** N/A  
**Infrastructure/Integration:** PARTIAL  
**Tests:** COMPLETE  

### What Already Exists

- ReverseCommission append-only; Appendix C examples tested; chargeback reverses



### What Is Missing

- Dedicated refund webhook path from processors



### What Is Partial

*N/A or covered under Missing/Exists.*

### Codebase Evidence

- apps/api/control_plane/commission/application/reverse.py
- apps/api/tests/test_appendix_c.py
- apps/api/control_plane/risk/application/apply_chargeback.py



### Dependency Verification

**Jira Dependencies:** VKT-048, VKT-045, VKT-046

**Dependency Status:**

- VKT-048 = COMPLETE
- VKT-045 = COMPLETE
- VKT-046 = COMPLETE

Dependencies are COMPLETE or do not block evaluating this task's own gaps.

### Acceptance / QA Coverage

Automated tests covering the core DoD behaviors were found (see Evidence).

### Required Remaining Work

- Add refund event normalization + ReverseCommission wiring from PaymentWebhookView



### Audit Conclusion

VKT-057 is **PARTIAL**. Keep existing evidence; finish only the listed remaining work.

---



# VKT-058 — Implement confirmed chargeback customer freeze and re-onboarding prevention



## Jira Definition

**Sprint:** Sprint 3  
**Portal / Layer:** Platform  
**Epic:** Risk  
**Module:** Customer chargeback freeze/re-onboarding rules  
**Priority:** Must  
**Story Points:** 8  
**Estimated Hours:** 8  
**Dependencies:** VKT-057, VKT-006, VKT-012  
**Dependency Category:** BLOCKING  
**Flow:** Chargeback -> customer frozen -> agents disabled -> onboarding blocked -> risk/audit/notifications.  

### Definition of Done

Confirmed chargeback freezes the customer, immediately disables all customer agents and production calling, blocks new resources except approved recovery payments, creates a risk event, notifies responsible parties and blocks re-onboarding where permanently banned.

### SRS Traceability

- **SRS Traceability (from XLS):** Risk rules §§16-24; BR-017
- **Business rules / state machines / events / acceptance / gates:** Interpreted only from the XLS SRS column and matching SRS sections; see SRS document for full text. Do not invent IDs beyond the XLS column.



### Current Implementation Status

**Overall:** COMPLETE

**Backend:** COMPLETE  
**UI:** N/A  
**Infrastructure/Integration:** COMPLETE  
**Tests:** COMPLETE  

### What Already Exists

- Chargeback → freeze customer, suspend agents, reverse commissions, ban keys



### What Is Missing

*Nothing material missing relative to DoD (COMPLETE).* 

### What Is Partial

*N/A or covered under Missing/Exists.*

### Codebase Evidence

- apps/api/control_plane/risk/application/apply_chargeback.py
- apps/api/tenant/agents/service.py — suspend_for_customer
- apps/api/tests/test_risk_api.py



### Dependency Verification

**Jira Dependencies:** VKT-057, VKT-006, VKT-012

**Dependency Status:**

- VKT-057 = PARTIAL
- VKT-006 = COMPLETE
- VKT-012 = PARTIAL

Dependencies are COMPLETE or do not block evaluating this task's own gaps.

### Acceptance / QA Coverage

Automated tests covering the core DoD behaviors were found (see Evidence).

### Required Remaining Work

- None for core freeze DoD; re-onboarding prevention covered in risk domain



### Audit Conclusion

VKT-058 is **COMPLETE** against repository evidence. **DO NOT REIMPLEMENT.** Only perform verification/QA if required for release.

---



# VKT-059 — Implement agency fraud/risk actions



## Jira Definition

**Sprint:** Sprint 3  
**Portal / Layer:** Platform  
**Epic:** Risk  
**Module:** Agency fraud/risk controls  
**Priority:** Must  
**Story Points:** 5  
**Estimated Hours:** 6  
**Dependencies:** VKT-022, VKT-058  
**Dependency Category:** BLOCKING  
**Flow:** Risk signal -> Super Admin action -> capability/status changes -> audit/notifications.  

### Definition of Done

Support freezing payouts/wallet, blocking customer/agent/number creation, requiring KYC/re-verification, investigation, suspension and termination while allowing existing services to be handled separately.

### SRS Traceability

- **SRS Traceability (from XLS):** Risk rules §§25-27
- **Business rules / state machines / events / acceptance / gates:** Interpreted only from the XLS SRS column and matching SRS sections; see SRS document for full text. Do not invent IDs beyond the XLS column.



### Current Implementation Status

**Overall:** PARTIAL

**Backend:** PARTIAL  
**UI:** PARTIAL  
**Infrastructure/Integration:** N/A  
**Tests:** PARTIAL  

### What Already Exists

- Risk flag/override tools, freeze capabilities



### What Is Missing

- Agency fraud investigation UX depth



### What Is Partial

*N/A or covered under Missing/Exists.*

### Codebase Evidence

- apps/api/control_plane/risk/application/flag_risk.py
- apps/api/control_plane/risk/application/override.py
- apps/api/tests/test_risk_domain.py



### Dependency Verification

**Jira Dependencies:** VKT-022, VKT-058

**Dependency Status:**

- VKT-022 = PARTIAL
- VKT-058 = COMPLETE

Remaining work may still depend on: VKT-022.

### Acceptance / QA Coverage

Some automated tests exist; gaps remain relative to full DoD/acceptance (see Missing/Remaining).

### Required Remaining Work

- Build agency risk action UX on existing APIs



### Audit Conclusion

VKT-059 is **PARTIAL**. Keep existing evidence; finish only the listed remaining work.

---



# VKT-060 — Implement billing/wallet notification triggers



## Jira Definition

**Sprint:** Sprint 3  
**Portal / Layer:** Platform  
**Epic:** Notifications  
**Module:** Billing/wallet notifications  
**Priority:** Must  
**Story Points:** 3  
**Estimated Hours:** 5  
**Dependencies:** VKT-012, VKT-047, VKT-055  
**Dependency Category:** PARALLEL  
**Flow:** Event -> recipient selection -> in-app/email -> preference enforcement.  

### Definition of Done

Implement payment success/failure, low minutes, commission available, payout requested/paid/rejected and agency restriction/suspension notification triggers.

### SRS Traceability

- **SRS Traceability (from XLS):** §19; NOT-001..005
- **Business rules / state machines / events / acceptance / gates:** Interpreted only from the XLS SRS column and matching SRS sections; see SRS document for full text. Do not invent IDs beyond the XLS column.



### Current Implementation Status

**Overall:** NOT_IMPLEMENTED

**Backend:** NOT_IMPLEMENTED  
**UI:** N/A  
**Infrastructure/Integration:** N/A  
**Tests:** NOT_IMPLEMENTED  

### What Already Exists

- EVENT_CATALOG includes payment/commission/payout events
- NotificationControl.dispatch exists



### What Is Missing

- Dispatch hooks from SettlePayment, ReleaseHolds, DecidePayout, RequestAgencyPayout



### What Is Partial

*N/A or covered under Missing/Exists.*

### Codebase Evidence

- apps/api/control_plane/notifications/domain/types.py — EVENT_CATALOG
- apps/api/control_plane/notifications/application/hooks.py — only deliver_invitation + kyc_notify
- SettlePayment/payout flows use log_event only



### Dependency Verification

**Jira Dependencies:** VKT-012, VKT-047, VKT-055

**Dependency Status:**

- VKT-012 = PARTIAL
- VKT-047 = PARTIAL
- VKT-055 = COMPLETE

Remaining work may still depend on: VKT-012, VKT-047.

### Acceptance / QA Coverage

Required tests for this DoD were not found or are insufficient.

### Required Remaining Work

- Wire notification hooks into billing/commission/payout lifecycle
- Add tests that assert notification delivery on settle/hold/payout



### Audit Conclusion

VKT-060 is **NOT_IMPLEMENTED**. Build the Missing/Remaining items; do not assume adjacent features cover this DoD.

---



# VKT-061 — Build global agent directory and diagnostics entry



## Jira Definition

**Sprint:** Sprint 4  
**Portal / Layer:** Super Admin  
**Epic:** Agents  
**Module:** Agent directory  
**Priority:** Must  
**Story Points:** 3  
**Estimated Hours:** 5  
**Dependencies:** VKT-005, VKT-016  
**Dependency Category:** PARALLEL  
**Flow:** Agents -> filters -> detail/diagnostics.  

### Definition of Done

List all agents by agency/customer/status/type/number; expose runtime configuration, recent calls, errors and integrations.

### SRS Traceability

- **SRS Traceability (from XLS):** SA5-001..003
- **Business rules / state machines / events / acceptance / gates:** Interpreted only from the XLS SRS column and matching SRS sections; see SRS document for full text. Do not invent IDs beyond the XLS column.



### Current Implementation Status

**Overall:** PARTIAL

**Backend:** COMPLETE  
**UI:** PARTIAL  
**Infrastructure/Integration:** N/A  
**Tests:** PARTIAL  

### What Already Exists

- PlatformAgentsScreen + agent directory APIs



### What Is Missing

- Deep diagnostics entry UX



### What Is Partial

*N/A or covered under Missing/Exists.*

### Codebase Evidence

- packages/web-ui/src/features/agents/PlatformAgentsScreen.tsx
- apps/api/control_plane/agents/api/



### Dependency Verification

**Jira Dependencies:** VKT-005, VKT-016

**Dependency Status:**

- VKT-005 = PARTIAL
- VKT-016 = COMPLETE

Remaining work may still depend on: VKT-005.

### Acceptance / QA Coverage

Some automated tests exist; gaps remain relative to full DoD/acceptance (see Missing/Remaining).

### Required Remaining Work

- Add diagnostics drilldown for SA



### Audit Conclusion

VKT-061 is **PARTIAL**. Keep existing evidence; finish only the listed remaining work.

---



# VKT-062 — Implement Super Admin agent lifecycle actions



## Jira Definition

**Sprint:** Sprint 4  
**Portal / Layer:** Super Admin  
**Epic:** Agents  
**Module:** Lifecycle actions  
**Priority:** Must  
**Story Points:** 5  
**Estimated Hours:** 6  
**Dependencies:** VKT-061, VKT-008  
**Dependency Category:** BLOCKING  
**Flow:** Agent action -> validation -> state transition -> audit/event.  

### Definition of Done

Implement create/edit/pause/publish/clone/archive and immediate disable actions with permission checks and audit/history.

### SRS Traceability

- **SRS Traceability (from XLS):** SA5-002..004; AGT-003
- **Business rules / state machines / events / acceptance / gates:** Interpreted only from the XLS SRS column and matching SRS sections; see SRS document for full text. Do not invent IDs beyond the XLS column.



### Current Implementation Status

**Overall:** PARTIAL

**Backend:** PARTIAL  
**UI:** PARTIAL  
**Infrastructure/Integration:** N/A  
**Tests:** PARTIAL  

### What Already Exists

- Some SA agent lifecycle APIs



### What Is Missing

- Complete Super Admin lifecycle action set in UI



### What Is Partial

*N/A or covered under Missing/Exists.*

### Codebase Evidence

- apps/api/control_plane/agents/
- packages/web-ui/src/features/agents/PlatformAgentsScreen.tsx



### Dependency Verification

**Jira Dependencies:** VKT-061, VKT-008

**Dependency Status:**

- VKT-061 = PARTIAL
- VKT-008 = PARTIAL

Remaining work may still depend on: VKT-061, VKT-008.

### Acceptance / QA Coverage

Some automated tests exist; gaps remain relative to full DoD/acceptance (see Missing/Remaining).

### Required Remaining Work

- Expose pause/force-disable/diagnostics actions in SA UI



### Audit Conclusion

VKT-062 is **PARTIAL**. Keep existing evidence; finish only the listed remaining work.

---



# VKT-063 — Build agency agent directory and creation entry



## Jira Definition

**Sprint:** Sprint 4  
**Portal / Layer:** Agency  
**Epic:** Agents  
**Module:** Agent list/create  
**Priority:** Must  
**Story Points:** 3  
**Estimated Hours:** 5  
**Dependencies:** VKT-041, VKT-061  
**Dependency Category:** BLOCKING  
**Flow:** Agency -> Agents -> Create -> source choice -> Draft.  

### Definition of Done

List customer agents within agency scope and start creation from scratch or an allowed template.

### SRS Traceability

- **SRS Traceability (from XLS):** AG3-001
- **Business rules / state machines / events / acceptance / gates:** Interpreted only from the XLS SRS column and matching SRS sections; see SRS document for full text. Do not invent IDs beyond the XLS column.



### Current Implementation Status

**Overall:** PARTIAL

**Backend:** COMPLETE  
**UI:** PARTIAL  
**Infrastructure/Integration:** N/A  
**Tests:** PARTIAL  

### What Already Exists

- Agency agent directory + create entry



### What Is Missing

- Full directory filters/status UX



### What Is Partial

*N/A or covered under Missing/Exists.*

### Codebase Evidence

- packages/web-ui/src/productScreens.tsx — AgentsScreen
- apps/api/control_plane/agents/api/views.py



### Dependency Verification

**Jira Dependencies:** VKT-041, VKT-061

**Dependency Status:**

- VKT-041 = NOT_IMPLEMENTED
- VKT-061 = PARTIAL

Remaining work may still depend on: VKT-041, VKT-061.

### Acceptance / QA Coverage

Some automated tests exist; gaps remain relative to full DoD/acceptance (see Missing/Remaining).

### Required Remaining Work

- Polish agency agent directory



### Audit Conclusion

VKT-063 is **PARTIAL**. Keep existing evidence; finish only the listed remaining work.

---



# VKT-064 — Build Identity stage



## Jira Definition

**Sprint:** Sprint 4  
**Portal / Layer:** Agency  
**Epic:** Agents  
**Module:** Agent Builder - Identity  
**Priority:** Must  
**Story Points:** 2  
**Estimated Hours:** 3  
**Dependencies:** VKT-063  
**Dependency Category:** BLOCKING  
**Flow:** Create -> Identity -> save Draft.  

### Definition of Done

Configure agent name, customer, use case/type, status and timezone. New agent begins Draft.

### SRS Traceability

- **SRS Traceability (from XLS):** §12.2; AGT-001
- **Business rules / state machines / events / acceptance / gates:** Interpreted only from the XLS SRS column and matching SRS sections; see SRS document for full text. Do not invent IDs beyond the XLS column.



### Current Implementation Status

**Overall:** PARTIAL

**Backend:** PARTIAL  
**UI:** PARTIAL  
**Infrastructure/Integration:** N/A  
**Tests:** PARTIAL  

### What Already Exists

- ConfigureAgent covers identity fields in single builder form



### What Is Missing

- Distinct Identity stage wizard UX



### What Is Partial

*N/A or covered under Missing/Exists.*

### Codebase Evidence

- apps/api/control_plane/agents/application/builder.py
- packages/web-ui AgentsScreen builder form



### Dependency Verification

**Jira Dependencies:** VKT-063

**Dependency Status:**

- VKT-063 = PARTIAL

Remaining work may still depend on: VKT-063.

### Acceptance / QA Coverage

Some automated tests exist; gaps remain relative to full DoD/acceptance (see Missing/Remaining).

### Required Remaining Work

- Split builder into Identity stage UI



### Audit Conclusion

VKT-064 is **PARTIAL**. Keep existing evidence; finish only the listed remaining work.

---



# VKT-065 — Build Voice & Language stage



## Jira Definition

**Sprint:** Sprint 4  
**Portal / Layer:** Agency  
**Epic:** Agents  
**Module:** Agent Builder - Voice & Language  
**Priority:** Must  
**Story Points:** 3  
**Estimated Hours:** 4  
**Dependencies:** VKT-064  
**Dependency Category:** BLOCKING  
**Flow:** Draft -> Voice/Language -> save configuration.  

### Definition of Done

Configure provider, voice, language and supported speaking style/speed settings.

### SRS Traceability

- **SRS Traceability (from XLS):** §12.2
- **Business rules / state machines / events / acceptance / gates:** Interpreted only from the XLS SRS column and matching SRS sections; see SRS document for full text. Do not invent IDs beyond the XLS column.



### Current Implementation Status

**Overall:** PARTIAL

**Backend:** PARTIAL  
**UI:** PARTIAL  
**Infrastructure/Integration:** N/A  
**Tests:** PARTIAL  

### What Already Exists

- Voice/language fields in agent configure domain



### What Is Missing

- Dedicated Voice & Language stage UI



### What Is Partial

*N/A or covered under Missing/Exists.*

### Codebase Evidence

- apps/api/control_plane/agents/application/builder.py
- packages/web-ui AgentsScreen



### Dependency Verification

**Jira Dependencies:** VKT-064

**Dependency Status:**

- VKT-064 = PARTIAL

Remaining work may still depend on: VKT-064.

### Acceptance / QA Coverage

Some automated tests exist; gaps remain relative to full DoD/acceptance (see Missing/Remaining).

### Required Remaining Work

- Build Voice & Language stage UI



### Audit Conclusion

VKT-065 is **PARTIAL**. Keep existing evidence; finish only the listed remaining work.

---



# VKT-066 — Build Persona/Instructions stage



## Jira Definition

**Sprint:** Sprint 4  
**Portal / Layer:** Agency  
**Epic:** Agents  
**Module:** Agent Builder - Persona & Instructions  
**Priority:** Must  
**Story Points:** 5  
**Estimated Hours:** 6  
**Dependencies:** VKT-064, VKT-070, VKT-071  
**Dependency Category:** BLOCKING  
**Flow:** Draft -> instructions -> resolve Platform -> Template -> Agency -> Customer -> Agent.  

### Definition of Done

Configure role, goals, constraints, greeting, fallback behavior and layered instruction fields while preserving deterministic precedence.

### SRS Traceability

- **SRS Traceability (from XLS):** §12.2; INS-001..004
- **Business rules / state machines / events / acceptance / gates:** Interpreted only from the XLS SRS column and matching SRS sections; see SRS document for full text. Do not invent IDs beyond the XLS column.



### Current Implementation Status

**Overall:** PARTIAL

**Backend:** PARTIAL  
**UI:** PARTIAL  
**Infrastructure/Integration:** N/A  
**Tests:** PARTIAL  

### What Already Exists

- Persona/instructions configuration backend



### What Is Missing

- Dedicated Persona/Instructions stage UI with inheritance preview



### What Is Partial

*N/A or covered under Missing/Exists.*

### Codebase Evidence

- apps/api/control_plane/agents/application/resolve.py
- packages/web-ui AgentsScreen



### Dependency Verification

**Jira Dependencies:** VKT-064, VKT-070, VKT-071

**Dependency Status:**

- VKT-064 = PARTIAL
- VKT-070 = COMPLETE
- VKT-071 = PARTIAL

Remaining work may still depend on: VKT-064, VKT-071.

### Acceptance / QA Coverage

Some automated tests exist; gaps remain relative to full DoD/acceptance (see Missing/Remaining).

### Required Remaining Work

- Build instructions stage with resolved preview



### Audit Conclusion

VKT-066 is **PARTIAL**. Keep existing evidence; finish only the listed remaining work.

---



# VKT-067 — Build Knowledge attachment stage



## Jira Definition

**Sprint:** Sprint 4  
**Portal / Layer:** Agency  
**Epic:** Agents  
**Module:** Agent Builder - Knowledge  
**Priority:** Must  
**Story Points:** 3  
**Estimated Hours:** 5  
**Dependencies:** VKT-064, VKT-072, VKT-073  
**Dependency Category:** BLOCKING  
**Flow:** Builder -> Knowledge -> select sources -> attach -> resolved agent knowledge.  

### Definition of Done

Select allowed global/agency/customer/agent sources and attach/detach them while enforcing retrieval scope.

### SRS Traceability

- **SRS Traceability (from XLS):** §12.2; KB-001..004; AGT-007
- **Business rules / state machines / events / acceptance / gates:** Interpreted only from the XLS SRS column and matching SRS sections; see SRS document for full text. Do not invent IDs beyond the XLS column.



### Current Implementation Status

**Overall:** PARTIAL

**Backend:** PARTIAL  
**UI:** PARTIAL  
**Infrastructure/Integration:** N/A  
**Tests:** PARTIAL  

### What Already Exists

- Knowledge attach APIs



### What Is Missing

- Dedicated Knowledge attachment stage UI



### What Is Partial

*N/A or covered under Missing/Exists.*

### Codebase Evidence

- apps/api/control_plane/agents/application/knowledge.py
- packages/web-ui AgentsScreen



### Dependency Verification

**Jira Dependencies:** VKT-064, VKT-072, VKT-073

**Dependency Status:**

- VKT-064 = PARTIAL
- VKT-072 = PARTIAL
- VKT-073 = PARTIAL

Remaining work may still depend on: VKT-064, VKT-072, VKT-073.

### Acceptance / QA Coverage

Some automated tests exist; gaps remain relative to full DoD/acceptance (see Missing/Remaining).

### Required Remaining Work

- Build knowledge attachment stage UI



### Audit Conclusion

VKT-067 is **PARTIAL**. Keep existing evidence; finish only the listed remaining work.

---



# VKT-068 — Build Call Handling stage



## Jira Definition

**Sprint:** Sprint 4  
**Portal / Layer:** Agency  
**Epic:** Agents  
**Module:** Agent Builder - Call Handling  
**Priority:** Must  
**Story Points:** 3  
**Estimated Hours:** 5  
**Dependencies:** VKT-064  
**Dependency Category:** BLOCKING  
**Flow:** Builder -> Call Handling -> save -> publish preflight consumes settings.  

### Definition of Done

Configure inbound/outbound permissions, business hours, voicemail/fallback, silence/timeouts and interruption settings.

### SRS Traceability

- **SRS Traceability (from XLS):** §12.2
- **Business rules / state machines / events / acceptance / gates:** Interpreted only from the XLS SRS column and matching SRS sections; see SRS document for full text. Do not invent IDs beyond the XLS column.



### Current Implementation Status

**Overall:** PARTIAL

**Backend:** PARTIAL  
**UI:** PARTIAL  
**Infrastructure/Integration:** N/A  
**Tests:** PARTIAL  

### What Already Exists

- Call handling fields in agent/telephony config



### What Is Missing

- Dedicated Call Handling stage UI



### What Is Partial

*N/A or covered under Missing/Exists.*

### Codebase Evidence

- apps/api/control_plane/agents/
- apps/api/control_plane/telephony/



### Dependency Verification

**Jira Dependencies:** VKT-064

**Dependency Status:**

- VKT-064 = PARTIAL

Remaining work may still depend on: VKT-064.

### Acceptance / QA Coverage

Some automated tests exist; gaps remain relative to full DoD/acceptance (see Missing/Remaining).

### Required Remaining Work

- Build Call Handling stage UI



### Audit Conclusion

VKT-068 is **PARTIAL**. Keep existing evidence; finish only the listed remaining work.

---



# VKT-069 — Build Tools/Actions stage



## Jira Definition

**Sprint:** Sprint 4  
**Portal / Layer:** Agency  
**Epic:** Agents  
**Module:** Agent Builder - Tools/Actions  
**Priority:** Must  
**Story Points:** 3  
**Estimated Hours:** 5  
**Dependencies:** VKT-064, VKT-088  
**Dependency Category:** BLOCKING  
**Flow:** Builder -> Tools -> allowlist -> action schema -> runtime authorization.  

### Definition of Done

Select explicitly allowed normalized actions and parameter schemas; only configured tools can execute.

### SRS Traceability

- **SRS Traceability (from XLS):** §12.2; AGT-005; INT-003..004
- **Business rules / state machines / events / acceptance / gates:** Interpreted only from the XLS SRS column and matching SRS sections; see SRS document for full text. Do not invent IDs beyond the XLS column.



### Current Implementation Status

**Overall:** PARTIAL

**Backend:** PARTIAL  
**UI:** PARTIAL  
**Infrastructure/Integration:** N/A  
**Tests:** PARTIAL  

### What Already Exists

- Tool allowlist in domain



### What Is Missing

- Dedicated Tools/Actions stage UI + mapping (see VKT-084)



### What Is Partial

*N/A or covered under Missing/Exists.*

### Codebase Evidence

- apps/api/control_plane/agents/domain/types.py — ALLOWED_TOOLS
- packages/web-ui AgentsScreen



### Dependency Verification

**Jira Dependencies:** VKT-064, VKT-088

**Dependency Status:**

- VKT-064 = PARTIAL
- VKT-088 = COMPLETE

Remaining work may still depend on: VKT-064.

### Acceptance / QA Coverage

Some automated tests exist; gaps remain relative to full DoD/acceptance (see Missing/Remaining).

### Required Remaining Work

- Build Tools/Actions stage UI



### Audit Conclusion

VKT-069 is **PARTIAL**. Keep existing evidence; finish only the listed remaining work.

---



# VKT-070 — Implement deterministic instruction inheritance/resolution



## Jira Definition

**Sprint:** Sprint 4  
**Portal / Layer:** Platform  
**Epic:** Instructions  
**Module:** Instruction resolution  
**Priority:** Must  
**Story Points:** 5  
**Estimated Hours:** 6  
**Dependencies:** VKT-008, VKT-006  
**Dependency Category:** BLOCKING  
**Flow:** Resolve at runtime/build preview -> ordered layers -> final effective instructions.  

### Definition of Done

Enforce Platform Safety/Global -> Template/Base -> Agency -> Customer -> Agent precedence. Mandatory platform safety rules cannot be overridden.

### SRS Traceability

- **SRS Traceability (from XLS):** §14.1; INS-001..004
- **Business rules / state machines / events / acceptance / gates:** Interpreted only from the XLS SRS column and matching SRS sections; see SRS document for full text. Do not invent IDs beyond the XLS column.



### Current Implementation Status

**Overall:** COMPLETE

**Backend:** COMPLETE  
**UI:** N/A  
**Infrastructure/Integration:** N/A  
**Tests:** COMPLETE  

### What Already Exists

- Deterministic instruction layer resolution platform→template→agency→customer→agent



### What Is Missing

*Nothing material missing relative to DoD (COMPLETE).* 

### What Is Partial

*N/A or covered under Missing/Exists.*

### Codebase Evidence

- apps/api/control_plane/agents/domain/policies.py — resolve_instructions
- apps/api/control_plane/agents/application/resolve.py
- apps/api/tests/test_agents_domain.py / test_agents_api.py



### Dependency Verification

**Jira Dependencies:** VKT-008, VKT-006

**Dependency Status:**

- VKT-008 = PARTIAL
- VKT-006 = COMPLETE

Dependencies are COMPLETE or do not block evaluating this task's own gaps.

### Acceptance / QA Coverage

Automated tests covering the core DoD behaviors were found (see Evidence).

### Required Remaining Work

- None for resolution DoD



### Audit Conclusion

VKT-070 is **COMPLETE** against repository evidence. **DO NOT REIMPLEMENT.** Only perform verification/QA if required for release.

---



# VKT-071 — Build global and template instruction management

## Jira Definition

**Sprint:** Sprint 4  
**Portal / Layer:** Super Admin  
**Epic:** Instructions  
**Module:** Global/template instruction screens  
**Priority:** Must  
**Story Points:** 3  
**Estimated Hours:** 4  
**Dependencies:** VKT-070, VKT-016  

### Definition of Done

Manage platform safety/behavior instructions and reusable template instructions with version/audit history.

### SRS Traceability

- **SRS Traceability (from XLS):** SA7-001..004

### Current Implementation Status

**Overall:** COMPLETE

**Backend:** COMPLETE  
**UI:** COMPLETE  
**Infrastructure/Integration:** N/A  
**Tests:** PARTIAL  

**Frontend re-audit (2026-09-12):** PlatformInstructionsScreen manages global/platform instructions via API.

### Backend — Existing Implementation

- Prior backend audit findings retained unless contradicted; see Backend Evidence / previous COMPLETE notes for domain services.

### Frontend/UI — Existing Implementation

- packages/web-ui/src/features/instructions/PlatformInstructionsScreen.tsx
- packages/web-ui/src/features/instructions/hooks/usePlatformInstructions.ts

### What Is Complete

- Overall status after frontend pull: **COMPLETE**
- Backend: COMPLETE; UI: COMPLETE

### What Is Partial

_N/A or minor residual notes only._

### What Is Missing

- _Nothing material missing relative to DoD (COMPLETE)._

### Backend Evidence

- See prior audit evidence for this VKT ID (domain/API/tests under `apps/api`).

### Frontend Evidence

- `packages/web-ui/src/features/instructions/PlatformInstructionsScreen.tsx`
- `packages/web-ui/src/features/instructions/hooks/usePlatformInstructions.ts`

### Test Evidence

- Backend tests: see `apps/api/tests/` (status **PARTIAL**).
- Frontend automated tests: **MISSING** (no vitest/RTL/Playwright under `packages/web-ui`).

### Dependency Verification

Jira dependencies: VKT-070, VKT-016

### Required Remaining Work

_None — treat as COMPLETE; only verify/QA if release requires re-attestation._

### Audit Conclusion

VKT-071 is **COMPLETE** after frontend re-audit. **DO NOT REIMPLEMENT.** Previous status was PARTIAL.

---
# VKT-072 — Build global knowledge source management

## Jira Definition

**Sprint:** Sprint 4  
**Portal / Layer:** Super Admin  
**Epic:** Knowledge  
**Module:** Global knowledge screen  
**Priority:** Must  
**Story Points:** 3  
**Estimated Hours:** 5  
**Dependencies:** VKT-014, VKT-016  

### Definition of Done

Create shared platform knowledge sources using supported source types and processing states.

### SRS Traceability

- **SRS Traceability (from XLS):** SA8-001..004; KB-001..002

### Current Implementation Status

**Overall:** COMPLETE

**Backend:** COMPLETE  
**UI:** COMPLETE  
**Infrastructure/Integration:** N/A  
**Tests:** PARTIAL  

**Frontend re-audit (2026-09-12):** PlatformKnowledgeScreen provides global knowledge source management UI.

### Backend — Existing Implementation

- Prior backend audit findings retained unless contradicted; see Backend Evidence / previous COMPLETE notes for domain services.

### Frontend/UI — Existing Implementation

- packages/web-ui/src/features/knowledge/PlatformKnowledgeScreen.tsx
- packages/web-ui/src/features/knowledge/hooks/usePlatformKnowledge.ts

### What Is Complete

- Overall status after frontend pull: **COMPLETE**
- Backend: COMPLETE; UI: COMPLETE

### What Is Partial

_N/A or minor residual notes only._

### What Is Missing

- Async Queued/Processing/Failed pipeline UI still absent (VKT-074).

### Backend Evidence

- See prior audit evidence for this VKT ID (domain/API/tests under `apps/api`).

### Frontend Evidence

- `packages/web-ui/src/features/knowledge/PlatformKnowledgeScreen.tsx`
- `packages/web-ui/src/features/knowledge/hooks/usePlatformKnowledge.ts`

### Test Evidence

- Backend tests: see `apps/api/tests/` (status **PARTIAL**).
- Frontend automated tests: **MISSING** (no vitest/RTL/Playwright under `packages/web-ui`).

### Dependency Verification

Jira dependencies: VKT-014, VKT-016

### Required Remaining Work

- Async Queued/Processing/Failed pipeline UI still absent (VKT-074).

### Audit Conclusion

VKT-072 is **COMPLETE** after frontend re-audit. **DO NOT REIMPLEMENT.** Previous status was PARTIAL.

---
# VKT-073 — Build agency-wide and customer-specific knowledge management



## Jira Definition

**Sprint:** Sprint 4  
**Portal / Layer:** Agency  
**Epic:** Knowledge  
**Module:** Agency/customer knowledge  
**Priority:** Must  
**Story Points:** 5  
**Estimated Hours:** 6  
**Dependencies:** VKT-072, VKT-041  
**Dependency Category:** BLOCKING  
**Flow:** Agency/Customer -> Knowledge -> source -> processing -> attach to agent.  

### Definition of Done

Create reusable agency knowledge and customer-specific sources; attach/detach sources to agents; enforce source ownership.

### SRS Traceability

- **SRS Traceability (from XLS):** AG7-001..004; KB-001..004
- **Business rules / state machines / events / acceptance / gates:** Interpreted only from the XLS SRS column and matching SRS sections; see SRS document for full text. Do not invent IDs beyond the XLS column.



### Current Implementation Status

**Overall:** PARTIAL

**Backend:** PARTIAL  
**UI:** PARTIAL  
**Infrastructure/Integration:** N/A  
**Tests:** PARTIAL  

### What Already Exists

- Agency/customer knowledge scope APIs + isolation tests



### What Is Missing

- Full agency/customer knowledge management UIs



### What Is Partial

*N/A or covered under Missing/Exists.*

### Codebase Evidence

- apps/api/tests/test_agents_api.py — knowledge isolation
- apps/api/control_plane/agents/domain/types.py — KnowledgeScope



### Dependency Verification

**Jira Dependencies:** VKT-072, VKT-041

**Dependency Status:**

- VKT-072 = PARTIAL
- VKT-041 = NOT_IMPLEMENTED

Remaining work may still depend on: VKT-072, VKT-041.

### Acceptance / QA Coverage

Some automated tests exist; gaps remain relative to full DoD/acceptance (see Missing/Remaining).

### Required Remaining Work

- Build scoped knowledge UIs



### Audit Conclusion

VKT-073 is **PARTIAL**. Keep existing evidence; finish only the listed remaining work.

---



# VKT-074 — Implement knowledge processing states and failure-safe behavior



## Jira Definition

**Sprint:** Sprint 4  
**Portal / Layer:** Platform  
**Epic:** Knowledge  
**Module:** Ingestion/processing  
**Priority:** Must  
**Story Points:** 5  
**Estimated Hours:** 7  
**Dependencies:** VKT-014, VKT-073  
**Dependency Category:** BLOCKING  
**Flow:** Upload/URL/Q&A -> queue -> processing -> Ready/Failed/Stale -> safe fallback to last valid source.  

### Definition of Done

Support Queued, Processing, Ready, Failed and Stale/Needs Refresh. Failed ingestion must not break a published agent using last valid knowledge where safe.

### SRS Traceability

- **SRS Traceability (from XLS):** KB-001..005; §28
- **Business rules / state machines / events / acceptance / gates:** Interpreted only from the XLS SRS column and matching SRS sections; see SRS document for full text. Do not invent IDs beyond the XLS column.



### Current Implementation Status

**Overall:** NOT_IMPLEMENTED

**Backend:** NOT_IMPLEMENTED  
**UI:** N/A  
**Infrastructure/Integration:** NOT_IMPLEMENTED  
**Tests:** NOT_IMPLEMENTED  

### What Already Exists

- KnowledgeStatus enum includes processing-like values



### What Is Missing

- Async Queued/Processing/Failed/Stale pipeline — ingest is synchronous to ready



### What Is Partial

*N/A or covered under Missing/Exists.*

### Codebase Evidence

- apps/api/control_plane/agents/domain/types.py — KnowledgeStatus
- apps/api/control_plane/agents/application/knowledge.py — sync status=ready



### Dependency Verification

**Jira Dependencies:** VKT-014, VKT-073

**Dependency Status:**

- VKT-014 = PARTIAL
- VKT-073 = PARTIAL

Remaining work may still depend on: VKT-014, VKT-073.

### Acceptance / QA Coverage

Required tests for this DoD were not found or are insufficient.

### Required Remaining Work

- Implement async ingest job + state transitions + failure-safe agent behavior
- Add tests for Failed/Stale handling



### Audit Conclusion

VKT-074 is **NOT_IMPLEMENTED**. Build the Missing/Remaining items; do not assume adjacent features cover this DoD.

---



# VKT-075 — Build template catalog management UI

## Jira Definition

**Sprint:** Sprint 4  
**Portal / Layer:** Super Admin  
**Epic:** Templates  
**Module:** Template catalog screens  
**Priority:** Must  
**Story Points:** 3  
**Estimated Hours:** 5  
**Dependencies:** VKT-005, VKT-016  

### Definition of Done

List/create/edit/version/archive reusable templates and expose metadata/visibility controls.

### SRS Traceability

- **SRS Traceability (from XLS):** SA6-001..004; TPL-001..005

### Current Implementation Status

**Overall:** COMPLETE

**Backend:** COMPLETE  
**UI:** COMPLETE  
**Infrastructure/Integration:** N/A  
**Tests:** PARTIAL  

**Frontend re-audit (2026-09-12):** PlatformTemplatesScreen provides template catalog management UI.

### Backend — Existing Implementation

- Prior backend audit findings retained unless contradicted; see Backend Evidence / previous COMPLETE notes for domain services.

### Frontend/UI — Existing Implementation

- packages/web-ui/src/features/templates/PlatformTemplatesScreen.tsx
- packages/web-ui/src/features/templates/hooks/usePlatformTemplates.ts

### What Is Complete

- Overall status after frontend pull: **COMPLETE**
- Backend: COMPLETE; UI: COMPLETE

### What Is Partial

_N/A or minor residual notes only._

### What Is Missing

- _Nothing material missing relative to DoD (COMPLETE)._

### Backend Evidence

- See prior audit evidence for this VKT ID (domain/API/tests under `apps/api`).

### Frontend Evidence

- `packages/web-ui/src/features/templates/PlatformTemplatesScreen.tsx`
- `packages/web-ui/src/features/templates/hooks/usePlatformTemplates.ts`

### Test Evidence

- Backend tests: see `apps/api/tests/` (status **PARTIAL**).
- Frontend automated tests: **MISSING** (no vitest/RTL/Playwright under `packages/web-ui`).

### Dependency Verification

Jira dependencies: VKT-005, VKT-016

### Required Remaining Work

_None — treat as COMPLETE; only verify/QA if release requires re-attestation._

### Audit Conclusion

VKT-075 is **COMPLETE** after frontend re-audit. **DO NOT REIMPLEMENT.** Previous status was PARTIAL.

---
# VKT-076 — Implement template metadata, visibility and versioning



## Jira Definition

**Sprint:** Sprint 4  
**Portal / Layer:** Super Admin  
**Epic:** Templates  
**Module:** Template metadata/version/visibility  
**Priority:** Must  
**Story Points:** 5  
**Estimated Hours:** 6  
**Dependencies:** VKT-075, VKT-071  
**Dependency Category:** BLOCKING  
**Flow:** Create template -> version -> visibility -> publish.  

### Definition of Done

Configure industry, use case, description, languages, default voice, instructions, recommended tools/knowledge, visibility and versions; revisions cannot silently alter deployed agents.

### SRS Traceability

- **SRS Traceability (from XLS):** TPL-001..005
- **Business rules / state machines / events / acceptance / gates:** Interpreted only from the XLS SRS column and matching SRS sections; see SRS document for full text. Do not invent IDs beyond the XLS column.



### Current Implementation Status

**Overall:** PARTIAL

**Backend:** PARTIAL  
**UI:** PARTIAL  
**Infrastructure/Integration:** N/A  
**Tests:** PARTIAL  

### What Already Exists

- Template metadata/visibility fields in domain



### What Is Missing

- Versioning UI and full visibility controls



### What Is Partial

*N/A or covered under Missing/Exists.*

### Codebase Evidence

- apps/api/control_plane/agents/application/templates.py



### Dependency Verification

**Jira Dependencies:** VKT-075, VKT-071

**Dependency Status:**

- VKT-075 = PARTIAL
- VKT-071 = PARTIAL

Remaining work may still depend on: VKT-075, VKT-071.

### Acceptance / QA Coverage

Some automated tests exist; gaps remain relative to full DoD/acceptance (see Missing/Remaining).

### Required Remaining Work

- Complete template versioning + visibility UI/API gaps



### Audit Conclusion

VKT-076 is **PARTIAL**. Keep existing evidence; finish only the listed remaining work.

---



# VKT-077 — Implement independent editable template installation



## Jira Definition

**Sprint:** Sprint 4  
**Portal / Layer:** Agency  
**Epic:** Templates  
**Module:** Install/clone template  
**Priority:** Must  
**Story Points:** 3  
**Estimated Hours:** 5  
**Dependencies:** VKT-076, VKT-063  
**Dependency Category:** BLOCKING  
**Flow:** Catalog -> Install -> visibility check -> clone configuration -> Draft agent.  

### Definition of Done

Agency installs allowed template and receives an independent editable agent configuration rather than a live shared dependency.

### SRS Traceability

- **SRS Traceability (from XLS):** TPL-002, TPL-004
- **Business rules / state machines / events / acceptance / gates:** Interpreted only from the XLS SRS column and matching SRS sections; see SRS document for full text. Do not invent IDs beyond the XLS column.



### Current Implementation Status

**Overall:** COMPLETE

**Backend:** COMPLETE  
**UI:** N/A  
**Infrastructure/Integration:** N/A  
**Tests:** COMPLETE  

### What Already Exists

- InstallTemplate creates independent editable draft



### What Is Missing

*Nothing material missing relative to DoD (COMPLETE).* 

### What Is Partial

*N/A or covered under Missing/Exists.*

### Codebase Evidence

- apps/api/control_plane/agents/application/templates.py — InstallTemplate
- apps/api/tests/test_agents_api.py — test_template_clone_is_independent



### Dependency Verification

**Jira Dependencies:** VKT-076, VKT-063

**Dependency Status:**

- VKT-076 = PARTIAL
- VKT-063 = PARTIAL

Dependencies are COMPLETE or do not block evaluating this task's own gaps.

### Acceptance / QA Coverage

Automated tests covering the core DoD behaviors were found (see Evidence).

### Required Remaining Work

- None for install DoD



### Audit Conclusion

VKT-077 is **COMPLETE** against repository evidence. **DO NOT REIMPLEMENT.** Only perform verification/QA if required for release.

---



# VKT-078 — Implement telephony provider abstraction



## Jira Definition

**Sprint:** Sprint 4  
**Portal / Layer:** Platform  
**Epic:** Telephony  
**Module:** Provider adapter  
**Priority:** Must  
**Story Points:** 5  
**Estimated Hours:** 6  
**Dependencies:** VKT-011, VKT-010  
**Dependency Category:** BLOCKING  
**Flow:** Core telephony -> adapter -> provider -> normalized result.  

### Definition of Done

Create adapter boundary for number search/purchase/assignment/release and call routing so provider-specific fields do not leak into core business logic.

### SRS Traceability

- **SRS Traceability (from XLS):** TEL-001
- **Business rules / state machines / events / acceptance / gates:** Interpreted only from the XLS SRS column and matching SRS sections; see SRS document for full text. Do not invent IDs beyond the XLS column.



### Current Implementation Status

**Overall:** COMPLETE

**Backend:** COMPLETE  
**UI:** N/A  
**Infrastructure/Integration:** PARTIAL  
**Tests:** PARTIAL  

**Note:** Abstraction COMPLETE; production provider = lab/partial infra.

### What Already Exists

- Telephony provider port + adapters (memory/edge)



### What Is Missing

- Production carrier adapter certification



### What Is Partial

*N/A or covered under Missing/Exists.*

### Codebase Evidence

- apps/api/providers/telephony/
- apps/api/control_plane/telephony/application/ports.py
- apps/api/tests/test_numbers_api.py



### Dependency Verification

**Jira Dependencies:** VKT-011, VKT-010

**Dependency Status:**

- VKT-011 = COMPLETE
- VKT-010 = PARTIAL

Dependencies are COMPLETE or do not block evaluating this task's own gaps.

### Acceptance / QA Coverage

Some automated tests exist; gaps remain relative to full DoD/acceptance (see Missing/Remaining).

### Required Remaining Work

- Bind production provider adapter; keep abstraction COMPLETE



### Audit Conclusion

VKT-078 is **COMPLETE** against repository evidence. **DO NOT REIMPLEMENT.** Only perform verification/QA if required for release.

---



# VKT-079 — Build phone number search UI

## Jira Definition

**Sprint:** Sprint 4  
**Portal / Layer:** Agency  
**Epic:** Phone Numbers  
**Module:** Number search screen  
**Priority:** Must  
**Story Points:** 3  
**Estimated Hours:** 5  
**Dependencies:** VKT-078, VKT-008  

### Definition of Done

Search available supported numbers by country/area/capability and show provider metadata needed for selection.

### SRS Traceability

- **SRS Traceability (from XLS):** TEL-002; AG4-001

### Current Implementation Status

**Overall:** COMPLETE

**Backend:** COMPLETE  
**UI:** COMPLETE  
**Infrastructure/Integration:** PARTIAL  
**Tests:** PARTIAL  

**Frontend re-audit (2026-09-12):** Agency NumbersScreen search + PlatformNumbersScreen inventory; agency search/reserve/assign wired.

### Backend — Existing Implementation

- Prior backend audit findings retained unless contradicted; see Backend Evidence / previous COMPLETE notes for domain services.

### Frontend/UI — Existing Implementation

- packages/web-ui/src/productScreens.tsx — NumbersScreen search/reserve/assign
- packages/web-ui/src/features/numbers/PlatformNumbersScreen.tsx

### What Is Complete

- Overall status after frontend pull: **COMPLETE**
- Backend: COMPLETE; UI: COMPLETE

### What Is Partial

_N/A or minor residual notes only._

### What Is Missing

- _Nothing material missing relative to DoD (COMPLETE)._

### Backend Evidence

- See prior audit evidence for this VKT ID (domain/API/tests under `apps/api`).

### Frontend Evidence

- `packages/web-ui/src/productScreens.tsx` — NumbersScreen search/reserve/assign
- `packages/web-ui/src/features/numbers/PlatformNumbersScreen.tsx`

### Test Evidence

- Backend tests: see `apps/api/tests/` (status **PARTIAL**).
- Frontend automated tests: **MISSING** (no vitest/RTL/Playwright under `packages/web-ui`).

### Dependency Verification

Jira dependencies: VKT-078, VKT-008

### Required Remaining Work

_None — treat as COMPLETE; only verify/QA if release requires re-attestation._

### Audit Conclusion

VKT-079 is **COMPLETE** after frontend re-audit. **DO NOT REIMPLEMENT.** Previous status was PARTIAL.

---
# VKT-080 — Implement number purchase, assignment, release and provisioning states



## Jira Definition

**Sprint:** Sprint 4  
**Portal / Layer:** Agency  
**Epic:** Phone Numbers  
**Module:** Purchase/assignment/release  
**Priority:** Must  
**Story Points:** 8  
**Estimated Hours:** 8  
**Dependencies:** VKT-079, VKT-033, VKT-078  
**Dependency Category:** BLOCKING  
**Flow:** Search -> purchase -> Pending/Active/Failed -> assign -> release -> Releasing/Released.  

### Definition of Done

Purchase only when tenant status, entitlement, payment/balance rules and provider success permit. Assign one active routing target. Release requires confirmation and impact warning.

### SRS Traceability

- **SRS Traceability (from XLS):** TEL-003..010; AG4-001..004
- **Business rules / state machines / events / acceptance / gates:** Interpreted only from the XLS SRS column and matching SRS sections; see SRS document for full text. Do not invent IDs beyond the XLS column.



### Current Implementation Status

**Overall:** PARTIAL

**Backend:** PARTIAL  
**UI:** PARTIAL  
**Infrastructure/Integration:** PARTIAL  
**Tests:** PARTIAL  

### What Already Exists

- Reserve/assign/release flows in domain/API



### What Is Missing

- Full purchase→provision production path UI + provider purchase



### What Is Partial

*N/A or covered under Missing/Exists.*

### Codebase Evidence

- apps/api/control_plane/telephony/models.py — PhoneNumber, PhoneNumberReservation
- apps/api/tests/test_numbers_api.py
- apps/api/tests/test_numbers_domain.py



### Dependency Verification

**Jira Dependencies:** VKT-079, VKT-033, VKT-078

**Dependency Status:**

- VKT-079 = PARTIAL
- VKT-033 = PARTIAL
- VKT-078 = COMPLETE

Remaining work may still depend on: VKT-079, VKT-033.

### Acceptance / QA Coverage

Some automated tests exist; gaps remain relative to full DoD/acceptance (see Missing/Remaining).

### Required Remaining Work

- Complete purchase/provision against real provider; finish UI



### Audit Conclusion

VKT-080 is **PARTIAL**. Keep existing evidence; finish only the listed remaining work.

---



# VKT-081 — Implement idempotent number purchase reconciliation



## Jira Definition

**Sprint:** Sprint 4  
**Portal / Layer:** Platform  
**Epic:** Telephony  
**Module:** Purchase reconciliation  
**Priority:** Must  
**Story Points:** 3  
**Estimated Hours:** 5  
**Dependencies:** VKT-080, VKT-012  
**Dependency Category:** BLOCKING  
**Flow:** Purchase -> timeout/partial result -> provider reconciliation -> final state.  

### Definition of Done

Detect provider success/local timeout or local/provider ambiguity and reconcile through provider query/import or escalation without duplicate purchase.

### SRS Traceability

- **SRS Traceability (from XLS):** TEL-010; §28
- **Business rules / state machines / events / acceptance / gates:** Interpreted only from the XLS SRS column and matching SRS sections; see SRS document for full text. Do not invent IDs beyond the XLS column.



### Current Implementation Status

**Overall:** PARTIAL

**Backend:** PARTIAL  
**UI:** N/A  
**Infrastructure/Integration:** PARTIAL  
**Tests:** PARTIAL  

### What Already Exists

- Reservation/reconcile concepts; inventory reconcile endpoints



### What Is Missing

- Idempotent purchase reconciliation tests/coverage completeness vs DoD



### What Is Partial

*N/A or covered under Missing/Exists.*

### Codebase Evidence

- apps/api/control_plane/telephony/
- apps/api/tests/test_numbers_api.py



### Dependency Verification

**Jira Dependencies:** VKT-080, VKT-012

**Dependency Status:**

- VKT-080 = PARTIAL
- VKT-012 = PARTIAL

Remaining work may still depend on: VKT-080, VKT-012.

### Acceptance / QA Coverage

Some automated tests exist; gaps remain relative to full DoD/acceptance (see Missing/Remaining).

### Required Remaining Work

- Harden purchase idempotency + orphan reconciliation tests



### Audit Conclusion

VKT-081 is **PARTIAL**. Keep existing evidence; finish only the listed remaining work.

---



# VKT-082 — Build transfer destination/team management



## Jira Definition

**Sprint:** Sprint 4  
**Portal / Layer:** Agency  
**Epic:** Transfers  
**Module:** Destination/team screen  
**Priority:** Must  
**Story Points:** 3  
**Estimated Hours:** 5  
**Dependencies:** VKT-078, VKT-008  
**Dependency Category:** BLOCKING  
**Flow:** Transfers -> destination -> validation/verification -> active target.  

### Definition of Done

Create verified/validated transfer destinations such as phone number, department, queue or supported SIP/client target.

### SRS Traceability

- **SRS Traceability (from XLS):** XFER-001..002; AG6-001
- **Business rules / state machines / events / acceptance / gates:** Interpreted only from the XLS SRS column and matching SRS sections; see SRS document for full text. Do not invent IDs beyond the XLS column.



### Current Implementation Status

**Overall:** PARTIAL

**Backend:** PARTIAL  
**UI:** PARTIAL  
**Infrastructure/Integration:** N/A  
**Tests:** PARTIAL  

### What Already Exists

- TransferDestination entities + APIs



### What Is Missing

- Full transfer destination/team management UI



### What Is Partial

*N/A or covered under Missing/Exists.*

### Codebase Evidence

- apps/api/tenant/media/domain.py — TransferDestination
- apps/api/control_plane/telephony/models.py — TransferDestinationIndex



### Dependency Verification

**Jira Dependencies:** VKT-078, VKT-008

**Dependency Status:**

- VKT-078 = COMPLETE
- VKT-008 = PARTIAL

Remaining work may still depend on: VKT-008.

### Acceptance / QA Coverage

Some automated tests exist; gaps remain relative to full DoD/acceptance (see Missing/Remaining).

### Required Remaining Work

- Build transfer destination/team UI



### Audit Conclusion

VKT-082 is **PARTIAL**. Keep existing evidence; finish only the listed remaining work.

---



# VKT-083 — Build transfer rules



## Jira Definition

**Sprint:** Sprint 4  
**Portal / Layer:** Agency  
**Epic:** Transfers  
**Module:** Rules screen  
**Priority:** Must  
**Story Points:** 3  
**Estimated Hours:** 5  
**Dependencies:** VKT-082, VKT-064  
**Dependency Category:** BLOCKING  
**Flow:** Destination -> trigger -> business hours -> transfer -> fallback.  

### Definition of Done

Configure triggers, business hours, timeout/no-answer and fallback behavior, including conditional rules.

### SRS Traceability

- **SRS Traceability (from XLS):** XFER-003..005; AG6-002
- **Business rules / state machines / events / acceptance / gates:** Interpreted only from the XLS SRS column and matching SRS sections; see SRS document for full text. Do not invent IDs beyond the XLS column.



### Current Implementation Status

**Overall:** NOT_IMPLEMENTED

**Backend:** NOT_IMPLEMENTED  
**UI:** NOT_IMPLEMENTED  
**Infrastructure/Integration:** N/A  
**Tests:** NOT_IMPLEMENTED  

### What Already Exists

- TransferDestination exists (not TransferRule)



### What Is Missing

- TransferRule entity and rules engine as specified in Jira/design docs



### What Is Partial

*N/A or covered under Missing/Exists.*

### Codebase Evidence

- docs/execution/04-DATABASE-DESIGN.md mentions transfer_rules
- No TransferRule model under apps/api



### Dependency Verification

**Jira Dependencies:** VKT-082, VKT-064

**Dependency Status:**

- VKT-082 = PARTIAL
- VKT-064 = PARTIAL

Remaining work may still depend on: VKT-082, VKT-064.

### Acceptance / QA Coverage

Required tests for this DoD were not found or are insufficient.

### Required Remaining Work

- Decide: implement TransferRule or formally accept destination-only model via ADR
- If required, build rules + UI



### Audit Conclusion

VKT-083 is **NOT_IMPLEMENTED**. Build the Missing/Remaining items; do not assume adjacent features cover this DoD.

---



# VKT-084 — Build integration/action mapping stage



## Jira Definition

**Sprint:** Sprint 4  
**Portal / Layer:** Agency  
**Epic:** Agents  
**Module:** Agent Builder - Integrations  
**Priority:** Must  
**Story Points:** 3  
**Estimated Hours:** 5  
**Dependencies:** VKT-069, VKT-086  
**Dependency Category:** BLOCKING  
**Flow:** Builder -> Integration -> connection/action -> test -> save mapping.  

### Definition of Done

Map normalized agent actions to authorized CRM/automation/API connections; credentials remain hidden.

### SRS Traceability

- **SRS Traceability (from XLS):** §12.2; INT-001..008
- **Business rules / state machines / events / acceptance / gates:** Interpreted only from the XLS SRS column and matching SRS sections; see SRS document for full text. Do not invent IDs beyond the XLS column.



### Current Implementation Status

**Overall:** NOT_IMPLEMENTED

**Backend:** PARTIAL  
**UI:** NOT_IMPLEMENTED  
**Infrastructure/Integration:** N/A  
**Tests:** PARTIAL  

### What Already Exists

- Action categories + provider_supports_action + connection resolve isolation



### What Is Missing

- Builder stage mapping actions↔connections UI
- First-class AgentAction mapping persistence if required



### What Is Partial

*N/A or covered under Missing/Exists.*

### Codebase Evidence

- apps/api/control_plane/integrations/domain/types.py
- apps/api/control_plane/integrations/application/service.py — _resolve_connection



### Dependency Verification

**Jira Dependencies:** VKT-069, VKT-086

**Dependency Status:**

- VKT-069 = PARTIAL
- VKT-086 = PARTIAL

Remaining work may still depend on: VKT-069, VKT-086.

### Acceptance / QA Coverage

Some automated tests exist; gaps remain relative to full DoD/acceptance (see Missing/Remaining).

### Required Remaining Work

- Build action↔connection mapping stage UI + persistence



### Audit Conclusion

VKT-084 is **NOT_IMPLEMENTED**. Build the Missing/Remaining items; do not assume adjacent features cover this DoD.

---



# VKT-085 — Build Transfers, Phone Number and Compliance stages



## Jira Definition

**Sprint:** Sprint 4  
**Portal / Layer:** Agency  
**Epic:** Agents  
**Module:** Agent Builder - Transfers/Number/Compliance  
**Priority:** Must  
**Story Points:** 5  
**Estimated Hours:** 6  
**Dependencies:** VKT-080, VKT-083, VKT-084  
**Dependency Category:** BLOCKING  
**Flow:** Builder -> Transfers -> Number -> Compliance -> preflight-ready configuration.  

### Definition of Done

Configure transfers, assigned phone number and compliance fields including recording disclosure, prohibited behavior and required disclaimers where configured.

### SRS Traceability

- **SRS Traceability (from XLS):** §12.2; TEL-005..006; XFER-003..005
- **Business rules / state machines / events / acceptance / gates:** Interpreted only from the XLS SRS column and matching SRS sections; see SRS document for full text. Do not invent IDs beyond the XLS column.



### Current Implementation Status

**Overall:** PARTIAL

**Backend:** PARTIAL  
**UI:** PARTIAL  
**Infrastructure/Integration:** N/A  
**Tests:** PARTIAL  

### What Already Exists

- Compliance/telephony fields in domain; some screens



### What Is Missing

- Unified Transfers/Phone/Compliance builder stages UI



### What Is Partial

*N/A or covered under Missing/Exists.*

### Codebase Evidence

- apps/api/control_plane/agents/
- apps/api/control_plane/telephony/
- packages/web-ui AgentsScreen



### Dependency Verification

**Jira Dependencies:** VKT-080, VKT-083, VKT-084

**Dependency Status:**

- VKT-080 = PARTIAL
- VKT-083 = NOT_IMPLEMENTED
- VKT-084 = NOT_IMPLEMENTED

Remaining work may still depend on: VKT-080, VKT-083, VKT-084.

### Acceptance / QA Coverage

Some automated tests exist; gaps remain relative to full DoD/acceptance (see Missing/Remaining).

### Required Remaining Work

- Complete multi-stage builder UX for these areas



### Audit Conclusion

VKT-085 is **PARTIAL**. Keep existing evidence; finish only the listed remaining work.

---



# VKT-086 — Implement integration ownership/OAuth/credential isolation



## Jira Definition

**Sprint:** Sprint 4  
**Portal / Layer:** Platform  
**Epic:** Integrations  
**Module:** Connection service  
**Priority:** Must  
**Story Points:** 5  
**Estimated Hours:** 7  
**Dependencies:** VKT-010, VKT-008  
**Dependency Category:** BLOCKING  
**Flow:** Connect -> OAuth/credential storage -> Active -> disconnect -> revoke/disable dependent actions.  

### Definition of Done

Support agency/customer-owned connections, OAuth where supported, encrypted refresh tokens, revocation and dependent-action disablement.

### SRS Traceability

- **SRS Traceability (from XLS):** INT-001..002, INT-008
- **Business rules / state machines / events / acceptance / gates:** Interpreted only from the XLS SRS column and matching SRS sections; see SRS document for full text. Do not invent IDs beyond the XLS column.



### Current Implementation Status

**Overall:** PARTIAL

**Backend:** PARTIAL  
**UI:** N/A  
**Infrastructure/Integration:** PARTIAL  
**Tests:** PARTIAL  

### What Already Exists

- Per-customer integration ownership + credential SecretRef isolation
- Tenant isolation tests



### What Is Missing

- Real OAuth CRM authorize/callback flows



### What Is Partial

*N/A or covered under Missing/Exists.*

### Codebase Evidence

- apps/api/control_plane/integrations/application/service.py — connect()
- apps/api/providers/integrations/adapters.py — memory stub
- apps/api/tests/test_integrations_api.py



### Dependency Verification

**Jira Dependencies:** VKT-010, VKT-008

**Dependency Status:**

- VKT-010 = PARTIAL
- VKT-008 = PARTIAL

Remaining work may still depend on: VKT-010, VKT-008.

### Acceptance / QA Coverage

Some automated tests exist; gaps remain relative to full DoD/acceptance (see Missing/Remaining).

### Required Remaining Work

- Implement OAuth for HubSpot/Salesforce/Zoho; keep credential isolation



### Audit Conclusion

VKT-086 is **PARTIAL**. Keep existing evidence; finish only the listed remaining work.

---



# VKT-087 — Build integrations UI



## Jira Definition

**Sprint:** Sprint 4  
**Portal / Layer:** Agency  
**Epic:** Integrations  
**Module:** Connection screens  
**Priority:** Must  
**Story Points:** 5  
**Estimated Hours:** 6  
**Dependencies:** VKT-086, VKT-041  
**Dependency Category:** BLOCKING  
**Flow:** Integrations -> provider -> connect -> status -> test -> active/error.  

### Definition of Done

Connect authorized HubSpot, Salesforce, Zoho, QuickBooks and configure n8n/Zapier/Make through webhook/API patterns; never display stored credentials/tokens.

### SRS Traceability

- **SRS Traceability (from XLS):** AG8-001..005
- **Business rules / state machines / events / acceptance / gates:** Interpreted only from the XLS SRS column and matching SRS sections; see SRS document for full text. Do not invent IDs beyond the XLS column.



### Current Implementation Status

**Overall:** PARTIAL

**Backend:** PARTIAL  
**UI:** PARTIAL  
**Infrastructure/Integration:** N/A  
**Tests:** PARTIAL  

### What Already Exists

- Integration APIs; generic UI modules



### What Is Missing

- Full integrations management UI



### What Is Partial

*N/A or covered under Missing/Exists.*

### Codebase Evidence

- packages/web-ui platformModules — integrations
- apps/api/control_plane/integrations/api/views.py



### Dependency Verification

**Jira Dependencies:** VKT-086, VKT-041

**Dependency Status:**

- VKT-086 = PARTIAL
- VKT-041 = NOT_IMPLEMENTED

Remaining work may still depend on: VKT-086, VKT-041.

### Acceptance / QA Coverage

Some automated tests exist; gaps remain relative to full DoD/acceptance (see Missing/Remaining).

### Required Remaining Work

- Build integrations UI with connect/rotate/test



### Audit Conclusion

VKT-087 is **PARTIAL**. Keep existing evidence; finish only the listed remaining work.

---



# VKT-088 — Implement normalized action execution



## Jira Definition

**Sprint:** Sprint 4  
**Portal / Layer:** Platform  
**Epic:** Integrations  
**Module:** Normalized action runtime  
**Priority:** Must  
**Story Points:** 8  
**Estimated Hours:** 8  
**Dependencies:** VKT-086, VKT-087, VKT-069  
**Dependency Category:** BLOCKING  
**Flow:** Agent -> normalized action -> connection -> provider/API -> sanitized result/error.  

### Definition of Done

Implement action schemas, timeout/error behavior, sanitized failures, provider rate limits and authorization so only configured actions execute.

### SRS Traceability

- **SRS Traceability (from XLS):** INT-003..007
- **Business rules / state machines / events / acceptance / gates:** Interpreted only from the XLS SRS column and matching SRS sections; see SRS document for full text. Do not invent IDs beyond the XLS column.



### Current Implementation Status

**Overall:** COMPLETE

**Backend:** COMPLETE  
**UI:** N/A  
**Infrastructure/Integration:** PARTIAL  
**Tests:** COMPLETE  

### What Already Exists

- Normalized tool/action invoke gateway with allowlist



### What Is Missing

*Nothing material missing relative to DoD (COMPLETE).* 

### What Is Partial

*N/A or covered under Missing/Exists.*

### Codebase Evidence

- apps/api/control_plane/integrations/application/service.py
- apps/api/control_plane/agents/domain/policies.py — assert_tools
- apps/api/tests/test_integrations_api.py



### Dependency Verification

**Jira Dependencies:** VKT-086, VKT-087, VKT-069

**Dependency Status:**

- VKT-086 = PARTIAL
- VKT-087 = PARTIAL
- VKT-069 = PARTIAL

Dependencies are COMPLETE or do not block evaluating this task's own gaps.

### Acceptance / QA Coverage

Automated tests covering the core DoD behaviors were found (see Evidence).

### Required Remaining Work

- None for normalize/execute DoD in lab



### Audit Conclusion

VKT-088 is **COMPLETE** against repository evidence. **DO NOT REIMPLEMENT.** Only perform verification/QA if required for release.

---



# VKT-089 — Build webhook endpoint management



## Jira Definition

**Sprint:** Sprint 4  
**Portal / Layer:** Agency  
**Epic:** Webhooks  
**Module:** Endpoint CRUD/subscription screens  
**Priority:** Must  
**Story Points:** 5  
**Estimated Hours:** 6  
**Dependencies:** VKT-010, VKT-012, VKT-041  
**Dependency Category:** BLOCKING  
**Flow:** Webhooks -> endpoint -> event subscriptions -> secret -> test -> active.  

### Definition of Done

Create/update/disable endpoints, subscribe to allowed events, generate/rotate tenant-specific signing secret and send safe test events.

### SRS Traceability

- **SRS Traceability (from XLS):** AG9-001..005; WH-001..005
- **Business rules / state machines / events / acceptance / gates:** Interpreted only from the XLS SRS column and matching SRS sections; see SRS document for full text. Do not invent IDs beyond the XLS column.



### Current Implementation Status

**Overall:** PARTIAL

**Backend:** COMPLETE  
**UI:** PARTIAL  
**Infrastructure/Integration:** N/A  
**Tests:** PARTIAL  

### What Already Exists

- Webhook endpoint CRUD APIs



### What Is Missing

- Rotate/test UI polish



### What Is Partial

*N/A or covered under Missing/Exists.*

### Codebase Evidence

- apps/api/control_plane/integrations/api/
- packages/web-ui — webhooks often generic/missing in agency nav



### Dependency Verification

**Jira Dependencies:** VKT-010, VKT-012, VKT-041

**Dependency Status:**

- VKT-010 = PARTIAL
- VKT-012 = PARTIAL
- VKT-041 = NOT_IMPLEMENTED

Remaining work may still depend on: VKT-010, VKT-012, VKT-041.

### Acceptance / QA Coverage

Some automated tests exist; gaps remain relative to full DoD/acceptance (see Missing/Remaining).

### Required Remaining Work

- Build webhook management UI with rotate/test



### Audit Conclusion

VKT-089 is **PARTIAL**. Keep existing evidence; finish only the listed remaining work.

---



# VKT-090 — Implement signed webhook delivery



## Jira Definition

**Sprint:** Sprint 4  
**Portal / Layer:** Platform  
**Epic:** Webhooks  
**Module:** Signed delivery/retry/replay  
**Priority:** Must  
**Story Points:** 8  
**Estimated Hours:** 8  
**Dependencies:** VKT-089, VKT-012, VKT-011  
**Dependency Category:** BLOCKING  
**Flow:** Domain event -> scoped endpoint -> signed delivery -> response -> retry/replay.  

### Definition of Done

Create unique delivery/event IDs, sign payloads, retry transient failures with bounded backoff, log status/attempts/timestamps, allow eligible replay and support synchronous agent/knowledge webhook patterns.

### SRS Traceability

- **SRS Traceability (from XLS):** WH-001..008; §30.3
- **Business rules / state machines / events / acceptance / gates:** Interpreted only from the XLS SRS column and matching SRS sections; see SRS document for full text. Do not invent IDs beyond the XLS column.



### Current Implementation Status

**Overall:** COMPLETE

**Backend:** COMPLETE  
**UI:** N/A  
**Infrastructure/Integration:** COMPLETE  
**Tests:** COMPLETE  

### What Already Exists

- Signed delivery, retry command, replay API



### What Is Missing

*Nothing material missing relative to DoD (COMPLETE).* 

### What Is Partial

*N/A or covered under Missing/Exists.*

### Codebase Evidence

- apps/api/control_plane/integrations/application/service.py — X-Vokit-Signature
- apps/api/control_plane/integrations/management/commands/retry_webhooks.py
- apps/api/control_plane/integrations/api/urls.py — AgencyWebhookReplayView
- apps/api/tests/test_integrations_api.py



### Dependency Verification

**Jira Dependencies:** VKT-089, VKT-012, VKT-011

**Dependency Status:**

- VKT-089 = PARTIAL
- VKT-012 = PARTIAL
- VKT-011 = COMPLETE

Dependencies are COMPLETE or do not block evaluating this task's own gaps.

### Acceptance / QA Coverage

Automated tests covering the core DoD behaviors were found (see Evidence).

### Required Remaining Work

- None for signed delivery DoD



### Audit Conclusion

VKT-090 is **COMPLETE** against repository evidence. **DO NOT REIMPLEMENT.** Only perform verification/QA if required for release.

---



# VKT-091 — Build browser/simulator test screen

## Jira Definition

**Sprint:** Sprint 5  
**Portal / Layer:** Agency  
**Epic:** Agents  
**Module:** Agent Builder - Test  
**Priority:** Must  
**Story Points:** 5  
**Estimated Hours:** 7  
**Dependencies:** VKT-064, VKT-067, VKT-068, VKT-069, VKT-084, VKT-085  

### Definition of Done

Allow agent test/simulator execution with transcript and tool traces where enabled; Draft/Testing agents cannot receive production traffic.

### SRS Traceability

- **SRS Traceability (from XLS):** AG3-003; §12.2

### Current Implementation Status

**Overall:** PARTIAL

**Backend:** PARTIAL  
**UI:** NOT_IMPLEMENTED  
**Infrastructure/Integration:** N/A  
**Tests:** PARTIAL  

**Frontend re-audit (2026-09-12):** Test-session API remains; no dedicated browser/simulator UI after frontend pull.

### Backend — Existing Implementation

- Prior backend audit findings retained unless contradicted; see Backend Evidence / previous COMPLETE notes for domain services.

### Frontend/UI — Existing Implementation

- AgencyDashboard Test agent CTA navigates to /agents only
- No simulator route under packages/web-ui

### What Is Complete

- Overall status after frontend pull: **PARTIAL**
- Backend: PARTIAL; UI: NOT_IMPLEMENTED

### What Is Partial

- Build simulator/test-session screen consuming agency test-sessions API

### What Is Missing

- Build simulator/test-session screen consuming agency test-sessions API

### Backend Evidence

- See prior audit evidence for this VKT ID (domain/API/tests under `apps/api`).

### Frontend Evidence

- `AgencyDashboard Test agent CTA navigates to /agents only`
- `No simulator route under packages/web-ui`

### Test Evidence

- Backend tests: see `apps/api/tests/` (status **PARTIAL**).
- Frontend automated tests: **MISSING** (no vitest/RTL/Playwright under `packages/web-ui`).

### Dependency Verification

Jira dependencies: VKT-064, VKT-067, VKT-068, VKT-069, VKT-084, VKT-085

### Required Remaining Work

- Build simulator/test-session screen consuming agency test-sessions API

### Audit Conclusion

VKT-091 remains **PARTIAL**. Test-session API remains; no dedicated browser/simulator UI after frontend pull.

---
# VKT-092 — Implement agent publish validation



## Jira Definition

**Sprint:** Sprint 5  
**Portal / Layer:** Platform  
**Epic:** Agents  
**Module:** Publish preflight  
**Priority:** Must  
**Story Points:** 5  
**Estimated Hours:** 7  
**Dependencies:** VKT-091, VKT-033, VKT-036, VKT-080, VKT-070  
**Dependency Category:** BLOCKING  
**Flow:** Draft/Testing -> preflight -> pass -> Active; fail -> actionable validation errors and no production traffic.  

### Definition of Done

Before publish validate customer status, plan entitlement, number/routing, instructions, voice/provider and required compliance fields.

### SRS Traceability

- **SRS Traceability (from XLS):** AGT-002
- **Business rules / state machines / events / acceptance / gates:** Interpreted only from the XLS SRS column and matching SRS sections; see SRS document for full text. Do not invent IDs beyond the XLS column.



### Current Implementation Status

**Overall:** COMPLETE

**Backend:** COMPLETE  
**UI:** N/A  
**Infrastructure/Integration:** N/A  
**Tests:** COMPLETE  

### What Already Exists

- publish_failures preflight gate



### What Is Missing

*Nothing material missing relative to DoD (COMPLETE).* 

### What Is Partial

*N/A or covered under Missing/Exists.*

### Codebase Evidence

- apps/api/control_plane/agents/domain/policies.py — publish_failures
- apps/api/control_plane/agents/application/builder.py — PublishAgent
- apps/api/tests/test_agents_api.py



### Dependency Verification

**Jira Dependencies:** VKT-091, VKT-033, VKT-036, VKT-080, VKT-070

**Dependency Status:**

- VKT-091 = PARTIAL
- VKT-033 = PARTIAL
- VKT-036 = PARTIAL
- VKT-080 = PARTIAL
- VKT-070 = COMPLETE

Dependencies are COMPLETE or do not block evaluating this task's own gaps.

### Acceptance / QA Coverage

Automated tests covering the core DoD behaviors were found (see Evidence).

### Required Remaining Work

- None for validation DoD



### Audit Conclusion

VKT-092 is **COMPLETE** against repository evidence. **DO NOT REIMPLEMENT.** Only perform verification/QA if required for release.

---



# VKT-093 — Build publish, activate, pause and clone actions



## Jira Definition

**Sprint:** Sprint 5  
**Portal / Layer:** Agency  
**Epic:** Agents  
**Module:** Publish/lifecycle screen  
**Priority:** Must  
**Story Points:** 3  
**Estimated Hours:** 5  
**Dependencies:** VKT-092, VKT-062  
**Dependency Category:** BLOCKING  
**Flow:** Test -> Publish -> Active; Active -> Paused; configuration retained.  

### Definition of Done

Implement publish/activate/deactivate/pause and clone flows subject to status, entitlement and permissions. Published changes preserve audit/revision history.

### SRS Traceability

- **SRS Traceability (from XLS):** AG3-004..005; AGT-003..004
- **Business rules / state machines / events / acceptance / gates:** Interpreted only from the XLS SRS column and matching SRS sections; see SRS document for full text. Do not invent IDs beyond the XLS column.



### Current Implementation Status

**Overall:** PARTIAL

**Backend:** PARTIAL  
**UI:** PARTIAL  
**Infrastructure/Integration:** N/A  
**Tests:** PARTIAL  

### What Already Exists

- Publish/pause/clone APIs in agency path



### What Is Missing

- Complete SA lifecycle UI; polished agency action UX



### What Is Partial

*N/A or covered under Missing/Exists.*

### Codebase Evidence

- apps/api/control_plane/agents/application/builder.py
- packages/web-ui AgentsScreen



### Dependency Verification

**Jira Dependencies:** VKT-092, VKT-062

**Dependency Status:**

- VKT-092 = COMPLETE
- VKT-062 = PARTIAL

Remaining work may still depend on: VKT-062.

### Acceptance / QA Coverage

Some automated tests exist; gaps remain relative to full DoD/acceptance (see Missing/Remaining).

### Required Remaining Work

- Complete publish/activate/pause/clone UI across portals



### Audit Conclusion

VKT-093 is **PARTIAL**. Keep existing evidence; finish only the listed remaining work.

---



# VKT-094 — Implement call ingestion and lifecycle persistence



## Jira Definition

**Sprint:** Sprint 5  
**Portal / Layer:** Platform  
**Epic:** Calls  
**Module:** Call lifecycle  
**Priority:** Must  
**Story Points:** 8  
**Estimated Hours:** 8  
**Dependencies:** VKT-078, VKT-093, VKT-005  
**Dependency Category:** BLOCKING  
**Flow:** Call started -> answered -> terminal state -> persisted Call.  

### Definition of Done

Record Vokit/provider IDs, tenant ownership, direction, caller/callee, timestamps, status/disconnect reason, duration and billable usage fields.

### SRS Traceability

- **SRS Traceability (from XLS):** CALL-001..002; §16.1
- **Business rules / state machines / events / acceptance / gates:** Interpreted only from the XLS SRS column and matching SRS sections; see SRS document for full text. Do not invent IDs beyond the XLS column.



### Current Implementation Status

**Overall:** COMPLETE

**Backend:** COMPLETE  
**UI:** N/A  
**Infrastructure/Integration:** COMPLETE  
**Tests:** COMPLETE  

### What Already Exists

- Call lifecycle persistence + indexes



### What Is Missing

*Nothing material missing relative to DoD (COMPLETE).* 

### What Is Partial

*N/A or covered under Missing/Exists.*

### Codebase Evidence

- apps/api/control_plane/telephony/application/session.py
- apps/api/control_plane/telephony/models.py
- apps/api/tests/test_voice_api.py
- apps/api/tests/test_voice_domain.py



### Dependency Verification

**Jira Dependencies:** VKT-078, VKT-093, VKT-005

**Dependency Status:**

- VKT-078 = COMPLETE
- VKT-093 = PARTIAL
- VKT-005 = PARTIAL

Dependencies are COMPLETE or do not block evaluating this task's own gaps.

### Acceptance / QA Coverage

Automated tests covering the core DoD behaviors were found (see Evidence).

### Required Remaining Work

- None for ingestion/lifecycle DoD (lab)



### Audit Conclusion

VKT-094 is **COMPLETE** against repository evidence. **DO NOT REIMPLEMENT.** Only perform verification/QA if required for release.

---



# VKT-095 — Implement inbound routing to assigned agent/fallback



## Jira Definition

**Sprint:** Sprint 5  
**Portal / Layer:** Platform  
**Epic:** Calls  
**Module:** Inbound routing  
**Priority:** Must  
**Story Points:** 8  
**Estimated Hours:** 8  
**Dependencies:** VKT-080, VKT-093, VKT-094  
**Dependency Category:** BLOCKING  
**Flow:** Inbound number -> assignment -> active agent -> call; otherwise configured fallback.  

### Definition of Done

Route incoming calls to the assigned active agent and configured fallback; enforce agent/customer/agency state and provider policy.

### SRS Traceability

- **SRS Traceability (from XLS):** TEL-004..006
- **Business rules / state machines / events / acceptance / gates:** Interpreted only from the XLS SRS column and matching SRS sections; see SRS document for full text. Do not invent IDs beyond the XLS column.



### Current Implementation Status

**Overall:** COMPLETE

**Backend:** COMPLETE  
**UI:** N/A  
**Infrastructure/Integration:** COMPLETE  
**Tests:** COMPLETE  

### What Already Exists

- DID resolve + admission + route to agent



### What Is Missing

*Nothing material missing relative to DoD (COMPLETE).* 

### What Is Partial

*N/A or covered under Missing/Exists.*

### Codebase Evidence

- apps/api/control_plane/telephony/api/internal.py
- apps/api/control_plane/telephony/application/session.py — resolve_did
- apps/api/tests/test_voice_api.py



### Dependency Verification

**Jira Dependencies:** VKT-080, VKT-093, VKT-094

**Dependency Status:**

- VKT-080 = PARTIAL
- VKT-093 = PARTIAL
- VKT-094 = COMPLETE

Dependencies are COMPLETE or do not block evaluating this task's own gaps.

### Acceptance / QA Coverage

Automated tests covering the core DoD behaviors were found (see Evidence).

### Required Remaining Work

- Live canary attestation (VKT-143/150) still open



### Audit Conclusion

VKT-095 is **COMPLETE** against repository evidence. **DO NOT REIMPLEMENT.** Only perform verification/QA if required for release.

---



# VKT-096 — Implement outbound calling/caller ID where enabled



## Jira Definition

**Sprint:** Sprint 5  
**Portal / Layer:** Platform  
**Epic:** Calls  
**Module:** Outbound calling  
**Priority:** Must  
**Story Points:** 5  
**Estimated Hours:** 6  
**Dependencies:** VKT-095, VKT-093  
**Dependency Category:** BLOCKING  
**Flow:** Agent outbound -> entitlement/config check -> authorized caller ID -> provider -> Call.  

### Definition of Done

Support outbound agent calling where enabled by configuration/provider policy, using authorized caller ID and normalized number rules.

### SRS Traceability

- **SRS Traceability (from XLS):** TEL-006; §2.1
- **Business rules / state machines / events / acceptance / gates:** Interpreted only from the XLS SRS column and matching SRS sections; see SRS document for full text. Do not invent IDs beyond the XLS column.



### Current Implementation Status

**Overall:** PARTIAL

**Backend:** PARTIAL  
**UI:** N/A  
**Infrastructure/Integration:** PARTIAL  
**Tests:** PARTIAL  

### What Already Exists

- Agency outbound call API + session outbound path



### What Is Missing

- Production outbound/caller-ID certification



### What Is Partial

*N/A or covered under Missing/Exists.*

### Codebase Evidence

- apps/api/control_plane/telephony/api/views.py — AgencyOutboundCallView
- apps/api/tests/test_media_api.py



### Dependency Verification

**Jira Dependencies:** VKT-095, VKT-093

**Dependency Status:**

- VKT-095 = COMPLETE
- VKT-093 = PARTIAL

Remaining work may still depend on: VKT-093.

### Acceptance / QA Coverage

Some automated tests exist; gaps remain relative to full DoD/acceptance (see Missing/Remaining).

### Required Remaining Work

- Enable/verify outbound where entitled; live attestation



### Audit Conclusion

VKT-096 is **PARTIAL**. Keep existing evidence; finish only the listed remaining work.

---



# VKT-097 — Implement billable usage and entitlement linkage



## Jira Definition

**Sprint:** Sprint 5  
**Portal / Layer:** Platform  
**Epic:** Calls  
**Module:** Usage charging  
**Priority:** Must  
**Story Points:** 8  
**Estimated Hours:** 8  
**Dependencies:** VKT-094, VKT-043  
**Dependency Category:** BLOCKING  
**Flow:** Call duration -> billable units -> plan allocation/overage -> usage/balance.  

### Definition of Done

Calculate billable usage consistently and link usage to customer subscription/balance, plan allocation and overage/hard-stop behavior.

### SRS Traceability

- **SRS Traceability (from XLS):** CALL-002; PLAN-002..005
- **Business rules / state machines / events / acceptance / gates:** Interpreted only from the XLS SRS column and matching SRS sections; see SRS document for full text. Do not invent IDs beyond the XLS column.



### Current Implementation Status

**Overall:** COMPLETE

**Backend:** COMPLETE  
**UI:** N/A  
**Infrastructure/Integration:** N/A  
**Tests:** COMPLETE  

### What Already Exists

- billable minutes, grace/overage continue decisions, lot drain



### What Is Missing

*Nothing material missing relative to DoD (COMPLETE).* 

### What Is Partial

*N/A or covered under Missing/Exists.*

### Codebase Evidence

- apps/api/control_plane/telephony/domain/admission.py
- apps/api/tests/test_voice_domain.py — grace/overage tests



### Dependency Verification

**Jira Dependencies:** VKT-094, VKT-043

**Dependency Status:**

- VKT-094 = COMPLETE
- VKT-043 = PARTIAL

Dependencies are COMPLETE or do not block evaluating this task's own gaps.

### Acceptance / QA Coverage

Automated tests covering the core DoD behaviors were found (see Evidence).

### Required Remaining Work

- None for entitlement linkage DoD



### Audit Conclusion

VKT-097 is **COMPLETE** against repository evidence. **DO NOT REIMPLEMENT.** Only perform verification/QA if required for release.

---



# VKT-098 — Implement recording/transcript/summary artifact service



## Jira Definition

**Sprint:** Sprint 5  
**Portal / Layer:** Platform  
**Epic:** Calls  
**Module:** Artifacts  
**Priority:** Must  
**Story Points:** 8  
**Estimated Hours:** 8  
**Dependencies:** VKT-094, VKT-014  
**Dependency Category:** BLOCKING  
**Flow:** Call completed -> artifacts ready -> permission check -> authorized viewer.  

### Definition of Done

Persist recording/transcript/summary references and optional sentiment/outcome/tool activity; enforce role, tenant, legal configuration and retention metadata.

### SRS Traceability

- **SRS Traceability (from XLS):** CALL-003..005; PRIV-003..004
- **Business rules / state machines / events / acceptance / gates:** Interpreted only from the XLS SRS column and matching SRS sections; see SRS document for full text. Do not invent IDs beyond the XLS column.



### Current Implementation Status

**Overall:** COMPLETE

**Backend:** COMPLETE  
**UI:** N/A  
**Infrastructure/Integration:** PARTIAL  
**Tests:** COMPLETE  

**Note:** Django artifact service COMPLETE per ADR-002; recording server is separate infra.

### What Already Exists

- Recording metadata + grants + internal ingest; transcript/summary as artifacts model



### What Is Missing

- In-repo recording server binary (separate plane)



### What Is Partial

*N/A or covered under Missing/Exists.*

### Codebase Evidence

- apps/api/control_plane/recordings/application/service.py
- apps/api/control_plane/recordings/api/
- apps/api/tests/test_recordings_api.py
- docs/adr/ADR-002-recording-storage-separation.md



### Dependency Verification

**Jira Dependencies:** VKT-094, VKT-014

**Dependency Status:**

- VKT-094 = COMPLETE
- VKT-014 = PARTIAL

Dependencies are COMPLETE or do not block evaluating this task's own gaps.

### Acceptance / QA Coverage

Automated tests covering the core DoD behaviors were found (see Evidence).

### Required Remaining Work

- Operate separate recording plane; live play attestation



### Audit Conclusion

VKT-098 is **COMPLETE** against repository evidence. **DO NOT REIMPLEMENT.** Only perform verification/QA if required for release.

---



# VKT-099 — Implement transfer execution and call linkage



## Jira Definition

**Sprint:** Sprint 5  
**Portal / Layer:** Platform  
**Epic:** Transfers  
**Module:** Human handoff runtime  
**Priority:** Must  
**Story Points:** 5  
**Estimated Hours:** 7  
**Dependencies:** VKT-083, VKT-095, VKT-094  
**Dependency Category:** BLOCKING  
**Flow:** Call -> trigger -> destination -> connect/no-answer -> fallback -> call outcome.  

### Definition of Done

Execute configured transfer triggers/business hours/fallback; preserve context/whisper where supported and record transfer attempt/outcome in call record.

### SRS Traceability

- **SRS Traceability (from XLS):** XFER-003..007
- **Business rules / state machines / events / acceptance / gates:** Interpreted only from the XLS SRS column and matching SRS sections; see SRS document for full text. Do not invent IDs beyond the XLS column.



### Current Implementation Status

**Overall:** PARTIAL

**Backend:** COMPLETE  
**UI:** N/A  
**Infrastructure/Integration:** PARTIAL  
**Tests:** COMPLETE  

### What Already Exists

- request_transfer / transfer_status Django path + ADR-006



### What Is Missing

- Full production transfer media certification



### What Is Partial

*N/A or covered under Missing/Exists.*

### Codebase Evidence

- apps/api/control_plane/telephony/application/session.py — request_transfer
- docs/adr/ADR-006-transfer-voicemail-media-contracts.md
- apps/api/tests/test_media_api.py — transfer tests



### Dependency Verification

**Jira Dependencies:** VKT-083, VKT-095, VKT-094

**Dependency Status:**

- VKT-083 = NOT_IMPLEMENTED
- VKT-095 = COMPLETE
- VKT-094 = COMPLETE

Remaining work may still depend on: VKT-083.

### Acceptance / QA Coverage

Automated tests covering the core DoD behaviors were found (see Evidence).

### Required Remaining Work

- Live transfer acceptance under VKT-144



### Audit Conclusion

VKT-099 is **PARTIAL**. Keep existing evidence; finish only the listed remaining work.

---



# VKT-100 — Build Super Admin call monitoring

## Jira Definition

**Sprint:** Sprint 5  
**Portal / Layer:** Super Admin  
**Epic:** Calls  
**Module:** Global call list/detail  
**Priority:** Must  
**Story Points:** 5  
**Estimated Hours:** 6  
**Dependencies:** VKT-094, VKT-098, VKT-016  

### Definition of Done

Search all calls by agency/customer/agent/number/date/status/direction; detail shows provider ID, timestamps, duration, billable units, artifacts and tool activity; platform cost is permission-gated.

### SRS Traceability

- **SRS Traceability (from XLS):** SA14-001..004

### Current Implementation Status

**Overall:** COMPLETE

**Backend:** COMPLETE  
**UI:** COMPLETE  
**Infrastructure/Integration:** N/A  
**Tests:** PARTIAL  

**Frontend re-audit (2026-09-12):** PlatformCallsScreen provides dedicated SA call monitoring list/detail.

### Backend — Existing Implementation

- Prior backend audit findings retained unless contradicted; see Backend Evidence / previous COMPLETE notes for domain services.

### Frontend/UI — Existing Implementation

- packages/web-ui/src/features/calls/PlatformCallsScreen.tsx
- packages/web-ui/src/features/calls/hooks/usePlatformCalls.ts

### What Is Complete

- Overall status after frontend pull: **COMPLETE**
- Backend: COMPLETE; UI: COMPLETE

### What Is Partial

_N/A or minor residual notes only._

### What Is Missing

- _Nothing material missing relative to DoD (COMPLETE)._

### Backend Evidence

- See prior audit evidence for this VKT ID (domain/API/tests under `apps/api`).

### Frontend Evidence

- `packages/web-ui/src/features/calls/PlatformCallsScreen.tsx`
- `packages/web-ui/src/features/calls/hooks/usePlatformCalls.ts`

### Test Evidence

- Backend tests: see `apps/api/tests/` (status **PARTIAL**).
- Frontend automated tests: **MISSING** (no vitest/RTL/Playwright under `packages/web-ui`).

### Dependency Verification

Jira dependencies: VKT-094, VKT-098, VKT-016

### Required Remaining Work

_None — treat as COMPLETE; only verify/QA if release requires re-attestation._

### Audit Conclusion

VKT-100 is **COMPLETE** after frontend re-audit. **DO NOT REIMPLEMENT.** Previous status was PARTIAL.

---
# VKT-101 — Build agency call monitoring



## Jira Definition

**Sprint:** Sprint 5  
**Portal / Layer:** Agency  
**Epic:** Calls  
**Module:** Agency call list/detail  
**Priority:** Must  
**Story Points:** 3  
**Estimated Hours:** 5  
**Dependencies:** VKT-100, VKT-008  
**Dependency Category:** BLOCKING  
**Flow:** Agency -> Calls -> filter -> detail -> privacy authorization.  

### Definition of Done

Agency-wide call list/detail with filters and recording/transcript/summary/outcome/tools where enabled, subject to customer agreement/platform privacy policy.

### SRS Traceability

- **SRS Traceability (from XLS):** AG5-001..003
- **Business rules / state machines / events / acceptance / gates:** Interpreted only from the XLS SRS column and matching SRS sections; see SRS document for full text. Do not invent IDs beyond the XLS column.



### Current Implementation Status

**Overall:** PARTIAL

**Backend:** PARTIAL  
**UI:** PARTIAL  
**Infrastructure/Integration:** N/A  
**Tests:** PARTIAL  

### What Already Exists

- Agency call list APIs / screens (limited)



### What Is Missing

- Full agency call monitoring UX



### What Is Partial

*N/A or covered under Missing/Exists.*

### Codebase Evidence

- packages/web-ui productScreens / nav
- apps/api/control_plane/telephony/



### Dependency Verification

**Jira Dependencies:** VKT-100, VKT-008

**Dependency Status:**

- VKT-100 = PARTIAL
- VKT-008 = PARTIAL

Remaining work may still depend on: VKT-100, VKT-008.

### Acceptance / QA Coverage

Some automated tests exist; gaps remain relative to full DoD/acceptance (see Missing/Remaining).

### Required Remaining Work

- Build agency call monitoring with filters



### Audit Conclusion

VKT-101 is **PARTIAL**. Keep existing evidence; finish only the listed remaining work.

---



# VKT-102 — Build Customer Portal shell



## Jira Definition

**Sprint:** Sprint 5  
**Portal / Layer:** Customer  
**Epic:** Portal Shell  
**Module:** Layout/navigation  
**Priority:** Must  
**Story Points:** 3  
**Estimated Hours:** 5  
**Dependencies:** VKT-042, VKT-008  
**Dependency Category:** BLOCKING  
**Flow:** Customer login -> shell -> customer-owned modules only.  

### Definition of Done

Create authenticated customer layout, responsive monitoring/basic-action navigation and customer-scope route guards.

### SRS Traceability

- **SRS Traceability (from XLS):** §9; NFR-009
- **Business rules / state machines / events / acceptance / gates:** Interpreted only from the XLS SRS column and matching SRS sections; see SRS document for full text. Do not invent IDs beyond the XLS column.



### Current Implementation Status

**Overall:** COMPLETE

**Backend:** N/A  
**UI:** COMPLETE  
**Infrastructure/Integration:** N/A  
**Tests:** N/A  

### What Already Exists

- Customer portal shell mounting PortalApp



### What Is Missing

*Nothing material missing relative to DoD (COMPLETE).* 

### What Is Partial

*N/A or covered under Missing/Exists.*

### Codebase Evidence

- apps/web-customer/src/main.tsx
- packages/web-ui/src/PortalApp.tsx
- packages/web-ui/src/components/layout/AppShell.tsx



### Dependency Verification

**Jira Dependencies:** VKT-042, VKT-008

**Dependency Status:**

- VKT-042 = COMPLETE
- VKT-008 = PARTIAL

Dependencies are COMPLETE or do not block evaluating this task's own gaps.

### Acceptance / QA Coverage

Test applicability limited (N/A) or not separately scored.

### Required Remaining Work

- None for shell DoD



### Audit Conclusion

VKT-102 is **COMPLETE** against repository evidence. **DO NOT REIMPLEMENT.** Only perform verification/QA if required for release.

---



# VKT-103 — Build Customer dashboard



## Jira Definition

**Sprint:** Sprint 5  
**Portal / Layer:** Customer  
**Epic:** Dashboard  
**Module:** Dashboard  
**Priority:** Must  
**Story Points:** 5  
**Estimated Hours:** 6  
**Dependencies:** VKT-097, VKT-043, VKT-102  
**Dependency Category:** BLOCKING  
**Flow:** Login -> dashboard -> KPI/alert -> linked module.  

### Definition of Done

Show agents, calls this month, minutes used/remaining, plan, invoice status, recent calls and service alerts for low minutes/payment due/agent offline/important notifications.

### SRS Traceability

- **SRS Traceability (from XLS):** CU1-001..002
- **Business rules / state machines / events / acceptance / gates:** Interpreted only from the XLS SRS column and matching SRS sections; see SRS document for full text. Do not invent IDs beyond the XLS column.



### Current Implementation Status

**Overall:** PARTIAL

**Backend:** PARTIAL  
**UI:** PARTIAL  
**Infrastructure/Integration:** N/A  
**Tests:** PARTIAL  

### What Already Exists

- CustomerDashboard component + APIs



### What Is Missing

- Complete KPI set / drilldowns



### What Is Partial

*N/A or covered under Missing/Exists.*

### Codebase Evidence

- packages/web-ui/src/features/dashboard/CustomerDashboard.tsx
- apps/api/control_plane/reporting/



### Dependency Verification

**Jira Dependencies:** VKT-097, VKT-043, VKT-102

**Dependency Status:**

- VKT-097 = COMPLETE
- VKT-043 = PARTIAL
- VKT-102 = COMPLETE

Remaining work may still depend on: VKT-043.

### Acceptance / QA Coverage

Some automated tests exist; gaps remain relative to full DoD/acceptance (see Missing/Remaining).

### Required Remaining Work

- Complete customer dashboard KPIs



### Audit Conclusion

VKT-103 is **PARTIAL**. Keep existing evidence; finish only the listed remaining work.

---



# VKT-104 — Build customer agent monitoring



## Jira Definition

**Sprint:** Sprint 5  
**Portal / Layer:** Customer  
**Epic:** Agents  
**Module:** Agent list/detail  
**Priority:** Must  
**Story Points:** 3  
**Estimated Hours:** 5  
**Dependencies:** VKT-093, VKT-102  
**Dependency Category:** BLOCKING  
**Flow:** Customer -> Agents -> detail -> permission check -> optional pause/resume.  

### Definition of Done

Show assigned agents, status, number and high-level configuration. Editing is disabled by default; only explicitly permitted actions/fields are available.

### SRS Traceability

- **SRS Traceability (from XLS):** CU2-001..003
- **Business rules / state machines / events / acceptance / gates:** Interpreted only from the XLS SRS column and matching SRS sections; see SRS document for full text. Do not invent IDs beyond the XLS column.



### Current Implementation Status

**Overall:** PARTIAL

**Backend:** PARTIAL  
**UI:** PARTIAL  
**Infrastructure/Integration:** N/A  
**Tests:** PARTIAL  

### What Already Exists

- Customer-scoped agent APIs likely; UI partial



### What Is Missing

- Customer agent monitoring UX



### What Is Partial

*N/A or covered under Missing/Exists.*

### Codebase Evidence

- packages/web-ui customer portal routes
- apps/api/control_plane/agents/



### Dependency Verification

**Jira Dependencies:** VKT-093, VKT-102

**Dependency Status:**

- VKT-093 = PARTIAL
- VKT-102 = COMPLETE

Remaining work may still depend on: VKT-093.

### Acceptance / QA Coverage

Some automated tests exist; gaps remain relative to full DoD/acceptance (see Missing/Remaining).

### Required Remaining Work

- Build customer agent monitoring screens



### Audit Conclusion

VKT-104 is **PARTIAL**. Keep existing evidence; finish only the listed remaining work.

---



# VKT-105 — Build customer call history and artifacts



## Jira Definition

**Sprint:** Sprint 5  
**Portal / Layer:** Customer  
**Epic:** Calls  
**Module:** Call history/detail  
**Priority:** Must  
**Story Points:** 5  
**Estimated Hours:** 6  
**Dependencies:** VKT-101, VKT-098, VKT-102  
**Dependency Category:** BLOCKING  
**Flow:** Customer -> Calls -> filters -> detail -> artifact authorization.  

### Definition of Done

Show only customer-owned calls; filter by agent/number/date/direction/outcome; display recording/transcript/summary only if enabled/authorized; export only when permitted.

### SRS Traceability

- **SRS Traceability (from XLS):** CU3-001..004
- **Business rules / state machines / events / acceptance / gates:** Interpreted only from the XLS SRS column and matching SRS sections; see SRS document for full text. Do not invent IDs beyond the XLS column.



### Current Implementation Status

**Overall:** PARTIAL

**Backend:** PARTIAL  
**UI:** PARTIAL  
**Infrastructure/Integration:** N/A  
**Tests:** PARTIAL  

### What Already Exists

- Customer call/artifact access APIs with authz



### What Is Missing

- Full customer call history + artifact UI



### What Is Partial

*N/A or covered under Missing/Exists.*

### Codebase Evidence

- apps/api/control_plane/recordings/api/views.py
- packages/web-ui customer screens — generic gaps



### Dependency Verification

**Jira Dependencies:** VKT-101, VKT-098, VKT-102

**Dependency Status:**

- VKT-101 = PARTIAL
- VKT-098 = COMPLETE
- VKT-102 = COMPLETE

Remaining work may still depend on: VKT-101.

### Acceptance / QA Coverage

Some automated tests exist; gaps remain relative to full DoD/acceptance (see Missing/Remaining).

### Required Remaining Work

- Build call history + artifact access UI



### Audit Conclusion

VKT-105 is **PARTIAL**. Keep existing evidence; finish only the listed remaining work.

---



# VKT-106 — Build customer usage and top-up screen

## Jira Definition

**Sprint:** Sprint 5  
**Portal / Layer:** Customer  
**Epic:** Usage  
**Module:** Usage/minutes  
**Priority:** Must  
**Story Points:** 5  
**Estimated Hours:** 6  
**Dependencies:** VKT-097, VKT-044, VKT-102  

### Definition of Done

Show included, consumed, remaining and additional minutes; breakdown by agent/date where feasible; allow purchase of Vokit-offered additional minute packages.

### SRS Traceability

- **SRS Traceability (from XLS):** CU4-001..003

### Current Implementation Status

**Overall:** PARTIAL

**Backend:** COMPLETE  
**UI:** PARTIAL  
**Infrastructure/Integration:** N/A  
**Tests:** PARTIAL  

**Frontend re-audit (2026-09-12):** Customer /usage is GenericModuleScreen GET-only; top-up form only in dead screens.tsx (not routed).

### Backend — Existing Implementation

- Prior backend audit findings retained unless contradicted; see Backend Evidence / previous COMPLETE notes for domain services.

### Frontend/UI — Existing Implementation

- packages/web-ui/src/productScreens.tsx — GenericModuleScreen for usage
- packages/web-ui/src/screens.tsx — top-up form (NOT imported / dead)

### What Is Complete

- Overall status after frontend pull: **PARTIAL**
- Backend: COMPLETE; UI: PARTIAL

### What Is Partial

- Wire usage screen + top-up POST /api/v1/customer/usage/top-ups into PortalApp path

### What Is Missing

- Wire usage screen + top-up POST /api/v1/customer/usage/top-ups into PortalApp path

### Backend Evidence

- See prior audit evidence for this VKT ID (domain/API/tests under `apps/api`).

### Frontend Evidence

- `packages/web-ui/src/productScreens.tsx` — GenericModuleScreen for usage
- `packages/web-ui/src/screens.tsx` — top-up form (NOT imported / dead)

### Test Evidence

- Backend tests: see `apps/api/tests/` (status **PARTIAL**).
- Frontend automated tests: **MISSING** (no vitest/RTL/Playwright under `packages/web-ui`).

### Dependency Verification

Jira dependencies: VKT-097, VKT-044, VKT-102

### Required Remaining Work

- Wire usage screen + top-up POST /api/v1/customer/usage/top-ups into PortalApp path

### Audit Conclusion

VKT-106 remains **PARTIAL**. Customer /usage is GenericModuleScreen GET-only; top-up form only in dead screens.tsx (not routed).

---
# VKT-107 — Build customer invoices and payment UI

## Jira Definition

**Sprint:** Sprint 5  
**Portal / Layer:** Customer  
**Epic:** Billing  
**Module:** Invoices/payments  
**Priority:** Must  
**Story Points:** 5  
**Estimated Hours:** 7  
**Dependencies:** VKT-043, VKT-044, VKT-102  

### Definition of Done

List open/paid/failed/refunded invoices; pay outstanding invoices through Vokit; add/update payment method through processor-hosted secure flow where possible; download receipts/invoices.

### SRS Traceability

- **SRS Traceability (from XLS):** CU5-001..004; SEC-004

### Current Implementation Status

**Overall:** PARTIAL

**Backend:** COMPLETE  
**UI:** PARTIAL  
**Infrastructure/Integration:** N/A  
**Tests:** PARTIAL  

**Frontend re-audit (2026-09-12):** Customer invoices list exists; pay-invoice action UI still missing.

### Backend — Existing Implementation

- Prior backend audit findings retained unless contradicted; see Backend Evidence / previous COMPLETE notes for domain services.

### Frontend/UI — Existing Implementation

- packages/web-ui/src/productScreens.tsx — InvoicesScreen GenericModuleScreen
- CustomerDashboard shows invoices but no pay action

### What Is Complete

- Overall status after frontend pull: **PARTIAL**
- Backend: COMPLETE; UI: PARTIAL

### What Is Partial

- Customer pay invoice / checkout UI

### What Is Missing

- Customer pay invoice / checkout UI

### Backend Evidence

- See prior audit evidence for this VKT ID (domain/API/tests under `apps/api`).

### Frontend Evidence

- `packages/web-ui/src/productScreens.tsx` — InvoicesScreen GenericModuleScreen
- `CustomerDashboard shows invoices but no pay action`

### Test Evidence

- Backend tests: see `apps/api/tests/` (status **PARTIAL**).
- Frontend automated tests: **MISSING** (no vitest/RTL/Playwright under `packages/web-ui`).

### Dependency Verification

Jira dependencies: VKT-043, VKT-044, VKT-102

### Required Remaining Work

- Customer pay invoice / checkout UI

### Audit Conclusion

VKT-107 remains **PARTIAL**. Customer invoices list exists; pay-invoice action UI still missing.

---
# VKT-108 — Build customer knowledge view/edit where granted



## Jira Definition

**Sprint:** Sprint 5  
**Portal / Layer:** Customer  
**Epic:** Knowledge  
**Module:** Knowledge  
**Priority:** Must  
**Story Points:** 3  
**Estimated Hours:** 4  
**Dependencies:** VKT-073, VKT-074, VKT-102  
**Dependency Category:** PARALLEL  
**Flow:** Customer -> Knowledge -> source -> permission -> view/edit -> processing.  

### Definition of Done

View customer knowledge attached to agents; upload/edit only where agency explicitly grants permission.

### SRS Traceability

- **SRS Traceability (from XLS):** CU6-001..002
- **Business rules / state machines / events / acceptance / gates:** Interpreted only from the XLS SRS column and matching SRS sections; see SRS document for full text. Do not invent IDs beyond the XLS column.



### Current Implementation Status

**Overall:** PARTIAL

**Backend:** PARTIAL  
**UI:** PARTIAL  
**Infrastructure/Integration:** N/A  
**Tests:** PARTIAL  

### What Already Exists

- Knowledge scope APIs



### What Is Missing

- Customer knowledge view/edit UI where granted



### What Is Partial

*N/A or covered under Missing/Exists.*

### Codebase Evidence

- apps/api/control_plane/agents/application/knowledge.py



### Dependency Verification

**Jira Dependencies:** VKT-073, VKT-074, VKT-102

**Dependency Status:**

- VKT-073 = PARTIAL
- VKT-074 = NOT_IMPLEMENTED
- VKT-102 = COMPLETE

Remaining work may still depend on: VKT-073, VKT-074.

### Acceptance / QA Coverage

Some automated tests exist; gaps remain relative to full DoD/acceptance (see Missing/Remaining).

### Required Remaining Work

- Build customer knowledge UI with permission gates



### Audit Conclusion

VKT-108 is **PARTIAL**. Keep existing evidence; finish only the listed remaining work.

---



# VKT-109 — Build customer integration visibility and permitted self-service



## Jira Definition

**Sprint:** Sprint 5  
**Portal / Layer:** Customer  
**Epic:** Integrations  
**Module:** Integration status/self-service  
**Priority:** Must  
**Story Points:** 3  
**Estimated Hours:** 4  
**Dependencies:** VKT-087, VKT-102  
**Dependency Category:** PARALLEL  
**Flow:** Customer -> Integrations -> status -> if enabled connect customer-owned account.  

### Definition of Done

Show integrations relevant to customer; allow customer-owned connection only when agency enables self-service.

### SRS Traceability

- **SRS Traceability (from XLS):** CU7-001..002
- **Business rules / state machines / events / acceptance / gates:** Interpreted only from the XLS SRS column and matching SRS sections; see SRS document for full text. Do not invent IDs beyond the XLS column.



### Current Implementation Status

**Overall:** PARTIAL

**Backend:** PARTIAL  
**UI:** PARTIAL  
**Infrastructure/Integration:** N/A  
**Tests:** PARTIAL  

### What Already Exists

- Customer integration visibility APIs (scoped)



### What Is Missing

- Customer self-serve integration UI



### What Is Partial

*N/A or covered under Missing/Exists.*

### Codebase Evidence

- apps/api/control_plane/integrations/



### Dependency Verification

**Jira Dependencies:** VKT-087, VKT-102

**Dependency Status:**

- VKT-087 = PARTIAL
- VKT-102 = COMPLETE

Remaining work may still depend on: VKT-087.

### Acceptance / QA Coverage

Some automated tests exist; gaps remain relative to full DoD/acceptance (see Missing/Remaining).

### Required Remaining Work

- Build permitted customer integration UI



### Audit Conclusion

VKT-109 is **PARTIAL**. Keep existing evidence; finish only the listed remaining work.

---



# VKT-110 — Build customer team, notifications and profile settings



## Jira Definition

**Sprint:** Sprint 5  
**Portal / Layer:** Customer  
**Epic:** Team/Settings  
**Module:** Team/settings  
**Priority:** Must  
**Story Points:** 3  
**Estimated Hours:** 5  
**Dependencies:** VKT-102, VKT-008  
**Dependency Category:** PARALLEL  
**Flow:** Customer -> Team/Settings -> permission -> update/invite.  

### Definition of Done

Invite/manage customer team by role; configure notification preferences; manage allowed business/contact settings.

### SRS Traceability

- **SRS Traceability (from XLS):** CU8-001..003
- **Business rules / state machines / events / acceptance / gates:** Interpreted only from the XLS SRS column and matching SRS sections; see SRS document for full text. Do not invent IDs beyond the XLS column.



### Current Implementation Status

**Overall:** PARTIAL

**Backend:** PARTIAL  
**UI:** PARTIAL  
**Infrastructure/Integration:** N/A  
**Tests:** PARTIAL  

### What Already Exists

- Team/notification preference APIs exist in identity/notifications



### What Is Missing

- Customer team/notifications/profile settings UI



### What Is Partial

*N/A or covered under Missing/Exists.*

### Codebase Evidence

- apps/api/control_plane/notifications/api/views.py
- packages/web-ui customer GenericModuleScreen gaps



### Dependency Verification

**Jira Dependencies:** VKT-102, VKT-008

**Dependency Status:**

- VKT-102 = COMPLETE
- VKT-008 = PARTIAL

Remaining work may still depend on: VKT-008.

### Acceptance / QA Coverage

Some automated tests exist; gaps remain relative to full DoD/acceptance (see Missing/Remaining).

### Required Remaining Work

- Build customer settings screens



### Audit Conclusion

VKT-110 is **PARTIAL**. Keep existing evidence; finish only the listed remaining work.

---



# VKT-111 — Build agency team, notification and security settings



## Jira Definition

**Sprint:** Sprint 5  
**Portal / Layer:** Agency  
**Epic:** Team/Settings  
**Module:** Team/settings  
**Priority:** Must  
**Story Points:** 5  
**Estimated Hours:** 6  
**Dependencies:** VKT-008, VKT-034  
**Dependency Category:** PARALLEL  
**Flow:** Agency -> Team/Settings -> invite/role/revoke; Preferences/Security updates.  

### Definition of Done

Invite/assign/revoke agency users within allowed roles; configure notification preferences, allowed profile/branding fields and sessions/password/MFA when supported.

### SRS Traceability

- **SRS Traceability (from XLS):** AG13-001..003; AG14-001..003
- **Business rules / state machines / events / acceptance / gates:** Interpreted only from the XLS SRS column and matching SRS sections; see SRS document for full text. Do not invent IDs beyond the XLS column.



### Current Implementation Status

**Overall:** PARTIAL

**Backend:** PARTIAL  
**UI:** PARTIAL  
**Infrastructure/Integration:** N/A  
**Tests:** PARTIAL  

### What Already Exists

- Agency team/notification APIs



### What Is Missing

- Agency team/security settings UI completeness
- Agency nav omits some modules



### What Is Partial

*N/A or covered under Missing/Exists.*

### Codebase Evidence

- packages/web-ui/src/components/layout/navGroups.ts
- apps/api/control_plane/identity/
- apps/api/control_plane/notifications/



### Dependency Verification

**Jira Dependencies:** VKT-008, VKT-034

**Dependency Status:**

- VKT-008 = PARTIAL
- VKT-034 = PARTIAL

Remaining work may still depend on: VKT-008, VKT-034.

### Acceptance / QA Coverage

Some automated tests exist; gaps remain relative to full DoD/acceptance (see Missing/Remaining).

### Required Remaining Work

- Complete agency team/notification/security settings UI



### Audit Conclusion

VKT-111 is **PARTIAL**. Keep existing evidence; finish only the listed remaining work.

---



# VKT-112 — Build Super Admin user and role management

## Jira Definition

**Sprint:** Sprint 5  
**Portal / Layer:** Super Admin  
**Epic:** Users/Roles  
**Module:** Platform users/roles  
**Priority:** Must  
**Story Points:** 5  
**Estimated Hours:** 6  
**Dependencies:** VKT-008, VKT-016  

### Definition of Done

Invite/disable platform users; create role/permission bundles; keep KYC, payout, wallet adjustment, commission edit and impersonation permissions explicit.

### SRS Traceability

- **SRS Traceability (from XLS):** SA18-001..003

### Current Implementation Status

**Overall:** COMPLETE

**Backend:** COMPLETE  
**UI:** COMPLETE  
**Infrastructure/Integration:** N/A  
**Tests:** PARTIAL  

**Frontend re-audit (2026-09-12):** PlatformUsersScreen covers users, invite, roles/RBAC matrix, sensitive permissions.

### Backend — Existing Implementation

- Prior backend audit findings retained unless contradicted; see Backend Evidence / previous COMPLETE notes for domain services.

### Frontend/UI — Existing Implementation

- packages/web-ui/src/features/users/PlatformUsersScreen.tsx
- packages/web-ui/src/features/users/hooks/usePlatformUsers.ts

### What Is Complete

- Overall status after frontend pull: **COMPLETE**
- Backend: COMPLETE; UI: COMPLETE

### What Is Partial

_N/A or minor residual notes only._

### What Is Missing

- Custom editable role bundles still catalog-based (by design).

### Backend Evidence

- See prior audit evidence for this VKT ID (domain/API/tests under `apps/api`).

### Frontend Evidence

- `packages/web-ui/src/features/users/PlatformUsersScreen.tsx`
- `packages/web-ui/src/features/users/hooks/usePlatformUsers.ts`

### Test Evidence

- Backend tests: see `apps/api/tests/` (status **PARTIAL**).
- Frontend automated tests: **MISSING** (no vitest/RTL/Playwright under `packages/web-ui`).

### Dependency Verification

Jira dependencies: VKT-008, VKT-016

### Required Remaining Work

- Custom editable role bundles still catalog-based (by design).

### Audit Conclusion

VKT-112 is **COMPLETE** after frontend re-audit. **DO NOT REIMPLEMENT.** Previous status was PARTIAL.

---
# VKT-113 — Complete notification preference and template engine



## Jira Definition

**Sprint:** Sprint 5  
**Portal / Layer:** Platform  
**Epic:** Notifications  
**Module:** Notification engine/preferences  
**Priority:** Must  
**Story Points:** 5  
**Estimated Hours:** 7  
**Dependencies:** VKT-034, VKT-060, VKT-006  
**Dependency Category:** BLOCKING  
**Flow:** Event -> preference check -> mandatory/non-mandatory -> render -> deliver -> log.  

### Definition of Done

Support in-app/email, validated template variables, escaped untrusted content, mandatory notice categories and delivery status where provider supports.

### SRS Traceability

- **SRS Traceability (from XLS):** NOT-001..005
- **Business rules / state machines / events / acceptance / gates:** Interpreted only from the XLS SRS column and matching SRS sections; see SRS document for full text. Do not invent IDs beyond the XLS column.



### Current Implementation Status

**Overall:** PARTIAL

**Backend:** PARTIAL  
**UI:** PARTIAL  
**Infrastructure/Integration:** N/A  
**Tests:** PARTIAL  

### What Already Exists

- Notification templates + preferences + mandatory notices
- Email queue task



### What Is Missing

- Complete preference UX; billing triggers (VKT-060)



### What Is Partial

*N/A or covered under Missing/Exists.*

### Codebase Evidence

- apps/api/control_plane/notifications/application/service.py
- apps/api/tests/test_notifications_domain.py
- apps/api/tests/test_notification_email_queue.py



### Dependency Verification

**Jira Dependencies:** VKT-034, VKT-060, VKT-006

**Dependency Status:**

- VKT-034 = PARTIAL
- VKT-060 = NOT_IMPLEMENTED
- VKT-006 = COMPLETE

Remaining work may still depend on: VKT-034, VKT-060.

### Acceptance / QA Coverage

Some automated tests exist; gaps remain relative to full DoD/acceptance (see Missing/Remaining).

### Required Remaining Work

- Finish preference/template admin UX; wire missing events



### Audit Conclusion

VKT-113 is **PARTIAL**. Keep existing evidence; finish only the listed remaining work.

---



# VKT-114 — Build Super Admin notification administration

## Jira Definition

**Sprint:** Sprint 5  
**Portal / Layer:** Super Admin  
**Epic:** Notifications  
**Module:** Template/delivery/announcement screens  
**Priority:** Must  
**Story Points:** 3  
**Estimated Hours:** 5  
**Dependencies:** VKT-113, VKT-016  

### Definition of Done

Manage system email/in-app templates, inspect delivery status where supported and send platform/agency-targeted announcements.

### SRS Traceability

- **SRS Traceability (from XLS):** SA16-001..003

### Current Implementation Status

**Overall:** COMPLETE

**Backend:** COMPLETE  
**UI:** COMPLETE  
**Infrastructure/Integration:** N/A  
**Tests:** PARTIAL  

**Frontend re-audit (2026-09-12):** PlatformNotificationsScreen administers templates, deliveries, announcements, inbox.

### Backend — Existing Implementation

- Prior backend audit findings retained unless contradicted; see Backend Evidence / previous COMPLETE notes for domain services.

### Frontend/UI — Existing Implementation

- packages/web-ui/src/features/notifications/PlatformNotificationsScreen.tsx
- packages/web-ui/src/features/notifications/hooks/usePlatformNotifications.ts

### What Is Complete

- Overall status after frontend pull: **COMPLETE**
- Backend: COMPLETE; UI: COMPLETE

### What Is Partial

_N/A or minor residual notes only._

### What Is Missing

- _Nothing material missing relative to DoD (COMPLETE)._

### Backend Evidence

- See prior audit evidence for this VKT ID (domain/API/tests under `apps/api`).

### Frontend Evidence

- `packages/web-ui/src/features/notifications/PlatformNotificationsScreen.tsx`
- `packages/web-ui/src/features/notifications/hooks/usePlatformNotifications.ts`

### Test Evidence

- Backend tests: see `apps/api/tests/` (status **PARTIAL**).
- Frontend automated tests: **MISSING** (no vitest/RTL/Playwright under `packages/web-ui`).

### Dependency Verification

Jira dependencies: VKT-113, VKT-016

### Required Remaining Work

_None — treat as COMPLETE; only verify/QA if release requires re-attestation._

### Audit Conclusion

VKT-114 is **COMPLETE** after frontend re-audit. **DO NOT REIMPLEMENT.** Previous status was PARTIAL.

---
# VKT-115 — Build provider registry and tenant connection visibility

## Jira Definition

**Sprint:** Sprint 6  
**Portal / Layer:** Super Admin  
**Epic:** Integrations  
**Module:** Provider registry/connection visibility  
**Priority:** Must  
**Story Points:** 3  
**Estimated Hours:** 5  
**Dependencies:** VKT-086, VKT-016  

### Definition of Done

Configure available integration/provider strategy and inspect tenant connection status without exposing secrets; allow disabling compromised connections.

### SRS Traceability

- **SRS Traceability (from XLS):** SA15-001..004

### Current Implementation Status

**Overall:** COMPLETE

**Backend:** COMPLETE  
**UI:** COMPLETE  
**Infrastructure/Integration:** PARTIAL  
**Tests:** PARTIAL  

**Frontend re-audit (2026-09-12):** PlatformIntegrationsScreen shows provider registry and tenant connection visibility.

### Backend — Existing Implementation

- Prior backend audit findings retained unless contradicted; see Backend Evidence / previous COMPLETE notes for domain services.

### Frontend/UI — Existing Implementation

- packages/web-ui/src/features/integrations/PlatformIntegrationsScreen.tsx
- packages/web-ui/src/features/integrations/hooks/usePlatformIntegrations.ts

### What Is Complete

- Overall status after frontend pull: **COMPLETE**
- Backend: COMPLETE; UI: COMPLETE

### What Is Partial

_N/A or minor residual notes only._

### What Is Missing

- OAuth connect flows still absent (VKT-086).

### Backend Evidence

- See prior audit evidence for this VKT ID (domain/API/tests under `apps/api`).

### Frontend Evidence

- `packages/web-ui/src/features/integrations/PlatformIntegrationsScreen.tsx`
- `packages/web-ui/src/features/integrations/hooks/usePlatformIntegrations.ts`

### Test Evidence

- Backend tests: see `apps/api/tests/` (status **PARTIAL**).
- Frontend automated tests: **MISSING** (no vitest/RTL/Playwright under `packages/web-ui`).

### Dependency Verification

Jira dependencies: VKT-086, VKT-016

### Required Remaining Work

- OAuth connect flows still absent (VKT-086).

### Audit Conclusion

VKT-115 is **COMPLETE** after frontend re-audit. **DO NOT REIMPLEMENT.** Previous status was PARTIAL.

---
# VKT-116 — Build webhook delivery log and replay UI

## Jira Definition

**Sprint:** Sprint 6  
**Portal / Layer:** Super Admin  
**Epic:** Webhooks  
**Module:** Webhook logs/replay  
**Priority:** Must  
**Story Points:** 3  
**Estimated Hours:** 5  
**Dependencies:** VKT-090, VKT-016  

### Definition of Done

Inspect endpoint, event, status, retries, timestamps and response codes/metadata; replay only eligible failed deliveries.

### SRS Traceability

- **SRS Traceability (from XLS):** SA15-003; WH-005..006

### Current Implementation Status

**Overall:** PARTIAL

**Backend:** COMPLETE  
**UI:** NOT_IMPLEMENTED  
**Infrastructure/Integration:** N/A  
**Tests:** PARTIAL  

**Frontend re-audit (2026-09-12):** Webhook create/list exists; delivery log + replay UI still not implemented.

### Backend — Existing Implementation

- Prior backend audit findings retained unless contradicted; see Backend Evidence / previous COMPLETE notes for domain services.

### Frontend/UI — Existing Implementation

- packages/web-ui/src/productScreens.tsx — WebhooksScreen create/list only
- PlatformIntegrationsScreen notes agency deliveries not wired

### What Is Complete

- Overall status after frontend pull: **PARTIAL**
- Backend: COMPLETE; UI: NOT_IMPLEMENTED

### What Is Partial

- Delivery log + replay UI for agency webhooks

### What Is Missing

- Delivery log + replay UI for agency webhooks

### Backend Evidence

- See prior audit evidence for this VKT ID (domain/API/tests under `apps/api`).

### Frontend Evidence

- `packages/web-ui/src/productScreens.tsx` — WebhooksScreen create/list only
- `PlatformIntegrationsScreen notes agency deliveries not wired`

### Test Evidence

- Backend tests: see `apps/api/tests/` (status **PARTIAL**).
- Frontend automated tests: **MISSING** (no vitest/RTL/Playwright under `packages/web-ui`).

### Dependency Verification

Jira dependencies: VKT-090, VKT-016

### Required Remaining Work

- Delivery log + replay UI for agency webhooks

### Audit Conclusion

VKT-116 remains **PARTIAL**. Webhook create/list exists; delivery log + replay UI still not implemented.

---
# VKT-117 — Build transfer monitoring

## Jira Definition

**Sprint:** Sprint 6  
**Portal / Layer:** Super Admin  
**Epic:** Transfers  
**Module:** Transfer directory/diagnostics  
**Priority:** Must  
**Story Points:** 3  
**Estimated Hours:** 4  
**Dependencies:** VKT-083, VKT-099  

### Definition of Done

View tenant transfer destinations/rules; disable unsafe/invalid targets and inspect failed transfers where supported.

### SRS Traceability

- **SRS Traceability (from XLS):** SA10-001..003

### Current Implementation Status

**Overall:** COMPLETE

**Backend:** COMPLETE  
**UI:** COMPLETE  
**Infrastructure/Integration:** PARTIAL  
**Tests:** PARTIAL  

**Frontend re-audit (2026-09-12):** PlatformTransfersScreen provides transfer directory/monitoring/diagnostics.

### Backend — Existing Implementation

- Prior backend audit findings retained unless contradicted; see Backend Evidence / previous COMPLETE notes for domain services.

### Frontend/UI — Existing Implementation

- packages/web-ui/src/features/transfers/PlatformTransfersScreen.tsx
- packages/web-ui/src/features/transfers/hooks/usePlatformTransfers.ts

### What Is Complete

- Overall status after frontend pull: **COMPLETE**
- Backend: COMPLETE; UI: COMPLETE

### What Is Partial

_N/A or minor residual notes only._

### What Is Missing

- TransferRule editor still missing (VKT-083).

### Backend Evidence

- See prior audit evidence for this VKT ID (domain/API/tests under `apps/api`).

### Frontend Evidence

- `packages/web-ui/src/features/transfers/PlatformTransfersScreen.tsx`
- `packages/web-ui/src/features/transfers/hooks/usePlatformTransfers.ts`

### Test Evidence

- Backend tests: see `apps/api/tests/` (status **PARTIAL**).
- Frontend automated tests: **MISSING** (no vitest/RTL/Playwright under `packages/web-ui`).

### Dependency Verification

Jira dependencies: VKT-083, VKT-099

### Required Remaining Work

- TransferRule editor still missing (VKT-083).

### Audit Conclusion

VKT-117 is **COMPLETE** after frontend re-audit. **DO NOT REIMPLEMENT.** Previous status was PARTIAL.

---
# VKT-118 — Build immutable audit log search/detail

## Jira Definition

**Sprint:** Sprint 6  
**Portal / Layer:** Super Admin  
**Epic:** Audit  
**Module:** Audit log search/detail  
**Priority:** Must  
**Story Points:** 3  
**Estimated Hours:** 5  
**Dependencies:** VKT-006, VKT-016  

### Definition of Done

Search by actor, action, entity, tenant, IP/time and severity. Do not allow edit/delete. Redact secrets/full payment data/raw KYC content.

### SRS Traceability

- **SRS Traceability (from XLS):** SA17-001..003; AUD-001..005

### Current Implementation Status

**Overall:** COMPLETE

**Backend:** COMPLETE  
**UI:** COMPLETE  
**Infrastructure/Integration:** N/A  
**Tests:** PARTIAL  

**Frontend re-audit (2026-09-12):** PlatformAuditScreen provides filtered search + detail panel.

### Backend — Existing Implementation

- Prior backend audit findings retained unless contradicted; see Backend Evidence / previous COMPLETE notes for domain services.

### Frontend/UI — Existing Implementation

- packages/web-ui/src/features/audit/PlatformAuditScreen.tsx
- packages/web-ui/src/features/audit/hooks/usePlatformAudit.ts

### What Is Complete

- Overall status after frontend pull: **COMPLETE**
- Backend: COMPLETE; UI: COMPLETE

### What Is Partial

_N/A or minor residual notes only._

### What Is Missing

- _Nothing material missing relative to DoD (COMPLETE)._

### Backend Evidence

- See prior audit evidence for this VKT ID (domain/API/tests under `apps/api`).

### Frontend Evidence

- `packages/web-ui/src/features/audit/PlatformAuditScreen.tsx`
- `packages/web-ui/src/features/audit/hooks/usePlatformAudit.ts`

### Test Evidence

- Backend tests: see `apps/api/tests/` (status **PARTIAL**).
- Frontend automated tests: **MISSING** (no vitest/RTL/Playwright under `packages/web-ui`).

### Dependency Verification

Jira dependencies: VKT-006, VKT-016

### Required Remaining Work

_None — treat as COMPLETE; only verify/QA if release requires re-attestation._

### Audit Conclusion

VKT-118 is **COMPLETE** after frontend re-audit. **DO NOT REIMPLEMENT.** Previous status was PARTIAL.

---
# VKT-119 — Implement Super Admin override workflow



## Jira Definition

**Sprint:** Sprint 6  
**Portal / Layer:** Super Admin  
**Epic:** Overrides  
**Module:** High-risk override framework  
**Priority:** Must  
**Story Points:** 5  
**Estimated Hours:** 7  
**Dependencies:** VKT-008, VKT-022, VKT-039, VKT-054, VKT-062, VKT-118  
**Dependency Category:** BLOCKING  
**Flow:** Select override -> permission -> impact warning -> reason/confirmation -> state/ledger -> audit.  

### Definition of Done

Allow authorized overrides for agency/customer status, feature gates, agent status, number assignment, plan, KYC, payout eligibility/state, wallet freeze and commission rate. Require reason and production-call impact warning where applicable.

### SRS Traceability

- **SRS Traceability (from XLS):** §21.1; BR-008; AUD-004..005
- **Business rules / state machines / events / acceptance / gates:** Interpreted only from the XLS SRS column and matching SRS sections; see SRS document for full text. Do not invent IDs beyond the XLS column.



### Current Implementation Status

**Overall:** PARTIAL

**Backend:** PARTIAL  
**UI:** PARTIAL  
**Infrastructure/Integration:** N/A  
**Tests:** PARTIAL  

### What Already Exists

- Override workflows for KYC/risk/settings with audit



### What Is Missing

- Unified Super Admin override workflow UI



### What Is Partial

*N/A or covered under Missing/Exists.*

### Codebase Evidence

- apps/api/control_plane/kyc/application/override_case.py
- apps/api/control_plane/risk/application/override.py
- apps/api/tests/test_ops_api.py



### Dependency Verification

**Jira Dependencies:** VKT-008, VKT-022, VKT-039, VKT-054, VKT-062, VKT-118

**Dependency Status:**

- VKT-008 = PARTIAL
- VKT-022 = PARTIAL
- VKT-039 = PARTIAL
- VKT-054 = COMPLETE
- VKT-062 = PARTIAL
- VKT-118 = PARTIAL

Remaining work may still depend on: VKT-008, VKT-022, VKT-039, VKT-062, VKT-118.

### Acceptance / QA Coverage

Some automated tests exist; gaps remain relative to full DoD/acceptance (see Missing/Remaining).

### Required Remaining Work

- Build unified override workflow UI with audit trail



### Audit Conclusion

VKT-119 is **PARTIAL**. Keep existing evidence; finish only the listed remaining work.

---



# VKT-120 — Build platform settings UI

## Jira Definition

**Sprint:** Sprint 6  
**Portal / Layer:** Super Admin  
**Epic:** Settings  
**Module:** Platform settings  
**Priority:** Must  
**Story Points:** 5  
**Estimated Hours:** 7  
**Dependencies:** VKT-010, VKT-016  

### Definition of Done

Configure commercial, payout, telephony, AI, compliance, notifications, security and feature-flag settings listed by the SRS.

### SRS Traceability

- **SRS Traceability (from XLS):** §22

### Current Implementation Status

**Overall:** COMPLETE

**Backend:** COMPLETE  
**UI:** COMPLETE  
**Infrastructure/Integration:** N/A  
**Tests:** PARTIAL  

**Frontend re-audit (2026-09-12):** PlatformSettingsScreen edits platform settings/flags via API.

### Backend — Existing Implementation

- Prior backend audit findings retained unless contradicted; see Backend Evidence / previous COMPLETE notes for domain services.

### Frontend/UI — Existing Implementation

- packages/web-ui/src/features/settings/PlatformSettingsScreen.tsx
- packages/web-ui/src/features/settings/hooks/usePlatformSettings.ts

### What Is Complete

- Overall status after frontend pull: **COMPLETE**
- Backend: COMPLETE; UI: COMPLETE

### What Is Partial

_N/A or minor residual notes only._

### What Is Missing

- _Nothing material missing relative to DoD (COMPLETE)._

### Backend Evidence

- See prior audit evidence for this VKT ID (domain/API/tests under `apps/api`).

### Frontend Evidence

- `packages/web-ui/src/features/settings/PlatformSettingsScreen.tsx`
- `packages/web-ui/src/features/settings/hooks/usePlatformSettings.ts`

### Test Evidence

- Backend tests: see `apps/api/tests/` (status **PARTIAL**).
- Frontend automated tests: **MISSING** (no vitest/RTL/Playwright under `packages/web-ui`).

### Dependency Verification

Jira dependencies: VKT-010, VKT-016

### Required Remaining Work

_None — treat as COMPLETE; only verify/QA if release requires re-attestation._

### Audit Conclusion

VKT-120 is **COMPLETE** after frontend re-audit. **DO NOT REIMPLEMENT.** Previous status was PARTIAL.

---
# VKT-121 — Implement centralized configurable business rules



## Jira Definition

**Sprint:** Sprint 6  
**Portal / Layer:** Platform  
**Epic:** Settings  
**Module:** Business policy/config service  
**Priority:** Must  
**Story Points:** 5  
**Estimated Hours:** 6  
**Dependencies:** VKT-120, VKT-033, VKT-047, VKT-046  
**Dependency Category:** BLOCKING  
**Flow:** Module -> policy service -> current configured rule -> decision.  

### Definition of Done

Centralize hold duration, payout thresholds, commissionability, KYC gates, recording disclosure/retention, allowed countries/providers and other policy controls instead of duplicating them in UI code.

### SRS Traceability

- **SRS Traceability (from XLS):** NFR-014
- **Business rules / state machines / events / acceptance / gates:** Interpreted only from the XLS SRS column and matching SRS sections; see SRS document for full text. Do not invent IDs beyond the XLS column.



### Current Implementation Status

**Overall:** PARTIAL

**Backend:** PARTIAL  
**UI:** N/A  
**Infrastructure/Integration:** N/A  
**Tests:** PARTIAL  

### What Already Exists

- Central platform_settings service for many business rules



### What Is Missing

- All SRS-configurable rules centralized and documented
- hold_days wiring gap (VKT-047)



### What Is Partial

*N/A or covered under Missing/Exists.*

### Codebase Evidence

- apps/api/control_plane/platform_settings/application/service.py
- apps/api/control_plane/platform_settings/domain/



### Dependency Verification

**Jira Dependencies:** VKT-120, VKT-033, VKT-047, VKT-046

**Dependency Status:**

- VKT-120 = PARTIAL
- VKT-033 = PARTIAL
- VKT-047 = PARTIAL
- VKT-046 = COMPLETE

Remaining work may still depend on: VKT-120, VKT-033, VKT-047.

### Acceptance / QA Coverage

Some automated tests exist; gaps remain relative to full DoD/acceptance (see Missing/Remaining).

### Required Remaining Work

- Inventory SRS knobs vs settings keys; close wiring gaps



### Audit Conclusion

VKT-121 is **PARTIAL**. Keep existing evidence; finish only the listed remaining work.

---



# VKT-122 — Implement configurable retention and deletion-request controls



## Jira Definition

**Sprint:** Sprint 6  
**Portal / Layer:** Platform  
**Epic:** Privacy  
**Module:** Retention/deletion workflow  
**Priority:** Must  
**Story Points:** 5  
**Estimated Hours:** 7  
**Dependencies:** VKT-098, VKT-014, VKT-121, VKT-118  
**Dependency Category:** BLOCKING  
**Flow:** Policy -> retention metadata -> scheduled action -> deletion request -> exceptions -> audit.  

### Definition of Done

Support retention for recordings, transcripts, logs, KYC and financial records subject to legal constraints; support customer/agency deletion requests with financial/KYC/legal exceptions.

### SRS Traceability

- **SRS Traceability (from XLS):** PRIV-001..006
- **Business rules / state machines / events / acceptance / gates:** Interpreted only from the XLS SRS column and matching SRS sections; see SRS document for full text. Do not invent IDs beyond the XLS column.



### Current Implementation Status

**Overall:** PARTIAL

**Backend:** PARTIAL  
**UI:** N/A  
**Infrastructure/Integration:** PARTIAL  
**Tests:** PARTIAL  

### What Already Exists

- Recording retention/legal hold concepts in recordings domain



### What Is Missing

- Configurable deletion-request workflow/API across tenant data



### What Is Partial

*N/A or covered under Missing/Exists.*

### Codebase Evidence

- apps/api/control_plane/recordings/domain/policies.py
- SRS PRIV retention requirements



### Dependency Verification

**Jira Dependencies:** VKT-098, VKT-014, VKT-121, VKT-118

**Dependency Status:**

- VKT-098 = COMPLETE
- VKT-014 = PARTIAL
- VKT-121 = PARTIAL
- VKT-118 = PARTIAL

Remaining work may still depend on: VKT-014, VKT-121, VKT-118.

### Acceptance / QA Coverage

Some automated tests exist; gaps remain relative to full DoD/acceptance (see Missing/Remaining).

### Required Remaining Work

- Implement deletion-request controls + retention policy UI/API



### Audit Conclusion

VKT-122 is **PARTIAL**. Keep existing evidence; finish only the listed remaining work.

---



# VKT-123 — Implement authorized tenant data export



## Jira Definition

**Sprint:** Sprint 6  
**Portal / Layer:** Platform  
**Epic:** Privacy  
**Module:** Authorized data export  
**Priority:** Must  
**Story Points:** 3  
**Estimated Hours:** 4  
**Dependencies:** VKT-008, VKT-118  
**Dependency Category:** PARALLEL  
**Flow:** Tenant request -> authorization -> scoped export -> audit.  

### Definition of Done

Provide authorized operational data export where supported; enforce tenant scope and audit sensitive exports.

### SRS Traceability

- **SRS Traceability (from XLS):** PRIV-007; CALL-007
- **Business rules / state machines / events / acceptance / gates:** Interpreted only from the XLS SRS column and matching SRS sections; see SRS document for full text. Do not invent IDs beyond the XLS column.



### Current Implementation Status

**Overall:** NOT_IMPLEMENTED

**Backend:** NOT_IMPLEMENTED  
**UI:** N/A  
**Infrastructure/Integration:** NOT_IMPLEMENTED  
**Tests:** NOT_IMPLEMENTED  

### What Already Exists

- Backup/restore for ops (not tenant self-serve export)



### What Is Missing

- Authorized tenant data export API (PRIV-007)



### What Is Partial

*N/A or covered under Missing/Exists.*

### Codebase Evidence

- No export module under apps/api/control_plane/
- SRS PRIV-005/007 in Vokit_V1_Agency_Platform_SRS_v1.0.md



### Dependency Verification

**Jira Dependencies:** VKT-008, VKT-118

**Dependency Status:**

- VKT-008 = PARTIAL
- VKT-118 = PARTIAL

Remaining work may still depend on: VKT-008, VKT-118.

### Acceptance / QA Coverage

Required tests for this DoD were not found or are insufficient.

### Required Remaining Work

- Design + implement authorized export with audit + RBAC



### Audit Conclusion

VKT-123 is **NOT_IMPLEMENTED**. Build the Missing/Remaining items; do not assume adjacent features cover this DoD.

---



# VKT-124 — Build platform operational/financial reporting



## Jira Definition

**Sprint:** Sprint 6  
**Portal / Layer:** Super Admin  
**Epic:** Reporting  
**Module:** Platform reports  
**Priority:** Must  
**Story Points:** 5  
**Estimated Hours:** 7  
**Dependencies:** VKT-048, VKT-094, VKT-032, VKT-043  
**Dependency Category:** BLOCKING  
**Flow:** Reports -> period/timezone/tenant filters -> ledger/payment/call sources -> export where permitted.  

### Definition of Done

Report MRR, agencies, customers, agents, calls, minutes, failed payments, commission liability, held/available wallet, pending payouts, payout aging, KYC aging, provider costs and gross margin using authoritative data.

### SRS Traceability

- **SRS Traceability (from XLS):** §29; RPT-001..005
- **Business rules / state machines / events / acceptance / gates:** Interpreted only from the XLS SRS column and matching SRS sections; see SRS document for full text. Do not invent IDs beyond the XLS column.



### Current Implementation Status

**Overall:** PARTIAL

**Backend:** PARTIAL  
**UI:** PARTIAL  
**Infrastructure/Integration:** N/A  
**Tests:** PARTIAL  

### What Already Exists

- Platform reporting/dashboard APIs



### What Is Missing

- Complete operational/financial reporting (MRR, aging, provider cost)



### What Is Partial

*N/A or covered under Missing/Exists.*

### Codebase Evidence

- apps/api/control_plane/reporting/
- apps/api/tests/test_reporting_domain.py
- apps/api/tests/test_dashboard_api.py



### Dependency Verification

**Jira Dependencies:** VKT-048, VKT-094, VKT-032, VKT-043

**Dependency Status:**

- VKT-048 = COMPLETE
- VKT-094 = COMPLETE
- VKT-032 = PARTIAL
- VKT-043 = PARTIAL

Remaining work may still depend on: VKT-032, VKT-043.

### Acceptance / QA Coverage

Some automated tests exist; gaps remain relative to full DoD/acceptance (see Missing/Remaining).

### Required Remaining Work

- Complete report metrics and SA report UI



### Audit Conclusion

VKT-124 is **PARTIAL**. Keep existing evidence; finish only the listed remaining work.

---



# VKT-125 — Complete agency KPI/report data layer



## Jira Definition

**Sprint:** Sprint 6  
**Portal / Layer:** Agency  
**Epic:** Reporting  
**Module:** Agency dashboard data  
**Priority:** Must  
**Story Points:** 3  
**Estimated Hours:** 5  
**Dependencies:** VKT-124, VKT-051  
**Dependency Category:** PARALLEL  
**Flow:** Agency dashboard -> scoped reporting query -> KPI/trend/alerts.  

### Definition of Done

Provide customer MRR, expected commission MRR, earned/held/available/lifetime paid, customers, agents, calls, minutes, top customers and payout status for agency dashboard.

### SRS Traceability

- **SRS Traceability (from XLS):** AG1-001..003; §29
- **Business rules / state machines / events / acceptance / gates:** Interpreted only from the XLS SRS column and matching SRS sections; see SRS document for full text. Do not invent IDs beyond the XLS column.



### Current Implementation Status

**Overall:** PARTIAL

**Backend:** PARTIAL  
**UI:** PARTIAL  
**Infrastructure/Integration:** N/A  
**Tests:** PARTIAL  

### What Already Exists

- Agency dashboard data layer partial



### What Is Missing

- Complete agency KPI/report coverage



### What Is Partial

*N/A or covered under Missing/Exists.*

### Codebase Evidence

- packages/web-ui/src/features/dashboard/AgencyDashboard.tsx
- apps/api/control_plane/reporting/



### Dependency Verification

**Jira Dependencies:** VKT-124, VKT-051

**Dependency Status:**

- VKT-124 = PARTIAL
- VKT-051 = PARTIAL

Remaining work may still depend on: VKT-124, VKT-051.

### Acceptance / QA Coverage

Some automated tests exist; gaps remain relative to full DoD/acceptance (see Missing/Remaining).

### Required Remaining Work

- Complete agency KPI data layer



### Audit Conclusion

VKT-125 is **PARTIAL**. Keep existing evidence; finish only the listed remaining work.

---



# VKT-126 — Complete customer KPI/report data layer



## Jira Definition

**Sprint:** Sprint 6  
**Portal / Layer:** Customer  
**Epic:** Reporting  
**Module:** Customer dashboard data  
**Priority:** Must  
**Story Points:** 3  
**Estimated Hours:** 4  
**Dependencies:** VKT-124, VKT-103  
**Dependency Category:** PARALLEL  
**Flow:** Customer dashboard -> customer-scoped reporting query -> cards/lists.  

### Definition of Done

Provide plan, minutes used/remaining, call count/duration, agent activity, invoice/payment status and top-up history for customer views.

### SRS Traceability

- **SRS Traceability (from XLS):** CU1-001; §29
- **Business rules / state machines / events / acceptance / gates:** Interpreted only from the XLS SRS column and matching SRS sections; see SRS document for full text. Do not invent IDs beyond the XLS column.



### Current Implementation Status

**Overall:** PARTIAL

**Backend:** PARTIAL  
**UI:** PARTIAL  
**Infrastructure/Integration:** N/A  
**Tests:** PARTIAL  

### What Already Exists

- Customer dashboard data partial



### What Is Missing

- Complete customer KPI/report coverage



### What Is Partial

*N/A or covered under Missing/Exists.*

### Codebase Evidence

- packages/web-ui/src/features/dashboard/CustomerDashboard.tsx



### Dependency Verification

**Jira Dependencies:** VKT-124, VKT-103

**Dependency Status:**

- VKT-124 = PARTIAL
- VKT-103 = PARTIAL

Remaining work may still depend on: VKT-124, VKT-103.

### Acceptance / QA Coverage

Some automated tests exist; gaps remain relative to full DoD/acceptance (see Missing/Remaining).

### Required Remaining Work

- Complete customer KPI data layer



### Audit Conclusion

VKT-126 is **PARTIAL**. Keep existing evidence; finish only the listed remaining work.

---



# VKT-127 — Implement structured logs, metrics, traces and correlation IDs



## Jira Definition

**Sprint:** Sprint 6  
**Portal / Layer:** Platform  
**Epic:** Observability  
**Module:** Critical workflow telemetry  
**Priority:** Must  
**Story Points:** 5  
**Estimated Hours:** 6  
**Dependencies:** VKT-011, VKT-012, VKT-010  
**Dependency Category:** BLOCKING  
**Flow:** Request/event -> correlation ID -> structured telemetry -> alerting.  

### Definition of Done

Add observability for authentication, payments, commission/ledger, payout, KYC, telephony, webhooks, integrations and calls. Redact secrets and sensitive documents.

### SRS Traceability

- **SRS Traceability (from XLS):** NFR-006; SEC-015
- **Business rules / state machines / events / acceptance / gates:** Interpreted only from the XLS SRS column and matching SRS sections; see SRS document for full text. Do not invent IDs beyond the XLS column.



### Current Implementation Status

**Overall:** PARTIAL

**Backend:** PARTIAL  
**UI:** N/A  
**Infrastructure/Integration:** NOT_IMPLEMENTED  
**Tests:** PARTIAL  

### What Already Exists

- Structured logging + correlation IDs



### What Is Missing

- Metrics exporters, distributed traces, alerting stack in deploy/



### What Is Partial

*N/A or covered under Missing/Exists.*

### Codebase Evidence

- apps/api/shared_kernel/logging.py
- apps/api/shared_kernel/http/correlation.py
- apps/api/control_plane/ops/application/catalog.py — VOKIT_EVIDENCE_ALERTING
- No Prometheus/Grafana under deploy/



### Dependency Verification

**Jira Dependencies:** VKT-011, VKT-012, VKT-010

**Dependency Status:**

- VKT-011 = COMPLETE
- VKT-012 = PARTIAL
- VKT-010 = PARTIAL

Remaining work may still depend on: VKT-012, VKT-010.

### Acceptance / QA Coverage

Some automated tests exist; gaps remain relative to full DoD/acceptance (see Missing/Remaining).

### Required Remaining Work

- Deploy metrics/traces/alerts; wire business-impact metrics



### Audit Conclusion

VKT-127 is **PARTIAL**. Keep existing evidence; finish only the listed remaining work.

---



# VKT-128 — Implement automated backups and recovery test



## Jira Definition

**Sprint:** Sprint 6  
**Portal / Layer:** Platform  
**Epic:** Reliability  
**Module:** Backup/recovery validation  
**Priority:** Must  
**Story Points:** 3  
**Estimated Hours:** 5  
**Dependencies:** VKT-015, VKT-127  
**Dependency Category:** BLOCKING  
**Flow:** Scheduled backup -> stored backup -> restore test -> documented result.  

### Definition of Done

Configure automated database/configuration backup and execute a recovery validation sufficient for production release.

### SRS Traceability

- **SRS Traceability (from XLS):** NFR-007
- **Business rules / state machines / events / acceptance / gates:** Interpreted only from the XLS SRS column and matching SRS sections; see SRS document for full text. Do not invent IDs beyond the XLS column.



### Current Implementation Status

**Overall:** PARTIAL

**Backend:** COMPLETE  
**UI:** N/A  
**Infrastructure/Integration:** PARTIAL  
**Tests:** COMPLETE  

### What Already Exists

- Backup/restore commands + isolation test
- Runbook



### What Is Missing

- Live dated restore drill attestation



### What Is Partial

*N/A or covered under Missing/Exists.*

### Codebase Evidence

- apps/api/tests/test_backup_restore.py
- docs/execution/runbooks/backup-restore.md
- docs/execution/26-PHASE-19-EVIDENCE.md — VOKIT_EVIDENCE_RESTORE_DRILL Missing



### Dependency Verification

**Jira Dependencies:** VKT-015, VKT-127

**Dependency Status:**

- VKT-015 = PARTIAL
- VKT-127 = PARTIAL

Remaining work may still depend on: VKT-015, VKT-127.

### Acceptance / QA Coverage

Automated tests covering the core DoD behaviors were found (see Evidence).

### Required Remaining Work

- Perform and record live restore drill



### Audit Conclusion

VKT-128 is **PARTIAL**. Keep existing evidence; finish only the listed remaining work.

---



# VKT-129 — Automate commission/wallet/payout state transition tests



## Jira Definition

**Sprint:** Sprint 6  
**Portal / Layer:** QA  
**Epic:** Automated Tests  
**Module:** Financial state tests  
**Priority:** Must  
**Story Points:** 8  
**Estimated Hours:** 8  
**Dependencies:** VKT-047, VKT-048, VKT-052, VKT-057  
**Dependency Category:** BLOCKING  
**Flow:** Arrange financial state -> event -> assert ledger/state/balance invariants.  

### Definition of Done

Cover payment success, independent 15-day holds, reversal during/after hold, payout reservation race, payout states, negative balance and corrective ledger behavior.

### SRS Traceability

- **SRS Traceability (from XLS):** §31.2; WAL-001..007
- **Business rules / state machines / events / acceptance / gates:** Interpreted only from the XLS SRS column and matching SRS sections; see SRS document for full text. Do not invent IDs beyond the XLS column.



### Current Implementation Status

**Overall:** COMPLETE

**Backend:** COMPLETE  
**UI:** N/A  
**Infrastructure/Integration:** N/A  
**Tests:** COMPLETE  

### What Already Exists

- Appendix C + commission API tests cover state transitions



### What Is Missing

*Nothing material missing relative to DoD (COMPLETE).* 

### What Is Partial

*N/A or covered under Missing/Exists.*

### Codebase Evidence

- apps/api/tests/test_appendix_c.py
- apps/api/tests/test_commission_api.py
- apps/api/tests/test_phase17_matrices.py



### Dependency Verification

**Jira Dependencies:** VKT-047, VKT-048, VKT-052, VKT-057

**Dependency Status:**

- VKT-047 = PARTIAL
- VKT-048 = COMPLETE
- VKT-052 = COMPLETE
- VKT-057 = PARTIAL

Dependencies are COMPLETE or do not block evaluating this task's own gaps.

### Acceptance / QA Coverage

Automated tests covering the core DoD behaviors were found (see Evidence).

### Required Remaining Work

- None for automation DoD



### Audit Conclusion

VKT-129 is **COMPLETE** against repository evidence. **DO NOT REIMPLEMENT.** Only perform verification/QA if required for release.

---



# VKT-130 — Automate cross-tenant authorization tests



## Jira Definition

**Sprint:** Sprint 6  
**Portal / Layer:** QA  
**Epic:** Automated Tests  
**Module:** Tenant isolation tests  
**Priority:** Must  
**Story Points:** 8  
**Estimated Hours:** 7  
**Dependencies:** VKT-008, VKT-033, VKT-094  
**Dependency Category:** BLOCKING  
**Flow:** Actor A -> request tenant B ID -> deny/not-found without disclosure.  

### Definition of Done

Verify agency cannot access another agency's customers/calls/agents/knowledge/wallet/payouts and customer cannot access other customer data; API manipulation cannot bypass restrictions.

### SRS Traceability

- **SRS Traceability (from XLS):** §31.2; TEN-001..005
- **Business rules / state machines / events / acceptance / gates:** Interpreted only from the XLS SRS column and matching SRS sections; see SRS document for full text. Do not invent IDs beyond the XLS column.



### Current Implementation Status

**Overall:** COMPLETE

**Backend:** COMPLETE  
**UI:** N/A  
**Infrastructure/Integration:** N/A  
**Tests:** COMPLETE  

### What Already Exists

- Tenant routing matrix + optional MySQL isolation in CI



### What Is Missing

*Nothing material missing relative to DoD (COMPLETE).* 

### What Is Partial

*N/A or covered under Missing/Exists.*

### Codebase Evidence

- apps/api/tests/test_tenant_routing.py
- apps/api/tests/test_mysql_isolation.py
- apps/api/tests/test_phase17_matrices.py



### Dependency Verification

**Jira Dependencies:** VKT-008, VKT-033, VKT-094

**Dependency Status:**

- VKT-008 = PARTIAL
- VKT-033 = PARTIAL
- VKT-094 = COMPLETE

Dependencies are COMPLETE or do not block evaluating this task's own gaps.

### Acceptance / QA Coverage

Automated tests covering the core DoD behaviors were found (see Evidence).

### Required Remaining Work

- None for automation DoD



### Audit Conclusion

VKT-130 is **COMPLETE** against repository evidence. **DO NOT REIMPLEMENT.** Only perform verification/QA if required for release.

---



# VKT-131 — Automate payment/webhook/payout/number idempotency tests



## Jira Definition

**Sprint:** Sprint 6  
**Portal / Layer:** QA  
**Epic:** Automated Tests  
**Module:** Idempotency tests  
**Priority:** Must  
**Story Points:** 8  
**Estimated Hours:** 7  
**Dependencies:** VKT-045, VKT-052, VKT-081, VKT-090  
**Dependency Category:** BLOCKING  
**Flow:** Duplicate event/request -> same outcome -> no duplicate side effect.  

### Definition of Done

Verify duplicate payment webhooks, duplicate payout requests/reservation races and irreversible number purchases do not double-apply.

### SRS Traceability

- **SRS Traceability (from XLS):** §31.2; NFR-005
- **Business rules / state machines / events / acceptance / gates:** Interpreted only from the XLS SRS column and matching SRS sections; see SRS document for full text. Do not invent IDs beyond the XLS column.



### Current Implementation Status

**Overall:** PARTIAL

**Backend:** PARTIAL  
**UI:** N/A  
**Infrastructure/Integration:** N/A  
**Tests:** PARTIAL  

### What Already Exists

- Payment webhook idempotency + payout concurrent reserve tests



### What Is Missing

- Complete number purchase idempotency suite vs DoD



### What Is Partial

*N/A or covered under Missing/Exists.*

### Codebase Evidence

- apps/api/tests/test_billing_api.py
- apps/api/tests/test_commission_api.py
- apps/api/tests/test_numbers_api.py



### Dependency Verification

**Jira Dependencies:** VKT-045, VKT-052, VKT-081, VKT-090

**Dependency Status:**

- VKT-045 = COMPLETE
- VKT-052 = COMPLETE
- VKT-081 = PARTIAL
- VKT-090 = COMPLETE

Remaining work may still depend on: VKT-081.

### Acceptance / QA Coverage

Some automated tests exist; gaps remain relative to full DoD/acceptance (see Missing/Remaining).

### Required Remaining Work

- Expand number purchase idempotency/orphan tests



### Audit Conclusion

VKT-131 is **PARTIAL**. Keep existing evidence; finish only the listed remaining work.

---



# VKT-132 — Run security checks for auth/RBAC/secrets/webhooks/uploads/payments



## Jira Definition

**Sprint:** Sprint 6  
**Portal / Layer:** QA  
**Epic:** Security  
**Module:** Security test suite  
**Priority:** Must  
**Story Points:** 8  
**Estimated Hours:** 8  
**Dependencies:** VKT-009, VKT-010, VKT-014, VKT-090, VKT-118  
**Dependency Category:** BLOCKING  
**Flow:** Security test -> exploit attempt -> deny/secure result -> evidence.  

### Definition of Done

Validate secure sessions, CSRF, rate limits, secret isolation, inbound/outbound webhook signatures, upload controls, payment tokenization and log redaction.

### SRS Traceability

- **SRS Traceability (from XLS):** §25; §31.2
- **Business rules / state machines / events / acceptance / gates:** Interpreted only from the XLS SRS column and matching SRS sections; see SRS document for full text. Do not invent IDs beyond the XLS column.



### Current Implementation Status

**Overall:** PARTIAL

**Backend:** PARTIAL  
**UI:** N/A  
**Infrastructure/Integration:** N/A  
**Tests:** PARTIAL  

### What Already Exists

- Phase 17 security review doc + many security tests
- check_production_readiness



### What Is Missing

- Full checklist attestation for uploads/payment integration production



### What Is Partial

*N/A or covered under Missing/Exists.*

### Codebase Evidence

- docs/execution/24-PHASE-17-SECURITY-REVIEW.md
- apps/api/tests/test_phase17_matrices.py
- apps/api/tests/test_production_readiness.py



### Dependency Verification

**Jira Dependencies:** VKT-009, VKT-010, VKT-014, VKT-090, VKT-118

**Dependency Status:**

- VKT-009 = PARTIAL
- VKT-010 = PARTIAL
- VKT-014 = PARTIAL
- VKT-090 = COMPLETE
- VKT-118 = PARTIAL

Remaining work may still depend on: VKT-009, VKT-010, VKT-014, VKT-118.

### Acceptance / QA Coverage

Some automated tests exist; gaps remain relative to full DoD/acceptance (see Missing/Remaining).

### Required Remaining Work

- Close remaining security review open items; MFA enrollment



### Audit Conclusion

VKT-132 is **PARTIAL**. Keep existing evidence; finish only the listed remaining work.

---



# VKT-133 — Complete dashboard filter and drilldown behavior



## Jira Definition

**Sprint:** Sprint 7  
**Portal / Layer:** Super Admin  
**Epic:** UI Completion  
**Module:** Dashboard drilldowns/date filters  
**Priority:** Must  
**Story Points:** 2  
**Estimated Hours:** 3  
**Dependencies:** VKT-017, VKT-124  
**Dependency Category:** BLOCKING  
**Flow:** Dashboard -> filter -> KPI -> drilldown -> expected filtered list.  

### Definition of Done

Verify every dashboard card routes to the correct filtered module view and date filters support today, 7 days, 30 days, month-to-date and custom range.

### SRS Traceability

- **SRS Traceability (from XLS):** SA1-004..005
- **Business rules / state machines / events / acceptance / gates:** Interpreted only from the XLS SRS column and matching SRS sections; see SRS document for full text. Do not invent IDs beyond the XLS column.



### Current Implementation Status

**Overall:** PARTIAL

**Backend:** PARTIAL  
**UI:** PARTIAL  
**Infrastructure/Integration:** N/A  
**Tests:** PARTIAL  

### What Already Exists

- Dashboard filters/hooks partial



### What Is Missing

- Complete filter + drilldown behavior across portals



### What Is Partial

*N/A or covered under Missing/Exists.*

### Codebase Evidence

- packages/web-ui/src/features/dashboard/



### Dependency Verification

**Jira Dependencies:** VKT-017, VKT-124

**Dependency Status:**

- VKT-017 = PARTIAL
- VKT-124 = PARTIAL

Remaining work may still depend on: VKT-017, VKT-124.

### Acceptance / QA Coverage

Some automated tests exist; gaps remain relative to full DoD/acceptance (see Missing/Remaining).

### Required Remaining Work

- Implement remaining dashboard filter/drilldown



### Audit Conclusion

VKT-133 is **PARTIAL**. Keep existing evidence; finish only the listed remaining work.

---



# VKT-134 — Complete Super Admin screens and permission-aware states

## Jira Definition

**Sprint:** Sprint 7  
**Portal / Layer:** Super Admin  
**Epic:** UI Completion  
**Module:** All portal screens  
**Priority:** Must  
**Story Points:** 5  
**Estimated Hours:** 8  
**Dependencies:** VKT-018, VKT-020, VKT-030, VKT-032, VKT-061, VKT-075, VKT-071, VKT-072, VKT-080, VKT-117, VKT-036, VKT-049, VKT-053, VKT-100, VKT-115, VKT-116, VKT-114, VKT-118, VKT-112, VKT-120  

### Definition of Done

Finalize Agencies, Customers, KYC, Agents, Templates, Instructions, Knowledge, Phone Numbers, Transfers, Plans, Billing, Wallet/Payouts, Calls, Integrations/Webhooks, Notifications, Audit, Users/Roles and Settings with loading, empty, error and permission states.

### SRS Traceability

- **SRS Traceability (from XLS):** §7.1..7.19

### Current Implementation Status

**Overall:** PARTIAL

**Backend:** PARTIAL  
**UI:** PARTIAL  
**Infrastructure/Integration:** N/A  
**Tests:** N/A  

**Frontend re-audit (2026-09-12):** Most SA modules now dedicated screens; only risk remains PlatformResourceScreen. Permission-aware polish still incomplete.

### Backend — Existing Implementation

- Prior backend audit findings retained unless contradicted; see Backend Evidence / previous COMPLETE notes for domain services.

### Frontend/UI — Existing Implementation

- packages/web-ui/src/features/platform/renderPlatformScreen.tsx — dedicated routers
- packages/web-ui/src/features/platform/platformModules.ts — risk only

### What Is Complete

- Overall status after frontend pull: **PARTIAL**
- Backend: PARTIAL; UI: PARTIAL

### What Is Partial

- Replace risk generic screen; finish permission-aware empty/disabled states

### What Is Missing

- Replace risk generic screen; finish permission-aware empty/disabled states

### Backend Evidence

- See prior audit evidence for this VKT ID (domain/API/tests under `apps/api`).

### Frontend Evidence

- `packages/web-ui/src/features/platform/renderPlatformScreen.tsx` — dedicated routers
- `packages/web-ui/src/features/platform/platformModules.ts` — risk only

### Test Evidence

- Backend tests: see `apps/api/tests/` (status **N/A**).
- Frontend automated tests: **MISSING** (no vitest/RTL/Playwright under `packages/web-ui`).

### Dependency Verification

Jira dependencies: VKT-018, VKT-020, VKT-030, VKT-032, VKT-061, VKT-075, VKT-071, VKT-072, VKT-080, VKT-117, VKT-036, VKT-049, VKT-053, VKT-100, VKT-115, VKT-116, VKT-114, VKT-118, VKT-112, VKT-120

### Required Remaining Work

- Replace risk generic screen; finish permission-aware empty/disabled states

### Audit Conclusion

VKT-134 remains **PARTIAL**. Most SA modules now dedicated screens; only risk remains PlatformResourceScreen. Permission-aware polish still incomplete.

---
# VKT-135 — Complete Agency portal screens and state/permission UX



## Jira Definition

**Sprint:** Sprint 7  
**Portal / Layer:** Agency  
**Epic:** UI Completion  
**Module:** All portal screens  
**Priority:** Must  
**Story Points:** 5  
**Estimated Hours:** 8  
**Dependencies:** VKT-040, VKT-063, VKT-091, VKT-093, VKT-079, VKT-101, VKT-082, VKT-073, VKT-087, VKT-089, VKT-051, VKT-052, VKT-056, VKT-029, VKT-111, VKT-125  
**Dependency Category:** BLOCKING  
**Flow:** Agency module -> scoped API -> permission/status gate -> screen -> action -> feedback.  

### Definition of Done

Finalize Dashboard, Customers, Agents/Builder, Phone Numbers, Calls, Transfers, Knowledge, Integrations, Webhooks, Plans/Billing visibility, Wallet/Payouts, KYC, Team and Notifications/Settings including loading/empty/error/disabled states and status/capability messaging.

### SRS Traceability

- **SRS Traceability (from XLS):** §8.1..8.14
- **Business rules / state machines / events / acceptance / gates:** Interpreted only from the XLS SRS column and matching SRS sections; see SRS document for full text. Do not invent IDs beyond the XLS column.



### Current Implementation Status

**Overall:** PARTIAL

**Backend:** PARTIAL  
**UI:** PARTIAL  
**Infrastructure/Integration:** N/A  
**Tests:** N/A  

### What Already Exists

- Agency portal shell + key screens



### What Is Missing

- Many agency modules thin/generic; nav omissions
- State/permission UX incomplete



### What Is Partial

*N/A or covered under Missing/Exists.*

### Codebase Evidence

- packages/web-ui/src/productScreens.tsx
- packages/web-ui/src/components/layout/navGroups.ts



### Dependency Verification

**Jira Dependencies:** VKT-040, VKT-063, VKT-091, VKT-093, VKT-079, VKT-101, VKT-082, VKT-073, VKT-087, VKT-089, VKT-051, VKT-052, VKT-056, VKT-029, VKT-111, VKT-125

**Dependency Status:**

- VKT-040 = PARTIAL
- VKT-063 = PARTIAL
- VKT-091 = PARTIAL
- VKT-093 = PARTIAL
- VKT-079 = PARTIAL
- VKT-101 = PARTIAL
- VKT-082 = PARTIAL
- VKT-073 = PARTIAL
- VKT-087 = PARTIAL
- VKT-089 = PARTIAL
- VKT-051 = PARTIAL
- VKT-052 = COMPLETE
- VKT-056 = PARTIAL
- VKT-029 = COMPLETE
- VKT-111 = PARTIAL
- VKT-125 = PARTIAL

Remaining work may still depend on: VKT-040, VKT-063, VKT-091, VKT-093, VKT-079, VKT-101, VKT-082, VKT-073, VKT-087, VKT-089, VKT-051, VKT-056, VKT-111, VKT-125.

### Acceptance / QA Coverage

Test applicability limited (N/A) or not separately scored.

### Required Remaining Work

- Complete agency portal screens and permission UX



### Audit Conclusion

VKT-135 is **PARTIAL**. Keep existing evidence; finish only the listed remaining work.

---



# VKT-136 — Complete Customer portal screens and customer-scope UX



## Jira Definition

**Sprint:** Sprint 7  
**Portal / Layer:** Customer  
**Epic:** UI Completion  
**Module:** All portal screens  
**Priority:** Must  
**Story Points:** 5  
**Estimated Hours:** 8  
**Dependencies:** VKT-103, VKT-104, VKT-105, VKT-106, VKT-107, VKT-108, VKT-109, VKT-110, VKT-126  
**Dependency Category:** BLOCKING  
**Flow:** Customer module -> customer-scoped API -> permission -> screen/action -> feedback.  

### Definition of Done

Finalize Dashboard, Agents, Calls, Usage/Minutes, Invoices/Payments, Knowledge, Integrations and Team/Settings with responsive behavior and customer-only data visibility.

### SRS Traceability

- **SRS Traceability (from XLS):** §9.1..9.8; TEN-005
- **Business rules / state machines / events / acceptance / gates:** Interpreted only from the XLS SRS column and matching SRS sections; see SRS document for full text. Do not invent IDs beyond the XLS column.



### Current Implementation Status

**Overall:** PARTIAL

**Backend:** PARTIAL  
**UI:** PARTIAL  
**Infrastructure/Integration:** N/A  
**Tests:** N/A  

### What Already Exists

- Customer portal shell + dashboard



### What Is Missing

- Billing/usage/pay/knowledge/integrations UIs incomplete



### What Is Partial

*N/A or covered under Missing/Exists.*

### Codebase Evidence

- packages/web-ui customer portal paths
- GenericModuleScreen fallbacks



### Dependency Verification

**Jira Dependencies:** VKT-103, VKT-104, VKT-105, VKT-106, VKT-107, VKT-108, VKT-109, VKT-110, VKT-126

**Dependency Status:**

- VKT-103 = PARTIAL
- VKT-104 = PARTIAL
- VKT-105 = PARTIAL
- VKT-106 = PARTIAL
- VKT-107 = PARTIAL
- VKT-108 = PARTIAL
- VKT-109 = PARTIAL
- VKT-110 = PARTIAL
- VKT-126 = PARTIAL

Remaining work may still depend on: VKT-103, VKT-104, VKT-105, VKT-106, VKT-107, VKT-108, VKT-109, VKT-110, VKT-126.

### Acceptance / QA Coverage

Test applicability limited (N/A) or not separately scored.

### Required Remaining Work

- Complete customer-scope screens



### Audit Conclusion

VKT-136 is **PARTIAL**. Keep existing evidence; finish only the listed remaining work.

---



# VKT-137 — Verify payment and commission edge cases



## Jira Definition

**Sprint:** Sprint 7  
**Portal / Layer:** Platform  
**Epic:** Edge Cases  
**Module:** Payment/billing edge cases  
**Priority:** Must  
**Story Points:** 5  
**Estimated Hours:** 6  
**Dependencies:** VKT-129, VKT-131, VKT-057  
**Dependency Category:** BLOCKING  
**Flow:** Payment -> event/edge case -> idempotent/reconciled ledger outcome -> notifications/audit.  

### Definition of Done

Test repeated payment webhook, payment success with commission-write failure, refund during hold, refund after availability, chargeback after payout, commission-rate changes and payment-failure service rules.

### SRS Traceability

- **SRS Traceability (from XLS):** §28; Appendix C
- **Business rules / state machines / events / acceptance / gates:** Interpreted only from the XLS SRS column and matching SRS sections; see SRS document for full text. Do not invent IDs beyond the XLS column.



### Current Implementation Status

**Overall:** PARTIAL

**Backend:** PARTIAL  
**UI:** N/A  
**Infrastructure/Integration:** N/A  
**Tests:** PARTIAL  

### What Already Exists

- Appendix C + billing domain tests cover many edge cases



### What Is Missing

- Single packaged acceptance journey for all payment/commission edges



### What Is Partial

*N/A or covered under Missing/Exists.*

### Codebase Evidence

- apps/api/tests/test_appendix_c.py
- apps/api/tests/test_billing_domain.py



### Dependency Verification

**Jira Dependencies:** VKT-129, VKT-131, VKT-057

**Dependency Status:**

- VKT-129 = COMPLETE
- VKT-131 = PARTIAL
- VKT-057 = PARTIAL

Remaining work may still depend on: VKT-131, VKT-057.

### Acceptance / QA Coverage

Some automated tests exist; gaps remain relative to full DoD/acceptance (see Missing/Remaining).

### Required Remaining Work

- Add consolidated acceptance test suite / checklist execution record



### Audit Conclusion

VKT-137 is **PARTIAL**. Keep existing evidence; finish only the listed remaining work.

---



# VKT-138 — Verify payout and risk edge cases



## Jira Definition

**Sprint:** Sprint 7  
**Portal / Layer:** Platform  
**Epic:** Edge Cases  
**Module:** Payout/risk edge cases  
**Priority:** Must  
**Story Points:** 5  
**Estimated Hours:** 6  
**Dependencies:** VKT-129, VKT-119, VKT-054  
**Dependency Category:** BLOCKING  
**Flow:** Risk/payout event -> policy gate -> state/ledger correction -> audit/notification.  

### Definition of Done

Test agency suspension with requested payout, KYC expiry with available funds, accidental Paid state, missing proof, payout race conditions and negative balance recovery.

### SRS Traceability

- **SRS Traceability (from XLS):** §28; §24.5
- **Business rules / state machines / events / acceptance / gates:** Interpreted only from the XLS SRS column and matching SRS sections; see SRS document for full text. Do not invent IDs beyond the XLS column.



### Current Implementation Status

**Overall:** PARTIAL

**Backend:** PARTIAL  
**UI:** N/A  
**Infrastructure/Integration:** N/A  
**Tests:** PARTIAL  

### What Already Exists

- Payout + risk API tests



### What Is Missing

- Formal packaged acceptance for all payout/risk edges



### What Is Partial

*N/A or covered under Missing/Exists.*

### Codebase Evidence

- apps/api/tests/test_commission_api.py
- apps/api/tests/test_risk_api.py



### Dependency Verification

**Jira Dependencies:** VKT-129, VKT-119, VKT-054

**Dependency Status:**

- VKT-129 = COMPLETE
- VKT-119 = PARTIAL
- VKT-054 = COMPLETE

Remaining work may still depend on: VKT-119.

### Acceptance / QA Coverage

Some automated tests exist; gaps remain relative to full DoD/acceptance (see Missing/Remaining).

### Required Remaining Work

- Run and document payout/risk acceptance pack



### Audit Conclusion

VKT-138 is **PARTIAL**. Keep existing evidence; finish only the listed remaining work.

---



# VKT-139 — Verify number/call/agent failure behavior



## Jira Definition

**Sprint:** Sprint 7  
**Portal / Layer:** Platform  
**Epic:** Edge Cases  
**Module:** Telephony/agent edge cases  
**Priority:** Must  
**Story Points:** 5  
**Estimated Hours:** 7  
**Dependencies:** VKT-081, VKT-097, VKT-088, VKT-074, VKT-119  
**Dependency Category:** BLOCKING  
**Flow:** Runtime failure -> configured fallback/reconciliation -> safe continuation/disablement -> audit.  

### Definition of Done

Test provider/local number purchase mismatch, customer out of minutes during call, integration timeout during call, knowledge ingestion failure, agent pause/error/fallback and active-call override warnings.

### SRS Traceability

- **SRS Traceability (from XLS):** §28; AGT-008; TEL-010
- **Business rules / state machines / events / acceptance / gates:** Interpreted only from the XLS SRS column and matching SRS sections; see SRS document for full text. Do not invent IDs beyond the XLS column.



### Current Implementation Status

**Overall:** PARTIAL

**Backend:** PARTIAL  
**UI:** N/A  
**Infrastructure/Integration:** N/A  
**Tests:** PARTIAL  

### What Already Exists

- Number/call/agent failure tests exist across suites



### What Is Missing

- Unified failure-behavior acceptance pack



### What Is Partial

*N/A or covered under Missing/Exists.*

### Codebase Evidence

- apps/api/tests/test_numbers_api.py
- apps/api/tests/test_voice_api.py
- apps/api/tests/test_agents_api.py



### Dependency Verification

**Jira Dependencies:** VKT-081, VKT-097, VKT-088, VKT-074, VKT-119

**Dependency Status:**

- VKT-081 = PARTIAL
- VKT-097 = COMPLETE
- VKT-088 = COMPLETE
- VKT-074 = NOT_IMPLEMENTED
- VKT-119 = PARTIAL

Remaining work may still depend on: VKT-081, VKT-074, VKT-119.

### Acceptance / QA Coverage

Some automated tests exist; gaps remain relative to full DoD/acceptance (see Missing/Remaining).

### Required Remaining Work

- Consolidate and execute failure acceptance checklist



### Audit Conclusion

VKT-139 is **PARTIAL**. Keep existing evidence; finish only the listed remaining work.

---



# VKT-140 — Run confirmed chargeback shutdown and re-onboarding prevention



## Jira Definition

**Sprint:** Sprint 7  
**Portal / Layer:** Platform  
**Epic:** Risk  
**Module:** Chargeback shutdown and ban  
**Priority:** Must  
**Story Points:** 8  
**Estimated Hours:** 7  
**Dependencies:** VKT-058, VKT-059, VKT-137, VKT-139  
**Dependency Category:** BLOCKING  
**Flow:** Chargeback -> customer freeze -> agent shutdown -> restrictions -> commission reversal -> risk/audit/notifications -> re-onboarding block.  

### Definition of Done

Verify chargeback freezes customer, immediately disables all customer agents and production calling, blocks new minutes/numbers/agents/subscriptions/payment except approved recovery, notifies agency/Super Admin, reverses commission by state, and blocks re-onboarding across agencies where permanently banned.

### SRS Traceability

- **SRS Traceability (from XLS):** Risk rules §§16-24; core rules summary
- **Business rules / state machines / events / acceptance / gates:** Interpreted only from the XLS SRS column and matching SRS sections; see SRS document for full text. Do not invent IDs beyond the XLS column.



### Current Implementation Status

**Overall:** PARTIAL

**Backend:** COMPLETE  
**UI:** N/A  
**Infrastructure/Integration:** N/A  
**Tests:** COMPLETE  

### What Already Exists

- Chargeback shutdown automated tests



### What Is Missing

- Formal re-onboarding prevention acceptance run recorded as release evidence



### What Is Partial

*N/A or covered under Missing/Exists.*

### Codebase Evidence

- apps/api/tests/test_risk_api.py
- apps/api/control_plane/risk/application/apply_chargeback.py



### Dependency Verification

**Jira Dependencies:** VKT-058, VKT-059, VKT-137, VKT-139

**Dependency Status:**

- VKT-058 = COMPLETE
- VKT-059 = PARTIAL
- VKT-137 = PARTIAL
- VKT-139 = PARTIAL

Remaining work may still depend on: VKT-059, VKT-137, VKT-139.

### Acceptance / QA Coverage

Automated tests covering the core DoD behaviors were found (see Evidence).

### Required Remaining Work

- Execute and file acceptance evidence for release



### Audit Conclusion

VKT-140 is **PARTIAL**. Keep existing evidence; finish only the listed remaining work.

---



# VKT-141 — Run complete agency lifecycle acceptance test



## Jira Definition

**Sprint:** Sprint 7  
**Portal / Layer:** QA  
**Epic:** E2E  
**Module:** Agency onboarding/KYC  
**Priority:** Must  
**Story Points:** 5  
**Estimated Hours:** 5  
**Dependencies:** VKT-019, VKT-024, VKT-029, VKT-032, VKT-033  
**Dependency Category:** BLOCKING  
**Flow:** SA create -> invitation -> Agency onboarding/KYC -> review -> Verified -> Active.  

### Definition of Done

Create agency as Super Admin, send invitation, accept/create credentials, complete KYC, review/decision, verify activation and ensure payout remains blocked until KYC Verified.

### SRS Traceability

- **SRS Traceability (from XLS):** §6.1; §31.1
- **Business rules / state machines / events / acceptance / gates:** Interpreted only from the XLS SRS column and matching SRS sections; see SRS document for full text. Do not invent IDs beyond the XLS column.



### Current Implementation Status

**Overall:** PARTIAL

**Backend:** PARTIAL  
**UI:** PARTIAL  
**Infrastructure/Integration:** N/A  
**Tests:** PARTIAL  

### What Already Exists

- Agency create/KYC/capability pieces tested separately



### What Is Missing

- End-to-end agency lifecycle acceptance test as one journey



### What Is Partial

*N/A or covered under Missing/Exists.*

### Codebase Evidence

- apps/api/tests/test_sa2_agency_api.py
- apps/api/tests/test_kyc_api.py
- apps/api/tests/test_staging_sandbox_e2e.py



### Dependency Verification

**Jira Dependencies:** VKT-019, VKT-024, VKT-029, VKT-032, VKT-033

**Dependency Status:**

- VKT-019 = PARTIAL
- VKT-024 = PARTIAL
- VKT-029 = COMPLETE
- VKT-032 = PARTIAL
- VKT-033 = PARTIAL

Remaining work may still depend on: VKT-019, VKT-024, VKT-032, VKT-033.

### Acceptance / QA Coverage

Some automated tests exist; gaps remain relative to full DoD/acceptance (see Missing/Remaining).

### Required Remaining Work

- Author E2E agency lifecycle acceptance test + record results



### Audit Conclusion

VKT-141 is **PARTIAL**. Keep existing evidence; finish only the listed remaining work.

---



# VKT-142 — Run customer commercial flow acceptance test



## Jira Definition

**Sprint:** Sprint 7  
**Portal / Layer:** QA  
**Epic:** E2E  
**Module:** Customer/payment/commission  
**Priority:** Must  
**Story Points:** 8  
**Estimated Hours:** 6  
**Dependencies:** VKT-040, VKT-043, VKT-044, VKT-046, VKT-047, VKT-060  
**Dependency Category:** BLOCKING  
**Flow:** Agency -> Customer -> Plan -> Invoice -> Payment -> Commission On Hold -> entitlements.  

### Definition of Done

Create customer when agency is permitted, assign versioned plan, create invoice, pay Vokit directly, create exactly one commission with correct rate snapshot and 15-day availability date, activate entitlements and notifications.

### SRS Traceability

- **SRS Traceability (from XLS):** §10.3; §31.1
- **Business rules / state machines / events / acceptance / gates:** Interpreted only from the XLS SRS column and matching SRS sections; see SRS document for full text. Do not invent IDs beyond the XLS column.



### Current Implementation Status

**Overall:** PARTIAL

**Backend:** PARTIAL  
**UI:** PARTIAL  
**Infrastructure/Integration:** N/A  
**Tests:** PARTIAL  

### What Already Exists

- Billing/customer APIs tested



### What Is Missing

- Full customer commercial flow acceptance (plan→pay→usage) as one test



### What Is Partial

*N/A or covered under Missing/Exists.*

### Codebase Evidence

- apps/api/tests/test_billing_api.py
- apps/api/tests/test_sa3_customer_api.py



### Dependency Verification

**Jira Dependencies:** VKT-040, VKT-043, VKT-044, VKT-046, VKT-047, VKT-060

**Dependency Status:**

- VKT-040 = PARTIAL
- VKT-043 = PARTIAL
- VKT-044 = PARTIAL
- VKT-046 = COMPLETE
- VKT-047 = PARTIAL
- VKT-060 = NOT_IMPLEMENTED

Remaining work may still depend on: VKT-040, VKT-043, VKT-044, VKT-047, VKT-060.

### Acceptance / QA Coverage

Some automated tests exist; gaps remain relative to full DoD/acceptance (see Missing/Remaining).

### Required Remaining Work

- Author commercial flow acceptance E2E



### Audit Conclusion

VKT-142 is **PARTIAL**. Keep existing evidence; finish only the listed remaining work.

---



# VKT-143 — Run telephony production-path acceptance test



## Jira Definition

**Sprint:** Sprint 7  
**Portal / Layer:** QA  
**Epic:** E2E  
**Module:** Number/agent/call  
**Priority:** Must  
**Story Points:** 8  
**Estimated Hours:** 6  
**Dependencies:** VKT-080, VKT-093, VKT-095, VKT-097, VKT-098  
**Dependency Category:** BLOCKING  
**Flow:** Number -> Agent -> Publish -> Inbound call -> Call record -> usage/artifacts.  

### Definition of Done

Purchase/assign number, configure inbound routing, publish compliant agent, place inbound call, verify correct tenant/customer agent receives it and Call record/artifacts/usage are written according to configuration.

### SRS Traceability

- **SRS Traceability (from XLS):** §15; §16; §31.1
- **Business rules / state machines / events / acceptance / gates:** Interpreted only from the XLS SRS column and matching SRS sections; see SRS document for full text. Do not invent IDs beyond the XLS column.



### Current Implementation Status

**Overall:** PARTIAL

**Backend:** PARTIAL  
**UI:** N/A  
**Infrastructure/Integration:** PARTIAL  
**Tests:** PARTIAL  

### What Already Exists

- Lab voice/DID/outbound tests; VMware lab docs



### What Is Missing

- Production-path live telephony acceptance attestation



### What Is Partial

*N/A or covered under Missing/Exists.*

### Codebase Evidence

- docs/vmware-lab-inbound.md
- docs/execution/26-PHASE-19-EVIDENCE.md — LIVE_INBOUND/OUTBOUND Missing
- apps/api/tests/test_voice_api.py



### Dependency Verification

**Jira Dependencies:** VKT-080, VKT-093, VKT-095, VKT-097, VKT-098

**Dependency Status:**

- VKT-080 = PARTIAL
- VKT-093 = PARTIAL
- VKT-095 = COMPLETE
- VKT-097 = COMPLETE
- VKT-098 = COMPLETE

Remaining work may still depend on: VKT-080, VKT-093.

### Acceptance / QA Coverage

Some automated tests exist; gaps remain relative to full DoD/acceptance (see Missing/Remaining).

### Required Remaining Work

- Run live canary inbound/outbound and attach evidence



### Audit Conclusion

VKT-143 is **PARTIAL**. Keep existing evidence; finish only the listed remaining work.

---



# VKT-144 — Run tools, integration and human handoff acceptance test



## Jira Definition

**Sprint:** Sprint 7  
**Portal / Layer:** QA  
**Epic:** E2E  
**Module:** Agent integration/transfer  
**Priority:** Must  
**Story Points:** 5  
**Estimated Hours:** 5  
**Dependencies:** VKT-088, VKT-090, VKT-099  
**Dependency Category:** BLOCKING  
**Flow:** Agent -> action/transfer -> provider/integration -> result/fallback -> call/audit.  

### Definition of Done

Configure authorized integration/action and transfer destination/rules, test action execution with sanitized failures and verify transfer attempt/outcome is captured.

### SRS Traceability

- **SRS Traceability (from XLS):** §17; §18; §31.1
- **Business rules / state machines / events / acceptance / gates:** Interpreted only from the XLS SRS column and matching SRS sections; see SRS document for full text. Do not invent IDs beyond the XLS column.



### Current Implementation Status

**Overall:** PARTIAL

**Backend:** PARTIAL  
**UI:** N/A  
**Infrastructure/Integration:** PARTIAL  
**Tests:** PARTIAL  

### What Already Exists

- Tools/integrations/transfer lab tests



### What Is Missing

- Packaged human-handoff acceptance on production path



### What Is Partial

*N/A or covered under Missing/Exists.*

### Codebase Evidence

- apps/api/tests/test_integrations_api.py
- apps/api/tests/test_media_api.py



### Dependency Verification

**Jira Dependencies:** VKT-088, VKT-090, VKT-099

**Dependency Status:**

- VKT-088 = COMPLETE
- VKT-090 = COMPLETE
- VKT-099 = PARTIAL

Remaining work may still depend on: VKT-099.

### Acceptance / QA Coverage

Some automated tests exist; gaps remain relative to full DoD/acceptance (see Missing/Remaining).

### Required Remaining Work

- Execute tools+handoff acceptance with evidence



### Audit Conclusion

VKT-144 is **PARTIAL**. Keep existing evidence; finish only the listed remaining work.

---



# VKT-145 — Verify customer portal scope and permitted functions



## Jira Definition

**Sprint:** Sprint 7  
**Portal / Layer:** QA  
**Epic:** E2E  
**Module:** Customer portal isolation  
**Priority:** Must  
**Story Points:** 5  
**Estimated Hours:** 5  
**Dependencies:** VKT-136, VKT-130, VKT-107  
**Dependency Category:** BLOCKING  
**Flow:** Customer login -> scoped data -> permitted action -> cross-tenant attempt denied.  

### Definition of Done

Confirm customer sees only owned agents/calls/invoices/usage, can pay invoices/top up where configured, and cannot access agency/platform data or restricted agent fields.

### SRS Traceability

- **SRS Traceability (from XLS):** §9; TEN-005; §31.1
- **Business rules / state machines / events / acceptance / gates:** Interpreted only from the XLS SRS column and matching SRS sections; see SRS document for full text. Do not invent IDs beyond the XLS column.



### Current Implementation Status

**Overall:** PARTIAL

**Backend:** PARTIAL  
**UI:** PARTIAL  
**Infrastructure/Integration:** N/A  
**Tests:** PARTIAL  

### What Already Exists

- Server-side customer scope enforcement in APIs



### What Is Missing

- UI verification pack for customer portal permitted functions



### What Is Partial

*N/A or covered under Missing/Exists.*

### Codebase Evidence

- apps/api/tests/ — customer isolation cases across modules
- packages/web-ui customer portal



### Dependency Verification

**Jira Dependencies:** VKT-136, VKT-130, VKT-107

**Dependency Status:**

- VKT-136 = PARTIAL
- VKT-130 = COMPLETE
- VKT-107 = PARTIAL

Remaining work may still depend on: VKT-136, VKT-107.

### Acceptance / QA Coverage

Some automated tests exist; gaps remain relative to full DoD/acceptance (see Missing/Remaining).

### Required Remaining Work

- Execute customer portal scope acceptance checklist



### Audit Conclusion

VKT-145 is **PARTIAL**. Keep existing evidence; finish only the listed remaining work.

---



# VKT-146 — Run payout request-to-receipt acceptance test



## Jira Definition

**Sprint:** Sprint 7  
**Portal / Layer:** QA  
**Epic:** E2E  
**Module:** Payout lifecycle  
**Priority:** Must  
**Story Points:** 8  
**Estimated Hours:** 5  
**Dependencies:** VKT-052, VKT-053, VKT-054, VKT-055, VKT-056  
**Dependency Category:** BLOCKING  
**Flow:** Available -> Withdraw -> Requested -> Review -> Approved -> Processing -> proof -> Paid -> receipt.  

### Definition of Done

Verify only Available funds can be requested, atomic reservation occurs, admin review/actions work, private proof remains inaccessible to agency, Paid generates receipt and notification.

### SRS Traceability

- **SRS Traceability (from XLS):** §11.3; §11.4; §31.1
- **Business rules / state machines / events / acceptance / gates:** Interpreted only from the XLS SRS column and matching SRS sections; see SRS document for full text. Do not invent IDs beyond the XLS column.



### Current Implementation Status

**Overall:** PARTIAL

**Backend:** COMPLETE  
**UI:** PARTIAL  
**Infrastructure/Integration:** N/A  
**Tests:** COMPLETE  

### What Already Exists

- Backend payout request→reserve→approve→proof→paid→receipt covered by tests



### What Is Missing

- UI acceptance journey + formal release evidence pack



### What Is Partial

*N/A or covered under Missing/Exists.*

### Codebase Evidence

- apps/api/tests/test_commission_api.py



### Dependency Verification

**Jira Dependencies:** VKT-052, VKT-053, VKT-054, VKT-055, VKT-056

**Dependency Status:**

- VKT-052 = COMPLETE
- VKT-053 = PARTIAL
- VKT-054 = COMPLETE
- VKT-055 = COMPLETE
- VKT-056 = PARTIAL

Remaining work may still depend on: VKT-053, VKT-056.

### Acceptance / QA Coverage

Automated tests covering the core DoD behaviors were found (see Evidence).

### Required Remaining Work

- Run payout-to-receipt acceptance including UI once VKT-053/056 done



### Audit Conclusion

VKT-146 is **PARTIAL**. Keep existing evidence; finish only the listed remaining work.

---



# VKT-147 — Execute requirement-by-requirement Must regression



## Jira Definition

**Sprint:** Sprint 7  
**Portal / Layer:** QA  
**Epic:** Release  
**Module:** Must-requirement regression  
**Priority:** Must  
**Story Points:** 8  
**Estimated Hours:** 8  
**Dependencies:** VKT-129, VKT-130, VKT-131, VKT-132, VKT-141, VKT-142, VKT-143, VKT-144, VKT-145, VKT-146  
**Dependency Category:** BLOCKING  
**Flow:** Requirement -> test -> pass/fail -> defect -> retest.  

### Definition of Done

Run traceable regression covering all Must requirements in the SRS, with failures linked to exact requirement IDs and no scope additions.

### SRS Traceability

- **SRS Traceability (from XLS):** All Must requirements
- **Business rules / state machines / events / acceptance / gates:** Interpreted only from the XLS SRS column and matching SRS sections; see SRS document for full text. Do not invent IDs beyond the XLS column.



### Current Implementation Status

**Overall:** PARTIAL

**Backend:** PARTIAL  
**UI:** N/A  
**Infrastructure/Integration:** N/A  
**Tests:** PARTIAL  

### What Already Exists

- Phase 17 required test catalog
- Feature matrix



### What Is Missing

- Requirement-by-requirement Must regression mapped to every SRS Must ID



### What Is Partial

*N/A or covered under Missing/Exists.*

### Codebase Evidence

- apps/api/tests/test_phase17_matrices.py
- docs/execution/12-FEATURE-MATRIX.md



### Dependency Verification

**Jira Dependencies:** VKT-129, VKT-130, VKT-131, VKT-132, VKT-141, VKT-142, VKT-143, VKT-144, VKT-145, VKT-146

**Dependency Status:**

- VKT-129 = COMPLETE
- VKT-130 = COMPLETE
- VKT-131 = PARTIAL
- VKT-132 = PARTIAL
- VKT-141 = PARTIAL
- VKT-142 = PARTIAL
- VKT-143 = PARTIAL
- VKT-144 = PARTIAL
- VKT-145 = PARTIAL
- VKT-146 = PARTIAL

Remaining work may still depend on: VKT-131, VKT-132, VKT-141, VKT-142, VKT-143, VKT-144, VKT-145, VKT-146.

### Acceptance / QA Coverage

Some automated tests exist; gaps remain relative to full DoD/acceptance (see Missing/Remaining).

### Required Remaining Work

- Produce SRS Must ID regression matrix with pass/fail evidence



### Audit Conclusion

VKT-147 is **PARTIAL**. Keep existing evidence; finish only the listed remaining work.

---



# VKT-148 — Verify SRS functional and engineering/QA release gates



## Jira Definition

**Sprint:** Sprint 7  
**Portal / Layer:** QA  
**Epic:** Release  
**Module:** Release gate verification  
**Priority:** Must  
**Story Points:** 5  
**Estimated Hours:** 5  
**Dependencies:** VKT-147  
**Dependency Category:** BLOCKING  
**Flow:** Release checklist -> evidence -> gate pass/fail -> sign-off.  

### Definition of Done

Verify agency/KYC/customer/payment/commission/wallet/payout, suspension, telephony, customer scope, signed integrations/webhooks, reversal, roles, automated tests and security review gates.

### SRS Traceability

- **SRS Traceability (from XLS):** §31.1; §31.2
- **Business rules / state machines / events / acceptance / gates:** Interpreted only from the XLS SRS column and matching SRS sections; see SRS document for full text. Do not invent IDs beyond the XLS column.



### Current Implementation Status

**Overall:** PARTIAL

**Backend:** PARTIAL  
**UI:** N/A  
**Infrastructure/Integration:** PARTIAL  
**Tests:** PARTIAL  

### What Already Exists

- Lab gate PASS via check_production_readiness --lab
- Functional backends for many §31.1 gates



### What Is Missing

- Engineering gates: observability alerts, live provider E2E, live restore
- Formal §31 gate attestation



### What Is Partial

*N/A or covered under Missing/Exists.*

### Codebase Evidence

- apps/api/control_plane/ops/management/commands/check_production_readiness.py
- docs/execution/26-PHASE-19-EVIDENCE.md — NO-GO
- SRS §31.1 / §31.2



### Dependency Verification

**Jira Dependencies:** VKT-147

**Dependency Status:**

- VKT-147 = PARTIAL

Remaining work may still depend on: VKT-147.

### Acceptance / QA Coverage

Some automated tests exist; gaps remain relative to full DoD/acceptance (see Missing/Remaining).

### Required Remaining Work

- Drive each release gate to PASS with evidence



### Audit Conclusion

VKT-148 is **PARTIAL**. Keep existing evidence; finish only the listed remaining work.

---



# VKT-149 — Prepare production configuration and operational runbook



## Jira Definition

**Sprint:** Sprint 7  
**Portal / Layer:** Operations  
**Epic:** Release  
**Module:** Production configuration/runbook  
**Priority:** Must  
**Story Points:** 5  
**Estimated Hours:** 6  
**Dependencies:** VKT-120, VKT-121, VKT-127, VKT-128, VKT-148  
**Dependency Category:** BLOCKING  
**Flow:** Staging config -> reviewed production config -> secrets -> smoke test -> runbook.  

### Definition of Done

Configure providers, currencies, business-day/payout settings, compliance/retention settings, feature flags, notification sender and operational runbook without hard-coded secrets. Document unresolved jurisdiction/legal dependencies.

### SRS Traceability

- **SRS Traceability (from XLS):** §22; §26; NFR-006..007
- **Business rules / state machines / events / acceptance / gates:** Interpreted only from the XLS SRS column and matching SRS sections; see SRS document for full text. Do not invent IDs beyond the XLS column.



### Current Implementation Status

**Overall:** PARTIAL

**Backend:** PARTIAL  
**UI:** N/A  
**Infrastructure/Integration:** PARTIAL  
**Tests:** N/A  

### What Already Exists

- Runbooks under docs/execution/runbooks/
- Production checklists
- post_deploy_smoke command



### What Is Missing

- Completed production config pack with real secrets placement verified



### What Is Partial

*N/A or covered under Missing/Exists.*

### Codebase Evidence

- docs/execution/runbooks/README.md
- docs/execution/21-RELEASE-CHECKLISTS.md
- docs/execution/22-PRODUCTION-CHECKLIST.md



### Dependency Verification

**Jira Dependencies:** VKT-120, VKT-121, VKT-127, VKT-128, VKT-148

**Dependency Status:**

- VKT-120 = PARTIAL
- VKT-121 = PARTIAL
- VKT-127 = PARTIAL
- VKT-128 = PARTIAL
- VKT-148 = PARTIAL

Remaining work may still depend on: VKT-120, VKT-121, VKT-127, VKT-128, VKT-148.

### Acceptance / QA Coverage

Test applicability limited (N/A) or not separately scored.

### Required Remaining Work

- Fill production configuration checklist with environment-specific values (not in git)



### Audit Conclusion

VKT-149 is **PARTIAL**. Keep existing evidence; finish only the listed remaining work.

---



# VKT-150 — Deploy V1 and validate critical production paths



## Jira Definition

**Sprint:** Sprint 7  
**Portal / Layer:** Operations  
**Epic:** Release  
**Module:** Production deployment/smoke/rollback  
**Priority:** Must  
**Story Points:** 5  
**Estimated Hours:** 6  
**Dependencies:** VKT-149  
**Dependency Category:** BLOCKING  
**Flow:** Deploy -> smoke -> monitor -> accept or rollback.  

### Definition of Done

Deploy the release, run smoke tests for authentication, tenancy, agency/KYC gate, customer creation, payment/commission, payout controls, number/agent/call routing and customer isolation. Confirm rollback readiness.

### SRS Traceability

- **SRS Traceability (from XLS):** §31; NFR-001..007
- **Business rules / state machines / events / acceptance / gates:** Interpreted only from the XLS SRS column and matching SRS sections; see SRS document for full text. Do not invent IDs beyond the XLS column.



### Current Implementation Status

**Overall:** PARTIAL

**Backend:** PARTIAL  
**UI:** N/A  
**Infrastructure/Integration:** NOT_IMPLEMENTED  
**Tests:** PARTIAL  

### What Already Exists

- Deploy templates, lab compose, smoke commands



### What Is Missing

- Actual V1 production deploy + critical path validation evidence



### What Is Partial

*N/A or covered under Missing/Exists.*

### Codebase Evidence

- deploy/
- docs/execution/26-PHASE-19-EVIDENCE.md — all live attestations Missing
- apps/api/control_plane/ops/



### Dependency Verification

**Jira Dependencies:** VKT-149

**Dependency Status:**

- VKT-149 = PARTIAL

Remaining work may still depend on: VKT-149.

### Acceptance / QA Coverage

Some automated tests exist; gaps remain relative to full DoD/acceptance (see Missing/Remaining).

### Required Remaining Work

- Deploy only after gates; validate critical paths; attach evidence



### Audit Conclusion

VKT-150 is **PARTIAL**. Keep existing evidence; finish only the listed remaining work.

---



# VKT-151 — Close release with explicit V1 boundary



## Jira Definition

**Sprint:** Sprint 7  
**Portal / Layer:** Product/QA  
**Epic:** Release  
**Module:** Final baseline sign-off/deferred scope  
**Priority:** Must  
**Story Points:** 2  
**Estimated Hours:** 3  
**Dependencies:** VKT-150  
**Dependency Category:** BLOCKING  
**Flow:** Release gates pass -> sign-off -> production baseline; deferred items remain outside V1.  

### Definition of Done

Record Product, Engineering, QA, Finance/Operations and Compliance/Legal sign-off. Confirm explicitly deferred capabilities remain outside V1.

### SRS Traceability

- **SRS Traceability (from XLS):** §2.2; §32; SRS Baseline Sign-off
- **Business rules / state machines / events / acceptance / gates:** Interpreted only from the XLS SRS column and matching SRS sections; see SRS document for full text. Do not invent IDs beyond the XLS column.



### Current Implementation Status

**Overall:** PARTIAL

**Backend:** N/A  
**UI:** N/A  
**Infrastructure/Integration:** N/A  
**Tests:** N/A  

### What Already Exists

- SRS §32 deferred scope documented
- Phase 19 evidence pack with sign-off table



### What Is Missing

- Explicit signed V1 boundary close-out with owner/QA/finance/legal signatures



### What Is Partial

*N/A or covered under Missing/Exists.*

### Codebase Evidence

- docs/Vokit_V1_Agency_Platform_SRS_v1.0.md §32
- docs/execution/26-PHASE-19-EVIDENCE.md — Sign-off empty



### Dependency Verification

**Jira Dependencies:** VKT-150

**Dependency Status:**

- VKT-150 = PARTIAL

Remaining work may still depend on: VKT-150.

### Acceptance / QA Coverage

Test applicability limited (N/A) or not separately scored.

### Required Remaining Work

- Complete sign-off once gates PASS; publish V1 boundary statement



### Audit Conclusion

VKT-151 is **PARTIAL**. Keep existing evidence; finish only the listed remaining work.

---



## Sprint Summary

### Sprint 1

```text
Total tasks: 15
Complete: 4
Partial: 11
Not implemented: 0
Blocked: 0
Manual review: 0
```

### Sprint 2

```text
Total tasks: 19
Complete: 13
Partial: 5
Not implemented: 1
Blocked: 0
Manual review: 0
```

### Sprint 3

```text
Total tasks: 26
Complete: 14
Partial: 10
Not implemented: 2
Blocked: 0
Manual review: 0
```

### Sprint 4

```text
Total tasks: 30
Complete: 9
Partial: 18
Not implemented: 3
Blocked: 0
Manual review: 0
```

### Sprint 5

```text
Total tasks: 24
Complete: 9
Partial: 15
Not implemented: 0
Blocked: 0
Manual review: 0
```

### Sprint 6

```text
Total tasks: 18
Complete: 6
Partial: 11
Not implemented: 1
Blocked: 0
Manual review: 0
```

### Sprint 7

```text
Total tasks: 19
Complete: 0
Partial: 19
Not implemented: 0
Blocked: 0
Manual review: 0
```

## Epic / Module Summary



### By Epic

**Agencies** — total 6: Complete 0, Partial 6, Missing 0, Blocked 0, NMR 0

**Agents** — total 15: Complete 1, Partial 13, Missing 1, Blocked 0, NMR 0

**Audit** — total 1: Complete 0, Partial 1, Missing 0, Blocked 0, NMR 0

**Automated Tests** — total 3: Complete 2, Partial 1, Missing 0, Blocked 0, NMR 0

**Billing** — total 5: Complete 1, Partial 4, Missing 0, Blocked 0, NMR 0

**Billing/Commission** — total 1: Complete 0, Partial 1, Missing 0, Blocked 0, NMR 0

**Calls** — total 8: Complete 4, Partial 4, Missing 0, Blocked 0, NMR 0

**Commission** — total 2: Complete 1, Partial 1, Missing 0, Blocked 0, NMR 0

**Customers** — total 5: Complete 0, Partial 4, Missing 1, Blocked 0, NMR 0

**Dashboard** — total 2: Complete 0, Partial 2, Missing 0, Blocked 0, NMR 0

**E2E** — total 6: Complete 0, Partial 6, Missing 0, Blocked 0, NMR 0

**Edge Cases** — total 3: Complete 0, Partial 3, Missing 0, Blocked 0, NMR 0

**Foundation** — total 15: Complete 4, Partial 11, Missing 0, Blocked 0, NMR 0

**Instructions** — total 2: Complete 1, Partial 1, Missing 0, Blocked 0, NMR 0

**Integrations** — total 5: Complete 1, Partial 4, Missing 0, Blocked 0, NMR 0

**KYC** — total 8: Complete 5, Partial 2, Missing 1, Blocked 0, NMR 0

**Knowledge** — total 4: Complete 0, Partial 3, Missing 1, Blocked 0, NMR 0

**Notifications** — total 4: Complete 0, Partial 3, Missing 1, Blocked 0, NMR 0

**Observability** — total 1: Complete 0, Partial 1, Missing 0, Blocked 0, NMR 0

**Onboarding** — total 3: Complete 1, Partial 2, Missing 0, Blocked 0, NMR 0

**Overrides** — total 1: Complete 0, Partial 1, Missing 0, Blocked 0, NMR 0

**Phone Numbers** — total 2: Complete 0, Partial 2, Missing 0, Blocked 0, NMR 0

**Plans** — total 2: Complete 0, Partial 2, Missing 0, Blocked 0, NMR 0

**Portal Shell** — total 2: Complete 2, Partial 0, Missing 0, Blocked 0, NMR 0

**Privacy** — total 2: Complete 0, Partial 1, Missing 1, Blocked 0, NMR 0

**Release** — total 5: Complete 0, Partial 5, Missing 0, Blocked 0, NMR 0

**Reliability** — total 1: Complete 0, Partial 1, Missing 0, Blocked 0, NMR 0

**Reporting** — total 3: Complete 0, Partial 3, Missing 0, Blocked 0, NMR 0

**Risk** — total 3: Complete 1, Partial 2, Missing 0, Blocked 0, NMR 0

**Security** — total 1: Complete 0, Partial 1, Missing 0, Blocked 0, NMR 0

**Settings** — total 2: Complete 0, Partial 2, Missing 0, Blocked 0, NMR 0

**Team/Settings** — total 2: Complete 0, Partial 2, Missing 0, Blocked 0, NMR 0

**Telephony** — total 2: Complete 1, Partial 1, Missing 0, Blocked 0, NMR 0

**Templates** — total 3: Complete 1, Partial 2, Missing 0, Blocked 0, NMR 0

**Transfers** — total 4: Complete 0, Partial 3, Missing 1, Blocked 0, NMR 0

**UI Completion** — total 4: Complete 0, Partial 4, Missing 0, Blocked 0, NMR 0

**Usage** — total 1: Complete 0, Partial 1, Missing 0, Blocked 0, NMR 0

**Users/Roles** — total 1: Complete 0, Partial 1, Missing 0, Blocked 0, NMR 0

**Wallet** — total 1: Complete 1, Partial 0, Missing 0, Blocked 0, NMR 0

**Wallet/Payouts** — total 7: Complete 3, Partial 4, Missing 0, Blocked 0, NMR 0

**Webhooks** — total 3: Complete 1, Partial 2, Missing 0, Blocked 0, NMR 0

### By Module

**15-day hold scheduler/state transition** — total 1: Complete 0, Partial 1, Missing 0

**API** — total 1: Complete 1, Partial 0, Missing 0

**Agency call list/detail** — total 1: Complete 0, Partial 1, Missing 0

**Agency dashboard data** — total 1: Complete 0, Partial 1, Missing 0

**Agency detail screen** — total 1: Complete 0, Partial 1, Missing 0

**Agency fraud/risk controls** — total 1: Complete 0, Partial 1, Missing 0

**Agency list screen** — total 1: Complete 0, Partial 1, Missing 0

**Agency onboarding/KYC** — total 1: Complete 0, Partial 1, Missing 0

**Agency/customer knowledge** — total 1: Complete 0, Partial 1, Missing 0

**Agency/customer/portal gate service** — total 1: Complete 0, Partial 1, Missing 0

**Agent Builder - Call Handling** — total 1: Complete 0, Partial 1, Missing 0

**Agent Builder - Identity** — total 1: Complete 0, Partial 1, Missing 0

**Agent Builder - Integrations** — total 1: Complete 0, Partial 0, Missing 1

**Agent Builder - Knowledge** — total 1: Complete 0, Partial 1, Missing 0

**Agent Builder - Persona & Instructions** — total 1: Complete 0, Partial 1, Missing 0

**Agent Builder - Test** — total 1: Complete 0, Partial 1, Missing 0

**Agent Builder - Tools/Actions** — total 1: Complete 0, Partial 1, Missing 0

**Agent Builder - Transfers/Number/Compliance** — total 1: Complete 0, Partial 1, Missing 0

**Agent Builder - Voice & Language** — total 1: Complete 0, Partial 1, Missing 0

**Agent directory** — total 1: Complete 0, Partial 1, Missing 0

**Agent integration/transfer** — total 1: Complete 0, Partial 1, Missing 0

**Agent list/create** — total 1: Complete 0, Partial 1, Missing 0

**Agent list/detail** — total 1: Complete 0, Partial 1, Missing 0

**All portal screens** — total 3: Complete 0, Partial 3, Missing 0

**Architecture** — total 1: Complete 0, Partial 1, Missing 0

**Artifacts** — total 1: Complete 1, Partial 0, Missing 0

**Audit log search/detail** — total 1: Complete 0, Partial 1, Missing 0

**Authentication** — total 1: Complete 0, Partial 1, Missing 0

**Authorization** — total 1: Complete 0, Partial 1, Missing 0

**Authorized data export** — total 1: Complete 0, Partial 0, Missing 1

**Backup/recovery validation** — total 1: Complete 0, Partial 1, Missing 0

**Billing/wallet notifications** — total 1: Complete 0, Partial 0, Missing 1

**Business policy/config service** — total 1: Complete 0, Partial 1, Missing 0

**Business profile screen** — total 1: Complete 1, Partial 0, Missing 0

**Call history/detail** — total 1: Complete 0, Partial 1, Missing 0

**Call lifecycle** — total 1: Complete 1, Partial 0, Missing 0

**Chargeback shutdown and ban** — total 1: Complete 0, Partial 1, Missing 0

**Commission calculation service** — total 1: Complete 1, Partial 0, Missing 0

**Commission control** — total 1: Complete 0, Partial 1, Missing 0

**Connection screens** — total 1: Complete 0, Partial 1, Missing 0

**Connection service** — total 1: Complete 0, Partial 1, Missing 0

**Create agency screen** — total 1: Complete 0, Partial 1, Missing 0

**Create/manage customer screen** — total 1: Complete 0, Partial 1, Missing 0

**Critical workflow telemetry** — total 1: Complete 0, Partial 1, Missing 0

**Customer chargeback freeze/re-onboarding rules** — total 1: Complete 1, Partial 0, Missing 0

**Customer dashboard data** — total 1: Complete 0, Partial 1, Missing 0

**Customer detail/resources screen** — total 1: Complete 0, Partial 0, Missing 1

**Customer directory screen** — total 1: Complete 0, Partial 1, Missing 0

**Customer invitation/activation** — total 1: Complete 1, Partial 0, Missing 0

**Customer list/create screen** — total 1: Complete 0, Partial 1, Missing 0

**Customer plan/balance/suspension actions** — total 1: Complete 0, Partial 1, Missing 0

**Customer portal isolation** — total 1: Complete 0, Partial 1, Missing 0

**Customer/payment/commission** — total 1: Complete 0, Partial 1, Missing 0

**Dashboard** — total 1: Complete 0, Partial 1, Missing 0

**Dashboard drilldowns/date filters** — total 1: Complete 0, Partial 1, Missing 0

**Dashboard screen** — total 1: Complete 0, Partial 1, Missing 0

**Database** — total 4: Complete 1, Partial 3, Missing 0

**Declarations & submit** — total 1: Complete 1, Partial 0, Missing 0

**Destination/team screen** — total 1: Complete 0, Partial 1, Missing 0

**Domain model** — total 1: Complete 1, Partial 0, Missing 0

**Endpoint CRUD/subscription screens** — total 1: Complete 0, Partial 1, Missing 0

**Environment** — total 1: Complete 0, Partial 1, Missing 0

**Events** — total 1: Complete 0, Partial 1, Missing 0

**Evidence upload screen** — total 1: Complete 1, Partial 0, Missing 0

**File security** — total 1: Complete 0, Partial 1, Missing 0

**Final baseline sign-off/deferred scope** — total 1: Complete 0, Partial 1, Missing 0

**Financial state tests** — total 1: Complete 1, Partial 0, Missing 0

**Global call list/detail** — total 1: Complete 0, Partial 1, Missing 0

**Global knowledge screen** — total 1: Complete 0, Partial 1, Missing 0

**Global/template instruction screens** — total 1: Complete 0, Partial 1, Missing 0

**High-risk override framework** — total 1: Complete 0, Partial 1, Missing 0

**Human handoff runtime** — total 1: Complete 0, Partial 1, Missing 0

**Idempotency tests** — total 1: Complete 0, Partial 1, Missing 0

**Immutable wallet ledger service** — total 1: Complete 1, Partial 0, Missing 0

**Inbound routing** — total 1: Complete 1, Partial 0, Missing 0

**Ingestion/processing** — total 1: Complete 0, Partial 0, Missing 1

**Install/clone template** — total 1: Complete 1, Partial 0, Missing 0

**Instruction resolution** — total 1: Complete 1, Partial 0, Missing 0

**Integration status/self-service** — total 1: Complete 0, Partial 1, Missing 0

**Invitation acceptance screen** — total 1: Complete 0, Partial 1, Missing 0

**Invoices/payments** — total 1: Complete 0, Partial 1, Missing 0

**KYC decision actions** — total 1: Complete 0, Partial 1, Missing 0

**KYC queue screen** — total 1: Complete 0, Partial 1, Missing 0

**KYC review detail** — total 1: Complete 1, Partial 0, Missing 0

**Knowledge** — total 1: Complete 0, Partial 1, Missing 0

**Layout & navigation** — total 1: Complete 1, Partial 0, Missing 0

**Layout/navigation** — total 1: Complete 1, Partial 0, Missing 0

**Lifecycle actions** — total 1: Complete 0, Partial 1, Missing 0

**Must-requirement regression** — total 1: Complete 0, Partial 1, Missing 0

**Normalized action runtime** — total 1: Complete 1, Partial 0, Missing 0

**Notification engine/preferences** — total 1: Complete 0, Partial 1, Missing 0

**Number search screen** — total 1: Complete 0, Partial 1, Missing 0

**Number/agent/call** — total 1: Complete 0, Partial 1, Missing 0

**Onboarding/KYC notifications** — total 1: Complete 0, Partial 1, Missing 0

**Outbound calling** — total 1: Complete 0, Partial 1, Missing 0

**Owner/controller screen** — total 1: Complete 1, Partial 0, Missing 0

**Payment processor adapter** — total 1: Complete 0, Partial 1, Missing 0

**Payment webhook idempotency/reconciliation** — total 1: Complete 1, Partial 0, Missing 0

**Payment/billing edge cases** — total 1: Complete 0, Partial 1, Missing 0

**Payments/invoices screen** — total 1: Complete 0, Partial 1, Missing 0

**Payout details screen** — total 1: Complete 0, Partial 0, Missing 1

**Payout history/receipt screen** — total 1: Complete 0, Partial 1, Missing 0

**Payout lifecycle** — total 1: Complete 0, Partial 1, Missing 0

**Payout proof + mark paid** — total 1: Complete 1, Partial 0, Missing 0

**Payout queue/detail screen** — total 1: Complete 0, Partial 1, Missing 0

**Payout receipt generator** — total 1: Complete 1, Partial 0, Missing 0

**Payout/risk edge cases** — total 1: Complete 0, Partial 1, Missing 0

**Plan create/edit/version screen** — total 1: Complete 0, Partial 1, Missing 0

**Plan list screen** — total 1: Complete 0, Partial 1, Missing 0

**Platform reports** — total 1: Complete 0, Partial 1, Missing 0

**Platform settings** — total 1: Complete 0, Partial 1, Missing 0

**Platform users/roles** — total 1: Complete 0, Partial 1, Missing 0

**Production configuration/runbook** — total 1: Complete 0, Partial 1, Missing 0

**Production deployment/smoke/rollback** — total 1: Complete 0, Partial 1, Missing 0

**Provider adapter** — total 1: Complete 1, Partial 0, Missing 0

**Provider registry/connection visibility** — total 1: Complete 0, Partial 1, Missing 0

**Publish preflight** — total 1: Complete 1, Partial 0, Missing 0

**Publish/lifecycle screen** — total 1: Complete 0, Partial 1, Missing 0

**Purchase reconciliation** — total 1: Complete 0, Partial 1, Missing 0

**Purchase/assignment/release** — total 1: Complete 0, Partial 1, Missing 0

**Refund/chargeback reversal service** — total 1: Complete 0, Partial 1, Missing 0

**Release gate verification** — total 1: Complete 0, Partial 1, Missing 0

**Retention/deletion workflow** — total 1: Complete 0, Partial 1, Missing 0

**Risk/internal notes** — total 1: Complete 0, Partial 1, Missing 0

**Rules screen** — total 1: Complete 0, Partial 0, Missing 1

**Secrets** — total 1: Complete 0, Partial 1, Missing 0

**Security** — total 1: Complete 0, Partial 1, Missing 0

**Security test suite** — total 1: Complete 0, Partial 1, Missing 0

**Signed delivery/retry/replay** — total 1: Complete 1, Partial 0, Missing 0

**Status/capability controls** — total 1: Complete 0, Partial 1, Missing 0

**Subscription/invoice domain service** — total 1: Complete 0, Partial 1, Missing 0

**Team/settings** — total 2: Complete 0, Partial 2, Missing 0

**Telephony/agent edge cases** — total 1: Complete 0, Partial 1, Missing 0

**Template catalog screens** — total 1: Complete 0, Partial 1, Missing 0

**Template metadata/version/visibility** — total 1: Complete 0, Partial 1, Missing 0

**Template/delivery/announcement screens** — total 1: Complete 0, Partial 1, Missing 0

**Tenant isolation tests** — total 1: Complete 1, Partial 0, Missing 0

**Time/money/phone** — total 1: Complete 1, Partial 0, Missing 0

**Transfer directory/diagnostics** — total 1: Complete 0, Partial 1, Missing 0

**Usage charging** — total 1: Complete 1, Partial 0, Missing 0

**Usage/minutes** — total 1: Complete 0, Partial 1, Missing 0

**Wallet overview screen** — total 1: Complete 0, Partial 1, Missing 0

**Wallet screen** — total 1: Complete 0, Partial 1, Missing 0

**Webhook logs/replay** — total 1: Complete 0, Partial 1, Missing 0

**Withdraw screen** — total 1: Complete 1, Partial 0, Missing 0

## Already Implemented — Do Not Rebuild

Tasks whose Definition of Done is satisfied after backend + frontend re-audit. Do not rebuild; verify/QA only if release requires.

### VKT-002

**Task:** Define tenant ownership model

**Status:** COMPLETE

**Evidence:**
- See detailed task record (backend + prior evidence).

**Conclusion:**
DO NOT REIMPLEMENT. Only perform verification/QA if required.

### VKT-006

**Task:** Create notification and audit tables

**Status:** COMPLETE

**Evidence:**
- See detailed task record (backend + prior evidence).

**Conclusion:**
DO NOT REIMPLEMENT. Only perform verification/QA if required.

### VKT-011

**Task:** Define versioned API conventions and error contract

**Status:** COMPLETE

**Evidence:**
- See detailed task record (backend + prior evidence).

**Conclusion:**
DO NOT REIMPLEMENT. Only perform verification/QA if required.

### VKT-013

**Task:** Implement canonical money, UTC and E.164 handling

**Status:** COMPLETE

**Evidence:**
- See detailed task record (backend + prior evidence).

**Conclusion:**
DO NOT REIMPLEMENT. Only perform verification/QA if required.

### VKT-016

**Task:** Build Super Admin application shell

**Status:** COMPLETE

**Evidence:**
- See detailed task record (backend + prior evidence).

**Conclusion:**
DO NOT REIMPLEMENT. Only perform verification/QA if required.

### VKT-018

**Task:** Build agency directory with search/filter/status ...

**Status:** COMPLETE

**Evidence:**
- See detailed task record (backend + prior evidence).

**Conclusion:**
DO NOT REIMPLEMENT. Only perform verification/QA if required.

### VKT-019

**Task:** Build Create Agency form

**Status:** COMPLETE

**Evidence:**
- packages/web-ui/src/features/agencies/PlatformAgencyCreateScreen.tsx — Database step
- packages/web-ui/src/features/agencies/hooks/useCreatePlatformAgency.ts — POST /api/v1/platform/agencies with database{}
- packages/web-ui/src/features/agencies/renderAgencyRoutes.tsx — /agencies/new

**Conclusion:**
DO NOT REIMPLEMENT. Only perform verification/QA if required.

### VKT-020

**Task:** Build agency profile/detail and resource tabs

**Status:** COMPLETE

**Evidence:**
- packages/web-ui/src/features/agencies/PlatformAgencyDetailScreen.tsx
- packages/web-ui/src/features/agencies/hooks/usePlatformAgencyDetail.ts

**Conclusion:**
DO NOT REIMPLEMENT. Only perform verification/QA if required.

### VKT-022

**Task:** Implement agency status and capability overrides

**Status:** COMPLETE

**Evidence:**
- See detailed task record (backend + prior evidence).

**Conclusion:**
DO NOT REIMPLEMENT. Only perform verification/QA if required.

### VKT-023

**Task:** Build internal notes/risk flags

**Status:** COMPLETE

**Evidence:**
- packages/web-ui/src/features/agencies/PlatformAgencyDetailScreen.tsx — notes tab
- packages/web-ui/src/features/agencies/hooks/usePlatformAgencyDetail.ts — GET/POST .../notes

**Conclusion:**
DO NOT REIMPLEMENT. Only perform verification/QA if required.

### VKT-025

**Task:** Build KYC business identity form

**Status:** COMPLETE

**Evidence:**
- See detailed task record (backend + prior evidence).

**Conclusion:**
DO NOT REIMPLEMENT. Only perform verification/QA if required.

### VKT-026

**Task:** Build owner/controller information form

**Status:** COMPLETE

**Evidence:**
- See detailed task record (backend + prior evidence).

**Conclusion:**
DO NOT REIMPLEMENT. Only perform verification/QA if required.

### VKT-027

**Task:** Build identity/business/address evidence upload

**Status:** COMPLETE

**Evidence:**
- See detailed task record (backend + prior evidence).

**Conclusion:**
DO NOT REIMPLEMENT. Only perform verification/QA if required.

### VKT-029

**Task:** Build declarations and KYC submission

**Status:** COMPLETE

**Evidence:**
- See detailed task record (backend + prior evidence).

**Conclusion:**
DO NOT REIMPLEMENT. Only perform verification/QA if required.

### VKT-030

**Task:** Build KYC review queue

**Status:** COMPLETE

**Evidence:**
- packages/web-ui/src/features/kyc/PlatformKycScreen.tsx
- packages/web-ui/src/features/kyc/hooks/usePlatformKyc.ts — GET /api/v1/platform/kyc/cases

**Conclusion:**
DO NOT REIMPLEMENT. Only perform verification/QA if required.

### VKT-031

**Task:** Build secure evidence review and notes

**Status:** COMPLETE

**Evidence:**
- See detailed task record (backend + prior evidence).

**Conclusion:**
DO NOT REIMPLEMENT. Only perform verification/QA if required.

### VKT-032

**Task:** Implement Verify / Reject / More Information

**Status:** COMPLETE

**Evidence:**
- packages/web-ui/src/features/kyc/PlatformKycScreen.tsx — decision actions
- packages/web-ui/src/features/kyc/types.ts — DECISION_STATUSES
- packages/web-ui/src/features/kyc/hooks/usePlatformKyc.ts — POST .../override

**Conclusion:**
DO NOT REIMPLEMENT. Only perform verification/QA if required.

### VKT-035

**Task:** Build plan catalog list

**Status:** COMPLETE

**Evidence:**
- packages/web-ui/src/features/plans/PlatformPlansScreen.tsx
- packages/web-ui/src/features/plans/hooks/usePlatformPlans.ts

**Conclusion:**
DO NOT REIMPLEMENT. Only perform verification/QA if required.

### VKT-036

**Task:** Implement plan CRUD/versioning and entitlements

**Status:** COMPLETE

**Evidence:**
- packages/web-ui/src/features/plans/PlatformPlansScreen.tsx
- packages/web-ui/src/features/plans/hooks/usePlatformPlans.ts

**Conclusion:**
DO NOT REIMPLEMENT. Only perform verification/QA if required.

### VKT-040

**Task:** Build Agency customer list and create flow

**Status:** COMPLETE

**Evidence:**
- See detailed task record (backend + prior evidence).

**Conclusion:**
DO NOT REIMPLEMENT. Only perform verification/QA if required.

### VKT-042

**Task:** Implement customer owner/admin invitation

**Status:** COMPLETE

**Evidence:**
- See detailed task record (backend + prior evidence).

**Conclusion:**
DO NOT REIMPLEMENT. Only perform verification/QA if required.

### VKT-045

**Task:** Implement payment webhook handling

**Status:** COMPLETE

**Evidence:**
- See detailed task record (backend + prior evidence).

**Conclusion:**
DO NOT REIMPLEMENT. Only perform verification/QA if required.

### VKT-046

**Task:** Implement commissionable revenue calculation

**Status:** COMPLETE

**Evidence:**
- See detailed task record (backend + prior evidence).

**Conclusion:**
DO NOT REIMPLEMENT. Only perform verification/QA if required.

### VKT-048

**Task:** Implement ledger entries and balance derivation

**Status:** COMPLETE

**Evidence:**
- See detailed task record (backend + prior evidence).

**Conclusion:**
DO NOT REIMPLEMENT. Only perform verification/QA if required.

### VKT-049

**Task:** Build Super Admin payments/invoices/reconciliatio...

**Status:** COMPLETE

**Evidence:**
- packages/web-ui/src/features/billing/PlatformBillingScreen.tsx
- packages/web-ui/src/features/billing/hooks/usePlatformBilling.ts

**Conclusion:**
DO NOT REIMPLEMENT. Only perform verification/QA if required.

### VKT-050

**Task:** Build agency wallet and bucket visibility

**Status:** COMPLETE

**Evidence:**
- See detailed task record (backend + prior evidence).

**Conclusion:**
DO NOT REIMPLEMENT. Only perform verification/QA if required.

### VKT-052

**Task:** Implement payout request validation and reservation

**Status:** COMPLETE

**Evidence:**
- See detailed task record (backend + prior evidence).

**Conclusion:**
DO NOT REIMPLEMENT. Only perform verification/QA if required.

### VKT-053

**Task:** Build payout review queue and detail

**Status:** COMPLETE

**Evidence:**
- packages/web-ui/src/features/payouts/PlatformPayoutsScreen.tsx
- packages/web-ui/src/features/payouts/hooks/usePlatformPayouts.ts
- packages/web-ui/src/features/payouts/types.ts — PAYOUT_ACTIONS

**Conclusion:**
DO NOT REIMPLEMENT. Only perform verification/QA if required.

### VKT-054

**Task:** Implement private proof upload and Paid transition

**Status:** COMPLETE

**Evidence:**
- See detailed task record (backend + prior evidence).

**Conclusion:**
DO NOT REIMPLEMENT. Only perform verification/QA if required.

### VKT-055

**Task:** Generate agency-visible payout receipt

**Status:** COMPLETE

**Evidence:**
- See detailed task record (backend + prior evidence).

**Conclusion:**
DO NOT REIMPLEMENT. Only perform verification/QA if required.

### VKT-058

**Task:** Implement confirmed chargeback customer freeze an...

**Status:** COMPLETE

**Evidence:**
- See detailed task record (backend + prior evidence).

**Conclusion:**
DO NOT REIMPLEMENT. Only perform verification/QA if required.

### VKT-070

**Task:** Implement deterministic instruction inheritance/r...

**Status:** COMPLETE

**Evidence:**
- See detailed task record (backend + prior evidence).

**Conclusion:**
DO NOT REIMPLEMENT. Only perform verification/QA if required.

### VKT-071

**Task:** Build global and template instruction management

**Status:** COMPLETE

**Evidence:**
- packages/web-ui/src/features/instructions/PlatformInstructionsScreen.tsx
- packages/web-ui/src/features/instructions/hooks/usePlatformInstructions.ts

**Conclusion:**
DO NOT REIMPLEMENT. Only perform verification/QA if required.

### VKT-072

**Task:** Build global knowledge source management

**Status:** COMPLETE

**Evidence:**
- packages/web-ui/src/features/knowledge/PlatformKnowledgeScreen.tsx
- packages/web-ui/src/features/knowledge/hooks/usePlatformKnowledge.ts

**Conclusion:**
DO NOT REIMPLEMENT. Only perform verification/QA if required.

### VKT-075

**Task:** Build template catalog management UI

**Status:** COMPLETE

**Evidence:**
- packages/web-ui/src/features/templates/PlatformTemplatesScreen.tsx
- packages/web-ui/src/features/templates/hooks/usePlatformTemplates.ts

**Conclusion:**
DO NOT REIMPLEMENT. Only perform verification/QA if required.

### VKT-077

**Task:** Implement independent editable template installation

**Status:** COMPLETE

**Evidence:**
- See detailed task record (backend + prior evidence).

**Conclusion:**
DO NOT REIMPLEMENT. Only perform verification/QA if required.

### VKT-078

**Task:** Implement telephony provider abstraction

**Status:** COMPLETE

**Evidence:**
- See detailed task record (backend + prior evidence).

**Conclusion:**
DO NOT REIMPLEMENT. Only perform verification/QA if required.

### VKT-079

**Task:** Build phone number search UI

**Status:** COMPLETE

**Evidence:**
- packages/web-ui/src/productScreens.tsx — NumbersScreen search/reserve/assign
- packages/web-ui/src/features/numbers/PlatformNumbersScreen.tsx

**Conclusion:**
DO NOT REIMPLEMENT. Only perform verification/QA if required.

### VKT-088

**Task:** Implement normalized action execution

**Status:** COMPLETE

**Evidence:**
- See detailed task record (backend + prior evidence).

**Conclusion:**
DO NOT REIMPLEMENT. Only perform verification/QA if required.

### VKT-090

**Task:** Implement signed webhook delivery

**Status:** COMPLETE

**Evidence:**
- See detailed task record (backend + prior evidence).

**Conclusion:**
DO NOT REIMPLEMENT. Only perform verification/QA if required.

### VKT-092

**Task:** Implement agent publish validation

**Status:** COMPLETE

**Evidence:**
- See detailed task record (backend + prior evidence).

**Conclusion:**
DO NOT REIMPLEMENT. Only perform verification/QA if required.

### VKT-094

**Task:** Implement call ingestion and lifecycle persistence

**Status:** COMPLETE

**Evidence:**
- See detailed task record (backend + prior evidence).

**Conclusion:**
DO NOT REIMPLEMENT. Only perform verification/QA if required.

### VKT-095

**Task:** Implement inbound routing to assigned agent/fallback

**Status:** COMPLETE

**Evidence:**
- See detailed task record (backend + prior evidence).

**Conclusion:**
DO NOT REIMPLEMENT. Only perform verification/QA if required.

### VKT-097

**Task:** Implement billable usage and entitlement linkage

**Status:** COMPLETE

**Evidence:**
- See detailed task record (backend + prior evidence).

**Conclusion:**
DO NOT REIMPLEMENT. Only perform verification/QA if required.

### VKT-098

**Task:** Implement recording/transcript/summary artifact s...

**Status:** COMPLETE

**Evidence:**
- See detailed task record (backend + prior evidence).

**Conclusion:**
DO NOT REIMPLEMENT. Only perform verification/QA if required.

### VKT-100

**Task:** Build Super Admin call monitoring

**Status:** COMPLETE

**Evidence:**
- packages/web-ui/src/features/calls/PlatformCallsScreen.tsx
- packages/web-ui/src/features/calls/hooks/usePlatformCalls.ts

**Conclusion:**
DO NOT REIMPLEMENT. Only perform verification/QA if required.

### VKT-102

**Task:** Build Customer Portal shell

**Status:** COMPLETE

**Evidence:**
- See detailed task record (backend + prior evidence).

**Conclusion:**
DO NOT REIMPLEMENT. Only perform verification/QA if required.

### VKT-112

**Task:** Build Super Admin user and role management

**Status:** COMPLETE

**Evidence:**
- packages/web-ui/src/features/users/PlatformUsersScreen.tsx
- packages/web-ui/src/features/users/hooks/usePlatformUsers.ts

**Conclusion:**
DO NOT REIMPLEMENT. Only perform verification/QA if required.

### VKT-114

**Task:** Build Super Admin notification administration

**Status:** COMPLETE

**Evidence:**
- packages/web-ui/src/features/notifications/PlatformNotificationsScreen.tsx
- packages/web-ui/src/features/notifications/hooks/usePlatformNotifications.ts

**Conclusion:**
DO NOT REIMPLEMENT. Only perform verification/QA if required.

### VKT-115

**Task:** Build provider registry and tenant connection vis...

**Status:** COMPLETE

**Evidence:**
- packages/web-ui/src/features/integrations/PlatformIntegrationsScreen.tsx
- packages/web-ui/src/features/integrations/hooks/usePlatformIntegrations.ts

**Conclusion:**
DO NOT REIMPLEMENT. Only perform verification/QA if required.

### VKT-117

**Task:** Build transfer monitoring

**Status:** COMPLETE

**Evidence:**
- packages/web-ui/src/features/transfers/PlatformTransfersScreen.tsx
- packages/web-ui/src/features/transfers/hooks/usePlatformTransfers.ts

**Conclusion:**
DO NOT REIMPLEMENT. Only perform verification/QA if required.

### VKT-118

**Task:** Build immutable audit log search/detail

**Status:** COMPLETE

**Evidence:**
- packages/web-ui/src/features/audit/PlatformAuditScreen.tsx
- packages/web-ui/src/features/audit/hooks/usePlatformAudit.ts

**Conclusion:**
DO NOT REIMPLEMENT. Only perform verification/QA if required.

### VKT-120

**Task:** Build platform settings UI

**Status:** COMPLETE

**Evidence:**
- packages/web-ui/src/features/settings/PlatformSettingsScreen.tsx
- packages/web-ui/src/features/settings/hooks/usePlatformSettings.ts

**Conclusion:**
DO NOT REIMPLEMENT. Only perform verification/QA if required.

### VKT-129

**Task:** Automate commission/wallet/payout state transitio...

**Status:** COMPLETE

**Evidence:**
- See detailed task record (backend + prior evidence).

**Conclusion:**
DO NOT REIMPLEMENT. Only perform verification/QA if required.

### VKT-130

**Task:** Automate cross-tenant authorization tests

**Status:** COMPLETE

**Evidence:**
- See detailed task record (backend + prior evidence).

**Conclusion:**
DO NOT REIMPLEMENT. Only perform verification/QA if required.

## Partially Implemented — Finish These

### VKT-001 — Baseline implementation traceability

**Already exists:**
- Backend: PARTIAL; UI: N/A (see detailed record)

**Still missing:**
- See detailed task record Required Remaining Work.

**Next action:**
Open detailed VKT section and finish listed remaining work.

### VKT-003 — Create core identity and tenancy tables

**Already exists:**
- Backend: PARTIAL; UI: N/A (see detailed record)

**Still missing:**
- See detailed task record Required Remaining Work.

**Next action:**
Open detailed VKT section and finish listed remaining work.

### VKT-004 — Create commercial and financial tables

**Already exists:**
- Backend: PARTIAL; UI: N/A (see detailed record)

**Still missing:**
- See detailed task record Required Remaining Work.

**Next action:**
Open detailed VKT section and finish listed remaining work.

### VKT-005 — Create AI/telephony/integration tables

**Already exists:**
- Backend: PARTIAL; UI: N/A (see detailed record)

**Still missing:**
- See detailed task record Required Remaining Work.

**Next action:**
Open detailed VKT section and finish listed remaining work.

### VKT-007 — Implement secure authentication/session foundation

**Already exists:**
- Backend: PARTIAL; UI: PARTIAL (see detailed record)

**Still missing:**
- See detailed task record Required Remaining Work.

**Next action:**
Open detailed VKT section and finish listed remaining work.

### VKT-008 — Implement server-side RBAC and tenant guards

**Already exists:**
- Backend: PARTIAL; UI: N/A (see detailed record)

**Still missing:**
- See detailed task record Required Remaining Work.

**Next action:**
Open detailed VKT section and finish listed remaining work.

### VKT-009 — Implement input validation and security middleware

**Already exists:**
- Backend: PARTIAL; UI: N/A (see detailed record)

**Still missing:**
- See detailed task record Required Remaining Work.

**Next action:**
Open detailed VKT section and finish listed remaining work.

### VKT-010 — Implement server-side secret management

**Already exists:**
- Backend: PARTIAL; UI: N/A (see detailed record)

**Still missing:**
- See detailed task record Required Remaining Work.

**Next action:**
Open detailed VKT section and finish listed remaining work.

### VKT-012 — Implement internal domain-event contract

**Already exists:**
- Backend: PARTIAL; UI: N/A (see detailed record)

**Still missing:**
- See detailed task record Required Remaining Work.

**Next action:**
Open detailed VKT section and finish listed remaining work.

### VKT-014 — Implement secure file upload abstraction

**Already exists:**
- Backend: PARTIAL; UI: N/A (see detailed record)

**Still missing:**
- See detailed task record Required Remaining Work.

**Next action:**
Open detailed VKT section and finish listed remaining work.

### VKT-015 — Create production-like staging environment and CI...

**Already exists:**
- Backend: PARTIAL; UI: N/A (see detailed record)

**Still missing:**
- See detailed task record Required Remaining Work.

**Next action:**
Open detailed VKT section and finish listed remaining work.

### VKT-017 — Build Super Admin dashboard

**Already exists:**
- Backend: PARTIAL; UI: PARTIAL (see detailed record)

**Still missing:**
- See detailed task record Required Remaining Work.

**Next action:**
Open detailed VKT section and finish listed remaining work.

### VKT-021 — Implement commission rate/effective-date UI and s...

**Already exists:**
- Backend: PARTIAL; UI: COMPLETE (see detailed record)

**Still missing:**
- See detailed task record Required Remaining Work.

**Next action:**
Open detailed VKT section and finish listed remaining work.

### VKT-024 — Build agency-owner invitation acceptance

**Already exists:**
- Backend: COMPLETE; UI: NOT_IMPLEMENTED (see detailed record)
- packages/web-ui/src/features/auth/components/LoginScreen.tsx — login only
- No accept-invite route in PortalApp / features/auth

**Still missing:**
- Build invitation acceptance page calling POST /api/v1/auth/invitations/accept

**Next action:**
Build invitation acceptance page calling POST /api/v1/auth/invitations/accept

### VKT-033 — Implement status/capability gates centrally

**Already exists:**
- Backend: PARTIAL; UI: N/A (see detailed record)

**Still missing:**
- See detailed task record Required Remaining Work.

**Next action:**
Open detailed VKT section and finish listed remaining work.

### VKT-034 — Implement onboarding/KYC notification triggers

**Already exists:**
- Backend: PARTIAL; UI: N/A (see detailed record)

**Still missing:**
- See detailed task record Required Remaining Work.

**Next action:**
Open detailed VKT section and finish listed remaining work.

### VKT-037 — Build global customer directory

**Already exists:**
- Backend: COMPLETE; UI: PARTIAL (see detailed record)

**Still missing:**
- See detailed task record Required Remaining Work.

**Next action:**
Open detailed VKT section and finish listed remaining work.

### VKT-038 — Implement Super Admin customer creation

**Already exists:**
- Backend: COMPLETE; UI: PARTIAL (see detailed record)

**Still missing:**
- See detailed task record Required Remaining Work.

**Next action:**
Open detailed VKT section and finish listed remaining work.

### VKT-039 — Implement customer plan assignment, ledger-backed...

**Already exists:**
- Backend: PARTIAL; UI: PARTIAL (see detailed record)

**Still missing:**
- See detailed task record Required Remaining Work.

**Next action:**
Open detailed VKT section and finish listed remaining work.

### VKT-043 — Implement customer subscription and invoice lifec...

**Already exists:**
- Backend: PARTIAL; UI: PARTIAL (see detailed record)

**Still missing:**
- See detailed task record Required Remaining Work.

**Next action:**
Open detailed VKT section and finish listed remaining work.

### VKT-044 — Implement hosted/tokenized payment integration bo...

**Already exists:**
- Backend: PARTIAL; UI: N/A (see detailed record)

**Still missing:**
- See detailed task record Required Remaining Work.

**Next action:**
Open detailed VKT section and finish listed remaining work.

### VKT-047 — Implement independent commission holds

**Already exists:**
- Backend: PARTIAL; UI: N/A (see detailed record)

**Still missing:**
- See detailed task record Required Remaining Work.

**Next action:**
Open detailed VKT section and finish listed remaining work.

### VKT-051 — Build Agency wallet summary and ledger

**Already exists:**
- Backend: COMPLETE; UI: PARTIAL (see detailed record)
- packages/web-ui/src/productScreens.tsx — PaymentsScreen /wallet
- packages/web-ui/src/features/payouts/PlatformPayoutsScreen.tsx — SA wallet buckets

**Still missing:**
- Agency ledger entry browser with held/available breakdown

**Next action:**
Agency ledger entry browser with held/available breakdown

### VKT-056 — Build agency payout history and receipt access

**Already exists:**
- Backend: COMPLETE; UI: PARTIAL (see detailed record)
- packages/web-ui/src/productScreens.tsx — PayoutsScreen list + request
- SA receipt tab on PlatformPayoutsScreen is platform-scoped

**Still missing:**
- Agency receipt view via GET /api/v1/agency/payouts/{id}/receipt

**Next action:**
Agency receipt view via GET /api/v1/agency/payouts/{id}/receipt

### VKT-057 — Implement commission reversal rules

**Already exists:**
- Backend: PARTIAL; UI: N/A (see detailed record)

**Still missing:**
- See detailed task record Required Remaining Work.

**Next action:**
Open detailed VKT section and finish listed remaining work.

### VKT-059 — Implement agency fraud/risk actions

**Already exists:**
- Backend: PARTIAL; UI: PARTIAL (see detailed record)

**Still missing:**
- See detailed task record Required Remaining Work.

**Next action:**
Open detailed VKT section and finish listed remaining work.

### VKT-061 — Build global agent directory and diagnostics entry

**Already exists:**
- Backend: COMPLETE; UI: PARTIAL (see detailed record)

**Still missing:**
- See detailed task record Required Remaining Work.

**Next action:**
Open detailed VKT section and finish listed remaining work.

### VKT-062 — Implement Super Admin agent lifecycle actions

**Already exists:**
- Backend: PARTIAL; UI: PARTIAL (see detailed record)

**Still missing:**
- See detailed task record Required Remaining Work.

**Next action:**
Open detailed VKT section and finish listed remaining work.

### VKT-063 — Build agency agent directory and creation entry

**Already exists:**
- Backend: COMPLETE; UI: PARTIAL (see detailed record)

**Still missing:**
- See detailed task record Required Remaining Work.

**Next action:**
Open detailed VKT section and finish listed remaining work.

### VKT-064 — Build Identity stage

**Already exists:**
- Backend: PARTIAL; UI: PARTIAL (see detailed record)

**Still missing:**
- See detailed task record Required Remaining Work.

**Next action:**
Open detailed VKT section and finish listed remaining work.

### VKT-065 — Build Voice & Language stage

**Already exists:**
- Backend: PARTIAL; UI: PARTIAL (see detailed record)

**Still missing:**
- See detailed task record Required Remaining Work.

**Next action:**
Open detailed VKT section and finish listed remaining work.

### VKT-066 — Build Persona/Instructions stage

**Already exists:**
- Backend: PARTIAL; UI: PARTIAL (see detailed record)

**Still missing:**
- See detailed task record Required Remaining Work.

**Next action:**
Open detailed VKT section and finish listed remaining work.

### VKT-067 — Build Knowledge attachment stage

**Already exists:**
- Backend: PARTIAL; UI: PARTIAL (see detailed record)

**Still missing:**
- See detailed task record Required Remaining Work.

**Next action:**
Open detailed VKT section and finish listed remaining work.

### VKT-068 — Build Call Handling stage

**Already exists:**
- Backend: PARTIAL; UI: PARTIAL (see detailed record)

**Still missing:**
- See detailed task record Required Remaining Work.

**Next action:**
Open detailed VKT section and finish listed remaining work.

### VKT-069 — Build Tools/Actions stage

**Already exists:**
- Backend: PARTIAL; UI: PARTIAL (see detailed record)

**Still missing:**
- See detailed task record Required Remaining Work.

**Next action:**
Open detailed VKT section and finish listed remaining work.

### VKT-073 — Build agency-wide and customer-specific knowledge...

**Already exists:**
- Backend: PARTIAL; UI: PARTIAL (see detailed record)

**Still missing:**
- See detailed task record Required Remaining Work.

**Next action:**
Open detailed VKT section and finish listed remaining work.

### VKT-076 — Implement template metadata, visibility and versi...

**Already exists:**
- Backend: PARTIAL; UI: PARTIAL (see detailed record)

**Still missing:**
- See detailed task record Required Remaining Work.

**Next action:**
Open detailed VKT section and finish listed remaining work.

### VKT-080 — Implement number purchase, assignment, release an...

**Already exists:**
- Backend: PARTIAL; UI: PARTIAL (see detailed record)

**Still missing:**
- See detailed task record Required Remaining Work.

**Next action:**
Open detailed VKT section and finish listed remaining work.

### VKT-081 — Implement idempotent number purchase reconciliation

**Already exists:**
- Backend: PARTIAL; UI: N/A (see detailed record)

**Still missing:**
- See detailed task record Required Remaining Work.

**Next action:**
Open detailed VKT section and finish listed remaining work.

### VKT-082 — Build transfer destination/team management

**Already exists:**
- Backend: PARTIAL; UI: PARTIAL (see detailed record)

**Still missing:**
- See detailed task record Required Remaining Work.

**Next action:**
Open detailed VKT section and finish listed remaining work.

### VKT-085 — Build Transfers, Phone Number and Compliance stages

**Already exists:**
- Backend: PARTIAL; UI: PARTIAL (see detailed record)

**Still missing:**
- See detailed task record Required Remaining Work.

**Next action:**
Open detailed VKT section and finish listed remaining work.

### VKT-086 — Implement integration ownership/OAuth/credential ...

**Already exists:**
- Backend: PARTIAL; UI: N/A (see detailed record)

**Still missing:**
- See detailed task record Required Remaining Work.

**Next action:**
Open detailed VKT section and finish listed remaining work.

### VKT-087 — Build integrations UI

**Already exists:**
- Backend: PARTIAL; UI: PARTIAL (see detailed record)

**Still missing:**
- See detailed task record Required Remaining Work.

**Next action:**
Open detailed VKT section and finish listed remaining work.

### VKT-089 — Build webhook endpoint management

**Already exists:**
- Backend: COMPLETE; UI: PARTIAL (see detailed record)

**Still missing:**
- See detailed task record Required Remaining Work.

**Next action:**
Open detailed VKT section and finish listed remaining work.

### VKT-091 — Build browser/simulator test screen

**Already exists:**
- Backend: PARTIAL; UI: NOT_IMPLEMENTED (see detailed record)
- AgencyDashboard Test agent CTA navigates to /agents only
- No simulator route under packages/web-ui

**Still missing:**
- Build simulator/test-session screen consuming agency test-sessions API

**Next action:**
Build simulator/test-session screen consuming agency test-sessions API

### VKT-093 — Build publish, activate, pause and clone actions

**Already exists:**
- Backend: PARTIAL; UI: PARTIAL (see detailed record)

**Still missing:**
- See detailed task record Required Remaining Work.

**Next action:**
Open detailed VKT section and finish listed remaining work.

### VKT-096 — Implement outbound calling/caller ID where enabled

**Already exists:**
- Backend: PARTIAL; UI: N/A (see detailed record)

**Still missing:**
- See detailed task record Required Remaining Work.

**Next action:**
Open detailed VKT section and finish listed remaining work.

### VKT-099 — Implement transfer execution and call linkage

**Already exists:**
- Backend: COMPLETE; UI: N/A (see detailed record)

**Still missing:**
- See detailed task record Required Remaining Work.

**Next action:**
Open detailed VKT section and finish listed remaining work.

### VKT-101 — Build agency call monitoring

**Already exists:**
- Backend: PARTIAL; UI: PARTIAL (see detailed record)

**Still missing:**
- See detailed task record Required Remaining Work.

**Next action:**
Open detailed VKT section and finish listed remaining work.

### VKT-103 — Build Customer dashboard

**Already exists:**
- Backend: PARTIAL; UI: PARTIAL (see detailed record)

**Still missing:**
- See detailed task record Required Remaining Work.

**Next action:**
Open detailed VKT section and finish listed remaining work.

### VKT-104 — Build customer agent monitoring

**Already exists:**
- Backend: PARTIAL; UI: PARTIAL (see detailed record)

**Still missing:**
- See detailed task record Required Remaining Work.

**Next action:**
Open detailed VKT section and finish listed remaining work.

### VKT-105 — Build customer call history and artifacts

**Already exists:**
- Backend: PARTIAL; UI: PARTIAL (see detailed record)

**Still missing:**
- See detailed task record Required Remaining Work.

**Next action:**
Open detailed VKT section and finish listed remaining work.

### VKT-106 — Build customer usage and top-up screen

**Already exists:**
- Backend: COMPLETE; UI: PARTIAL (see detailed record)
- packages/web-ui/src/productScreens.tsx — GenericModuleScreen for usage
- packages/web-ui/src/screens.tsx — top-up form (NOT imported / dead)

**Still missing:**
- Wire usage screen + top-up POST /api/v1/customer/usage/top-ups into PortalApp path

**Next action:**
Wire usage screen + top-up POST /api/v1/customer/usage/top-ups into PortalApp path

### VKT-107 — Build customer invoices and payment UI

**Already exists:**
- Backend: COMPLETE; UI: PARTIAL (see detailed record)
- packages/web-ui/src/productScreens.tsx — InvoicesScreen GenericModuleScreen
- CustomerDashboard shows invoices but no pay action

**Still missing:**
- Customer pay invoice / checkout UI

**Next action:**
Customer pay invoice / checkout UI

### VKT-108 — Build customer knowledge view/edit where granted

**Already exists:**
- Backend: PARTIAL; UI: PARTIAL (see detailed record)

**Still missing:**
- See detailed task record Required Remaining Work.

**Next action:**
Open detailed VKT section and finish listed remaining work.

### VKT-109 — Build customer integration visibility and permitt...

**Already exists:**
- Backend: PARTIAL; UI: PARTIAL (see detailed record)

**Still missing:**
- See detailed task record Required Remaining Work.

**Next action:**
Open detailed VKT section and finish listed remaining work.

### VKT-110 — Build customer team, notifications and profile se...

**Already exists:**
- Backend: PARTIAL; UI: PARTIAL (see detailed record)

**Still missing:**
- See detailed task record Required Remaining Work.

**Next action:**
Open detailed VKT section and finish listed remaining work.

### VKT-111 — Build agency team, notification and security sett...

**Already exists:**
- Backend: PARTIAL; UI: PARTIAL (see detailed record)

**Still missing:**
- See detailed task record Required Remaining Work.

**Next action:**
Open detailed VKT section and finish listed remaining work.

### VKT-113 — Complete notification preference and template engine

**Already exists:**
- Backend: PARTIAL; UI: PARTIAL (see detailed record)

**Still missing:**
- See detailed task record Required Remaining Work.

**Next action:**
Open detailed VKT section and finish listed remaining work.

### VKT-116 — Build webhook delivery log and replay UI

**Already exists:**
- Backend: COMPLETE; UI: NOT_IMPLEMENTED (see detailed record)
- packages/web-ui/src/productScreens.tsx — WebhooksScreen create/list only
- PlatformIntegrationsScreen notes agency deliveries not wired

**Still missing:**
- Delivery log + replay UI for agency webhooks

**Next action:**
Delivery log + replay UI for agency webhooks

### VKT-119 — Implement Super Admin override workflow

**Already exists:**
- Backend: PARTIAL; UI: PARTIAL (see detailed record)

**Still missing:**
- See detailed task record Required Remaining Work.

**Next action:**
Open detailed VKT section and finish listed remaining work.

### VKT-121 — Implement centralized configurable business rules

**Already exists:**
- Backend: PARTIAL; UI: N/A (see detailed record)

**Still missing:**
- See detailed task record Required Remaining Work.

**Next action:**
Open detailed VKT section and finish listed remaining work.

### VKT-122 — Implement configurable retention and deletion-req...

**Already exists:**
- Backend: PARTIAL; UI: N/A (see detailed record)

**Still missing:**
- See detailed task record Required Remaining Work.

**Next action:**
Open detailed VKT section and finish listed remaining work.

### VKT-124 — Build platform operational/financial reporting

**Already exists:**
- Backend: PARTIAL; UI: PARTIAL (see detailed record)

**Still missing:**
- See detailed task record Required Remaining Work.

**Next action:**
Open detailed VKT section and finish listed remaining work.

### VKT-125 — Complete agency KPI/report data layer

**Already exists:**
- Backend: PARTIAL; UI: PARTIAL (see detailed record)

**Still missing:**
- See detailed task record Required Remaining Work.

**Next action:**
Open detailed VKT section and finish listed remaining work.

### VKT-126 — Complete customer KPI/report data layer

**Already exists:**
- Backend: PARTIAL; UI: PARTIAL (see detailed record)

**Still missing:**
- See detailed task record Required Remaining Work.

**Next action:**
Open detailed VKT section and finish listed remaining work.

### VKT-127 — Implement structured logs, metrics, traces and co...

**Already exists:**
- Backend: PARTIAL; UI: N/A (see detailed record)

**Still missing:**
- See detailed task record Required Remaining Work.

**Next action:**
Open detailed VKT section and finish listed remaining work.

### VKT-128 — Implement automated backups and recovery test

**Already exists:**
- Backend: COMPLETE; UI: N/A (see detailed record)

**Still missing:**
- See detailed task record Required Remaining Work.

**Next action:**
Open detailed VKT section and finish listed remaining work.

### VKT-131 — Automate payment/webhook/payout/number idempotenc...

**Already exists:**
- Backend: PARTIAL; UI: N/A (see detailed record)

**Still missing:**
- See detailed task record Required Remaining Work.

**Next action:**
Open detailed VKT section and finish listed remaining work.

### VKT-132 — Run security checks for auth/RBAC/secrets/webhook...

**Already exists:**
- Backend: PARTIAL; UI: N/A (see detailed record)

**Still missing:**
- See detailed task record Required Remaining Work.

**Next action:**
Open detailed VKT section and finish listed remaining work.

### VKT-133 — Complete dashboard filter and drilldown behavior

**Already exists:**
- Backend: PARTIAL; UI: PARTIAL (see detailed record)

**Still missing:**
- See detailed task record Required Remaining Work.

**Next action:**
Open detailed VKT section and finish listed remaining work.

### VKT-134 — Complete Super Admin screens and permission-aware...

**Already exists:**
- Backend: PARTIAL; UI: PARTIAL (see detailed record)
- packages/web-ui/src/features/platform/renderPlatformScreen.tsx — dedicated routers
- packages/web-ui/src/features/platform/platformModules.ts — risk only

**Still missing:**
- Replace risk generic screen; finish permission-aware empty/disabled states

**Next action:**
Replace risk generic screen; finish permission-aware empty/disabled states

### VKT-135 — Complete Agency portal screens and state/permissi...

**Already exists:**
- Backend: PARTIAL; UI: PARTIAL (see detailed record)

**Still missing:**
- See detailed task record Required Remaining Work.

**Next action:**
Open detailed VKT section and finish listed remaining work.

### VKT-136 — Complete Customer portal screens and customer-sco...

**Already exists:**
- Backend: PARTIAL; UI: PARTIAL (see detailed record)

**Still missing:**
- See detailed task record Required Remaining Work.

**Next action:**
Open detailed VKT section and finish listed remaining work.

### VKT-137 — Verify payment and commission edge cases

**Already exists:**
- Backend: PARTIAL; UI: N/A (see detailed record)

**Still missing:**
- See detailed task record Required Remaining Work.

**Next action:**
Open detailed VKT section and finish listed remaining work.

### VKT-138 — Verify payout and risk edge cases

**Already exists:**
- Backend: PARTIAL; UI: N/A (see detailed record)

**Still missing:**
- See detailed task record Required Remaining Work.

**Next action:**
Open detailed VKT section and finish listed remaining work.

### VKT-139 — Verify number/call/agent failure behavior

**Already exists:**
- Backend: PARTIAL; UI: N/A (see detailed record)

**Still missing:**
- See detailed task record Required Remaining Work.

**Next action:**
Open detailed VKT section and finish listed remaining work.

### VKT-140 — Run confirmed chargeback shutdown and re-onboardi...

**Already exists:**
- Backend: COMPLETE; UI: N/A (see detailed record)

**Still missing:**
- See detailed task record Required Remaining Work.

**Next action:**
Open detailed VKT section and finish listed remaining work.

### VKT-141 — Run complete agency lifecycle acceptance test

**Already exists:**
- Backend: PARTIAL; UI: PARTIAL (see detailed record)

**Still missing:**
- See detailed task record Required Remaining Work.

**Next action:**
Open detailed VKT section and finish listed remaining work.

### VKT-142 — Run customer commercial flow acceptance test

**Already exists:**
- Backend: PARTIAL; UI: PARTIAL (see detailed record)

**Still missing:**
- See detailed task record Required Remaining Work.

**Next action:**
Open detailed VKT section and finish listed remaining work.

### VKT-143 — Run telephony production-path acceptance test

**Already exists:**
- Backend: PARTIAL; UI: N/A (see detailed record)

**Still missing:**
- See detailed task record Required Remaining Work.

**Next action:**
Open detailed VKT section and finish listed remaining work.

### VKT-144 — Run tools, integration and human handoff acceptan...

**Already exists:**
- Backend: PARTIAL; UI: N/A (see detailed record)

**Still missing:**
- See detailed task record Required Remaining Work.

**Next action:**
Open detailed VKT section and finish listed remaining work.

### VKT-145 — Verify customer portal scope and permitted functions

**Already exists:**
- Backend: PARTIAL; UI: PARTIAL (see detailed record)

**Still missing:**
- See detailed task record Required Remaining Work.

**Next action:**
Open detailed VKT section and finish listed remaining work.

### VKT-146 — Run payout request-to-receipt acceptance test

**Already exists:**
- Backend: COMPLETE; UI: PARTIAL (see detailed record)

**Still missing:**
- See detailed task record Required Remaining Work.

**Next action:**
Open detailed VKT section and finish listed remaining work.

### VKT-147 — Execute requirement-by-requirement Must regression

**Already exists:**
- Backend: PARTIAL; UI: N/A (see detailed record)

**Still missing:**
- See detailed task record Required Remaining Work.

**Next action:**
Open detailed VKT section and finish listed remaining work.

### VKT-148 — Verify SRS functional and engineering/QA release ...

**Already exists:**
- Backend: PARTIAL; UI: N/A (see detailed record)

**Still missing:**
- See detailed task record Required Remaining Work.

**Next action:**
Open detailed VKT section and finish listed remaining work.

### VKT-149 — Prepare production configuration and operational ...

**Already exists:**
- Backend: PARTIAL; UI: N/A (see detailed record)

**Still missing:**
- See detailed task record Required Remaining Work.

**Next action:**
Open detailed VKT section and finish listed remaining work.

### VKT-150 — Deploy V1 and validate critical production paths

**Already exists:**
- Backend: PARTIAL; UI: N/A (see detailed record)

**Still missing:**
- See detailed task record Required Remaining Work.

**Next action:**
Open detailed VKT section and finish listed remaining work.

### VKT-151 — Close release with explicit V1 boundary

**Already exists:**
- Backend: N/A; UI: N/A (see detailed record)

**Still missing:**
- See detailed task record Required Remaining Work.

**Next action:**
Open detailed VKT section and finish listed remaining work.

## NOT IMPLEMENTED TASKS

### VKT-028 — Build payout details capture

- **Overall:** NOT_IMPLEMENTED
- **UI:** NOT_IMPLEMENTED
- See detailed task record.

### VKT-041 — Build agency customer detail

- **Overall:** NOT_IMPLEMENTED
- **UI:** NOT_IMPLEMENTED
- **Why:** Platform customer detail exists, but AGENCY portal customer detail/tabs still missing (Jira is agency customer detail).
- **Exact implementation required:** Agency portal customer detail with resource tabs

### VKT-060 — Implement billing/wallet notification triggers

- **Overall:** NOT_IMPLEMENTED
- **UI:** N/A
- See detailed task record.

### VKT-074 — Implement knowledge processing states and failure...

- **Overall:** NOT_IMPLEMENTED
- **UI:** N/A
- See detailed task record.

### VKT-083 — Build transfer rules

- **Overall:** NOT_IMPLEMENTED
- **UI:** NOT_IMPLEMENTED
- See detailed task record.

### VKT-084 — Build integration/action mapping stage

- **Overall:** NOT_IMPLEMENTED
- **UI:** NOT_IMPLEMENTED
- See detailed task record.

### VKT-123 — Implement authorized tenant data export

- **Overall:** NOT_IMPLEMENTED
- **UI:** N/A
- See detailed task record.

## BLOCKED

None identified.

## NEEDS_MANUAL_REVIEW

None identified.

## SRS Requirements Without Sufficient Implementation



### 1. SRS requirements with no Jira task

- Deferred §32 items (marketplace, white-label domains, multi-currency, automated payout rails, native mobile, etc.) intentionally out of V1 Jira scope.
- Some Should-priority items (e.g. MFA privileged, impersonation) appear thinly in Jira or as PARTIAL foundation tasks only.



### 2. SRS requirements with Jira tasks but no implementation

- PRIV export (VKT-123)
- Async knowledge pipeline (VKT-074)
- TransferRule (VKT-083) if still required vs destinations
- Billing notification dispatch (VKT-060)
- Payout bank details capture (VKT-028)
- Agency customer detail tabs UI (VKT-041)
- Action↔connection mapping stage UI (VKT-084)



### 3. SRS requirements with partial implementation

- Most portal UI (SA/Agency/Customer) — backend ahead of UI
- Observability metrics/alerts (VKT-127)
- Production processor adapters (VKT-044)
- Deletion-request / retention controls (VKT-122)
- Capability enforcement completeness (VKT-033 / SA2 gaps)



### 4. SRS requirements implemented but missing required tests

- Number purchase idempotency completeness (VKT-081/131)
- Consolidated E2E acceptance journeys (VKT-141–146)
- Frontend/UI automated tests largely absent



### 5. SRS requirements changed by ADR

- Agency KYC document vault / in-app review → **ADR-005** external provider (VKT-025–027,029,031)
- Recording bytes not in Django → **ADR-002**
- Tenant DB topology → **ADR-001/003**
- Transfer/voicemail media contracts → **ADR-006**



### 6. SRS requirements deferred / known gaps

- `docs/known-gaps/SA2-AGENCIES-BACKEND-GAPS.md`
- `docs/known-gaps/SA3-CUSTOMERS-BACKEND-GAPS.md` (plan change, impersonation)
- `docs/known-gaps/TENANT-DB-PER-AGENCY-USER.md` (UI credential fields)
- SRS §32 Deferred / Post-V1 Scope



## Release-Gate Audit



### Release Gate: Agency create + commission + invitation

**SRS Reference:** §31.1  
**Required:** CreateAgency + invite + commission rate  
**Current Evidence:** Lab APIs/tests; UI credential fields PARTIAL  
**Status:** PASS  
**Remaining:** Complete SA create UI fields  

### Release Gate: KYC Verified before payout

**SRS Reference:** §31.1 / KYC-001 / ADR-005  
**Required:** assert_payout_eligible + RequestAgencyPayout  
**Current Evidence:** test_kyc_api payout gate  
**Status:** PASS  
**Remaining:** None for rule; SA override UI PARTIAL  

### Release Gate: Agency create customer when capability allows

**SRS Reference:** §31.1  
**Required:** Capability gates on customer create  
**Current Evidence:** Mostly enforced; SA2 remaining runtime gaps  
**Status:** PARTIAL  
**Remaining:** Close VKT-033/SA2 gaps  

### Release Gate: Customer plan + pay Vokit

**SRS Reference:** §31.1  
**Required:** AssignSubscription + PayInvoice + webhook settle  
**Current Evidence:** Lab path works; hosted fields/production adapters PARTIAL; customer pay UI PARTIAL  
**Status:** PARTIAL  
**Remaining:** VKT-044/107  

### Release Gate: Exactly one commission + snapshot + 15d

**SRS Reference:** §31.1  
**Required:** AccrueCommission + Appendix C  
**Current Evidence:** Logic COMPLETE; configurable hold_days wiring PARTIAL  
**Status:** PARTIAL  
**Remaining:** VKT-047 fix  

### Release Gate: Held funds not withdrawable

**SRS Reference:** §31.1  
**Required:** project_wallet + reserve rules  
**Current Evidence:** commission tests  
**Status:** PASS  
**Remaining:** None  

### Release Gate: Atomic payout reservation

**SRS Reference:** §31.1  
**Required:** select_for_update reserve  
**Current Evidence:** concurrent reserve tests  
**Status:** PASS  
**Remaining:** None  

### Release Gate: SA payout review + private proof + Paid + receipt

**SRS Reference:** §31.1  
**Required:** DecidePayout + proof + receipt  
**Current Evidence:** Backend PASS; review UI missing (VKT-053)  
**Status:** PARTIAL  
**Remaining:** Build UI  

### Release Gate: Agency receipt without proof

**SRS Reference:** §31.1  
**Required:** Agency proof 404 + receipt API  
**Current Evidence:** test_commission_api proof ACL  
**Status:** PASS  
**Remaining:** Receipt UI polish  

### Release Gate: Suspended agency restrictions

**SRS Reference:** §31.1  
**Required:** Status/capability policies  
**Current Evidence:** Core exists; full matrix PARTIAL  
**Status:** PARTIAL  
**Remaining:** Negative API matrix completion  

### Release Gate: Audited overrides

**SRS Reference:** §31.1  
**Required:** KYC/risk overrides audited  
**Current Evidence:** Backend strong; unified UI PARTIAL  
**Status:** PARTIAL  
**Remaining:** VKT-119  

### Release Gate: Number purchase/assign + publish agent

**SRS Reference:** §31.1  
**Required:** telephony + PublishAgent  
**Current Evidence:** Lab PASS; production purchase PARTIAL  
**Status:** PARTIAL  
**Remaining:** VKT-080/143  

### Release Gate: Inbound call correct tenant + call record

**SRS Reference:** §31.1  
**Required:** DID resolve + session  
**Current Evidence:** Lab PASS; live attestation FAIL/missing  
**Status:** PARTIAL  
**Remaining:** VKT-143/150  

### Release Gate: Customer portal scope isolation

**SRS Reference:** §31.1  
**Required:** API scope + portal shell  
**Current Evidence:** API strong; UI completeness PARTIAL  
**Status:** PARTIAL  
**Remaining:** VKT-136/145  

### Release Gate: Integrations/webhooks tenant-scoped + signed

**SRS Reference:** §31.1  
**Required:** signature + isolation tests  
**Current Evidence:** test_integrations_api  
**Status:** PASS  
**Remaining:** OAuth still PARTIAL  

### Release Gate: Refund/chargeback without rewriting ledger

**SRS Reference:** §31.1  
**Required:** ReverseCommission + chargeback  
**Current Evidence:** Chargeback PASS; refund webhook missing  
**Status:** PARTIAL  
**Remaining:** VKT-057  

### Release Gate: RBAC prevents unauthorized sensitive actions

**SRS Reference:** §31.1  
**Required:** permission namespaces + tests  
**Current Evidence:** Strong baseline; MFA enrollment missing  
**Status:** PARTIAL  
**Remaining:** VKT-007/132  

### Release Gate: Automated commission/wallet tests

**SRS Reference:** §31.2  
**Required:** test_appendix_c + commission_api  
**Current Evidence:** VKT-129  
**Status:** PASS  
**Remaining:** None  

### Release Gate: Automated tenant isolation tests

**SRS Reference:** §31.2  
**Required:** test_tenant_routing + mysql isolation  
**Current Evidence:** VKT-130  
**Status:** PASS  
**Remaining:** None  

### Release Gate: Automated idempotency payment/payout

**SRS Reference:** §31.2  
**Required:** billing + commission tests  
**Current Evidence:** Payment/payout strong; number purchase thin  
**Status:** PARTIAL  
**Remaining:** VKT-131  

### Release Gate: Security review auth/RBAC/secrets/webhooks/uploads/pay

**SRS Reference:** §31.2  
**Required:** Phase 17 doc + matrices  
**Current Evidence:** Documented; MFA/upload scan gaps  
**Status:** PARTIAL  
**Remaining:** VKT-132  

### Release Gate: Provider sandbox E2E numbers/calls

**SRS Reference:** §31.2  
**Required:** lab tests + staging sandbox e2e  
**Current Evidence:** In-process lab; not external staging  
**Status:** PARTIAL  
**Remaining:** VKT-015/143  

### Release Gate: Backup/restore test

**SRS Reference:** §31.2  
**Required:** test_backup_restore  
**Current Evidence:** Lab PASS; live drill missing  
**Status:** PARTIAL  
**Remaining:** VKT-128  

### Release Gate: Observability dashboards/alerts

**SRS Reference:** §31.2  
**Required:** logging only  
**Current Evidence:** No metrics/alert stack; evidence missing  
**Status:** FAIL  
**Remaining:** VKT-127  

### Release Gate: Production runbooks

**SRS Reference:** §31.2  
**Required:** docs/execution/runbooks/  
**Current Evidence:** Runbooks present  
**Status:** PASS  
**Remaining:** Keep current with ops  

## Security / Tenancy Audit


| Area                        | Status    | Related VKT | Evidence / gap                                  |
| --------------------------- | --------- | ----------- | ----------------------------------------------- |
| Authentication/session/CSRF | PARTIAL   | 007,009     | Login+CSRF+rate limit; MFA enrollment missing   |
| RBAC namespaces             | PARTIAL   | 008,112     | roles.py namespaces; custom roles/UI incomplete |
| Tenant isolation            | COMPLETE  | 002,130     | router fail-closed + tests                      |
| Agency ownership            | COMPLETE  | 002,019–022 | Tenant models + APIs                            |
| Customer ownership          | COMPLETE  | 037–042     | customer_id+tenant_id                           |
| Cross-tenant denial         | COMPLETE  | 130         | test_tenant_routing / mysql isolation           |
| Secrets                     | PARTIAL   | 010         | SecretRef+vault; prod KMS TBD                   |
| Uploads                     | PARTIAL   | 014         | object_ref; malware scan missing                |
| Webhook security            | COMPLETE  | 045,090     | HMAC verify + dedup (lab scheme)                |
| Idempotency                 | PARTIAL   | 045,052,131 | Strong payment/payout; numbers thinner          |
| Payment security            | PARTIAL   | 044,045     | Sandbox HMAC; not vendor-native yet             |
| KYC access                  | COMPLETE* | 025–032     | ADR-005; no doc vault                           |
| Payout restrictions         | COMPLETE  | 052,054     | KYC gate + private proof                        |
| Sensitive data exposure     | PARTIAL   | 054,098     | Proof ACL good; logging discipline present      |




## Finance Audit


| Area                            | Status           | VKT         | Notes                                    |
| ------------------------------- | ---------------- | ----------- | ---------------------------------------- |
| Subscriptions/invoices/payments | PARTIAL          | 043–045,049 | Core backend strong; UI/adapters partial |
| Payment webhooks                | COMPLETE         | 045         | Dedup+settle                             |
| Commission + snapshots          | COMPLETE         | 046         | Appendix C                               |
| Holds / availability            | PARTIAL          | 047         | Default 15d; settings wiring gap         |
| Wallet ledger                   | COMPLETE         | 048         | Insert-only                              |
| Payout reservation              | COMPLETE         | 052         | Atomic                                   |
| Payout approval                 | PARTIAL          | 053         | API COMPLETE; UI missing                 |
| Proof / receipt                 | COMPLETE         | 054–055     | ACL tested                               |
| Refund                          | PARTIAL          | 057         | Manual reverse; no refund webhook        |
| Chargeback                      | COMPLETE         | 058         | Freeze+disable                           |
| Billing notifications           | NOT_IMPLEMENTED  | 060         | Catalog only                             |
| Idempotency                     | COMPLETE/PARTIAL | 045,052,131 | See above                                |




## Telephony Audit


| Area                             | Lab                           | Production                             | VKT                    |
| -------------------------------- | ----------------------------- | -------------------------------------- | ---------------------- |
| Numbers inventory/reserve/assign | Implemented in lab            | Not production-verified purchase       | 078–081                |
| Inbound DID + admission          | Implemented in lab            | Live attestation missing               | 094–095,143            |
| Outbound                         | Implemented in lab            | Live attestation missing               | 096,143                |
| Asterisk / SIP edge / Pipecat    | Packages + deploy lab present | Not carrier-certified in evidence pack | 078,143                |
| STT/LLM/TTS                      | Pipecat package               | Lab                                    | packages/pipecat-voice |
| Balance enforcement              | Implemented in lab            | —                                      | 097                    |
| Transfers                        | Django path lab               | Live missing                           | 099,144                |
| TransferRule                     | NOT_IMPLEMENTED               | —                                      | 083                    |
| Recordings metadata + grants     | Implemented in lab            | Live play attestation missing          | 098                    |
| Transcripts/summaries            | Artifact model lab            | —                                      | 098                    |
| Agent actions/tools              | Allowlist + gateway lab       | OAuth CRM missing                      | 088,086                |


Do **not** claim production telephony readiness: `docs/execution/26-PHASE-19-EVIDENCE.md` is **NO-GO** for live production.

## UI Audit (Jira UI tasks only)

Only tasks whose XLS DoD defines UI/frontend work are scored for UI. Backend-only tasks are not marked UI-missing.

### Completed UI tasks

- VKT-016 Super Admin shell — COMPLETE
- VKT-102 Customer Portal shell — COMPLETE
- ADR-superseded KYC form UIs (025–027,029,031) — not required in-app



### Partial UI tasks (high impact)

- VKT-017–022,030,032,035–040,049–051,053,056,061–069,071–073,075–076,079–082,085,087,089,091,093,100–101,103–114,115–120,133–136
- Pattern: real screens for agencies/customers/agents/dashboards; most other SA modules are `PlatformResourceScreen` read-only tables



### Missing UI tasks

- VKT-023 Notes tab wiring (API exists)
- VKT-024 Invite acceptance page
- VKT-028 Payout details form
- VKT-041 Agency customer detail tabs
- VKT-053 Payout review actions UI
- VKT-084 Action mapping stage UI
- VKT-091 Simulator UI
- VKT-106 Usage/top-up UI



## Recommended Next Development Order

Derived from current backend + frontend status (post frontend pull) — not Sprint 1→7 order.

1. **VKT-060** — Wire billing/wallet/payout notification dispatch (backend catalog exists; still unwired).
2. **VKT-024** — Invitation acceptance UI (`POST /api/v1/auth/invitations/accept`).
3. **VKT-041** — Agency customer detail resource tabs (platform detail exists; agency portal still list-only).
4. **VKT-106 / VKT-107** — Customer usage/top-up + pay-invoice UI on active routes (not dead `screens.tsx`).
5. **VKT-056 / VKT-051** — Agency payout receipt viewer + wallet ledger depth.
6. **VKT-091** — Agent test/simulator UI on existing test-session API.
7. **VKT-116** — Webhook delivery log + replay UI.
8. **VKT-083 / VKT-084** — Transfer rules decision/implementation + action mapping UI.
9. **VKT-074** — Async knowledge ingest states.
10. **VKT-047** — Ensure settle path uses configurable hold_days.
11. **VKT-033** — Enforce `existing_customer_services` on voice/DID path.
12. **VKT-134 / VKT-135 / VKT-136** — Finish remaining SA risk screen + deepen agency/customer portal UX beyond `productScreens.tsx`.
13. **VKT-123 / VKT-122** — Data export + deletion-request.
14. **VKT-127** — Metrics/traces/alerts.
15. **VKT-007** — MFA enrollment.
16. **VKT-137–147** — Acceptance/regression packaging + frontend tests.
17. **VKT-148–151** — Live attestations and release sign-off.

**Do not rebuild** newly COMPLETE Super Admin UI modules (019, 020, 023, 030, 032, 035, 036, 049, 053, 071, 072, 075, 079, 100, 112, 114–115, 117–118, 120) or prior COMPLETE backend cores (ledger/commission/payout/chargeback/calls/recordings/ADR-005 KYC forms).

## Final Project Status (Closing)

```text
Total Jira Tasks: 151
COMPLETE: 55
PARTIAL: 89
NOT_IMPLEMENTED: 7
BLOCKED: 0
NEEDS_MANUAL_REVIEW: 0

Complete by task count: 36.4%
Partial by task count: 58.9%
Remaining by task count: 63.6%

Total Story Points: 698
Completed Story Points: 254
Partial Story Points: 421
Remaining Story Points: 444
```

### Validation

- Individual detailed records: 151
- VKT-001 present: yes
- VKT-151 present: yes
- Frontend re-audit applied: yes (2026-09-12)
- No application code, migrations, tests, XLS, or Jira tickets were modified during this audit.


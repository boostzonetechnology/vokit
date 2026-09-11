# Super Admin Customers backend gaps (SRS §7.3)

**Module:** Super Admin Portal — Customers (`SA3-*`)  
**Surface:** Django backend only  
**SoT:** `docs/Vokit_V1_Agency_Platform_SRS_v1.0.md` §7.3 (also §10.1 customer account, §24.2 customer status, Q-003 minutes vs money, Q-016 no reassignment in initial V1)  
**Recorded:** 2026-09-11  
**Status:** Plan slice implemented (2026-09-11). Items under **Remain open** stay deferred.

This document lists remaining gaps. Related IDs stay in their own modules unless required to close an `SA3` gap.

**Out of scope for this gap file (already decided elsewhere):**

- Cross-agency customer reassignment — deferred (Q-016 / Q-006).
- Per-customer physical DB — not V1 (ADR-001).
- Frontend Super Admin Customers UI.

---

## Remain open (do not invent; no code in current plan)

| Item | Why |
|---|---|
| Plan change / replace / version switch (SA3-004) | SRS does not define mid-cycle upgrade/downgrade behavior |
| Mid-cycle proration (PLAN-007) | Conditional Should; formulas undefined |
| Per-customer commercial overrides (SA3-004) | “Allowed overrides” undefined |
| Auto transitions to Payment Due / Restricted (§24.2) | Needs dunning/risk policy detail beyond suspend |
| SA3-006 Customer impersonation | Should; not scheduled |

---

## SA3-001 — Global customer directory

### Target in current plan

- Enrich list/detail projection (plan, remaining minutes, updated_at).
- Filters: agency, status, q, plan where implementable without breaking tenancy.

### Still after plan (if not fully closed)

- Heavy “activity” analytics beyond updated_at / available invoice signals.

---

## SA3-002 — Create customer

### Target in current plan

- `owner_email` **required**.
- Status **Invited** on create; accept invite → **Active**.
- `deliver_invitation`; no token in HTTP; `owner_conflict` on membership clash.
- Minimal profile fields: legal_name, phone, country, timezone (+ owner email as contact).

---

## SA3-003 — Customer balance

**Decided context (Q-003):** minutes (lots); money on invoices only.

### Target in current plan

- Platform GET usage/lots for a customer.
- `POST .../minutes-adjustment` ledger-backed credit/debit with reason + audit.

### Remain open

- Customer prepaid monetary wallet (out of V1 per Q-003).

---

## SA3-004 — Plan management

### Target in current plan

- GET current subscription for Super Admin.
- First-time assign remains as today.

### Remain open

- Plan change workflow, effective-date change semantics beyond first assign, overrides, proration.

---

## SA3-005 — Suspend customer

### Target in current plan

- Reason required for suspend/close; `record_audit` on status change.
- Keep active ↔ suspended ↔ close (privileged).

### Remain open

- Full §24.2 automation for Payment Due / Restricted.

---

## SA3-006 — Customer impersonation (Should)

### Remain open

- Entire flow (permission stub only today).

---

Do not start coding from deferred rows until the owner asks for a new plan.

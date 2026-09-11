# Super Admin Agencies backend gaps (SRS §7.2)

**Module:** Super Admin Portal — Agencies (`SA2-*`)  
**Surface:** Django backend only  
**SoT:** `docs/Vokit_V1_Agency_Platform_SRS_v1.0.md` §7.2 (also §6.1, §23 Agency entity, §24.1, BR-001 / BR-012–018)  
**Recorded:** 2026-09-11  
**Status:** Phase A backend gaps closed 2026-09-11 (see plan A1–A8). Phase B (per-agency MySQL user) backend closed 2026-09-11 — see [TENANT-DB-PER-AGENCY-USER.md](TENANT-DB-PER-AGENCY-USER.md). Remaining: Super Admin UI fields for DB credentials.

This document lists **only** remaining gaps for this module: items that exist but are not properly wired, and items that do not exist. It does not describe what is already correctly implemented.

Related IDs stay in their own modules (Agency Portal `AG*`, KYC `SA4`, payouts `SA13`, feature flags `SA19`) unless they are required to close an `SA2` gap.

---

## SA2-001 — Create agency

### Have but not wired / incomplete

- Invitation delivery exists (`deliver_invitation` → `invitation.agency` email/in-app) but `CreateAgency` never calls it. Platform `POST /platform/users` and `POST /platform/invitations` do send it; agency create does not.
- Owner token is returned on the create response (lab convenience), not treated as a mailed secret.
- If the email already has a membership, invite is swallowed (`membership_conflict` → `invitation_token=None`); agency still created with no owner path.
- `GET /platform/invitations` lists platform invitations only, so the owner invite created here is not visible on that list.
- Create ignores requested status; it always writes `AgencyStatus.ACTIVE` (tests assert `"status": "active"`). §6.1 Invited/Onboarding is not used.
- No region / operating country on create.
- Agency create does not always produce a real MySQL database Super Admin can use when `TENANT_RUNTIME=memory` in local/test. Production MySQL path provisions per-agency user (Phase B). See [tenant DB per-agency user](TENANT-DB-PER-AGENCY-USER.md).

### Don’t have

- States Invited and Onboarding (enum has `pending`, never set by create).
- Owner credential setup, email verify, terms accept as part of this command (those are later identity/KYC steps).
- `owner_user_id` / `kyc_status` on the agency resource (SRS §23 Agency entity).
- Secure invitation as the only token channel.
- Super Admin **UI** fields to set per-agency MySQL host, port, username, and password (API accepts them; see [TENANT-DB-PER-AGENCY-USER.md](TENANT-DB-PER-AGENCY-USER.md)).

---

## SA2-002 — Agency profile

### Have but not wired / incomplete

- Profile change only emits `agency.profile.changed` structured log. It does not write `audit_events` (unlike KYC override, wallet adjust, settings). BR-015 is not met for this path.
- List has pagination, no search/filter by status/KYC/name.

### Don’t have

- Operating/legal fields: entity type, registration number, addresses, countries, trading name, contacts, region.
- KYC status on this resource (lives on KYC cases, not joined here).
- Explicit “audit rules” (what Super Admin may vs may not edit after KYC).

---

## SA2-003 — Commission control

### Have but not wired / incomplete

- Effective date is not an input. API cannot schedule a future rate; it always takes effect immediately.
- No commission-rate history table or GET of past rates — only the current columns + per-entry snapshot.
- No API test hits `POST .../commission`.
- Rate change is not written to `audit_events` (log only). BR-015 gap.

### Don’t have

- Scheduled/future effective-date policy.
- Query of “rate as of date T” except by reading ledger snapshots after the fact.

---

## SA2-004 — Status control

### Have but not wired / incomplete

- `restrict` / `under_review` do not apply §24.1 default gates (e.g. Restricted: no customers / no payout by default). Only suspend mutates a capability.
- Status change is not `audit_events`; runbook says “Audit the status change” but code only logs `agency.status.changed`.
- `agency.suspended` notification exists, but it is fired from KYC status mapping, not from this status command.
- `close` does not terminate/migrate customer services (§24.1 Closed column).
- No reason / BR-012 “suspicious activity” payload on the status POST.

### Don’t have

- Invited, Onboarding (SRS §24.1). Code has unused `pending`.
- Closure workflow (retain records, disable services, migrate).
- Reopen from Closed.

---

## SA2-005 — Capability overrides

### Have but not wired / incomplete

- `create_agents` is never read by `CreateAgent`. Super Admin or agency can still create agents when the flag is false.
- `existing_customer_services` is not on the call/agent/number runtime path. Turning it off does not stop calls.
- Partial updates overwrite omitted flags to defaults (`True`). Sending `{ "capabilities": { "create_customers": false } }` resets agents/numbers/payouts/services to the dataclass defaults, not “leave unchanged.”
- Suspend only clears `create_customers`; it does not auto-clear agents/numbers/payouts (BR-013 says Super Admin controls those — so leaving them as-is can be intentional, but there is no explicit suspend-options payload).

### Don’t have

- Additional controlled capabilities beyond these five (feature flags live under SA19, not this resource).

---

## SA2-006 — Financial overview

### Have but not wired / incomplete

- Payout repository can filter `tenant_id`, but `GET /api/v1/platform/payouts` does not accept `agency_id`. Payout history is global, not agency-scoped.
- Dashboard labels period captured invoice totals as “Trailing period revenue” / `mrr_minor` — not subscription MRR, and not a separate commission MRR.
- Payments list is not agency-filtered the same way as invoices.
- No `GET /platform/agencies/{id}/finance` (or equivalent) that returns the SA2-006 shape in one contract.

### Don’t have

- True Customer MRR and Expected Commission MRR as distinct recurring metrics (BR-016).
- Agency-nested payout history + customer revenue rollup as specified for this module.

---

## SA2-007 — Resources

### Have but not wired for this module

- Team: `GET /platform/users` lists platform memberships only (`principal_type=PLATFORM`). It cannot list that agency’s users. Super Admin can invite an agency user via `POST /platform/users` with `tenant_id`, but cannot list them here.
- Knowledge: `GET /platform/knowledge` returns global sources only. Agency knowledge is `GET /agency/knowledge` (agency session), not Super Admin traversal of that tenant’s KB.
- No aggregator that Super Admin Agencies UI can treat as one “agency resources” contract.

### Don’t have

- Super Admin query of agency team and agency-scoped knowledge under the agency resource.

---

## SA2-008 — Internal notes (Should)

### Don’t have

- Agency-level notes collection.
- Agency risk flags on the tenant/agency record.
- Platform-only visibility rules for those notes.

---

## Out of scope for this file

- Frontend / Super Admin Agencies UI except the Super Admin DB-user fields described in [TENANT-DB-PER-AGENCY-USER.md](TENANT-DB-PER-AGENCY-USER.md).
- Agency Portal (`AG*`).
- Showing tenant DB username/password/host/port to the agency (future owner flow).
- Implementing the gaps (owner will specify the plan, then proceed).

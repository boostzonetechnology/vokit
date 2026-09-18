# Flow: Super Admin Agencies (VKT-018–023, VKT-033–034)

**Status:** Backend complete (2026-09-18)  
**Surface:** Django API `/api/v1/platform/agencies*` (Super Admin session only)  
**Related:** SRS §7.2 SA2-001..008, BR-001 / BR-011–016 / BR-018, AUD-004, §19 NOT-001–005, §24.1, ADR-010  
**Create + MySQL:** [Agency create + MySQL provisioning](../AGENCY-CREATE-MYSQL.md) (VKT-019 unchanged)

This is the contract the Super Admin Agencies UI should consume **now**. Agency Portal and Customer Portal must not call these routes (they get **403**).

Envelope is the usual `{ "data": …, "meta": { "request_id", "page"? } }`. Mutations need CSRF + cookie session.

---

## Ticket map (what backend closed)

| Ticket | What Super Admin UI can do |
|---|---|
| **VKT-018** | Directory: `GET /platform/agencies?status=&name=` + pagination. No extra filters. |
| **VKT-019** | Create + Invited + owner invite already shipped. **No region, no owner phone.** Post-invite KYC is another ticket. |
| **VKT-020** | PATCH names; resource lists with `?agency_id=`; finance MRR on `/finance`. |
| **VKT-021** | Commission with required `reason` and optional future `rate_effective_at`. Agency users cannot change rates. |
| **VKT-022** | Status/capabilities require `confirm: true`. Restrictive status + every capability save require `reason`. Suspend turns new work off; existing services stay on. |
| **VKT-023** | Platform-only notes on `/notes`. Notes are **not** on agency GET. No agency/customer notes APIs. |

---

## Shared agency payload

Returned by create, GET detail, PATCH, status, capabilities, and commission.

```json
{
  "id": "01…",
  "display_name": "Acme",
  "legal_name": "Acme LLC",
  "tenant_status": "ready",
  "status": "invited",
  "currency": "USD",
  "commission_rate_bps": 1500,
  "previous_commission_rate_bps": 1500,
  "rate_effective_at": "2026-09-18T08:00:00+00:00",
  "capabilities": {
    "create_customers": true,
    "create_agents": true,
    "purchase_numbers": true,
    "request_payouts": true,
    "existing_customer_services": true
  },
  "database": { "host": "…", "port": 3306, "name": "vokit_t_…", "username": "…", "status": "ready" }
}
```

**Frontend notes:**

- `status` = agency business status (`invited` / `pending` / `active` / `restricted` / `under_review` / `suspended` / `closed`).
- `tenant_status` = tenant DB health, not the same field.
- **Do not expect `notes` on this object.** Load notes from `/notes`.
- PATCH ignores commission fields. Use the commission POST.
- `confirm` must be JSON boolean `true`, not the string `"true"`.

How to show live vs scheduled rate:

```text
now >= rate_effective_at  →  live = commission_rate_bps
now <  rate_effective_at  →  live = previous_commission_rate_bps
                             scheduled = commission_rate_bps at rate_effective_at
```

---

## VKT-018 — Directory

`GET /api/v1/platform/agencies`

| Query | Meaning |
|---|---|
| `status` | Exact agency status. Invalid value → **400** |
| `name` | Case-insensitive substring of `display_name` or `legal_name` |
| `limit` / `offset` | Pagination (`meta.page`) |

Do **not** add KYC / country / currency filters; backend will not honor them.

Agency or customer session → **403**.

---

## VKT-019 — Create (no change in this slice)

`POST /api/v1/platform/agencies` still creates `status=invited` and emails the owner.

Required: `display_name`, `legal_name`, `owner_email`, `database.username`, `database.password`.  
Optional: `commission_rate_bps`, `capabilities`, `database.host` / `database.port`.  
Forbidden: `database.name`.

See [AGENCY-CREATE-MYSQL.md](../AGENCY-CREATE-MYSQL.md). Do not add region or owner phone.

---

## VKT-020 — Profile, resources, finance

### Profile

`PATCH /api/v1/platform/agencies/{id}`

```json
{ "display_name": "Acme", "legal_name": "Acme LLC" }
```

Only those two fields. Audits `agency.profile.changed`.

### Resource tabs

Pass `agency_id` on the existing list APIs. Do not fetch the full platform list and filter in the browser.

| Tab | Request |
|---|---|
| Customers | `GET /platform/customers?agency_id={id}` |
| Agents | `GET /platform/agents?agency_id={id}` |
| Numbers | `GET /platform/phone-numbers?agency_id={id}` |
| Calls | `GET /platform/calls?agency_id={id}` |
| Team | `GET /platform/users?agency_id={id}` |
| Knowledge | `GET /platform/knowledge?agency_id={id}` |
| Connections | `GET /platform/integrations?agency_id={id}` (same `agency_id` pattern) |

Numbers now honor `agency_id` the same way as the other tabs.

### Finance (SA2-006)

`GET /api/v1/platform/agencies/{id}/finance`  
Permission: `billing.view`

```json
{
  "agency_id": "01…",
  "mrr_minor": 10000,
  "commission_mrr_minor": 1000,
  "customer_revenue_minor": 0,
  "commission_earned_minor": 0,
  "buckets": { "pending_minor": 0, "on_hold_minor": 0, "available_minor": 0, "frozen_minor": 0 },
  "payouts": []
}
```

| Field | Meaning for UI |
|---|---|
| `mrr_minor` | Sum of **active monthly subscription** plan prices for that agency (not trailing paid invoices) |
| `commission_mrr_minor` | Commission on that MRR using the **currently effective** rate |
| `customer_revenue_minor` | Trailing **paid** invoice totals (different from MRR) |
| `commission_earned_minor` | Ledger commission earned |
| `buckets` | Wallet projection |
| `payouts` | Payout history for this agency |

Money is integer **minor units** (cents), USD. `/wallet` still exists for adjust/freeze; the finance overview for this screen is `/finance`.

---

## VKT-021 — Commission rate (HIGH)

`POST /api/v1/platform/agencies/{id}/commission`  
Permission: `commission.edit`  
Agency/customer sessions → **403**. There is **no** `/agency/.../commission` route.

```json
{
  "commission_rate_bps": 2500,
  "rate_effective_at": "2099-01-01T00:00:00+00:00",
  "reason": "contract renewal"
}
```

| Rule | UI behavior |
|---|---|
| `reason` required | Block submit if empty; backend **400** `reason is required.` |
| Omit `rate_effective_at` | Rate goes live immediately |
| Future ISO timestamp | Keep showing the old live rate until that time; new rate is scheduled |
| Past timestamp | **400** — do not offer backdating |
| `0`–`10000` bps | Invalid range → **400** |

Historical ledger rows keep their snapshot. Changing the rate never rewrites old earnings.

V1 allows **one** pending change. A new future date replaces the unused pending pair.

---

## VKT-022 — Status and capabilities

### Status

`POST /api/v1/platform/agencies/{id}/status`

```json
{ "action": "suspend", "confirm": true, "reason": "risk hold" }
```

| `action` | `confirm` | `reason` |
|---|---|---|
| `activate` / `reactivate` | required (`true`) | not required |
| `restrict` / `review` / `suspend` / `close` | required | required |

Missing confirm → **400** `This action requires explicit confirmation.`  
Closed agency → **409**. Illegal transition → **409**.

**Suspend defaults (§24.1)** — backend forces these off (AND with current flags):

- `create_customers`
- `create_agents`
- `purchase_numbers`
- `request_payouts`

`existing_customer_services` stays **on** unless Super Admin later turns it off on capabilities (BR-014 / BR-013).

Restricted default: customers + payouts off. Under review default: payouts off.

**Restrict notice:** `restrict` delivers mandatory `agency.suspended` (same template as suspend — “suspension or restriction”). Recipients are agency memberships. `review` does **not** send this notice.

### Capabilities

`POST /api/v1/platform/agencies/{id}/capabilities`

```json
{
  "confirm": true,
  "reason": "gate number purchase",
  "capabilities": { "purchase_numbers": false }
}
```

Omitted flags stay as they are (partial update). Always send `confirm: true` and `reason`. Audits `agency.capabilities.changed`. Closed agency → **409**.

Turning `existing_customer_services` **off** stops **new** production admission (`resolve_did` + `bootstrap` → `customer_services_disabled`). In-progress calls are not hung up. Test/training sessions are not gated by this flag.

---

## VKT-033 / VKT-034 — Status gates the UI cannot bypass

These are server-side. Do not rely on hiding buttons.

| Action | Invited / Pending / Restricted / Under review **agency actor** | Super Admin (flag on) | Suspended / Closed |
|---|---|---|---|
| Create customer | 409 | allowed if `create_customers` | 409 everyone |
| Create agent | 409 `agency_cannot_create_agent` | allowed if `create_agents` | 409 everyone |
| Purchase/assign numbers | 409 | allowed if `purchase_numbers` | 409 everyone |
| Request payout | Invited/Pending 409 `payout_agency_blocked` even after KYC Verified. Restricted/Under review follow `request_payouts` (defaults off). Also needs KYC Verified + unfrozen (BR-011). | same payout helper | 409 |

**Customer Restricted** is **risk status**, not `CustomerStatus`. It blocks **new** commercial work (agents, numbers, minute top-up, plan assign) with `customer_risk_blocked`. Existing production calls stay up unless Super Admin suspends the customer or risk is chargeback frozen / banned / suspended. **Payment Due** is still the invoice/dashboard alert — not an account status.

KYC in-app events: `kyc.submitted` / `kyc.approved` / `kyc.rejected` / `kyc.more_info` fire when the case status becomes that value (webhook or Super Admin override). Starting a KYC session (`incomplete`) does **not** send `kyc.submitted`.

---

## VKT-023 — Platform-only notes

`GET /api/v1/platform/agencies/{id}/notes` — list (`limit`/`offset`)  
`POST /api/v1/platform/agencies/{id}/notes`

```json
{ "body": "Chargeback watch", "risk_flag": true }
```

`body` required, max 2000 chars. Response includes `id`, `agency_id`, `body`, `risk_flag`, `created_by_id`, `created_at`.

- Agency/customer sessions → **403** on GET and POST
- Unknown agency → **404**
- No PATCH/DELETE notes
- No notes query filter
- Do **not** build agency-portal or customer-portal notes screens

---

## Frontend wiring checklist (current UI vs this contract)

The Super Admin Agencies screens exist but still send older bodies. After this backend slice they will **400** until updated:

| Screen / hook | Change |
|---|---|
| Directory `usePlatformAgencyList` | Send `?status=` and `?name=` instead of client-only filtering |
| Commission `setCommission` | Send `reason`; optional `rate_effective_at`; show `previous_commission_rate_bps` vs live |
| Status `setStatus` | Send `confirm: true`; collect `reason` for restrict/review/suspend/close |
| Capabilities `setCapabilities` | Send `confirm: true` and `reason` |
| Finance tab | Prefer `GET .../finance` for `mrr_minor` / `commission_mrr_minor` (dashboard period KPIs are not this MRR) |
| Resource tabs | Append `?agency_id={id}` on each list request |
| Types `AgencyRecord` | Add `previous_commission_rate_bps` |

---

## Errors to handle in UI

| HTTP | Typical `error.code` | When |
|---|---|---|
| 400 | `confirmation_required` | Missing `confirm: true` |
| 400 | `validation_error` | Missing reason, bad status, past `rate_effective_at`, invalid date |
| 403 | (platform perm) | Agency/customer session on these routes |
| 404 | `not_found` | Unknown agency (including notes) |
| 409 | `agency_closed` / `invalid_agency_status` | Closed or illegal transition |
| 409 | `agency_cannot_create_agent` | Agency actor not Active, or `create_agents` off, or Suspended/Closed |
| 409 | `payout_agency_blocked` | Invited/Pending/Suspended/Closed, or `request_payouts` off |
| 409 | `customer_services_disabled` | `existing_customer_services` off (new production calls) |
| 409 | `customer_risk_blocked` | Customer risk Restricted (new commercial) or frozen/banned/suspended |

Do not invent extra directory columns, note edit/delete, multi-step rate queues, or a second approver. Those are out of SRS/DoD for this slice.

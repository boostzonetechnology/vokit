# Flow: Plans, assign, caps, upgrade/downgrade

**Status:** Implemented (backend). No React in this slice. No customer self-cancel.  
**Surface:** Django API (`/api/v1/platform/plans*`, `/api/v1/platform/customers/{id}/subscription*`, agency twins for catalog GET, first assign, and change)  
**Related:** SRS PLAN-001, PLAN-005, PLAN-007, SA3-004, Q-004; ADR-011; Jira VKT-036 / VKT-039

Catalog is Super Admin only. Agencies may list active plans and assign/change a **customer** subscription. Customers may **pay** invoices (`billing.pay`), not create plans or request a change.

`0` on `max_agents` / `max_phone_numbers` / `max_concurrency` means unlimited. Empty `allowed_integrations` means every `ProviderKind`. `recording_allowed` defaults true. Existing versions keep those defaults.

---

## 1. Create / version

```text
POST /api/v1/platform/plans
  { name, price_minor, included_minutes, allow_topups, topup_*, overage_*,
    grace_seconds, max_agents?, max_phone_numbers?, max_concurrency?,
    recording_allowed?, allowed_integrations? }
        │
        ▼
  Plan ACTIVE + PlanVersion v1 (purchase-time snapshot)
        │
POST /api/v1/platform/plans/{id}/versions   → v2, v3, …
PATCH /api/v1/platform/plan-versions/{id}   → only while used_at is null
POST /api/v1/platform/plans/{id}/archive
GET  /api/v1/agency/plans                   → active catalog only
```

`GET` plan payloads include `available_integrations` from `ProviderKind` (not a separate catalog endpoint).

After first assign (or a paid upgrade/applied downgrade), that version gets `used_at`. Later PATCH → `409 plan_version_immutable`. Invoice lines store the version’s `amount_minor`. A later v2 price does not rewrite v1 invoices or commission snapshots.

---

## 2. First assign

```text
POST /api/v1/platform/customers/{id}/subscription
POST /api/v1/agency/customers/{id}/subscription
  { plan_version_id }
        │
        ▼
  Tenant subscriptions row (period_started_at = now, pending empty)
  OPEN invoice at current version price (due_at null — does not expire)
        │
        ▼
  Customer POST .../invoices/{id}/pay + processor webhook
        │
        ▼
  PAID + included-minute lots + commission on net total
```

A second first-assign is `409 subscription_exists`. Use change (below). Customer cannot assign.

`GET /api/v1/platform/customers/{id}/subscription` returns current version entitlements, `period_started_at`, `period_end` (calendar month from start), and pending fields.

---

## 3. Caps (per customer, current `plan_version_id`)

Enforced on platform and agency APIs after a subscription exists. No subscription → checks skipped (create-agent-before-subscribe still works).

| Cap | Counts | Blocked when over |
|---|---|---|
| `max_agents` | `AgentStatus.ACTIVE` only | create / clone / template install; publish; resume→active; platform status→active |
| `max_phone_numbers` | assigned numbers for that customer | assign number |
| `max_concurrency` | `RINGING` + `IN_PROGRESS` | voice admit (`concurrency_limit`) |
| `recording_allowed` | — | configure `recording_disclosure=true`; recording ingest |
| `allowed_integrations` | non-empty list | connect provider not on the list |

Pause/archive drop the active-agent count. Resume/publish again only under the cap. Existing integrations/recordings are not auto-disabled.

Codes: `plan_limit_agents`, `plan_limit_numbers`, `plan_limit_concurrency` (admit reason), `plan_recording_disabled`, `plan_integration_not_allowed`.

---

## 4. Upgrade (higher `price_minor`)

Actors: Super Admin (`customer.create`) or agency (`customer.update`).

```text
POST .../customers/{id}/subscription/change
  { plan_version_id }
        │
        ▼
  credit = floor(current_price_minor * remaining_seconds / period_seconds)
  total  = max(0, new_price_minor - credit)
  OPEN invoice, promo credit line, due_at = now + 1 day
  pending_kind=upgrade (plan_version_id unchanged)
        │
        ├── pay / $0 paid in-process → switch version, restart period_started_at,
        │     grant included minutes on the new invoice, mark version used_at
        └── unpaid and now >= due_at → VOID, clear pending, stay on old version
              pay → 409 invoice_expired; create a new change invoice
```

Same calendar month as first assign: `period_end = add_one_calendar_month(period_started_at)` (Jan 31 → Feb 28). Unused old minutes are not clawed back.

An open in-date upgrade invoice blocks another change (`409 subscription_change_pending`).

---

## 5. Downgrade (lower price, or same price with tighter caps/recording/integrations)

```text
POST .../subscription/change
        │
        ├── ACTIVE agents or assigned numbers exceed target
        │     → 409 extras_exceed_plan
        └── else pending_kind=downgrade, pending_effective_at=period_end, no invoice
              applied lazily on GET/change/enforcement, or
              manage.py apply_scheduled_plan_changes
```

Same price with no tighter entitlements applies immediately (no invoice). No customer self-cancel. No auto-renew.

---

## Error codes

| Code | When |
|---|---|
| `subscription_exists` | First-assign reused |
| `subscription_required` | Change without an active subscription |
| `subscription_change_pending` | Open upgrade invoice still in date |
| `upgrade_not_paid` | (reserved; unpaid upgrade never switches version) |
| `invoice_expired` | Pay after `due_at` |
| `extras_exceed_plan` | Downgrade while extras remain |
| `same_plan_version` | Target is already current |
| `plan_version_immutable` | PATCH after `used_at` |
| `plan_limit_*` / `plan_recording_disabled` / `plan_integration_not_allowed` | Caps |

Logs: `billing.subscription.changed`, `billing.invoice.expired` (tenant/customer/invoice ids; no secret amounts).

# Flow: Payout review → proof → Paid → receipt

**Status:** Implemented (backend). No React in this slice.  
**Surface:** Django API (`/api/v1/agency/wallet`, `/api/v1/agency/payouts*`, `/api/v1/platform/payouts*`)  
**Related:** SRS SA13-002..005, BR-009..010, §11.3–11.4, §19, NOT-001..005, WAL-001..007; Jira VKT-053 / VKT-054 / VKT-055 / VKT-060

Ledger entries are the wallet source of truth. Cached balances are not used. Private Super Admin proof is **default-private** (BR-009). TL product exception: Super Admin may set **per-payout** `agency_visible=true` so that agency can GET that payout's proof metadata only. There is no global share toggle.

There is **no** payout status `under_review`. Super Admin reviews rows in `requested` (the existing SA queue filter).

---

## End-to-end

```text
Customer payment captured
        │
        ▼
Invoice PAID + commission_earned (on hold)
  notify payment.success → customer + agency
        │
        ▼
available_at elapsed  (wallet may already treat funds as Available)
ReleaseHolds writes hold_released
  notify commission.available → agency
        │
        ▼
Agency POST /agency/payouts  (KYC verified, Available only)
  ledger payout_reserved  status=requested
  notify payout.requested → agency + platform payout.approve (incl. super_admin)
        │
        ▼
SA GET /platform/payouts  and  GET /platform/payouts/{id}
  requested_at + compliance (agency_status, kyc_*, payout_eligible, wallet_frozen)
        │
        ├── approve  → approved
        ├── process  → processing   (from approved)
        ├── freeze   → frozen       (reservation stays)
        └── reject   → rejected + payout_released
              notify payout.rejected → agency
        │
        ▼
SA POST /platform/payouts/{id}/proof
  multipart file (image/PDF) preferred, or legacy { object_ref, content_type, checksum }
  optional agency_visible on upload
  agency GET proof → 404 unless agency_visible
SA PATCH /platform/payouts/{id}/proof  { agency_visible: true|false }
GET .../proof/file  streams bytes (platform always; agency only when shared)
        │
        ▼
SA POST /platform/payouts/{id}/mark-paid  { transaction_ref }
  payout.proof_required (default true) → 409 payout_proof_required if missing
  ledger payout_paid  receipt_number  status=paid
  notify payout.paid → agency
        │
        ▼
Agency GET /agency/payouts/{id}/receipt
```

Failed capture webhook (`status` not captured): persist processor event `rejected`, notify `payment.failure` once, then `409 payment_not_captured`. Replay of the same event_id is duplicate (no second notice).

Minutes remaining crossing **below 10** (same threshold as the dashboard alert): one `minutes.low` to customer + agency. Further drains while already below 10 do not send again.

---

## 1. Earn and hold (before withdraw)

Settlement (`SettlePayment`) writes one `commission_earned` per payment. `available_at` = settlement + `payout.hold_days` (default 15).

Held funds are not withdrawable (`payout_insufficient`). Wallet availability is derived from `available_at` / freeze / reversal in `project_wallet`. `ReleaseHolds` is bookkeeping (`hold_released`) and the `commission.available` notify hook; it is **not** on Celery beat.

---

## 2. Agency request

```text
POST /api/v1/agency/payouts
  Idempotency-Key required
  { amount_minor, method_label? }
```

Gates: KYC verified, case not frozen, agency status allowed, capability `request_payouts`, amount ≤ Available.

Atomic: lock tenant wallet → `payout_reserved` + payout `requested`. Replay of the same key returns the existing payout and does **not** notify again.

---

## 3. Super Admin review (VKT-053)

| Method | Path | Perm |
|---|---|---|
| GET | `/api/v1/platform/payouts?status=&agency_id=` | `billing.view` |
| GET | `/api/v1/platform/payouts/{id}` | `billing.view` |
| POST | `/api/v1/platform/payouts/{id}/action` `{ action }` | `payout.approve` |

`action`: `approve` | `reject` | `freeze` | `process`.

Allowed transitions:

| From | Actions |
|---|---|
| requested | approve, reject, freeze |
| approved | process, freeze, reject, mark_paid |
| processing | freeze, mark_paid |
| frozen | reject |
| paid / rejected | terminal |

Reject writes `payout_released` (funds return to Available if eligible). Freeze does **not** release the reservation.

List/detail include `compliance`. Extra JSON; older clients can ignore it.

---

## 4. Private proof and Paid (VKT-054)

```text
POST /api/v1/platform/payouts/{id}/proof
  { object_ref, content_type, checksum }     # object storage ref, not file bytes

POST /api/v1/platform/payouts/{id}/mark-paid
  { transaction_ref }
```

Setting `payout.proof_required` (bool, default `true`). Agency `GET .../proof` is **404 by default** (BR-009). Super Admin may share **one payout's** proof via `PATCH .../proof` `{ "agency_visible": true }` (TL exception). Paid payouts reject new proof (`payout_already_paid`).

Mark-paid is allowed from `approved` or `processing` (existing SA path can skip `process`).

---

## 5. Agency receipt (VKT-055)

```text
GET /api/v1/agency/payouts/{id}/receipt
```

Only when status is `paid` and `receipt_number` exists (else 404). Payload includes receipt number (`VKT-PO-…`), payout id, agency display/legal name, amount/currency, request/paid dates, status, issuer (`payout.receipt_issuer`, default `Vokit`), disclaimer that this is not banking proof, and masked method/ref when they have no `*` and are longer than 4 characters (values like `bank ****1111` are left as stored).

---

## 6. Notifications (VKT-060)

Reuse existing catalog + `NotificationControl.dispatch` (in-app + email, billing/suspension mandatory). `billing_notify` runs **after** the financial write. Dispatch errors are logged and do not roll back ledger/payout/settlement.

| Event | When | Recipients |
|---|---|---|
| `payment.success` | New captured settlement only | customer + agency |
| `payment.failure` | New uncaptured webhook | customer + agency |
| `minutes.low` | Remaining crosses below 10 | customer + agency |
| `commission.available` | `ReleaseHolds` wrote `hold_released` for that tenant | agency |
| `payout.requested` | New request (not idempotent replay) | agency + platform `payout.approve` / `super_admin` |
| `payout.paid` | mark_paid | agency |
| `payout.rejected` | reject | agency |

Agency restrict/suspend already sends `agency.suspended`. That path was not duplicated here. Freeze/process do not notify.

---

## Settings

| Key | Default | Used for |
|---|---|---|
| `payout.hold_days` | 15 | `available_at` on commission earned |
| `payout.proof_required` | true | mark-paid proof gate |
| `payout.receipt_issuer` | `Vokit` | receipt issuer line |

---

## Explicitly not in this slice

- Payout status `under_review` or “internal follow-up”
- Celery beat schedule for `ReleaseHolds`
- Proof file bytes through Django (object_ref only; ADR-004)
- Frontend / React
- New ledger kinds

Exception handling: [`docs/execution/runbooks/payout-exception.md`](../execution/runbooks/payout-exception.md). API table: [`docs/execution/06-API-CONTRACTS.md`](../execution/06-API-CONTRACTS.md).

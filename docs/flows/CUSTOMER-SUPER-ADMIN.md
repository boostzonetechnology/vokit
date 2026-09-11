# Flow: Super Admin Customers (SA3)

**Status:** Partial — implemented per `docs/known-gaps/SA3-CUSTOMERS-BACKEND-GAPS.md` current plan  
**Surface:** Django API (`/api/v1/platform/customers*`)  
**Related:** SRS §7.3 (`SA3-001`…`SA3-006`), §10.1, §24.2, Q-003 (minutes), Q-016 (no reassignment)

---

## Done in this slice

| ID | Behavior |
|---|---|
| SA3-002 | `owner_email` required; create → **invited**; invite delivered (no token in HTTP); accept invite → **active**; `owner_conflict` on membership clash; profile fields `legal_name`, `phone`, `country`, `timezone` |
| SA3-005 | Suspend/close require `reason`; `customer.status.changed` audit |
| SA3-003 | `GET .../usage`; `POST .../minutes-adjustment` (ledger lots, `LotKind.adjustment`) |
| SA3-004 (partial) | `GET .../subscription` (current only); first assign unchanged |
| SA3-001 (partial) | List filters agency/status/`q`; detail includes profile + remaining minutes + subscription summary |

### Create sequence

```text
POST /api/v1/platform/customers
  { display_name, agency_id, owner_email, legal_name?, phone?, country?, timezone? }
        │
        ▼
  TenantCustomer status=invited + CustomerIndex
        │
        ▼
  InviteUser(customer_owner) + deliver_invitation
        │
        ▼
  HTTP 201 (no owner_invitation_token)
```

Accept: `POST /api/v1/auth/invitations/accept` → membership + Invited→Active.

Privileged platform `POST .../status` with `action=activate` can also promote Invited→Active (tests / ops).

Invite email is queued (`notifications.send_email` via Celery/Redis). Configure SMTP in `.env` (`EMAIL_*`). Local default `CELERY_TASK_ALWAYS_EAGER=true` sends inline; set to `0` and run a Celery worker for a real queue. See `apps/api/control_plane/notifications/README.md`.

### Minutes adjustment

```text
POST /api/v1/platform/customers/{id}/minutes-adjustment
  { minutes: ±N, reason }   # Q-003: minutes, not money wallet
```

Credit creates an `adjustment` lot; debit drains existing lots in drain order.

---

## Remain open (do not invent)

| Item | Notes |
|---|---|
| Plan change / version switch | SA3-004 mid-cycle undefined |
| PLAN-007 proration | Conditional Should |
| Commercial overrides | Undefined |
| Payment Due / Restricted automation | §24.2 beyond suspend |
| SA3-006 impersonation | Should; stub only |

---

## Tenant schema

Customer profile columns: tenant migration `0011_customer_profile` (`legal_name`, `owner_email`, `phone`, `country`, `timezone`).

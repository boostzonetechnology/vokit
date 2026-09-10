# Vokit API (Phase 19 production gate; live No-Go)

Django 5 + DRF modular monolith. Control-plane settings only. **No tenant router.**

## Run tests

```powershell
cd apps/api
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
.\.venv\Scripts\python.exe -m pytest
```

## Run locally

```powershell
cd apps/api
copy .env.example .env
# start MySQL + Redis: docker compose -f ../../deploy/compose/docker-compose.yml up -d
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe manage.py seed_phase2_demo
.\.venv\Scripts\python.exe manage.py seed_phase3_tenants
.\.venv\Scripts\python.exe manage.py seed_phase4_lifecycle
.\.venv\Scripts\python.exe manage.py runserver 0.0.0.0:8000
```

First Super Admin (optional):

```powershell
.\.venv\Scripts\python.exe manage.py bootstrap_platform_owner --email owner@vokit.test --password "your-long-password"
```

Demo users from `seed_phase2_demo` (password `Phase2-Demo!ok`):

- `platform@vokit.test` — Super Admin
- `agency@vokit.test` — agency owner
- `customer@vokit.test` — customer owner

## Auth

- `GET /api/v1/auth/csrf`
- `POST /api/v1/auth/login` (CSRF required; body is email + password only)
- `POST /api/v1/auth/logout`
- `GET /api/v1/auth/session`
- `POST /api/v1/auth/invitations/accept`
- Portal `GET /api/v1/{platform|agency|customer}/me` — wrong portal returns 403

Session cookie: `vokit_session` (HttpOnly). CSRF cookie: `vokit_csrf`.

Invitation tokens are emailed and still returned on the invite API for lab/accept flows. Do not put tokens in in-app bodies or logs.

Agencies and customers (Agency = physical DB; customer is a child scope):

- `GET/POST /api/v1/platform/agencies`
- `POST /api/v1/platform/agencies/{id}/status|capabilities|commission`
- `POST /api/v1/platform/agencies/{id}/reassign-customer` — always `409` (Q-016)
- `GET/POST /api/v1/platform/customers`
- `GET/POST /api/v1/agency/customers` — session tenant only
- `GET /api/v1/customer/account` — session `customer_id` only

Agency KYC (external provider; no document vault):

- `GET /api/v1/agency/kyc` — status + payout gate
- `POST /api/v1/agency/kyc/session` — start/resume hosted session
- `POST /api/v1/agency/payouts` — KYC verified + available balance reserved atomically
- `GET /api/v1/platform/kyc/cases` + `POST .../override`
- `POST /webhooks/kyc/{provider}/v1/` — signature required before parse

Billing (customer subscriptions only; Q-004):

- `GET/POST /api/v1/platform/plans` + `POST .../versions` + `PATCH /platform/plan-versions/{id}`
- `POST /api/v1/platform/customers/{id}/subscription`
- `GET /api/v1/platform/invoices` `/payments` `/disputes`
- `GET /api/v1/agency/plans` + `GET /agency/customer-invoices`
- `GET /api/v1/customer/invoices` + `POST .../{id}/pay`
- `GET /api/v1/customer/usage` + `POST /customer/usage/top-ups`
- `POST /webhooks/stripe/v1/` and `/webhooks/braintree/v1/` — signature + event-id dedup

Commission / wallet / payout (insert-only ledger):

- `GET /api/v1/agency/wallet` + `GET/POST /agency/payouts`
- `GET /agency/payouts/{id}/receipt` — agency cannot read `/proof`
- `GET /api/v1/platform/payouts` + `POST .../action|proof|mark-paid`
- `POST /platform/commissions/reverse` — compensating entry only
- `python manage.py release_commission_holds` / `reconcile_finance`

Customer payment risk (status independent of account status):

- `GET /api/v1/platform/risk/cases` + `POST .../override` — Super Admin / compliance only
- `GET /api/v1/agency/customers/{id}/risk` — agency cannot `POST .../override`
- `GET/POST /api/v1/customer/verification` — object refs + masked last-four; no PAN/CVV
- `GET/POST /api/v1/agency/customers/{id}/agents` — create starts `draft`
- Chargeback webhooks (`status=chargeback.confirmed`) freeze, suspend agents, reverse ledger, and ban re-onboard

Agents / templates / knowledge (unpublished is not production-routable):

- `GET/POST /api/v1/platform/agents` + `POST .../{id}/publish` — Super Admin directory (`agents.review`)
- `GET/POST /api/v1/platform/templates` `/platform/instructions` `/platform/knowledge`
- `GET/POST /api/v1/agency/agents` — scratch or `template_id` clone; `PATCH` configure
- `POST /api/v1/agency/agents/{id}/publish|pause|clone|test-sessions`
- `GET /api/v1/agency/agents/{id}/resolved-instructions` `/routing`
- `GET/POST /api/v1/agency/templates` `/agency/instructions` `/agency/knowledge`
- `GET/PATCH /api/v1/customer/agents/{id}` — greeting/instructions only when `customer_can_edit`
- Empty `QDRANT_URL` uses in-process memory vectors; collection `vokit_knowledge`

Phone numbers (platform inventory; 10-minute exclusive reservation; customer billed on assign):

- `GET/POST /api/v1/platform/phone-numbers` + `POST .../reconcile` + `POST .../{id}/release`
- `GET /api/v1/agency/phone-numbers` `/search`
- `POST /api/v1/agency/phone-numbers/reservations` `/assignments`
- `POST /api/v1/agency/phone-numbers/{id}/release` — `confirm: true` required
- Assignment requires `Idempotency-Key`; line kind `number` is not commissionable

Tenant data plane (Agency = physical DB):

- `GET/POST /api/v1/platform/tenants`
- `POST /api/v1/platform/tenants/{id}/provision/retry`
- `POST /api/v1/platform/tenants/{id}/migrations`
- `POST /api/v1/agency/data-plane/records` — writes an isolation record in the **session** tenant DB
- Forged `tenant_id` in the body/query cannot switch databases

`python manage.py migrate_tenants --canary <tenant-uuid>` applies tenant schema versions with canary-first ordering.
`--canary-only` stops after the canary. Backup/restore:

- `python manage.py backup_control_plane --out control.json`
- `python manage.py backup_tenant --tenant-id <uuid> --out tenant.json`
- `python manage.py restore_tenant --tenant-id <uuid> --snapshot tenant.json`

Health:

- `GET /health` — liveness
- `GET /ready` — control-plane DB check (production also requires tokens + MySQL TLS)
- `GET /api/v1/health`

Production gate:

- `python manage.py check_production_readiness --lab` — CI/lab evidence (`LAB_READY`)
- `python manage.py check_production_readiness` — live GO requires dated attestations
- `python manage.py post_deploy_smoke` — `/health` + `/ready` + `/api/v1/health`
- Live flags `calling_live` / `billing_live` / `recordings_live` default off in production
- `VOKIT_LAUNCH_GO` is not evidence. See `docs/execution/26-PHASE-19-EVIDENCE.md`

Production bind: `gunicorn --bind 0.0.0.0:$PORT config.wsgi:application`

Internal telephony (Pipecat / Asterisk; `X-Vokit-Internal-Token`):

- `POST /internal/telephony/v1/did/resolve/` and `/did-resolve/` — Asterisk `routable`
- `POST /internal/telephony/v1/voice-session/bootstrap|events|end|continue|transfer/`
- `GET  /internal/telephony/v1/voice-session/transfer/status/`
- `POST /internal/telephony/v1/voice-session/voicemail/` — inbound/outbound mailbox metadata
- `POST /internal/telephony/v1/tools/invoke/` — allowlisted stub (CRM I/O is Phase 14)
- `POST /internal/telephony/v1/training-session/bootstrap|propose|confirm|end/`
- `GET/POST /api/v1/agency/transfers` + `POST /agency/calls/outbound`
- `GET /api/v1/{platform|agency|customer}/calls`

Admission failures return HTTP 200 with `admitted`/`routable` false (Pipecat fail-closed). Missing token is 401. Do not serve recordings from this app.

Internal recording plane (`X-Vokit-Internal-Token` = `VOKIT_INTERNAL_RECORDING_TOKEN`):

- `POST /internal/recordings/v1/ingest/` — artifact available; tenant comes from `call_index`
- `POST /internal/recordings/v1/access/validate/` — single-use grant consume
- `POST /api/v1/{platform|agency|customer}/calls/{call_id}/artifacts/{artifact_id}/access`
- Agency/platform hold + delete after retention; `reconcile_recordings` for orphans

Tenant schema current version: `0010_integrations`.

Integrations (Q-009 / Q-010):

- `GET/POST /api/v1/agency/integrations` — customer-owned connections only
- `GET/POST /api/v1/customer/integrations` — own connections; connect if agency enabled self-service
- `GET/POST /api/v1/agency/webhooks` — signed outbound endpoints, rotate, replay
- `POST /internal/telephony/v1/tools/invoke/` — Django tool gateway; Pipecat never holds OAuth secrets
- `python manage.py retry_webhooks` — bounded retry / DLQ for failed deliveries

Notifications / audit / settings (control plane only):

- `GET /api/v1/platform/audit-events` — immutable search; PATCH/DELETE return `audit_immutable`
- `GET/PATCH /api/v1/platform/settings` + `POST /platform/settings/flags` — hold days, flags, masked secrets
- `GET/POST /api/v1/platform/notification-templates` `/announcements` `/notification-deliveries`
- `GET /api/v1/{platform|agency|customer}/notifications` — current-user inbox only
- `GET/PUT /api/v1/{agency|customer}/notification-preferences` — mandatory KYC/billing/security/suspension locked
- Commission accrual reads `payout.hold_days` from platform settings (default 15)

Dashboards (RPT-003 — money from ledger/invoices, not the UI):

- `GET /api/v1/platform/dashboard?period=30d&timezone=UTC` — optional `agency_id`
- `GET /api/v1/agency/dashboard` — session tenant only
- `GET /api/v1/customer/dashboard` — session customer only
- `GET /api/v1/customer/agents` — session customer list

Hardening:

- Isolation / finance / voice / recording matrices are executable (`tests/test_phase17_matrices.py`)
- `security.mfa_required_privileged` (default false) fails closed for privileged login until enrollment exists
- Impersonation is permission-catalogued only; no route is implemented

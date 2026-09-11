# Tenant database: per-agency MySQL user (owner-desired flow)

**Module:** Super Admin Agencies create / tenant provisioning (`SA2-001`, ADR-001, ADR-003)  
**Surface:** Django backend (done); Super Admin UI fields later  
**Recorded:** 2026-09-11  
**Status:** Backend Phase B closed 2026-09-11. Frontend Super Admin form fields remain open.

This is a HIGH tenancy/secrets change. Related SRS: Agency create (`SA2-001`). Related ADRs: physical Agency DB (ADR-001); registry + vault credentials (ADR-003 amended).

---

## Backend status (Phase B)

Implemented:

- ADR-003 amendment: per-tenant MySQL user; admin env for `CREATE DATABASE` / `CREATE USER` / `GRANT`; vault for passwords.
- `tenant_databases.db_username` + `tenant_db_credentials` ciphertext vault.
- Agency create requires `database.username` + `database.password`; optional host/port; rejects client `database.name`.
- Provisioning step `user_created`; runtime `open` uses per-tenant username + vault password (no shared `TENANT_DB_USER` fallback).
- GET agency/tenant payloads expose host/port/name/username metadata only — never password.

Remaining (frontend / ops):

- Super Admin Agencies UI fields for host, port, username, password.
- Optional management workflow to assign credentials to legacy rows with empty `db_username`.
- Live MySQL isolation CI can be upgraded to dedicated per-tenant users (optional harness still uses env stub vault).

---

## Owner-desired flow (target — now backend-backed)

1. Super Admin creates an agency (same product create as today).
2. Super Admin **sets** for that agency’s data-plane MySQL:
   - host
   - port
   - username
   - password
3. Database **name** stays as today: `vokit_t_<tenant_uuid_hex>`. Not chosen by the client.
4. Platform provisioning (admin MySQL identity, **not** the agency user):
   - `CREATE DATABASE` for that name
   - `CREATE USER` for the Super Admin–supplied username/password
   - `GRANT` **only** on that one database (`dbname.*`)
5. That MySQL user can see and manage **only their own** database.
6. Application runtime connects as that user via control-plane registry + vault.
7. Shared env `TENANT_DB_USER` / `TENANT_DB_PASSWORD` are not used for tenant runtime login.
8. Agency portal still does **not** receive MySQL credentials in V1 of this change.

Vokit portal login (agency owner email/password) stays separate from this MySQL user.

---

## What remains in env (not a tenant user)

- Control-plane DB: `CONTROL_PLANE_DB_*` (unchanged).
- Platform **admin** MySQL login: `TENANT_DB_ADMIN_USER` + `TENANT_DB_ADMIN_PASSWORD_REF`.
- `TENANT_RUNTIME` (`mysql` vs test `memory`).
- Optional default host/port: `TENANT_DB_HOST` / `TENANT_DB_PORT` when Super Admin omits them.
- Optional demo seed names `TENANT_DB_NAME_A` / `TENANT_DB_NAME_B` are not the new agency path.

---

## Security constraints

- Password write-only: vault only; never plaintext on `tenant_databases`; never log or return password on GET.
- Agency/customer HTTP never selects database name (ADR-003).
- Fail closed; never fall back to another tenant DB or shared tenant login.
- Least-privilege GRANT on one schema only; no `*.*`.
- Audit provision steps without secrets.

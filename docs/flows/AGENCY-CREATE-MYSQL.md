# Flow: Agency create + MySQL provisioning

**Status:** Implemented (Phase A SA2 + Phase B per-agency MySQL user)  
**Surface:** Django API (`POST /api/v1/platform/agencies`)  
**Related:** SRS `SA2-001`, ADR-001, ADR-003 (amended), `docs/known-gaps/TENANT-DB-PER-AGENCY-USER.md`

This is the flow that runs when Super Admin creates an agency with MySQL credentials.

---

## Actors and MySQL identities

Three different MySQL logins are involved. Do not collapse them.

| Identity | Config / source | Used for |
|---|---|---|
| Control-plane app user | `CONTROL_PLANE_DB_*` (e.g. `vokit`) | Everyday Django reads/writes on `vokit_control` only |
| Tenant DB admin | `TENANT_DB_ADMIN_USER` + `TENANT_DB_ADMIN_PASSWORD_REF` (e.g. `root`) | Only during provision: `CREATE DATABASE`, `CREATE USER`, `GRANT` |
| Per-agency tenant user | Super Admin body `database.username` / `database.password` | Runtime open/pool for that agency’s `vokit_t_…` DB only |

Portal login (agency owner email/password) is **separate** from the MySQL user.

---

## High-level sequence

```text
Super Admin (authenticated platform principal)
  │
  │  POST /api/v1/platform/agencies
  │  { display_name, legal_name, owner_email, commission_rate_bps?,
  │    database: { username, password, host?, port? } }
  ▼
AgencyCollectionView
  │  rejects client database.name
  ▼
CreateAgency
  │  1. validate + check db_username uniqueness
  │  2. allocate_tenant_database → name = vokit_t_<tenant_uuid_hex>
  │  3. ProvisionTenant saga
  │  4. set agency_status = invited
  │  5. InviteUser (agency_owner) + deliver_invitation (email)
  ▼
HTTP 201 agency payload
  (status=invited, database metadata without password,
   no owner_invitation_token)
```

---

## Step-by-step (what the code does)

### 1. Authorization

- Caller must be platform principal with `agencies.create`.
- CSRF required for browser/Postman cookie sessions.

### 2. Request contract

Required:

- `display_name`
- `legal_name` (may fall back to display name in domain)
- `owner_email`
- `database.username`
- `database.password` (min 12 characters)

Optional:

- `database.host` / `database.port` (else `TENANT_DB_HOST` / `TENANT_DB_PORT`)
- `commission_rate_bps`
- `capabilities`

Forbidden:

- `database.name` → `400 validation_error` (server allocates the name)

### 3. Allocate registry coordinates

`allocate_tenant_database`:

- Builds immutable `tenant_id` (UUIDv7) if not provided.
- Sets DB **name** to `vokit_t_<tenant_uuid_hex>` (never from the client).
- Validates username / password / host / port.
- Returns coordinates + plaintext password **only to the provisioner** (never in HTTP).

### 4. Provisioning saga (`ProvisionTenant`)

Control-plane rows are written first (`tenants`, `tenant_databases`, `tenant_provisioning_jobs`), password stored in vault (`tenant_db_credentials`), then MySQL work runs:

| Step | Value | Action |
|---|---|---|
| Created | `created` | Job opened |
| Database allocated | `database_allocated` | Admin: `CREATE DATABASE IF NOT EXISTS` |
| User created | `user_created` | Admin: `CREATE USER` + `GRANT` on **that DB only** (`dbname.*`) |
| Schema applied | `schema_applied` | Connect as **agency user** (vault password), apply tenant schema |
| Verified | `verified` | Schema version check; registry marked healthy |
| Ready | `ready` | Tenant status `READY` |

Admin is used only for create/grant. Schema apply and later runtime use the per-agency user.

### 5. Agency lifecycle after DB ready

- Agency status set to **`invited`** (not `active`).
- Agency profile written into the tenant lifecycle store.
- Owner invitation created (`agency_owner` membership binding).
- `deliver_invitation` sends `invitation.agency` email with a one-time token.
- Create response does **not** include the invitation token or DB password.

### 6. Owner accepts invitation (separate call)

```text
POST /api/v1/auth/invitations/accept
{ "token": "<from email>", "password": "<new portal password>" }
```

Creates the portal user. MySQL credentials are never sent to the owner in V1.

### 7. Later platform actions (same agency module)

Typical follow-ups (already implemented):

- `POST .../status` with `activate` / `suspend` / `restrict` / `review` (+ reason where required)
- Commission / capabilities / finance / notes endpoints
- List filters `?status=` / `?name=`

---

## What is stored where

### Control plane (`vokit_control`)

| Table / store | Contents |
|---|---|
| `tenants` | Agency identity, `agency_status`, commission, capabilities |
| `tenant_databases` | host, port, name, `db_username`, TLS, status, schema_version (`secret_ref` = vault marker) |
| `tenant_db_credentials` | Encrypted password ciphertext (vault) |
| `tenant_provisioning_jobs` | Saga step / attempts / last_error |
| Identity invitations / notifications | Owner invite + delivery |

### Tenant data plane (`vokit_t_<hex>`)

- Tenant business schema (customers, agents, calls metadata, etc. as implemented).
- Accessed only with that agency’s MySQL user after provision.

---

## Runtime routing after create

```text
Authenticated request with agency membership
  → resolve tenant_id from membership (never from client DB name)
  → load tenant_databases row
  → require non-empty db_username (fail closed if empty)
  → vault.get(database_id) → password
  → open MySQL as db_username / password on database.name
```

Shared env `TENANT_DB_USER` / `TENANT_DB_PASSWORD` are **not** used for tenant runtime login.

---

## API response rules

Agency create/detail may include:

```json
"database": {
  "host": "127.0.0.1",
  "port": 3306,
  "name": "vokit_t_...",
  "username": "u_test_agency_02",
  "status": "healthy",
  "schema_version": "...",
  "tls_required": false
}
```

Never returned:

- MySQL password
- vault ciphertext
- `owner_invitation_token`

---

## Failure modes (current)

| Condition | Typical code |
|---|---|
| Missing username/password | `validation_error` (400) |
| Client supplied `database.name` | `validation_error` (400) |
| Duplicate `database.username` | `db_username_conflict` (409) |
| Owner email already has membership | `owner_conflict` (409) |
| Admin cannot GRANT | `tenant_db_admin_denied` (503) |
| Other MySQL/provision exception | `tenant_provision_failed` (503) |
| Empty `db_username` on later open | `tenant_db_misconfigured` (503) |

Local lab: admin must be able to `CREATE DATABASE`, `CREATE USER`, and `GRANT` (usually MySQL `root` with a non-empty password in env).

---

## Env checklist (local)

```env
CONTROL_PLANE_DB_USER=vokit
CONTROL_PLANE_DB_PASSWORD=...

TENANT_RUNTIME=mysql
TENANT_DB_HOST=127.0.0.1
TENANT_DB_PORT=3306
TENANT_DB_ADMIN_USER=root
TENANT_DB_ADMIN_PASSWORD=...
TENANT_DB_ADMIN_PASSWORD_REF=TENANT_DB_ADMIN_PASSWORD
```

Apply migrations before create:

- `tenancy.0003_phase_sa2_notes`
- `tenancy.0004_phase_b_per_agency_user`

---

## Example create body (Postman)

```json
{
  "display_name": "Test Agency",
  "legal_name": "Test Agency LLC",
  "owner_email": "owner-test@example.com",
  "commission_rate_bps": 1000,
  "database": {
    "host": "127.0.0.1",
    "port": 3306,
    "username": "u_test_agency_02",
    "password": "TenantDbPass12!"
  }
}
```

Expected success: **201**, `status: "invited"`, `database.name` starts with `vokit_t_`, no password in body.

---

## Why control-plane user ≠ tenant admin

- Control-plane user runs on every request → keep it limited to `vokit_control`.
- Tenant admin is powerful and rare → only provision path.
- Per-agency user isolates each tenant schema → least privilege for runtime.

See ADR-003 amendment for the decision text.

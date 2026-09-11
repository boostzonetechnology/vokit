# ADR-003 — Remote MySQL Tenant Registry and Routing

Status: Accepted  
Date: 2026-09-09  
Accepted: 2026-09-10 (owner proceed)  
Amended: 2026-09-11 (per-tenant MySQL user — owner proceed Phase B)

## Decision

Maintain a control-plane tenant database registry containing logical tenant identity and remote MySQL connection metadata/credential references. Runtime database routing resolves tenant context server-side and selects the corresponding tenant DB.

## Amendment — Per-tenant MySQL user (2026-09-11)

Each Agency tenant database is accessed with a **dedicated MySQL username/password** supplied by Super Admin at agency create (or assigned later for legacy rows).

### Flow

1. Super Admin supplies `host` (optional), `port` (optional), `username`, and `password` for that agency’s data-plane MySQL.
2. Database **name** remains server-derived: `vokit_t_<tenant_uuid_hex>` (never client-chosen).
3. Platform connects as **admin** env identity (`TENANT_DB_ADMIN_USER` + `TENANT_DB_ADMIN_PASSWORD_REF`) only to:
   - `CREATE DATABASE`
   - `CREATE USER`
   - `GRANT` on that single database (`dbname.*` only — never `*.*`)
4. Runtime connections (`open` / pool acquire) use the per-tenant username and password resolved from the control-plane vault — not a shared `TENANT_DB_USER`.
5. Passwords are stored encrypted in `tenant_db_credentials` (vault), never plaintext on `tenant_databases`, never returned on GET, never logged.
6. Agency/Customer portals do **not** receive MySQL credentials in V1 of this amendment.

### Registry fields

- `tenant_databases.host`, `port`, `name`, `db_username`, TLS flags, status, schema_version
- `tenant_db_credentials` — ciphertext for the tenant DB password, keyed by database id

### Removed from tenant runtime

Shared env `TENANT_DB_USER` / `TENANT_DB_PASSWORD` / `TENANT_DB_PASSWORD_REF` are **not** used to open tenant connections. Optional default host/port (`TENANT_DB_HOST` / `TENANT_DB_PORT`) remain when Super Admin omits per-agency host/port.

### Backward compatibility

Existing `tenant_databases` rows with empty `db_username` fail closed on connect (no shared-user fallback). Retroactive credential assignment is a separate management workflow.

## Non-goals

- Do not expose DB credentials to tenant users (Agency/Customer portals).
- Do not store plaintext credentials in application tables.
- Do not route based on a request-supplied database **name**.
- Do not fall back to another tenant database.
- Do not use one shared MySQL login across all tenant schemas for application traffic.

## Operations

Tenant DBs have lifecycle states such as Provisioning, Healthy, Degraded, Migrating, Suspended and Decommissioning.  
Routing, migration, health and backup jobs operate with explicit tenant context.  
Provisioning saga includes `user_created` after database allocation and before schema apply.

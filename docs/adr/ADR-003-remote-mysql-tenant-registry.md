# ADR-003 — Remote MySQL Tenant Registry and Routing

Status: Accepted  
Date: 2026-09-09  
Accepted: 2026-09-10 (owner proceed)

## Decision

Maintain a control-plane tenant database registry containing logical tenant identity and remote MySQL connection metadata/credential references. Runtime database routing resolves tenant context server-side and selects the corresponding tenant DB.

## Non-goals

- Do not expose DB credentials to tenant users.
- Do not store plaintext credentials in application tables.
- Do not route based on a request-supplied database name/host.
- Do not fall back to another tenant database.

## Operations

Tenant DBs have lifecycle states such as Provisioning, Healthy, Degraded, Migrating, Suspended and Decommissioning.  
Routing, migration, health and backup jobs operate with explicit tenant context.

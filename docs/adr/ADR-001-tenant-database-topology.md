# ADR-001 — Tenant Database Topology

Status: Accepted  
Date: 2026-09-09  
Amended: 2026-09-10  
Accepted: 2026-09-10 (owner proceed)

## Decision

Use a control-plane + tenant-data-plane topology.

For V1, the top-level **physical** database tenant is the **Agency**. Each Agency receives a separate MySQL database.

**Customer remains a child authorization and data scope inside that Agency tenant database.** Customer-level authorization is still mandatory (TEN-002, TEN-005). V1 does **not** create one database per customer.

Each tenant database may reside on an independent remote MySQL host.

## Owner confirmation (2026-09-10)

Product owner confirmed: customers remain under agency scope for now. Do not change the physical boundary to Customer. Do not implement customer-to-customer database tenancy.

Customer reassignment across agencies (Q-006) remains a later Super Admin capability. It is **out of the initial V1 build**. Do not implement the cross-tenant move saga until the owner explicitly schedules it.

## Why

This preserves the SRS hierarchy while avoiding an operational explosion of one database per customer. It also provides strong agency-level isolation and allows future tenant placement, migration and regionalization.

## Consequences

Positive:

- strong database isolation;
- tenant-specific backup/restore;
- tenant-specific migrations;
- future data residency flexibility;
- reduced blast radius.

Trade-offs:

- connection-management complexity;
- per-tenant migration orchestration;
- tenant-aware observability;
- more complex cross-tenant reporting if customer moves are later enabled.

## Security

The browser never selects a database. Trusted server-side tenant context selects the database configuration. Failures fail closed.

## Change rule

If the product owner later changes the physical boundary to Customer, do **not** partially adapt the Agency topology. Redesign registry, routing, migrations, connection management, backup, authorization and operations, then record a new ADR before coding.

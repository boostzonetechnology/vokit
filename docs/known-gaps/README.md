# Known gaps

Open backend/module gaps versus the SRS. These files are a backlog, not an implementation plan, until the owner says proceed.

The SRS remains the product source of truth. If a gap file and the SRS conflict, the SRS wins.

| Doc | Module | Surface |
|---|---|---|
| [SA2 Agencies backend](SA2-AGENCIES-BACKEND-GAPS.md) | Super Admin §7.2 Agencies (`SA2-*`) | Django API |
| [Tenant DB per-agency user](TENANT-DB-PER-AGENCY-USER.md) | SA2-001 / tenancy — dedicated MySQL user per agency | Backend Phase B done; Super Admin UI later |

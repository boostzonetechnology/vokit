# Canary tenant migration

**Goal:** Apply tenant schema to one canary Agency, verify, then batch the rest.

```powershell
cd apps/api
.\.venv\Scripts\python.exe manage.py migrate_tenants --canary <CANARY_UUID> --canary-only
```

A failed canary **stops the batch**. Do not pass `--canary-only` off until:

- canary job `succeeded`
- tenant status `ready`
- agency login + one customer read works
- no `tenant_isolation_violation` / `tenant_route_denied` spike

Then:

```powershell
.\.venv\Scripts\python.exe manage.py migrate_tenants --canary <CANARY_UUID>
```

Concurrency is `TENANT_MIGRATION_CONCURRENCY` (default 2). Pause if more than one tenant fails in a batch; restore that tenant from backup rather than widening blast radius.

Evidence: `test_canary_migration_then_bounded_batch`, `test_migration_failure_isolates_one_tenant`.

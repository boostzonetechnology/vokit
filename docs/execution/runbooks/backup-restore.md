# Backup / restore

**Goal:** Restore control-plane metadata or **one** Agency tenant DB without opening another tenant.

## Backup

```powershell
cd apps/api
.\.venv\Scripts\python.exe manage.py backup_control_plane --out .\tmp\control.json
.\.venv\Scripts\python.exe manage.py backup_tenant --tenant-id <TENANT_UUID> --out .\tmp\tenant.json
```

Memory/lab writes a JSON snapshot (secret **refs** only). MySQL staging writes a `mysqldump` plan; resolve `secret_ref` from the secret manager, never the command line history if avoidable.

Control plane full logical dump (staging/prod):

```text
mysqldump --single-transaction --databases vokit_control
```

Tenant MySQL: dump **that database name** from the registry. Do not dump all tenant schemas into one file as the restore unit.

## Restore one tenant

1. Confirm tenant_id and database_id from the registry.
2. Take a fresh backup of the damaged tenant only.
3. Restore **only** that database / snapshot.

```powershell
.\.venv\Scripts\python.exe manage.py restore_tenant --tenant-id <TENANT_UUID> --snapshot .\tmp\tenant.json
```

4. Reconcile recordings: `manage.py reconcile_recordings`.
5. Smoke: agency login, one customer list, dashboard revenue vs ledger.

## Fail closed

- Snapshot tenant_id must match the restore target (`tenant_restore_mismatch`).
- Never “search all tenant DBs for the row.”
- Never restore Agency B to recover Agency A.
- Ledger history is append-only; do not rewrite commission rows after restore.

## Evidence

`pytest tests/test_backup_restore.py tests/test_staging_sandbox_e2e.py`

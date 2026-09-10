# Local data services

```powershell
docker compose -f deploy/compose/docker-compose.yml up -d
```

Creates `vokit_control`, `vokit_tenant_a`, and `vokit_tenant_b` on one MySQL 8 plus Redis.

Phase 1 API uses **control plane only**. Tenant A/B exist so Phase 3 isolation tests do not share a schema. Do not point `CONTROL_PLANE_DB_NAME` at a tenant database.

# Tenant DB outage

1. Fail closed. Do not route the tenant to another database.
2. Mark/observe `tenant_db_unavailable`. Other tenants must keep working.
3. Check pool saturation (`TENANT_POOL_MAX_PER_TENANT`, active-tenant cap). Do not raise by total tenant count.
4. Restore **that** tenant from backup if the volume is corrupt.
5. Preserve logs with correlation_id and tenant_id.

Evidence: `test_outage_does_not_fall_back`, `test_restore_one_tenant_does_not_touch_the_other`.

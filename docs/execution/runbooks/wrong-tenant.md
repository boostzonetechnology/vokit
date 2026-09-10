# Wrong-tenant suspicion (P0)

1. Contain: freeze the request path / worker; do not “fix” rows in place.
2. Preserve evidence (logs, audit, request_id). Do not delete audit events.
3. Confirm registry mapping vs membership tenant_id. Forged client tenant_id is ignored.
4. Blast radius: which tenant_ids appeared on the connection.
5. Mitigate: discard the pooled connection (`discard(tenant_id)`); rotate credentials if leakage is possible.
6. Verify isolation tests and a canary read of both tenants.

Never query all tenant DBs to find a missing object.

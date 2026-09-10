# Tenancy registry (control plane)

Physical tenant = Agency (ADR-001). Registry rows store host/port/name and a `SecretRef` key, never a password.

Provisioning is a resumable saga. A tenant is not `ready` until the tenant schema is applied and verified.

Routing is fail-closed. The browser never selects a database.

Backup/restore is tenant-scoped (`backup_tenant` / `restore_tenant`). Restoring Agency A
never opens Agency B. Canary migrations can stop after the canary (`--canary-only`).

Agency business status (`active` / `restricted` / `under_review` / `suspended` / `closed`) is separate from tenant DB status. A suspended agency stays routable so existing customer services are not cut off (BR-014).

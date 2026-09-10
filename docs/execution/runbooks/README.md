# Staging / operations runbooks

These are executable procedures. Do not destroy evidence to make dashboards green.

| Runbook | Trigger |
|---|---|
| [Payment reconciliation](payment-reconciliation.md) | Webhook gap / commission mismatch |
| [Payout exception](payout-exception.md) | Stuck Processing, missing proof |
| [Tenant DB outage](tenant-db-outage.md) | Routing failures, pool saturation |
| [Wrong-tenant suspicion](wrong-tenant.md) | Isolation alarm (P0) |
| [Telephony incident](telephony.md) | DID / Edge / Pipecat |
| [Recording ingest](recording-ingest.md) | Orphans, checksum fail |
| [Backup and restore](backup-restore.md) | Drill or tenant recovery |
| [Canary migration](canary-migration.md) | Tenant schema rollout |
| [KYC / risk](kyc-risk.md) | Provider lag, chargeback freeze |
| [Agency suspend](agency-suspend.md) | Capability + existing services |
| [Key rotation](key-rotation.md) | Webhook / telephony / tenant DB secrets |

Related: `19-DEPLOYMENT-OPERATIONS.md`, `20-PRODUCTION-DEPLOYMENT.md`, `25-CAPACITY-WORKSHEET.md`.

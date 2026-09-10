# Architecture Decision Records

Canonical location for Vokit ADRs.

| ADR | Topic | Status |
|---|---|---|
| [ADR-001](ADR-001-tenant-database-topology.md) | Agency is the physical DB tenant; Customer stays under Agency | Accepted |
| [ADR-002](ADR-002-recording-storage-separation.md) | Separate recording data plane | Accepted |
| [ADR-003](ADR-003-remote-mysql-tenant-registry.md) | Tenant registry and fail-closed routing | Accepted |
| [ADR-004](ADR-004-v1-implementation-stack.md) | Django/DRF, Celery, React, UUID, `/api/v1/` | Accepted |
| [ADR-005](ADR-005-external-kyc-provider.md) | External agency KYC via provider API keys | Accepted |
| [ADR-006](ADR-006-transfer-voicemail-media-contracts.md) | Queue/SIP-client/voicemail without rewriting Edge `{to}` | Accepted |

This directory is the only ADR location.

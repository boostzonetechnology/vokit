# Vokit Deployment Operations

## 1. Service units

| Unit | Type | Notes |
|---|---|---|
| `api` | Web | Django; `0.0.0.0:$PORT` |
| `worker` | Background | Celery (or accepted alternative) |
| `scheduler` | Beat | Hold release, dunning, reconcile, retention |
| `web-platform` | Static/SPA | |
| `web-agency` | Static/SPA | |
| `web-customer` | Static/SPA | |
| `pipecat` | Web/WS | Media; sticky/long-lived connections |
| `sip-edge` | Private network | Do not expose control API publicly |
| `asterisk` | Voice VM/VPS | RTP ports explicit |
| `recording` | Private + controlled egress | Separate credentials |
| `mysql-control` | Data | |
| `mysql-tenants` | Data | One or more hosts |
| `redis` | Cache/queue | Persistence policy required |
| `qdrant` | Vectors | |

Filesystem is ephemeral on typical PaaS. Recordings, payout proofs, and media **never** rely on local disk. Agency KYC documents stay at the external provider.

After each deploy: `python manage.py post_deploy_smoke` then
`python manage.py check_production_readiness` (or `--lab` in CI).

## 2. Deployment sequence (always)

1. Deploy backward-compatible code
2. Migrate control plane
3. Migrate canary tenant DBs
4. Smoke tests
5. Roll tenant migrations in bounded batches
6. Enable feature flag
7. Verify telemetry
8. Expand
9. Contract/remove obsolete schema only after stability

## 3. Runbooks (required before prod)

Procedures live in [`runbooks/`](runbooks/README.md).

| Runbook | Trigger |
|---|---|
| Payment reconciliation | Webhook gap / commission mismatch |
| Payout exception | Stuck Processing, missing proof |
| Tenant DB outage | Routing failures, pool saturation |
| Wrong-tenant suspicion | P0 — contain, do not “fix data” quietly |
| Telephony incident | DID/Edge/Pipecat |
| Recording ingest backlog | Orphans, checksum fail |
| KYC / risk surge | Provider status aging; webhook lag |
| Agency suspend | Capability + existing customer services |
| Customer chargeback | Auto-freeze verification (see KYC/risk) |
| Customer reassignment | Not in initial V1 (Q-016) |
| Key rotation | Webhook/payment/telephony secrets |
| Audit / notices | Immutable search; do not delete rows to “clean” dashboards |
| Backup / restore | Drill or single-tenant recovery |
| Canary migration | Tenant schema rollout |

## 4. Incident priority

P0/P1: isolation breach, wrong-tenant routing, financial inconsistency, call routing outage at scale, recording exposure, widespread payment/webhook failure.

Process: contain → preserve evidence → blast radius → mitigate → verify → communicate → RCA → corrective action.

## 5. Backups

- Automated backups for control plane and every tenant DB
- Tested restore of **one** tenant without touching others
- Recording object versioning + metadata reconcile
- RPO/RTO numbers decided at staging (still deferred as exact minutes)

## 6. Observability minimum

Business-impact metrics from the observability rule: routing, pools, migration backlog, ingest, call lifecycle, provider errors, API p95/p99, queues, payment lag, commission mismatch, payout aging, KYC aging, webhook retries, isolation violations.

## 7. Capacity

Before adding tenant hosts or replicas, estimate concurrent calls, connections per active tenant, active tenant count, queue throughput, ingest bandwidth, storage growth, webhook rate, provider limits, hotspot tenants.

Prefer bounded pools and active-tenant scheduling over connection × tenant_count.

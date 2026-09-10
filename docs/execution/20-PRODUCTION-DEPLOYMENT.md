# Vokit Production Deployment

## 1. Preconditions

- CI green
- Dependency/security checks done
- ADR-001–005 Accepted
- Control-plane migration reviewed
- Tenant migration plan reviewed
- Canary tenant chosen
- Tenant DB connectivity tested
- Recording server health tested
- Provider sandbox E2E previously passed; live keys loaded in secret manager
- Readiness/liveness live
- Alerting confirmed
- Rollback verified once in staging

## 2. Rollout

1. Deploy API/worker that is backward compatible with current media contracts.
2. Apply control-plane migrations.
3. Provision/migrate canary Agency DB.
4. Smoke: auth, tenant routing, one agency/customer workflow.
5. Batch-migrate remaining tenant DBs with a concurrency cap and pause threshold.
6. Deploy SPAs.
7. Enable flags: billing live, calling live, recordings live — independently if needed.
8. Canary production-like inbound and outbound call.
9. Verify payment webhook + commission on a small live charge or controlled canary invoice.
10. Expand DNS/traffic.
11. Watch p95, routing errors, queue age, ingest, isolation metrics for the soak window.

## 3. Media-path caution

Django deploys must not break Pipecat/Edge. If internal contracts change:

- Dual-read old/new
- Pin Edge `SIP_NODE_MEDIA_BASE_URL`
- Keep rollback URL documented
- Drain calls before killing old Pipecat replicas

## 4. Rollback

| Layer | Rollback |
|---|---|
| SPA | Prior artifact |
| API | Prior image **only if** schema still compatible |
| Control-plane schema | Expand/backfill only; no unexpand until stable |
| Tenant schema | Per-tenant rollback job or restore from backup |
| Media | Point Edge back at last known-good Pipecat |
| Flags | Disable calling/billing independently |

Never “fix” finance by rewriting ledger rows during rollback.

## 5. Post-deploy (blocking)

A deployment is not complete until [`23-FINAL-PRODUCTION-CHECKLIST.md`](23-FINAL-PRODUCTION-CHECKLIST.md) verification section is executed, not merely configured.

Executable gate: `python manage.py check_production_readiness` (production) or `--lab` (CI).
Evidence pack: [`26-PHASE-19-EVIDENCE.md`](26-PHASE-19-EVIDENCE.md). Current verdict: **No-Go** for live launch.

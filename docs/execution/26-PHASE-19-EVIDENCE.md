# Phase 19 evidence pack

**Date:** 2026-09-10  
**Verdict:** **NO-GO for live production.** Lab/CI gate is `LAB_READY`.

A config flag (`VOKIT_LAUNCH_GO`) is not evidence. Live items require a dated
`YYYY-MM-DD` attestation plus the operator artifact (call SID, invoice id,
restore log, alert screenshot, sign-off).

## Lab / CI (executable)

| Item | Evidence |
|---|---|
| Tenant isolation matrix | `tests/test_tenant_routing.py` + Phase 17 catalog |
| Recording negative matrix | `tests/test_recordings_api.py` |
| Payment idempotency | `tests/test_billing_api.py` |
| Sandbox E2E | `tests/test_staging_sandbox_e2e.py` |
| Backup/restore isolation | `tests/test_backup_restore.py` |
| Canary-only migrate | `tests/test_provision_migrate.py` |
| Security review | `24-PHASE-17-SECURITY-REVIEW.md` |
| Runbooks | `docs/execution/runbooks/` |
| Lab gate | `python manage.py check_production_readiness --lab` |
| Post-deploy smoke | `python manage.py post_deploy_smoke` |

## Live path (blocked)

| Item | Env attestation | Status |
|---|---|---|
| Inbound canary call | `VOKIT_EVIDENCE_LIVE_INBOUND_CALL` | Missing |
| Outbound canary call | `VOKIT_EVIDENCE_LIVE_OUTBOUND_CALL` | Missing |
| Live/canary payment + commission | `VOKIT_EVIDENCE_LIVE_PAYMENT` | Missing |
| Recording play via short-lived token | `VOKIT_EVIDENCE_LIVE_RECORDING` | Missing |
| Dated restore drill (control + one tenant) | `VOKIT_EVIDENCE_RESTORE_DRILL` | Missing |
| P0 alerting confirmed | `VOKIT_EVIDENCE_ALERTING` | Missing |
| Staging rollback performed | `VOKIT_EVIDENCE_ROLLBACK_STAGING` | Missing |
| Legal/compliance sign-off | `VOKIT_EVIDENCE_LEGAL_SIGN_OFF` | Missing |

## Independent flags (production default off)

`flags.calling_live`, `flags.billing_live`, `flags.recordings_live`. Enable only
after the matching attestation exists. Lab/tests set `LIVE_FLAGS_ENABLED_BY_DEFAULT=true`.

## Sign-off

| Role | Go/No-Go | Date |
|---|---|---|
| Engineering (gate shipped) | Lab ready / live No-Go | 2026-09-10 |
| Product Owner | | |
| QA Lead | | |
| Finance / Operations | | |
| Compliance / Legal | | |

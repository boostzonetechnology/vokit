# Vokit Release Engineering Skill

## When to use
Use for CI/CD, environments, migrations, releases, rollback, deployment, production verification and infrastructure changes.

## Procedure
1. Identify changed components and blast radius.
2. Verify tests, lint/type/security checks and contract compatibility.
3. Review migration safety using expand/contract where possible.
4. Verify environment/config/secret requirements.
5. Verify health/readiness endpoints and smoke tests.
6. Verify backup/restore readiness for data-impacting releases.
7. Deploy through reproducible automation; avoid manual production drift.
8. Run post-deploy checks for API, database, queues, payments/webhooks and voice routing.
9. Monitor error rate/latency/business KPIs before declaring success.
10. Keep rollback and forward-fix procedures explicit.

## Release gates
Do not call a release production-ready when critical tests, tenant isolation, financial idempotency, backup restore, or critical observability are missing.

# Vokit Production Readiness Skill

## Use when
Use before staging sign-off, production release, major infrastructure changes or scale events.

## Gate
Verify code, schema, tenant DBs, queues, provider contracts, Asterisk/SIP/Pipecat, recording server, secrets, backups, monitoring, alerts, smoke tests, rollback and runbooks.

## Evidence
Do not mark a gate passed because a config exists. Require executable evidence: test output, health checks, migration status, restore result, smoke test or telemetry.

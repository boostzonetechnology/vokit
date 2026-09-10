# Vokit Tenant Migration Skill

## Use when
Use for tenant DB schema upgrades or data migrations.

## Procedure
- preflight tenant health;
- acquire tenant-specific migration lock;
- verify supported source/target versions;
- run expand migration;
- validate;
- backfill in bounded chunks;
- verify checksums/counts/invariants;
- mark version;
- release lock;
- emit metrics/events.

## Scale rules
- canary first;
- bounded concurrency;
- resumable jobs;
- pause on error-rate threshold;
- never let one tenant migration block all tenants;
- retain failed tenant state for reconciliation.

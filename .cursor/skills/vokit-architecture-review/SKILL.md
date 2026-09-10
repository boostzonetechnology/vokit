# Vokit Architecture Review Skill

## Use when
Use for any cross-cutting feature or refactor.

## Review template
- requirement IDs;
- current architecture;
- proposed architecture;
- bounded context;
- data ownership;
- tenancy boundary;
- API/event contract;
- failure/retry/idempotency;
- security/privacy;
- observability;
- migration/deployment;
- rollback;
- tests;
- scale implications.

## Stop conditions
Reject changes that weaken tenant isolation, move core business rules into React, couple domain code to providers, make financial history mutable, expose raw recordings, or introduce unbounded per-tenant infrastructure.

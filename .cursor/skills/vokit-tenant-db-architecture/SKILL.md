# Vokit Tenant DB Architecture Skill

## Use when
Use for tenant provisioning, database routing, remote MySQL, connection management, migrations, backups, tenant isolation, database failures or scale planning.

## Workflow
1. Read SRS tenancy requirements and `docs/OPEN-QUESTIONS.md`.
2. Identify whether the change affects control plane, tenant data plane or both.
3. Resolve tenant context from trusted auth/membership state.
4. Design registry -> credential reference -> connection -> query path.
5. Define connection pooling, timeout, retry, circuit breaker and fail-closed behavior.
6. Define tenant provisioning lifecycle and migration versioning.
7. Define backup/restore and disaster recovery per tenant.
8. Add positive + negative tenant isolation tests.
9. Add metrics for routing, connection, pool saturation and migration health.
10. Record high-impact decisions in an ADR.

## Required design output
- topology diagram;
- tenant identity source;
- DB registry fields;
- routing flow;
- credential strategy;
- pool strategy;
- migration strategy;
- failure modes;
- security tests;
- operational runbook.

## Red flags
Reject shared mutable DB connection state, tenant_id from browser as routing authority, plaintext DB passwords, "fallback to default DB", cross-tenant SQL, or unbounded per-tenant connections.

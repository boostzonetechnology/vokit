# Vokit Architecture Skill

## When to use
Use for new modules, refactors, domain boundaries, ERD changes, integrations, service extraction and architectural decisions.

## Procedure
1. Read relevant SRS sections and `docs/OPEN-QUESTIONS.md`.
2. Inspect current code and dependencies before proposing changes.
3. Identify bounded context, owner/scope, invariants, commands, queries, events and external ports.
4. Decide whether the change belongs in Django domain/application/infrastructure/API, React, realtime voice, or deployment.
5. Design failure/retry/idempotency behavior before implementation.
6. Define migration/backward compatibility strategy.
7. Add/update ADR for consequential architectural decisions.
8. Implement with dependency inversion and test seams.
9. Validate tenant/security/financial/realtime boundaries.

## Output expected from planning
- Requirement IDs
- Context/boundary
- Data ownership
- API/event contract
- Failure modes
- Security impact
- Observability
- Tests
- Migration/deployment impact
- Rollback strategy

## Red flags
Reject an implementation that introduces hidden cross-tenant queries, business logic in React, provider SDK calls in domain objects, mutable financial truth, synchronous slow work in the realtime audio path, or irreversible schema changes without migration planning.

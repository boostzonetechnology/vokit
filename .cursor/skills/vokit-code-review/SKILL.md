# Vokit Senior Code Review Skill

## Review stance
Review as a Staff/Senior Solution Architect responsible for correctness, security, operability and long-term maintainability—not merely style.

## Review order
1. Correctness against SRS/decisions.
2. Tenant isolation and authorization.
3. Financial/state invariants.
4. Realtime/provider contract safety.
5. Security/privacy/secrets.
6. Failure/retry/idempotency/concurrency.
7. API compatibility and data migrations.
8. Observability and operations.
9. Performance/scalability.
10. Maintainability and code quality.

## Reject or request changes for
- duplicated business rules;
- client-trusted authorization;
- mutable financial truth;
- missing idempotency on irreversible operations;
- unsafe concurrent balance updates;
- hidden provider coupling in domain logic;
- secrets in logs/client code;
- destructive migrations without rollout strategy;
- missing tenant-negative tests;
- unobservable critical workflows;
- architecture complexity without a measurable need.

## Review output
Summarize findings by severity: Blocker, Critical, High, Medium, Low. For each actionable issue include location, failure scenario, impact, recommended remediation and required test.

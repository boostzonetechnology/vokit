# Vokit Observability Skill

## When to use
Use when implementing or reviewing any workflow that can fail, retry, queue, call providers, affect customers or money, or require production diagnosis.

## Procedure
1. Define business and technical signals before coding.
2. Add structured logs with safe fields only.
3. Propagate correlation/request IDs through HTTP, jobs and provider calls.
4. Add metrics for rate, errors, latency, saturation and business outcomes.
5. Add traces around critical cross-component workflows.
6. Add dashboards for platform, finance and operations.
7. Define actionable alerts with severity and runbook links.
8. Ensure logs/errors redact secrets and sensitive data.

## Critical Vokit signals
Payment/webhook failures and lag; commission reconciliation mismatch; payout failures/aging; KYC queue aging; call setup/answer/failure; realtime latency; transfer failures; number provisioning failures; agent runtime errors; knowledge ingestion failures; integration/webhook delivery failures; API latency/errors; queue depth/job failures; database health.

## Principle
Observability must explain what happened, for which tenant/resource, across which components, without exposing secrets or sensitive content.

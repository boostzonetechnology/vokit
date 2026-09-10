# Phase 17 capacity worksheet

**Date:** 2026-09-10  
**Rule:** Estimate before adding tenant hosts, replicas, or extra services. Scale only from a measured bottleneck plus an ADR (NFR-004, Phase 20).

This worksheet is a planning model. It is **not** production telemetry.

## Inputs (fill per environment)

| Input | Symbol | Lab default | Notes |
|---|---|---|---|
| Active agencies (DBs that receive traffic this hour) | `A` | 2 | Never use total registered tenants |
| Concurrent calls | `C` | 2 | Inbound + outbound answered |
| Peak calls/sec (setup) | `S` | 0.2 | Admission + bootstrap |
| Avg recording minutes / call | `M` | 3 | Object size ≈ `M * 0.5 MB` μ-law-ish |
| Webhook deliveries / min | `W` | 10 | Outbound + processor inbound |
| Control-plane API p95 budget | — | 300 ms | Exclude media path |
| Tenant pool per active tenant | `P` | 4 | Bounded; not `A × max_workers` |

## Derived demand

| Resource | Formula | Lab estimate |
|---|---|---|
| Tenant DB connections | `A * P` | 8 |
| Control-plane DB connections | API workers + beat + celery | Keep a single shared pool |
| RTP / media concurrency | `C` on Asterisk/Edge/Pipecat | 2 |
| Recording ingest bandwidth | `C * 64 kbps` while recording | ~128 kbps |
| Daily recording growth | `calls/day * M * 0.5 MB` | Measure in staging |
| Queue rate | holds + webhooks + ingest + migrate | Bound concurrency |
| Hotspot tenant | max(`C_tenant`) | One agency can dominate `C` |

## Hard constraints (do not violate)

- Do not open one persistent connection per registered tenant.
- Do not put recordings or payout proofs on the ephemeral app filesystem.
- Do not run tenant migrations as one global lock-step command.
- Django is not in the audio loop; Pipecat/Edge/Asterisk own realtime.
- Qdrant searches stay scoped to knowledge group IDs for the current tenant/customer.

## Scale triggers (need measurement + ADR)

| Trigger | First response |
|---|---|
| Tenant pool wait / `tenant_db_unavailable` | Raise `P` for **active** tenants only, or add a tenant host |
| Control-plane p99 + CPU | Extra API replicas behind the existing monolith |
| Recording ingest backlog / orphans | Extra recording workers; do not write audio into Django |
| Queue age (holds, webhooks) | Extra celery workers with tenant-safe routing |
| Provider quota (STT/TTS/LLM/PSTN) | Throttle admission; do not shard tenant DBs first |
| One hotspot agency | Isolate that tenant host; do not extract microservices |

## Phase 17 conclusion

Current lab/CI load is two synthetic agencies, in-memory tenant runtime unless MySQL isolation is opted in, and mock processors. The architecture already uses bounded pools and session-bound routing. **Do not add replicas, shards, or new services in Phase 17.** Revisit this sheet in Phase 18 with sandbox numbers and in Phase 20 with production telemetry.

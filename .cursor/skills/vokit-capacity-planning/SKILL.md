# Vokit Capacity Planning Skill

## Use when
Use before adding tenants, increasing call concurrency, changing DB topology, adding recording volume or changing provider workloads.

## Model
Estimate active tenants, DB connection demand, calls/sec, concurrent calls, audio bandwidth, recording ingest, storage growth, queue rate, webhook rate and provider quotas.

## Rule
Prefer measured bottleneck-driven scale changes. Do not introduce microservices, replicas or sharding without a concrete bottleneck and an ADR.

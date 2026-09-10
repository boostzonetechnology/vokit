# ADR-002 — Separate Call Recording Data Plane

Status: Accepted  
Date: 2026-09-09  
Accepted: 2026-09-10 (owner proceed)

## Decision

Raw call recordings are stored on a separate recording server/data plane. Vokit application databases store recording metadata and opaque object references only.

Playback/download uses a short-lived authorization mechanism after normal tenant/call authorization.

## Rationale

Recordings are high-volume, privacy-sensitive binary data and have different storage, retention, bandwidth and scaling characteristics from application transactions.

## Consequences

- separate scaling;
- independent retention/deletion;
- lower application DB/storage pressure;
- additional service-to-service authorization;
- artifact reconciliation becomes mandatory.

## Required controls

TLS, private access where possible, least privilege, integrity hashes, signed/short-lived access, audit logging, retention policy and orphan reconciliation.

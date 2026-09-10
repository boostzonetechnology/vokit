# Agency KYC (external)

Vokit stores mapped status, provider session/inquiry refs, and API-key **secret refs**. It does not store KYC document bytes.

Payout requests fail closed unless status is `verified` and the case is not frozen (KYC-001, ADR-005).

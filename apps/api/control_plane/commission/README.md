# Commission, wallet, payout

The wallet is a projection of an insert-only control-plane ledger (BR-020). Balances are never stored as mutable source of truth.

Commission is captured cash excluding tax; processor fees are ignored (Q-012). Each earning stores `eligible_base`, `rate_bps_snapshot`, `earned_at`, and `available_at` (WAL-001, WAL-003). Hold is 15 days per entry.

Payout request atomically reserves available funds (WAL-002). Super Admin proof is an object reference, never returned to the agency (BR-009). Marking paid generates a receipt (BR-010).

Corrections are compensating entries. Historical payouts stay Paid.

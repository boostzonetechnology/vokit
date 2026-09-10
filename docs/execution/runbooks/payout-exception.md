# Payout exception

1. Confirm KYC Verified and wallet available. Unverified → `payout_kyc_unverified`.
2. Held funds are not withdrawable. Release holds only via `release_commission_holds` after the hold window.
3. Missing proof blocks mark-paid (`payout_proof_required`). Upload private proof as Super Admin; agency GET proof is 404.
4. Concurrent second reservation must 409 `payout_insufficient`.
5. Do not reverse by deleting ledger entries. Use compensating entries.

Evidence: `test_agency_cannot_fetch_payout_proof`, `test_mark_paid_is_blocked_without_proof`.

# KYC / risk surge

1. Agency cannot PATCH itself to Verified. Only signed provider webhook or Super Admin override.
2. Unknown KYC status fails closed for payout.
3. Override requires reason + audit. Do not store KYC document bytes.
4. Chargeback: freeze, disable agents, compensating ledger. Do not rewrite history.
5. Unsigned webhooks → 401.

Evidence: `test_forged_webhook_is_rejected`, `test_chargeback_disables_agents_and_reverses_commission`.

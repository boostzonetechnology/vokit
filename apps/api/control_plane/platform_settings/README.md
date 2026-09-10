# Platform settings

Centralized hold days, feature flags, provider refs, and compliance knobs
(SA19-*, NFR-014). Secret values are never returned. Changes require a reason
and are audited. Commission accrual reads `payout.hold_days` from this registry.
Live flags (`calling_live`, `billing_live`, `recordings_live`) default off in
production; lab uses `LIVE_FLAGS_ENABLED_BY_DEFAULT`.

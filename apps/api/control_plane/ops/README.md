# Production operations

Independent live flags (`calling_live`, `billing_live`, `recordings_live`) default
off unless `LIVE_FLAGS_ENABLED_BY_DEFAULT` is true (lab/tests).

`check_production_readiness` is the go/no-go evaluator. A boolean env flag cannot
green a live item. Live paths require a dated attestation (`YYYY-MM-DD`).

`--lab` records lab/CI evidence only (`LAB_READY`). Production mode is `GO` only
when lab evidence and live attestations are both present.

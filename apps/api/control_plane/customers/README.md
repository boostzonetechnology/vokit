# Customer index (control plane)

`customer_id` is globally unique. The owning Agency is `tenant_id` and does not change in the initial V1 build (Q-016).

Customer rows live in the Agency tenant database. Super Admin lists from this index; agency users read only their session tenant.

The ban-index hook stores hashed keys only. Empty key lists are allowed. A match returns a generic ineligible error.

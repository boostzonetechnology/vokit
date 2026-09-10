# Identity (control plane)

Phase 2: users, one membership (platform XOR agency XOR customer), sessions, CSRF, invitations, RBAC namespaces.

No tenant database router. `tenant_id` / `customer_id` on memberships are opaque UUIDs until Phase 3.

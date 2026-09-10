# Agency suspend

1. Use the agency status machine (`suspended`). Existing customer services stay up when `existing_customer_services` is true (BR-014).
2. Agency create-customer and number purchase must fail when capabilities/status disallow.
3. Do not drop the tenant DB or route to another tenant.
4. Audit the status change.

Evidence: `test_suspended_agency_cannot_create_customer`.

"""Fixed demo identities for Phase 2. Not a tenant registry."""

from __future__ import annotations

import uuid

DEMO_AGENCY_TENANT_ID = uuid.UUID("0199aaaa-0000-7000-8000-000000000001")
DEMO_CUSTOMER_ID = uuid.UUID("0199aaaa-0000-7000-8000-000000000002")
DEMO_AGENCY_B_TENANT_ID = uuid.UUID("0199aaaa-0000-7000-8000-000000000003")
DEMO_AGENCY_B_EMAIL = "agency-b@vokit.test"
DEMO_CUSTOMER_B_ID = uuid.UUID("0199aaaa-0000-7000-8000-000000000004")
DEMO_CUSTOMER_B_EMAIL = "customer-b@vokit.test"

DEMO_PLATFORM_EMAIL = "platform@vokit.test"
DEMO_AGENCY_EMAIL = "agency@vokit.test"
DEMO_CUSTOMER_EMAIL = "customer@vokit.test"
DEMO_PASSWORD = "Phase2-Demo!ok"

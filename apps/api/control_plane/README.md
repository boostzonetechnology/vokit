# Control plane

Identity, tenancy registry, customer index, external KYC, billing, the commission ledger,
customer payment risk, agents/templates/knowledge, phone-number inventory, frozen
voice control APIs, outbound origination, transfer destinations, and voicemail metadata
are implemented. Recording metadata and customer-owned integrations / signed
webhooks / the Django tool gateway are implemented. In-app + email notifications,
immutable audit search, and centralized platform settings (hold days, flags,
provider refs) are implemented. Portal dashboards project KPIs from those
indexes and the ledger (`GET /api/v1/{platform|agency|customer}/dashboard`).

Production go/no-go lives in `control_plane/ops`. Do not add a tenant database router here.

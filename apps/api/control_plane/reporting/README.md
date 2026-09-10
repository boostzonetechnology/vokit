# Reporting / dashboards

`GET /api/v1/{platform|agency|customer}/dashboard` projects KPIs from control-plane
indexes and the commission ledger. The browser does not calculate money.
Period presets: `today`, `7d`, `30d`, `mtd`, `custom` with an explicit timezone.
Platform may filter by `agency_id`. Session scope still binds agency/customer
dashboards — the client cannot switch tenant databases.

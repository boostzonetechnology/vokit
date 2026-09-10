# Tenant data plane

One MySQL database per Agency. Connections are opened from the trusted control-plane registry through a bounded, tenant-safe pool.

Current tenant schema (`0010_integrations`): isolation tables, `agency_profiles`, `customers`,
subscriptions/invoices/payments/minute lots, agent builder tables,
`number_assignments`, `calls`, `call_events`, `transfer_destinations`,
`voicemail_messages`, `recording_artifacts`, plus customer-owned
`integration_connections`, `webhook_endpoints`, and `webhook_deliveries`.
Customer rows always store `tenant_id` (TEN-002). No per-customer database.

Workers must carry `tenant_id` + `correlation_id` and reconstruct routing. Do not serialize DSNs or passwords into jobs.

# Integrations & outbound webhooks

Connections are **customer-owned** (Q-010). Agency APIs always take `customer_id`.
Customer A cannot list, test, or invoke Customer B’s connection. Pipecat calls
`POST /internal/telephony/v1/tools/invoke/`; Django holds credentials and returns
a sanitized result (Q-009). Secrets live in a server-side vault and are never
returned after connect except a webhook signing secret once (create/rotate).

Outbound deliveries use `X-Vokit-Signature: sha256=…`, unique `event_id` +
`delivery_id`, bounded retry (`retry_webhooks`), and authorized replay.
`call.completed` is emitted from voice session end.

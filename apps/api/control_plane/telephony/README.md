# Phone-number inventory

The Vokit Platform owns the inventory (Q-002). Super Admin stocks or purchases numbers
into the control-plane catalog. Agencies search, reserve, and assign. Customers are
invoiced on assign; they cannot purchase.

A reservation lasts 10 minutes and is exclusive. A second agency cannot reserve or
assign that number while the hold is active. Assignment binds one number to one agent
routing target and writes a non-commissionable `number` invoice line on the customer.

Release requires explicit confirmation and returns the number to the platform pool
unless Super Admin also requests a provider release. Provider success/local mismatch
is detected by reconcile.

Frozen `/internal/telephony/v1/` paths authenticate with `X-Vokit-Internal-Token`.
DID resolve and bootstrap fail closed (`routable`/`admitted` false) when the agent is
unpublished, the number is unassigned, inbound is disabled, the shop is outside hours
with hangup fallback, risk is blocked, or minutes/overage/grace are exhausted.

Transfer destinations (E.164, department, queue, SIP client) live in the Agency tenant
DB. Django resolves them to Edge `POST /v1/calls/:id/transfer {to}` (ADR-006). Queues
hunt members; SIP clients are numeric extensions. Super Admin may disable a destination.

Outbound: `POST /agency/calls/outbound` → Edge `POST /v1/calls`. Voicemail is metadata
only (`POST .../voice-session/voicemail/`). Audio ingest is
`POST /internal/recordings/v1/ingest/`. Tool invoke is the Django integration
gateway (Q-009): credentials stay in Django; Pipecat receives a sanitized result.

# ADR-006 — Transfer destinations and voicemail without rewriting SIP Edge

Status: Accepted  
Date: 2026-09-10  
Accepted: 2026-09-10 (Q-008, Q-013 Decided)

## Context

XFER-001 requires transfer destinations of phone number, department, queue, and
supported SIP/client. Q-013 requires inbound and outbound voicemail.

Current SIP Edge remains:

- `POST /v1/calls` `{ to, from }`
- `POST /v1/calls/:id/transfer` `{ to, max_timeout_seconds? }`
- attended consult + REFER
- `to` is sanitized to digits / E.164 and placed in the SIP Request-URI user part

Edge has no queue object and no first-class SIP-client kind. Q-008 says implement
SRS queues and SIP clients, and keep existing Edge/Asterisk contracts unless a
change is genuinely required.

## Decision

Keep the SIP Edge HTTP contract unchanged. Django is the source of truth for
destination kind, business hours, hunt order, and voicemail policy.

Django resolves every destination to a concrete Edge `to`:

| Kind | Edge `to` |
|---|---|
| `e164` / `department` | E.164 |
| `sip_client` | numeric SIP extension routed by Asterisk (e.g. `1002`) |
| `queue` | Django hunts members in order; each member is E.164 or SIP extension |

Asterisk maps SIP-client extensions to PJSIP endpoints. Queue semantics live in
Django (ordered hunt + no-answer fallback). That is not an E.164-only product
model: kinds, members, and hours are first-class in Vokit.

Voicemail:

- inbound after hours or agent-unavailable with fallback `message` → mailbox path;
- outbound answering-machine / voicemail → agent may leave a configured message;
- Django stores mailbox **metadata** only (`call_id`, direction, status, object_ref);
- raw audio remains the recording data plane (ADR-002 / Phase 13).

New internal path (does not rename frozen Pipecat paths):

- `POST /internal/telephony/v1/voice-session/voicemail/`

Outbound origination is Django → Edge `POST /v1/calls`. Pipecat still bootstraps
on the resulting `edge_call_id`.

## Consequences

Positive:

- SRS queue / SIP-client / voicemail without an Edge rewrite;
- Pipecat transfer poll contract unchanged (`pending` → terminal);
- fail-closed platform disable of unsafe destinations.

Trade-offs:

- SIP clients must be numeric extensions because Edge `sanitize_number` strips
  non-digits. Named AORs stay an Asterisk mapping concern.
- Real PBX `Queue()` is optional lab sugar, not the control-plane contract.

## Change rule

If Edge later accepts SIP URIs or a `kind` field, record a new ADR before
changing the frozen `to` contract. Do not rename `/internal/telephony/v1/` paths.

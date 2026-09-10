# Vokit Production Checklist (Environment)

Environment and configuration readiness. Pair with the final launch checklist.

## Identity and access

- [ ] HTTPS only
- [ ] Session cookie flags correct
- [ ] CSRF enabled
- [ ] MFA enforced for Super Admin / Finance / KYC
- [ ] Break-glass admin documented

## Secrets

- [ ] Secret manager populated
- [ ] No plaintext DB passwords in tables
- [ ] Stripe **and** Braintree live/restricted keys separated from sandbox
- [ ] Internal telephony token rotated from example values
- [ ] Media WS token rotated
- [ ] Webhook signing secrets unique per tenant capability
- [ ] Recording service credentials ≠ API DB credentials

## Data stores

- [ ] Control-plane MySQL TLS
- [ ] Tenant registry rows for every Active agency
- [ ] Each tenant DB reachable from API/workers only
- [ ] Backups scheduled + restore drill dated
- [ ] Redis persistence/eviction policy understood
- [ ] Qdrant network-private

## Voice

- [ ] Asterisk/Edge RTP ranges open as designed
- [ ] Edge control API not public
- [ ] Pipecat replicas sized for concurrent calls
- [ ] DID resolve fail-closed tested
- [ ] Rollback media URL documented

## Recordings

- [ ] Separate bucket/server
- [ ] Object namespace convention live
- [ ] Signed URL TTL configured
- [ ] Retention job scheduled
- [ ] Legal-hold path documented

## Payments / KYC

- [ ] Processor webhooks verify in live mode
- [ ] Dispute/chargeback endpoints live
- [ ] KYC provider live/sandbox keys in secret manager (not in git)
- [ ] KYC webhook signature verified
- [ ] Payout-proof bucket private (not agency-readable)
- [ ] Card-image validation on

## Observability

- [ ] Correlation IDs in all services
- [ ] P0 alerts routed to humans
- [ ] Log redaction verified with a probe
- [ ] Dashboard for routing/pools/calls/payments/payouts

## Legal / config

- [ ] USD-only confirmed
- [ ] Recording disclosure defaults set for launched jurisdictions
- [ ] Retention periods set
- [ ] KYC gates set
- [ ] Terms/privacy URLs live

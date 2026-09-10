# Working-product Wave 4 — attestation status (2026-09-10)

**Verdict:** Lab product path is implementable; **live production remains NO-GO**.

Do **not** start Phase 20 scale until a live GO with dated evidence.

## Shipped for lab working product

| Wave | Outcome |
| --- | --- |
| 0 | Token alignment in `.env.example`; `scripts/dev-stack.ps1`; `scripts/dev-voice.ps1`; `docs/execution/27-LAB-VOICE-WIRING.md` |
| 1A | Agency create allocates `vokit_t_<uuid>` from settings; client `database` block rejected |
| 1B | Purpose-built portal screens (agencies, customers, agents, numbers, calls + remaining Must modules) |
| 1C | Voice process list documented for Windows + VMware Asterisk; edge/Pipecat start script |
| 2 | Stock numbers UI; sandbox settle/top-up UI; recording grant play; Qdrant notes |
| 3 | Outbound originate UI; voicemail fields; audit search; a11y skip-link / focus styles retained |
| 4 | This attestation tracker — no false GO |

## Still required for live GO (Phase 19)

See [26-PHASE-19-EVIDENCE.md](26-PHASE-19-EVIDENCE.md). Missing dated env attestations:

- `VOKIT_EVIDENCE_LIVE_INBOUND_CALL`
- `VOKIT_EVIDENCE_LIVE_OUTBOUND_CALL`
- `VOKIT_EVIDENCE_LIVE_PAYMENT`
- `VOKIT_EVIDENCE_LIVE_RECORDING`
- `VOKIT_EVIDENCE_RESTORE_DRILL`
- `VOKIT_EVIDENCE_ALERTING`
- `VOKIT_EVIDENCE_ROLLBACK_STAGING`
- `VOKIT_EVIDENCE_LEGAL_SIGN_OFF`

## Lab call proof checklist (operator)

1. Align tokens across Django / sip-edge / Pipecat / Asterisk
2. `.\scripts\dev-stack.ps1` then `.\scripts\dev-voice.ps1`
3. Start Asterisk on VMware with `deploy/asterisk/lab/`
4. Softphone → lab DID → Django call row + Pipecat audio
5. Only then set `VOKIT_EVIDENCE_LIVE_INBOUND_CALL=YYYY-MM-DD`

# VMware lab inbound voice (Windows host + Ubuntu Asterisk VM)

**Follow-along (start here):** [LAB-INBOUND-VMWARE.md](LAB-INBOUND-VMWARE.md) — full inbound lab from env files through Super Admin / Agency UI, Asterisk copy, MicroSIP, and troubleshooting. That document matches the current Django, portals, Pipecat, sip-edge, and `deploy/asterisk/lab/` configs.

**Authority:** SRS SIP path + ADR telephony contracts. vokit-old is reference for wire contracts only.

Full token/process list: [27-LAB-VOICE-WIRING.md](execution/27-LAB-VOICE-WIRING.md).
Asterisk files: `deploy/asterisk/lab/`.

## Topology

```text
Softphone → Asterisk (VM :5060)
         → Django DID-resolve (Windows :8000)
         → vokit-sip-edge (Windows :5071 / :8090)
         → Pipecat (Windows :8100 /sip/media)
         → Django bootstrap / events / end
```

Default host-only IPs: VM `192.168.56.100`, Windows `192.168.56.1`.

## Windows checklist

1. Align `VOKIT_INTERNAL_TELEPHONY_TOKEN` and `VOKIT_MEDIA_WS_TOKEN` across
   `apps/api/.env`, `packages/vokit-sip-edge/.env`, `packages/pipecat-voice/.env`.
   Asterisk uses header `X-Vokit-Internal-Token`, not `Authorization`.
2. Include `192.168.56.1` in `DJANGO_ALLOWED_HOSTS` (local settings also append it).
3. `SIP_EDGE_CONTROL_URL=http://127.0.0.1:8090`
4. `.\scripts\dev-stack.ps1`
5. `cargo build --release` in `packages/vokit-sip-edge` then `.\scripts\dev-voice.ps1`
6. Allow UDP 5071 and RTP 10000–20000 from the VM in Windows Firewall

## VMware checklist

1. Copy `deploy/asterisk/lab/*` to `/etc/asterisk/`
2. Set `VOKIT_INTERNAL_TOKEN` and `DJANGO_RESOLVE_URL` to the Windows host
3. Reload PJSIP + dialplan; register `labphone` / Softphone to the lab DID
4. Confirm Django creates a call row and Pipecat receives media

## Exit

One inbound lab call → Django call metadata row + Pipecat audio.
Live production attestations remain Phase 19 / Wave 4 — **no false GO**.

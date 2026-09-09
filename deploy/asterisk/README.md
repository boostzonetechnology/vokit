# Asterisk SIP gateway — config templates (manual install)

```text
ElevenSolution trunk
  ↔ Asterisk
  ↔ vokit-sip-edge (Rust)
  ↔ Pipecat /sip/media   (Phase 13 default)
     (legacy rollback: Django /sip/media)
```

Django remains the application brain (DID resolve, billing, hangup/transfer control).  
Pipecat is the realtime AI media peer. Cutover is edge env `SIP_NODE_MEDIA_BASE_URL`.

| Use case | Configs to copy |
|----------|-----------------|
| **Colocated VPS / staging** (Asterisk + edge on same host) | `deploy/asterisk/{pjsip,extensions,rtp}.conf` |
| **VMware lab** (Asterisk on VM, Django/edge on Windows) | `deploy/asterisk/lab/*` — see [lab/README.md](./lab/README.md) |

Inbound AI lab (PSTN): [docs/lab-inbound-voice.md](../../docs/lab-inbound-voice.md).  
**Full VPS staging (domain + HTTPS + real trunk):** [docs/vps-staging-deployment.md](../../docs/vps-staging-deployment.md).  
VMware mock trunk: [docs/vmware-lab-inbound.md](../../docs/vmware-lab-inbound.md).

## SIP scanners

Port `5060` attracts internet war-dialers. **Never** point an open `[anonymous]` endpoint at `from-carrier` with a catch-all `_X.` — that answers junk INVITEs (`80113…`, `00003…`) and floods vokit-edge. Only your DID should dial vokit-edge; lock ufw `5060/udp` to the ElevenSolution trunk IP.

**Digits only — no `+` prefix** on trunk INVITEs.

| Use | Example |
|-----|---------|
| Caller ID / From | `17134700972` |
| Destination | `18554244706` |
| DID | `17134700972` |

API/curl and vokit-sip-edge use `+1...` in the Request-URI. Asterisk dialplan must match `_+!` (leading plus) and strip to digits before trunk `Dial()`. If you only have `_X.` patterns, outbound fails with **SIP 404**.

## Config files (colocated VPS)

| Repo file | Copy to | Placeholders / edits |
|-----------|---------|----------------------|
| `pjsip.conf` | `/etc/asterisk/pjsip.conf` | `__VPS_PUBLIC_IP__`, `__PROVIDER_TRUNK_IP__`, `__SIP_DEFAULT_FROM__` (digits only, no `+`) |
| `extensions.conf` | `/etc/asterisk/extensions.conf` | `DJANGO_RESOLVE_URL` (default `http://127.0.0.1:8000/internal/telephony/v1/did-resolve/`), `__VOKIT_INTERNAL_TOKEN__` (= Django `VOKIT_INTERNAL_TELEPHONY_TOKEN`) |
| `rtp.conf` | `/etc/asterisk/rtp.conf` | (none) |

Requires Asterisk **PJSIP** + **`res_curl`** (DID resolve before Dial edge).

Do **not** use `lab/` configs on a real carrier VPS.

## vokit-edge `.env` (colocated VPS)

```env
SIP_TRUNK_HOST=127.0.0.1
SIP_TRUNK_PORT=5070
SIP_LOCAL_BIND=127.0.0.1:5071
SIP_PUBLIC_IP=YOUR_VPS_PUBLIC_IP
SIP_DEFAULT_FROM=17134700972
SIP_EDGE_HTTP_PORT=8090
# Phase 13 — Pipecat (token must match Django VOKIT_MEDIA_WS_TOKEN)
SIP_NODE_MEDIA_BASE_URL=ws://127.0.0.1:8100/sip/media?media_token=SAME_AS_VOKIT_MEDIA_WS_TOKEN
```

Full sample (lab + VPS): `packages/vokit-sip-edge/.env.example`.

`+` in edge `.env` is OK for E.164; Asterisk `pjsip.conf` placeholders must be **digits only**.

## Ports

| Port | Service |
|------|---------|
| 5060 | Asterisk ↔ carrier (firewall to trunk IP) |
| 5070 | vokit outbound → Asterisk (localhost on colocated VPS) |
| 5071 | Asterisk inbound → vokit (localhost on colocated VPS) |
| 8090 | Edge HTTP control — **private only** (Django hangup/transfer) |
| 8100 | Pipecat media WS — **private only** |
| 8000 | Django Daphne — private / reverse-proxy |
| 30000–40000 | Asterisk RTP |
| 10000–20000 | vokit-sip-edge RTP |

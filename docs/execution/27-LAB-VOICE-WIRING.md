# Lab voice wiring — Wave 0 / Wave 1C

**Authority:** SRS voice path + ADR telephony contracts. Asterisk first target: **VMware Ubuntu lab**; Django, sip-edge, and Pipecat stay on **Windows**.

## Token alignment (must match)

| Variable | Django (`apps/api/.env`) | sip-edge | Pipecat | Asterisk |
| --- | --- | --- | --- | --- |
| `VOKIT_INTERNAL_TELEPHONY_TOKEN` | yes | — | yes | DID-resolve `Authorization` |
| `VOKIT_MEDIA_WS_TOKEN` | yes | `media_token` in `SIP_NODE_MEDIA_BASE_URL` | yes | — |
| `SIP_EDGE_CONTROL_URL` | `http://127.0.0.1:8090` | listens `:8090` | — | — |
| `SIP_NODE_MEDIA_BASE_URL` | — | `ws://127.0.0.1:8100/sip/media?media_token=…` | serves `/sip/media` | — |

Never put these tokens in React.

## Process list

### Windows (host)

1. MySQL + Redis (Laragon or Docker Compose)
2. Django API `:8000` — `.\scripts\dev-stack.ps1`
3. Portals `:5173` / `:5174` / `:5175` — same script
4. `vokit-sip-edge` — SIP `:5071`, HTTP `:8090`
5. `pipecat-voice` — `:8100`

### VMware Ubuntu

1. Asterisk with `deploy/asterisk/lab/` (host-only NIC, e.g. `192.168.56.x`)
2. Softphone / mock trunk → lab DID
3. AGI/curl `DJANGO_RESOLVE_URL` → `http://<WINDOWS_HOST_IP>:8000/internal/telephony/v1/did-resolve/`
4. On routable DID → `Dial` Windows host `:5071`

## One-command helpers

```powershell
.\scripts\dev-stack.ps1
.\scripts\dev-voice.ps1
```

Put VM IPs only in **local** gitignored `.env` files.

## Exit criteria (Wave 1C)

One inbound lab call produces a Django call row and Pipecat audio. `calling_live` may be on in local settings; live production attestations remain Wave 4 / Phase 19 evidence.

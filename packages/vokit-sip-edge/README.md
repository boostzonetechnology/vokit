# vokit-sip-edge

Rust SIP B2BUA edge for Vokit — **no OpenAI/ElevenLabs dependencies**.

- SIP signaling (UDP) to provider trunk / Asterisk
- RTP G.711 μ-law (PCMU @ 8 kHz)
- HTTP control API (`POST /v1/calls`, `DELETE /v1/calls/:id`, transfer)
- WebSocket media bridge to the media peer (binary μ-law frames)
  - **Default (Phase 13):** Pipecat `packages/pipecat-voice` `/sip/media` on `:8100`
  - **Legacy rollback:** Django Channels `/sip/media` on `:8000`

## Build

Requires [Rust](https://rustup.rs/) 1.74+.

```powershell
cargo build --release --manifest-path packages/vokit-sip-edge/Cargo.toml
```

## Run (point media at Pipecat)

Copy `packages/vokit-sip-edge/.env.example` to `.env` (gitignored) and set the same values in your shell, or export them before running the binary. Critical match:

- Edge `SIP_NODE_MEDIA_BASE_URL` `media_token=…` **=** Django / Pipecat `VOKIT_MEDIA_WS_TOKEN`
- Django `SIP_EDGE_CONTROL_URL` **=** `http://<edge-host>:8090` (or your `SIP_EDGE_HTTP_PORT`)

### Colocated VPS / same-host (Asterisk + edge)

```powershell
$env:SIP_TRUNK_HOST="127.0.0.1"
$env:SIP_TRUNK_PORT="5070"
$env:SIP_LOCAL_BIND="127.0.0.1:5071"
$env:SIP_PUBLIC_IP="YOUR_PUBLIC_IP"
$env:SIP_DEFAULT_FROM="+18005551234"
$env:SIP_EDGE_HTTP_PORT="8090"
# Phase 13 — Pipecat peer (token must match VOKIT_MEDIA_WS_TOKEN)
$env:SIP_NODE_MEDIA_BASE_URL="ws://127.0.0.1:8100/sip/media?media_token=change-me-media-ws-secret"
# Legacy Django peer:
# $env:SIP_NODE_MEDIA_BASE_URL="ws://127.0.0.1:8000/sip/media?media_token=change-me-media-ws-secret"
.\packages\vokit-sip-edge\target\release\vokit-sip-edge.exe
```

On Linux VPS run the release binary without `.exe`. For VMware lab host IPs see `.env.example` block A and [docs/vmware-lab-inbound.md](../../docs/vmware-lab-inbound.md).

Originate a test outbound call (smoke; preserve outbound path):

```powershell
curl -X POST http://localhost:8090/v1/calls `
  -H "Content-Type: application/json" `
  -d '{"to":"+1DESTINATION","from":"+1YOUR_DID"}'
```

**Inbound AI lab:** [docs/lab-inbound-voice.md](../../docs/lab-inbound-voice.md).  
**Asterisk templates:** [deploy/asterisk/README.md](../../deploy/asterisk/README.md).

## Environment

| Variable | Description |
|----------|-------------|
| `SIP_TRUNK_HOST` | Asterisk / trunk host for outbound path |
| `SIP_TRUNK_PORT` | Signaling port (Asterisk gateway often `5070`) |
| `SIP_TRUNK_TRANSPORT` | `udp` or `tcp` |
| `SIP_LOCAL_BIND` | Local bind (inbound from Asterisk often `127.0.0.1:5071` colocated) |
| `SIP_PUBLIC_IP` | Public IP in SDP (whitelisted egress) |
| `SIP_DEFAULT_FROM` | Outbound caller ID |
| `SIP_CODECS` | `pcmu` (G.711 μ-law) |
| `RTP_PORT_MIN` / `RTP_PORT_MAX` | RTP UDP range |
| `SIP_EDGE_HTTP_PORT` | Control API port (default 8090) — keep private |
| `SIP_NODE_MEDIA_BASE_URL` | Media peer WS, e.g. `ws://127.0.0.1:8100/sip/media?media_token=…` |

## Architecture

```
curl → vokit-sip-edge:8090 → SIP INVITE → Asterisk/trunk → PSTN
                              RTP μ-law ↔ WS → Pipecat /sip/media → STT/LLM/TTS
                              (Django: DID resolve, bootstrap, billing, hangup)
```

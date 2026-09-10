# Asterisk configs for **VMware lab** (Ubuntu VM + Windows Django/edge/Pipecat)

Use these instead of the production templates under `deploy/asterisk/*.conf`
when Asterisk runs on the VM and Django / Pipecat / edge run on the Windows host.

**Do not** copy these lab files to a carrier staging/production VPS — use
`deploy/asterisk/{pjsip,extensions,rtp}.conf` there (colocated `127.0.0.1` edge).

| File | Copy to VM |
|------|------------|
| `lab/pjsip.conf` | `/etc/asterisk/pjsip.conf` |
| `lab/extensions.conf` | `/etc/asterisk/extensions.conf` |
| `lab/rtp.conf` | `/etc/asterisk/rtp.conf` |

**Required edit on VM only:** in `extensions.conf` globals, set:

```ini
VOKIT_INTERNAL_TOKEN=<same as application/.env VOKIT_INTERNAL_TELEPHONY_TOKEN>
```

Do not commit that real token into git.

Default lab IPs: VM `192.168.56.100`, Windows `192.168.56.1`.

## Softphones

| Role | SIP user | Password | Client tip |
|------|----------|----------|------------|
| Caller (inbound AI) | `labphone` | `labphone123` | MicroSIP |
| Human (attended transfer) | `labphone2` | `labphone123` | **Linphone** (or second MicroSIP portable) |

Do **not** register both accounts in one MicroSIP process — Asterisk will only keep one contact.

After copy/reload:

```bash
sudo asterisk -rx "module reload res_pjsip.so"
sudo asterisk -rx "dialplan reload"
sudo asterisk -rx "pjsip show contacts"
```

Expect both `labphone` and `labphone2` Reachable when both clients are registered.

## Attended transfer lab route

Edge consult INVITE / REFER to `+15550001002` hits `[from-vokit-edge]`:

```ini
exten => _+15550001002,1,Dial(PJSIP/labphone2,45)
```

Django Transfer Number for the agent must be **`+15550001002`** (Active + availability window).

Edge uses **consult INVITE first, REFER+Replaces only after human answers** so the AI leg stays up while `labphone2` rings. See `docs/sip-integration.md` §12 and `docs/lab-inbound-voice.md`.

Full inbound steps: [docs/vmware-lab-inbound.md](../../../docs/vmware-lab-inbound.md)
and [docs/execution/27-LAB-VOICE-WIRING.md](../../../docs/execution/27-LAB-VOICE-WIRING.md).

Start helpers on Windows: `.\scripts\dev-stack.ps1` then `.\scripts\dev-voice.ps1`.

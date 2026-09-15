# Lab inbound call — VMware Asterisk + Windows Django / sip-edge / Pipecat

Follow this document **in order**. It describes **this repository as it exists today**, not a generic PBX lab and not production PSTN.

**Scope:** one inbound AI test call. Softphone registers to Asterisk on the VM, Asterisk asks Django if the DID is routable, then dials `vokit-sip-edge` on Windows, which bridges μ-law audio to Pipecat. Pipecat bootstraps the agent from Django (including STT/TTS/LLM keys).

**Not this document:** outbound PSTN, attended transfer (`labphone2` / `+15550001002`), recordings playback, VPS colocated Asterisk (`deploy/asterisk/*.conf` without `lab/`).

Shorter wiring notes (same topology): [vmware-lab-inbound.md](vmware-lab-inbound.md), [execution/27-LAB-VOICE-WIRING.md](execution/27-LAB-VOICE-WIRING.md). Voice keys: [flows/VOICE-PROVIDERS.md](flows/VOICE-PROVIDERS.md). Asterisk files: `deploy/asterisk/lab/`.

---

## 0. Read this first (fresh VMware)

You do **not** install Django, Pipecat, or sip-edge on the VM. The VM is **Asterisk only**. Everything else stays on the Windows host that already has this git clone.

Work in this order:

1. Confirm (or set) host-only IPs to the values hardcoded in this repo — §2.
2. Create the Ubuntu VM and give it those IPs — §3–§5.
3. Open the lab ports on **both** Windows Firewall and Ubuntu `ufw` — §6.
4. Install Windows app stack, tokens, Super Admin + Agency product setup — §7–§11.
5. Start sip-edge + Pipecat — §12.
6. Install Asterisk on the VM and copy **lab** configs — §13.
7. Register MicroSIP and dial the lab DID — §14.

Do not skip the ping test in §5. If the VM cannot reach `192.168.56.1:8000`, Asterisk CURL will never resolve the DID.

---

## 1. Topology (fixed)

```text
MicroSIP (Windows)  --SIP UDP 5060-->  Asterisk on Ubuntu VM
                                          |
                                          | POST /internal/telephony/v1/did-resolve/
                                          | header X-Vokit-Internal-Token
                                          v
                                    Django on Windows :8000
                                          |
                    if "routable": true, Dial PJSIP/vokit-edge
                                          |
                                          v
                         vokit-sip-edge on Windows :5071 SIP + :8090 HTTP
                                          |
                                          | WS /sip/media?media_token=...
                                          v
                         Pipecat on Windows :8100
                                          |
                                          | POST /internal/telephony/v1/voice-session/bootstrap/
                                          v
                                    Django (agent + providers + billing)
                                          |
                                          v
                         Deepgram / Cartesia / ElevenLabs / OpenAI / Grok / Anthropic
```

| Process | Where it runs | Ports in this repo |
|---|---|---|
| MySQL + Redis | Windows (Laragon or `deploy/compose`) | 3306, 6379 |
| Django API | Windows `apps/api` | `0.0.0.0:8000` |
| Platform UI | Windows `apps/web-platform` | 5173 (proxies `/api` → `:8000`) |
| Agency UI | Windows `apps/web-agency` | 5174 |
| Customer UI | Windows `apps/web-customer` | 5175 (not required for this inbound lab) |
| `vokit-sip-edge` | Windows `packages/vokit-sip-edge` | SIP **5071**, HTTP **8090**, RTP **10000–20000** |
| `pipecat-voice` | Windows `packages/pipecat-voice` | **8100** `/sip/media` |
| Asterisk | **Ubuntu VMware VM only** | SIP **5060** (softphone), **5070** (edge transport), RTP **30000–40000** |

Django, Pipecat, and sip-edge do **not** run on the VM. Asterisk on the VM must reach the Windows host-only IP.

Pipecat `:8100` and edge HTTP `:8090` stay Windows → Windows (localhost). The VM never connects to 8090 or 8100.

---

## 2. Default IPs in the committed configs

These values are **hardcoded** in `deploy/asterisk/lab/pjsip.conf`, `deploy/asterisk/lab/extensions.conf`, and `packages/vokit-sip-edge/.env.example` **block A**. The easiest lab is to make VMware use **exactly** this subnet so you do not edit those files except the token.

| Role | Default in repo |
|---|---|
| Windows host-only NIC (VMnet1) | `192.168.56.1` |
| Ubuntu VM (static) | `192.168.56.100` |
| Host-only subnet | `192.168.56.0/24` |

`apps/api/config/settings/local.py` auto-appends **only** `192.168.56.1` to `ALLOWED_HOSTS`. Any other Windows host IP must be added to `DJANGO_ALLOWED_HOSTS` in `apps/api/.env`.

### 2.1 Files that contain those IPs (edit only if yours differ)

| File | What to change |
|---|---|
| `deploy/asterisk/lab/pjsip.conf` | `external_media_address`, `external_signaling_address`, `local_net`, `[vokit-edge]` `contact=sip:WINDOWS_IP:5071`, `[vokit-edge-identify]` `match=WINDOWS_IP` |
| `deploy/asterisk/lab/extensions.conf` | `DJANGO_RESOLVE_URL=http://WINDOWS_IP:8000/internal/telephony/v1/did-resolve/` and `Dial(PJSIP/vokit-edge/sip:${EXTEN}@WINDOWS_IP:5071,120)` |
| `packages/vokit-sip-edge/.env` | `SIP_TRUNK_HOST=VM_IP`, `SIP_PUBLIC_IP=WINDOWS_IP` |
| `apps/api/.env` | `DJANGO_ALLOWED_HOSTS` must include the Windows host-only IP |

The rest of this document uses the repo defaults.

---

## 3. Create the Ubuntu VM (fresh VMware)

You need **VMware Workstation Pro** or **VMware Workstation Player** on the same Windows PC that will run Django. Hyper-V / WSL2 sometimes conflicts with VMware virtual adapters; if **VMware Network Adapter VMnet1** never appears in `ipconfig`, fix VMware networking first (do not invent a different SIP topology).

### 3.1 Download

1. VMware Workstation Pro or Player (already installed if you have a fresh empty library).
2. Ubuntu Server ISO — **22.04 LTS or 24.04 LTS** (64-bit). Desktop Ubuntu also works; Server is enough because this VM only runs Asterisk + SSH.

### 3.2 Virtual network (do this **before** the guest OS)

The committed lab files assume **Host-only VMnet1 = `192.168.56.0/24`**, Windows = `.1`.

**Workstation Pro:**

1. **Edit → Virtual Network Editor** (run as Administrator if the list is empty).
2. Select **VMnet1**.
3. Type: **Host-only**.
4. Connect a host virtual adapter: **checked**.
5. Subnet IP: `192.168.56.0`, subnet mask `255.255.255.0`.
6. DHCP: you may leave VMware DHCP on. Reserve **`.100` as static on the guest** so DHCP does not also hand `.100` to another VM. Typical VMware DHCP range starts around `.128`.
7. **Apply**.

**Workstation Player:**

Player often already creates VMnet1 as host-only on `192.168.56.0/24`. Confirm on Windows:

```powershell
ipconfig
```

You must see an adapter named like **VMware Network Adapter VMnet1** with IPv4 **`192.168.56.1`**. If the host IPv4 is a different `192.168.56.x` or a different subnet, either change VMnet1 in Virtual Network Editor (if Player installed it) **or** edit every file in §2.1.

Do **not** use Bridged for this lab unless you rewrite those files. Bridged puts the VM on your LAN; the repo Dial/CURL URLs would be wrong.

### 3.3 Two NICs (recommended)

Give the VM:

| Adapter | VMware type | Why |
|---|---|---|
| Network Adapter | **Host-only (VMnet1)** | SIP + CURL to Windows `192.168.56.1`. This is the lab path. |
| Network Adapter 2 | **NAT (VMnet8)** | `apt install` needs internet. Host-only has no path to Ubuntu archives. |

Without NAT (or Bridged), the VM cannot `apt update` unless you copy `.deb` files by hand.

### 3.4 New Virtual Machine wizard

1. **File → New Virtual Machine** (Player: **Home → Create a New Virtual Machine**).
2. **Typical**.
3. Installer disc image file: select the Ubuntu ISO.
4. Guest OS: **Linux → Ubuntu 64-bit** (or Ubuntu 64-bit if listed).
5. Name: e.g. `vokit-asterisk-lab`. Store the VM disk on a local drive with enough space.
6. Disk: **40 GB** (or 20 GB minimum). Asterisk + logs do not need more for this lab.
7. **Customize Hardware** before Finish:
   - Memory: **2048 MB** minimum, **4096 MB** if the host can spare it.
   - Processors: **2**.
   - Network Adapter: **Host-only**.
   - **Add → Network Adapter** → **NAT**.
   - CD/DVD: Connected, ISO you selected.
8. Finish and power on.

### 3.5 Ubuntu installer (guest)

Use the Ubuntu Server text installer (Desktop: GUI equivalent).

1. Language, keyboard.
2. Network: if both NICs show DHCP, that is fine for install. You will set **static `192.168.56.100`** after first boot (§4). If the installer asks, you can already set the **host-only** NIC to `192.168.56.100/24` with **no default gateway** on that NIC, and leave NAT on DHCP (NAT keeps the default route for apt).
3. Mirror: default Ubuntu archive (needs NAT/internet).
4. Guided storage: use entire disk.
5. Profile: pick a username you will use for `scp` (this doc uses `vokit` as an example — use yours).
6. **Install OpenSSH server: yes.** You will copy configs from Windows with `scp`.
7. Do not install Docker / microk8s / extra snaps for this lab.
8. Reboot. Remove the ISO if the VM tries to install again.

### 3.6 After first boot

Log in on the VM console (or SSH once you know the IP).

```bash
sudo apt update
sudo apt install -y open-vm-tools openssh-server curl
sudo systemctl enable --now ssh
```

`open-vm-tools` is the in-guest VMware tools package (time sync, better shutdown). Not required for SIP, recommended.

Confirm SSH listens:

```bash
ss -lntp | grep ':22'
```

From **Windows** you will SSH after the static IP is set:

```powershell
ssh vokit@192.168.56.100
```

(replace `vokit` with your Ubuntu username)

---

## 4. Static IP on the VM (`192.168.56.100`)

Ubuntu 22.04/24.04 uses **netplan**. Interface names are **not** always `ens33`. Find them first:

```bash
ip -br addr
ip route
```

Typical pattern:

- One NIC has an address in `192.168.56.0/24` (host-only). It may be `.128` or another DHCP lease. **This** NIC must become `192.168.56.100/24`.
- The other NIC has an address in `192.168.x.x` via VMnet8 NAT (often `192.168.189.x` or `192.168.47.x`). That one stays DHCP. **Default route** (`default via …`) must stay on NAT, not on host-only.

List netplan files:

```bash
ls /etc/netplan/
sudo cat /etc/netplan/*.yaml
```

The YAML keys under `ethernets:` **must be the names from `ip -br addr`**. A common VMware Workstation pair is `ens33` (host-only) + `ens34` (NAT). If you copy `ens160` / `ens192` and those NICs do not exist, `netplan apply` does nothing useful: you keep a DHCP address such as `192.168.56.129`, **`192.168.56.100` is never assigned**, and Windows `ping 192.168.56.100` times out.

Example for `ens33` / `ens34` (change the names if yours differ):

```yaml
network:
  version: 2
  ethernets:
    ens33:
      dhcp4: no
      addresses:
        - 192.168.56.100/24
    ens34:
      dhcp4: yes
```

Apply:

```bash
sudo netplan apply
ip -4 addr
ip route
```

Confirm — this line **must print** `192.168.56.100`. Empty output means the static IP is not on any NIC; do not ping `.100` from Windows yet.

```bash
ip -4 addr show | grep 192.168.56.100
```

Ping the Windows host-only address from the VM:

```bash
ping -c 3 192.168.56.1
```

If that fails, the NIC you marked static is not the host-only adapter — swap the names and apply again.

---

## 5. Prove host ↔ VM before Asterisk or Django

On **Windows** PowerShell:

```powershell
ipconfig
ping 192.168.56.100
```

`ipconfig` must show VMnet1 = `192.168.56.1`. Ping to `.100` must reply.

If ping fails:

1. VM powered on, correct NIC, `ip -4 addr` shows `.100`.
2. Windows Firewall may drop ICMPv4 (Echo Request). Allow it in §6 even if you skip ping and use SSH instead.
3. VMnet1 host adapter disabled in Windows: **Control Panel → Network adapters** — enable **VMware Network Adapter VMnet1**.
4. Wrong network type on the VM adapter (NAT instead of Host-only) in VM settings while powered off.

SSH from Windows (proves TCP, not only ping):

```powershell
ssh vokit@192.168.56.100
```

Accept the host key. You will use this same session for Asterisk later.

Optional: set the Windows VMnet1 profile to **Private** so inbound firewall rules you add actually apply (Public profiles are stricter):

```powershell
Get-NetConnectionProfile
```

Find the alias that has `192.168.56.1`, then (Administrator PowerShell):

```powershell
Set-NetConnectionProfile -InterfaceAlias "VMware Network Adapter VMnet1" -NetworkCategory Private
```

The alias string must match `Get-NetConnectionProfile` exactly.

---

## 6. Firewalls (do this before starting Django or Asterisk)

Lab traffic that **crosses the host-only NIC**:

```text
Windows MicroSIP  --UDP 5060-->  VM Asterisk
Windows MicroSIP  --UDP 30000-40000-->  VM Asterisk RTP

VM Asterisk       --TCP 8000-->  Windows Django DID-resolve
VM Asterisk       --UDP 5071-->  Windows sip-edge SIP
VM Asterisk       --UDP 10000-20000-->  Windows sip-edge RTP
```

Do **not** open these ports to the whole Internet. Scope them to `192.168.56.0/24`.

Do **not** open Windows 8090, 8100, 5173–5175, or 3306 to the VM. Those stay on the host.

### 6.1 Windows Defender Firewall (Administrator PowerShell)

Run **Windows PowerShell as Administrator** on the host:

```powershell
$net = "192.168.56.0/24"

New-NetFirewallRule -DisplayName "Vokit lab ICMPv4 from host-only" `
  -Direction Inbound -Protocol ICMPv4 -RemoteAddress $net -Action Allow

New-NetFirewallRule -DisplayName "Vokit lab Django DID-resolve TCP 8000" `
  -Direction Inbound -Protocol TCP -LocalPort 8000 -RemoteAddress $net -Action Allow

New-NetFirewallRule -DisplayName "Vokit lab sip-edge SIP UDP 5071" `
  -Direction Inbound -Protocol UDP -LocalPort 5071 -RemoteAddress $net -Action Allow

New-NetFirewallRule -DisplayName "Vokit lab sip-edge RTP UDP 10000-20000" `
  -Direction Inbound -Protocol UDP -LocalPort 10000-20000 -RemoteAddress $net -Action Allow
```

List them:

```powershell
Get-NetFirewallRule -DisplayName "Vokit lab*" | Format-Table DisplayName, Enabled, Direction, Action
```

If you recreate the VM on another subnet, delete these rules and recreate with the new `RemoteAddress`.

Windows already allows **outbound** SSH (TCP 22) and MicroSIP (UDP 5060) to the VM unless you have a custom outbound-block policy. This lab does not require extra outbound allow rules on a default Windows install.

If a third-party antivirus firewall is installed, add the same inbound exceptions there. Windows Defender rules will not help if another product is the real filter.

### 6.2 Ubuntu `ufw` on the VM

Default Ubuntu Server may have **ufw inactive**. Check:

```bash
sudo ufw status
```

If you leave ufw inactive, the VM accepts SIP on 5060 from the host-only NIC (and from anything else that can route there). For a laptop lab that is usually only VMnet1. Still set explicit allows if you plan to `ufw enable`.

```bash
sudo ufw allow OpenSSH
sudo ufw allow from 192.168.56.0/24 to any port 5060 proto udp comment 'labphone MicroSIP'
sudo ufw allow from 192.168.56.0/24 to any port 5070 proto udp comment 'vokit-sip-edge trunk'
sudo ufw allow from 192.168.56.0/24 to any port 30000:40000 proto udp comment 'Asterisk RTP'
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw enable
sudo ufw status numbered
```

Outgoing must stay allowed: Asterisk `CURL()` is **outbound TCP 8000** to `192.168.56.1`. If you `default deny outgoing`, DID-resolve dies and you must add:

```bash
sudo ufw allow out to 192.168.56.1 port 8000 proto tcp
sudo ufw allow out to 192.168.56.1 port 5071 proto udp
sudo ufw allow out to 192.168.56.1 port 10000:20000 proto udp
```

NAT/internet for `apt` also needs outbound TCP 80/443 (default allow outgoing covers this).

Do **not** ufw-allow UDP 5060 from `Anywhere` on a bridged NIC. This lab VM should not be on the public Internet.

### 6.3 VMware / Windows extras that look like “firewall”

- VM **Settings → Network Adapter → Connected** and **Connect at power on** checked for **both** NICs.
- Do not enable VMware “incoming firewall” products; there is none required for this lab.
- Host sleep/hibernation drops SIP registrations. Keep the host awake while testing.

---

## 7. Tokens that must be identical

Never put these in React. They are not vendor STT/TTS/LLM keys.

| Secret | Django `apps/api/.env` | Pipecat `packages/pipecat-voice/.env` | sip-edge `packages/vokit-sip-edge/.env` | Asterisk VM |
|---|---|---|---|---|
| Internal telephony token | `VOKIT_INTERNAL_TELEPHONY_TOKEN` | `VOKIT_INTERNAL_TELEPHONY_TOKEN` | — | `VOKIT_INTERNAL_TOKEN` in `/etc/asterisk/extensions.conf`, sent as header **`X-Vokit-Internal-Token`** (not `Authorization`) |
| Media WS token | `VOKIT_MEDIA_WS_TOKEN` | `VOKIT_MEDIA_WS_TOKEN` | query `media_token=` on `SIP_NODE_MEDIA_BASE_URL` | — |
| Edge control URL | `SIP_EDGE_CONTROL_URL=http://127.0.0.1:8090` | — | listens `:8090` (`SIP_EDGE_HTTP_PORT`) | — |
| Media peer | Django does not authenticate the WS | serves `/sip/media` | `SIP_NODE_MEDIA_BASE_URL=ws://127.0.0.1:8100/sip/media?media_token=…` | — |
| Pipecat → Django | — | `DJANGO_INTERNAL_BASE_URL=http://127.0.0.1:8000` | — | — |

`.env.example` placeholders:

- `change-me-internal-telephony-secret`
- `change-me-media-ws-secret`

You may keep those **if every file uses the same strings**. Changing one file without the others breaks DID-resolve or the media WS.

### 7.1 Generate two random secrets (recommended)

These are **not** STT/TTS/LLM vendor keys. They are shared lab passwords so Asterisk, Django, Pipecat, and sip-edge trust each other.

In **PowerShell** (any window):

```powershell
"telephony: " + [Convert]::ToHexString([System.Security.Cryptography.RandomNumberGenerator]::GetBytes(32)).ToLower()
"media:      " + [Convert]::ToHexString([System.Security.Cryptography.RandomNumberGenerator]::GetBytes(32)).ToLower()
```

Git Bash:

```bash
openssl rand -hex 32
openssl rand -hex 32
```

You get two long hex strings. Treat the first as **internal telephony**, the second as **media WS**. Paste the **same** values into:

| Secret you generated | Put it here |
|---|---|
| Telephony hex | `apps/api/.env` → `VOKIT_INTERNAL_TELEPHONY_TOKEN=` |
| Telephony hex | `packages/pipecat-voice/.env` → `VOKIT_INTERNAL_TELEPHONY_TOKEN=` (create in §9.4) |
| Telephony hex | VM `/etc/asterisk/extensions.conf` → `VOKIT_INTERNAL_TOKEN=` (edit in §13.4, not now) |
| Media hex | `apps/api/.env` → `VOKIT_MEDIA_WS_TOKEN=` |
| Media hex | `packages/pipecat-voice/.env` → `VOKIT_MEDIA_WS_TOKEN=` |
| Media hex | `packages/vokit-sip-edge/.env` → inside `SIP_NODE_MEDIA_BASE_URL=...media_token=` (create in §9.3) |

Do **not** put spaces, quotes, or a `#` in the value. Hex from the commands above is safe.

Keep a one-line note of both strings until Asterisk is configured. Do not commit `.env` files.

If you skip generation, use the placeholders `change-me-internal-telephony-secret` and `change-me-media-ws-secret` in **every** file. Mixed values fail.

STT/TTS/LLM API keys do **not** go in Pipecat or sip-edge env. Super Admin stores them in platform settings (encrypted). Pipecat receives them only on bootstrap.

---

## 8. Lab DID (must match)

Committed sip-edge lab default:

```env
SIP_DEFAULT_FROM=+15550001001
```

Stock **this** E.164 in Django and dial **this** from MicroSIP. Asterisk sends Django the dialed digits; Django `normalize_did()` turns `15550001001` into `+15550001001`.

Transfer DID `+15550001002` / `labphone2` is in the dialplan for later transfer tests. Skip it for this inbound-only lab.

---

## 9. Windows — one-time software

On the Windows host (repo root `D:\laragon\www\vokit` or your clone):

- Python 3.12+ for Django (`apps/api`)
- Python 3.11+ for Pipecat (`packages/pipecat-voice`)
- Node.js 22+ (portals)
- Rust 1.74+ (`rustup`) for sip-edge
- MySQL 8 + Redis (Laragon **or** `deploy/compose/docker-compose.yml`)
- MicroSIP (or another UDP / PCMU softphone) on Windows
- `OpenSSH Client` Windows optional feature (for `scp` / `ssh` to the VM)

### 9.1 API venv

```powershell
cd apps\api
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
copy .env.example .env
```

Edit `apps/api/.env`:

1. `DJANGO_SETTINGS_MODULE=config.settings.local` (already in the example).
2. `DJANGO_ALLOWED_HOSTS` must include `192.168.56.1` (example already has it).
3. Point `CONTROL_PLANE_DB_*` at **your** MySQL. The example uses user `vokit` / password `vokit_local` and database `vokit_control` (created by `deploy/compose/mysql/init/01-databases.sql`). Laragon root often differs — use credentials that actually work.
4. `TENANT_RUNTIME=mysql`
5. `TENANT_DB_HOST` / `TENANT_DB_PORT` / `TENANT_DB_ADMIN_USER` / `TENANT_DB_ADMIN_PASSWORD` must be able to `CREATE DATABASE` / `CREATE USER` for agency tenant DBs.
6. `TENANT_DB_NAME_A=vokit_tenant_a` and `TENANT_DB_NAME_B=vokit_tenant_b` (demo seed).
7. `SIP_EDGE_CONTROL_URL=http://127.0.0.1:8090` (empty uses in-process `MemorySipEdge` — **not** a real lab call).
8. `LIVE_FLAGS_ENABLED_BY_DEFAULT=true` (local default; `calling_live` must be on or bootstrap returns `calling_not_live`).
9. Leave `VOICE_STT_PROVIDER` / `VOICE_TTS_*` / `VOICE_LLM_*` empty. They are unused at runtime.

Create the three databases if you are not using compose init:

- `vokit_control`
- `vokit_tenant_a`
- `vokit_tenant_b`

All utf8mb4.

```powershell
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe manage.py seed_phase2_demo
.\.venv\Scripts\python.exe manage.py seed_phase3_tenants
.\.venv\Scripts\python.exe manage.py seed_phase4_lifecycle
```

Demo logins from `control_plane/identity/demo.py` (password `Phase2-Demo!ok`):

| Email | Portal | Role |
|---|---|---|
| `platform@vokit.test` | http://127.0.0.1:5173 | Super Admin |
| `agency@vokit.test` | http://127.0.0.1:5174 | Agency owner (Demo Agency A) |
| `customer@vokit.test` | http://127.0.0.1:5175 | Customer owner (not required for this lab) |

`seed_phase4_lifecycle` creates agencies in status **`invited`** and activates demo customers. You still **Activate** the agency in the UI (next product section).

### 9.2 Portals

From repo root (workspaces in root `package.json`):

```powershell
npm install
```

You can start API + three Vite apps with:

```powershell
.\scripts\dev-stack.ps1
```

If PowerShell says scripts are disabled (typical on Windows), run this instead — Git Bash or PowerShell:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\dev-stack.ps1
```

That script starts Django as `manage.py runserver 0.0.0.0:8000` (required so the VM can hit `192.168.56.1:8000`). Vite apps: platform `5173`, agency `5174`, customer `5175`. Each `vite.config.ts` proxies `/api` to `http://127.0.0.1:8000`.

Health: `http://127.0.0.1:8000/api/v1/health`

### 9.3 sip-edge (build now, start later)

```powershell
cd packages\vokit-sip-edge
copy .env.example .env
cargo build --release
```

In `packages/vokit-sip-edge/.env` keep **block A** (VMware lab), not the colocated VPS block:

```env
SIP_TRUNK_HOST=192.168.56.100
SIP_TRUNK_PORT=5070
SIP_TRUNK_TRANSPORT=udp
SIP_LOCAL_BIND=0.0.0.0:5071
SIP_PUBLIC_IP=192.168.56.1
SIP_DEFAULT_FROM=+15550001001
SIP_CODECS=pcmu
RTP_PORT_MIN=10000
RTP_PORT_MAX=20000
SIP_EDGE_HTTP_PORT=8090
SIP_NODE_MEDIA_BASE_URL=ws://127.0.0.1:8100/sip/media?media_token=change-me-media-ws-secret
```

`media_token` **must** equal `VOKIT_MEDIA_WS_TOKEN`. Edge loads `.env` from repo root or `packages/vokit-sip-edge/.env` (`main.rs` `load_dotenv`).

Do not start edge until Pipecat is about to run (or start both via `dev-voice.ps1` after Pipecat venv exists).

### 9.4 Pipecat

```powershell
cd packages\pipecat-voice
copy .env.example .env
```

`packages/pipecat-voice/.env` must contain (no vendor API keys):

```env
VOKIT_MEDIA_WS_TOKEN=change-me-media-ws-secret
VOKIT_INTERNAL_TELEPHONY_TOKEN=change-me-internal-telephony-secret
DJANGO_INTERNAL_BASE_URL=http://127.0.0.1:8000
PIPECAT_HOST=0.0.0.0
PIPECAT_PORT=8100
PIPECAT_ALLOWED_ORIGINS=
```

`QDRANT_URL` may stay set; empty disables knowledge retrieve. Inbound speech does not require Qdrant.

Install (from `packages/pipecat-voice/README.md`):

```powershell
uv sync
```

or `pip install -e ".[dev]"` in that package. `scripts/dev-voice.ps1` prefers `packages\pipecat-voice\.venv\Scripts\python.exe`.

---

## 10. Super Admin — product setup (required for a routable DID)

Open **http://127.0.0.1:5173/login** as `platform@vokit.test` / `Phase2-Demo!ok`.

Nav labels below are `packages/web-ui/src/nav.ts` (platform).

### 10.1 Activate Demo Agency A

1. **Agencies** → open **Demo Agency A**.
2. Tab **Status** → **Activate / reactivate** (`POST /api/v1/platform/agencies/{id}/status` with `{ "action": "activate" }`).
3. Confirm status is `active`. Capabilities default includes `purchase_numbers` (`AgencyCapabilities` in `tenancy/domain/lifecycle.py`).

KYC Verified is **not** required to activate or to take a lab inbound call. KYC gates payouts.

### 10.2 Calling flag

Local settings default `LIVE_FLAGS_ENABLED_BY_DEFAULT=true`, so `flags.calling_live` is on unless you turned it off.

**Settings** → **Feature flags** → `flags.calling_live` must be `true`. If it is false, bootstrap returns `calling_not_live` and Asterisk will still Dial edge only when DID-resolve says `routable` — resolve uses the same live flag (`session.py`).

### 10.3 STT / TTS / LLM vendors

**Settings → Providers** can edit (UI group in `features/settings/types.ts`):

- `telephony.stt_provider` — `deepgram` | `elevenlabs` | `cartesia`
- `telephony.tts_provider` — same
- `telephony.llm_provider` — `openai` | `grok` | `anthropic`
- `ai.default_voice` — optional default TTS voice id if the agent has none

Click **Edit**, set the value, fill **reason** (API requires `reason`), save.

**Settings → Providers** also lists encrypted `voice.*.api_key` rows and optional `telephony.*_model`. Secrets show as masked (`has_value`); paste a new key only when rotating. Pick vendors you actually have keys for. Example mix that the Pipecat mapper already supports:

- STT `deepgram`
- TTS `cartesia`
- LLM `openai`

PowerShell (run on Windows; uses CSRF the same way API tests do):

```powershell
$base = "http://127.0.0.1:8000"
$session = New-Object Microsoft.PowerShell.Commands.WebRequestSession
$csrf = (Invoke-RestMethod -Uri "$base/api/v1/auth/csrf" -WebSession $session).data.csrf_token
$headers = @{ "X-CSRFTOKEN" = $csrf; "Content-Type" = "application/json" }
Invoke-RestMethod -Method POST -Uri "$base/api/v1/auth/login" -WebSession $session -Headers $headers -Body '{"email":"platform@vokit.test","password":"Phase2-Demo!ok"}' | Out-Null

function Set-VokitSetting($key, $value) {
  $csrf = (Invoke-RestMethod -Uri "$base/api/v1/auth/csrf" -WebSession $session).data.csrf_token
  $headers = @{ "X-CSRFTOKEN" = $csrf; "Content-Type" = "application/json" }
  $body = @{ key = $key; value = $value; reason = "lab inbound" } | ConvertTo-Json
  Invoke-RestMethod -Method PATCH -Uri "$base/api/v1/platform/settings" -WebSession $session -Headers $headers -Body $body | Out-Null
}

Set-VokitSetting "telephony.stt_provider" "deepgram"
Set-VokitSetting "telephony.tts_provider" "cartesia"
Set-VokitSetting "telephony.llm_provider" "openai"
Set-VokitSetting "voice.deepgram.api_key"  "<YOUR_DEEPGRAM_KEY>"
Set-VokitSetting "voice.cartesia.api_key"  "<YOUR_CARTESIA_KEY>"
Set-VokitSetting "voice.openai.api_key"    "<YOUR_OPENAI_KEY>"
```

GET settings never returns the key (`value` is null, `has_value` true). Empty PATCH for a voice key is rejected.

Prove TTS list (same Super Admin session):

```powershell
Invoke-RestMethod -Uri "$base/api/v1/platform/tts/voices" -WebSession $session
```

Expect HTTP 200 and `{ provider, voices: [{ id, name, language }] }`.  
`503 voice_provider_not_configured` = TTS vendor not set.  
`503 secret_missing` = `voice.{tts}.api_key` not stored.  
`502 provider_unavailable` = vendor HTTP failed (network/key/vendor outage).

Copy one `voices[].id` for the agent `voice_id` (must belong to the **active TTS**).

### 10.4 Plan + minutes

Seeds do **not** create a plan. Publish and DID-resolve both require an active customer subscription (`subscription_required` / `publish_preflight_failed`).

1. **Plans** → create a plan (`POST /api/v1/platform/plans`).
2. Suggested lab terms (same shape as `apps/api/tests/test_voice_api.py`): name `Lab Plan`, `price_minor` `10000`, `included_minutes` `100`, `allow_topups` off, `overage_enabled` off, `grace_seconds` `30`.
3. Open **Customers** → **Demo Customer A** → assign that plan version (`POST /api/v1/platform/customers/{id}/subscription`).  
   Or Plans → Assignment tab (same endpoint via `usePlatformPlans.assignToCustomer`).

Customer seed already **activated** Demo Customer A.

### 10.5 Stock the lab DID

**Numbers** → **Stock number** (`POST /api/v1/platform/phone-numbers`, no `purchase` flag):

| Field | Value |
|---|---|
| E.164 | `+15550001001` |
| Country | `US` |
| Monthly cost (minor) | `100` (or `500` as the form default) |
| Provider | `platform` |

Status should become inventory **available**.

---

## 11. Agency portal — agent + attach the number

Open **http://127.0.0.1:5174/login** as `agency@vokit.test` / `Phase2-Demo!ok`.

### 11.1 Create and configure the agent

1. **Agents** → **Create agent** → **From scratch**.
2. Customer: **Demo Customer A**. Display name e.g. `Lab inbound`.
3. Select the draft → **Configure**.
4. Set:

| Field in `AgencyAgentsScreen` | Value | Notes |
|---|---|---|
| Language | `en` | Required to publish |
| Voice provider | leave blank or anything | **Ignored at runtime.** Platform `telephony.tts_provider` wins |
| Voice id | an id from `GET /api/v1/agency/tts/voices` | Required to publish; must match active TTS |
| Greeting | e.g. `Hello from Vokit.` | Played as welcome |
| Instructions | e.g. `Answer briefly.` | Required to publish (non-empty resolved instructions) |
| Fallback behavior | `hangup` | Allowed: `message`, `transfer`, `hangup` |
| Inbound enabled | **checked** | Otherwise resolve/bootstrap `inbound_disabled` |
| Recording disclosure | **checked** | Required to publish |

Save configuration (`PATCH /api/v1/agency/agents/{id}`).

Optional: from PowerShell after agency login:

```powershell
Invoke-RestMethod -Uri "$base/api/v1/agency/tts/voices" -WebSession $agencySession
```

### 11.2 Publish

Agents → **Publish** tab → **Publish / activate** (`POST /api/v1/agency/agents/{id}/publish`).

If this returns `409 publish_preflight_failed`, read `error.details.failures`. Typical lab misses:

- `subscription_required` — §10.4
- `voice_required` — empty `voice_id` or `language`
- `instructions_required`
- `compliance_required` — recording disclosure not set
- `customer_inactive`

Status must become `active` with a `published_version`. DID-resolve uses `assert_production_routable` (draft/paused/unpublished → `unpublished`).

The **Test** tab (`POST /api/v1/agency/agents/{id}/test-sessions`) is a **text** test session, not the SIP inbound call.

### 11.3 Attach `+15550001001` to the agent

Django routes (tests and `control_plane/telephony/api/urls.py`):

- `GET /api/v1/agency/phone-numbers/search?country=US&capability=voice`
- `POST /api/v1/agency/phone-numbers/reservations` body `{ "number_id", "agent_id" }`
- `POST /api/v1/agency/phone-numbers/assignments` body `{ "reservation_id", "confirm": true }` header **`Idempotency-Key`** (required)

The Agency **Numbers** screen (`AgencyNumbersScreen`) search/reserve/assign UI posts `/reservations` and `/assignments` (same paths as Django). Platform **Stock** UI is also correct. The PowerShell below is optional if you prefer API.

Agency-login PowerShell:

```powershell
$csrf = (Invoke-RestMethod -Uri "$base/api/v1/auth/csrf" -WebSession $session).data.csrf_token
$headers = @{ "X-CSRFTOKEN" = $csrf; "Content-Type" = "application/json" }
Invoke-RestMethod -Method POST -Uri "$base/api/v1/auth/login" -WebSession $session -Headers $headers -Body '{"email":"agency@vokit.test","password":"Phase2-Demo!ok"}' | Out-Null

$search = Invoke-RestMethod -Uri "$base/api/v1/agency/phone-numbers/search?country=US&capability=voice" -WebSession $session
$number = @($search.data.inventory) | Where-Object { $_.e164 -eq "+15550001001" } | Select-Object -First 1
$agents = Invoke-RestMethod -Uri "$base/api/v1/agency/agents" -WebSession $session
$agentId = @($agents.data) | Where-Object { $_.display_name -eq "Lab inbound" } | Select-Object -ExpandProperty id

$csrf = (Invoke-RestMethod -Uri "$base/api/v1/auth/csrf" -WebSession $session).data.csrf_token
$headers = @{ "X-CSRFTOKEN" = $csrf; "Content-Type" = "application/json" }
$reserved = Invoke-RestMethod -Method POST -Uri "$base/api/v1/agency/phone-numbers/reservations" -WebSession $session -Headers $headers -Body (@{ number_id = $number.id; agent_id = $agentId } | ConvertTo-Json)

$csrf = (Invoke-RestMethod -Uri "$base/api/v1/auth/csrf" -WebSession $session).data.csrf_token
$headers = @{ "X-CSRFTOKEN" = $csrf; "Content-Type" = "application/json"; "Idempotency-Key" = "lab-did-1" }
Invoke-RestMethod -Method POST -Uri "$base/api/v1/agency/phone-numbers/assignments" -WebSession $session -Headers $headers -Body (@{ reservation_id = $reserved.data.id; confirm = $true } | ConvertTo-Json)
```

Assignment creates a number invoice. Tests do not require paying it before inbound.

Confirm: agency Agents list shows the E.164 on the agent, and platform/agency numbers status is **assigned**.

### 11.4 Prove DID-resolve **before** installing Asterisk configs

Django still running on `0.0.0.0:8000`. Token = `VOKIT_INTERNAL_TELEPHONY_TOKEN`.

From **Windows**:

```powershell
curl.exe -s -X POST http://127.0.0.1:8000/internal/telephony/v1/did-resolve/ `
  -H "Content-Type: application/json" `
  -H "X-Vokit-Internal-Token: change-me-internal-telephony-secret" `
  -d "{\"did\":\"+15550001001\"}"
```

You need `"routable": true`. `Authorization: Bearer …` is **rejected** (401). Asterisk must use `X-Vokit-Internal-Token`.

From the **VM** (proves firewall + `ALLOWED_HOSTS`, not only localhost):

```bash
curl -s -X POST http://192.168.56.1:8000/internal/telephony/v1/did-resolve/ \
  -H "Content-Type: application/json" \
  -H "X-Vokit-Internal-Token: change-me-internal-telephony-secret" \
  -d '{"did":"+15550001001"}'
```

If the VM curl fails with connection refused or timeout: Django is not on `0.0.0.0:8000`, or §6.1 TCP 8000 is blocked. If HTTP 400 DisallowedHost: Windows host-only IP missing from `DJANGO_ALLOWED_HOSTS`.

If `routable` is false, fix the agency/agent/number/subscription/flag before Asterisk. Common `reason` values from `_admit` in `session.py`: `number_unassigned`, `unpublished`, `inbound_disabled`, `customer_inactive`, `subscription_required`, `calling_not_live` (on bootstrap), `insufficient_minutes`.

---

## 12. Start sip-edge + Pipecat (Windows)

Django + portals already up. From repo root:

```powershell
.\scripts\dev-voice.ps1
```

That script:

1. Starts `packages\vokit-sip-edge\target\release\vokit-sip-edge.exe` if the binary exists (working directory `packages\vokit-sip-edge`).
2. Starts Pipecat: `python -m uvicorn --app-dir src vokit_pipecat_voice.app:app --host 0.0.0.0 --port 8100` in `packages\pipecat-voice`.

If it prints “Build edge first”, run `cargo build --release` in `packages/vokit-sip-edge`.

Health:

```powershell
curl.exe http://127.0.0.1:8090/health
curl.exe http://127.0.0.1:8100/health
```

Both must respond. If edge media URL still points at Django `:8000/sip/media`, inbound AI will not use Pipecat.

From the VM you should **not** need those two URLs. Optional check that Windows is listening on SIP 5071:

```powershell
netstat -an | findstr 5071
```

Expect `UDP 0.0.0.0:5071` (because `SIP_LOCAL_BIND=0.0.0.0:5071`). If you see only `127.0.0.1:5071`, Asterisk Dial from the VM cannot reach edge.

---

## 13. Ubuntu VM — install Asterisk and copy **lab** configs

Use **`deploy/asterisk/lab/`** only. Do **not** copy `deploy/asterisk/pjsip.conf` / `extensions.conf` (those are colocated VPS templates that Dial `127.0.0.1`).

### 13.1 Install packages

SSH into the VM. NAT must work (`ping -c 1 archive.ubuntu.com`).

```bash
sudo apt update
sudo apt install -y asterisk asterisk-modules curl
sudo systemctl enable --now asterisk
sudo systemctl status asterisk --no-pager
```

`asterisk-modules` is required on many Ubuntu versions for `func_curl` / `res_curl`. Without CURL, the dialplan never calls Django.

Confirm modules:

```bash
sudo asterisk -rx "core show function CURL"
sudo asterisk -rx "module show like pjsip"
sudo asterisk -rx "module show like curl"
```

`CURL` must be listed. If `core show function CURL` prints a synopsis, CURL is already loaded — **do not** run `module load`. That command fails when the module is already Running (Asterisk 22 on Ubuntu Resolute stores the `.so` files under a multiarch path, so `ls /usr/lib/asterisk/modules/*curl*` can be empty even when CURL works).

If CURL is **not** listed:

```bash
sudo asterisk -rx "module load res_curl.so"
sudo asterisk -rx "module load func_curl.so"
```

Load `res_curl` first. Exact `.so` names depend on the package. `core show function CURL` is the check that matters.

### 13.2 Stop chan_sip stealing UDP 5060

Ubuntu’s default Asterisk often loads **chan_sip** and **PJSIP**. Both cannot bind `0.0.0.0:5060`. This lab uses **PJSIP only** (`deploy/asterisk/lab/pjsip.conf` `bind=0.0.0.0:5060` and `0.0.0.0:5070`).

```bash
ss -ulnp | grep -E '5060|5070'
sudo asterisk -rx "module show like chan_sip"
```

If `ss` prints nothing and `chan_sip` shows **0 modules loaded**, skip `noload` and go to §13.3. Ubuntu’s default config often has no 5060/5070 bind yet. Those ports appear only after the lab `pjsip.conf` is copied and reloaded.

If `chan_sip` is loaded, add to `/etc/asterisk/modules.conf` under `[modules]`:

```ini
noload => chan_sip.so
```

Then:

```bash
sudo systemctl restart asterisk
ss -ulnp | grep -E '5060|5070'
```

After lab `pjsip.conf` is installed, you want UDP **5060** and **5070** owned by Asterisk (`asterisk` or `res_pjsip`).

### 13.3 Backup Ubuntu defaults, then copy lab files

On the VM:

```bash
sudo cp /etc/asterisk/pjsip.conf /etc/asterisk/pjsip.conf.ubuntu-orig || true
sudo cp /etc/asterisk/extensions.conf /etc/asterisk/extensions.conf.ubuntu-orig || true
sudo cp /etc/asterisk/rtp.conf /etc/asterisk/rtp.conf.ubuntu-orig || true
```

From **Windows** (repo root, your VM username):

```powershell
scp deploy\asterisk\lab\pjsip.conf deploy\asterisk\lab\extensions.conf deploy\asterisk\lab\rtp.conf vokit@192.168.56.100:~/
```

If `scp` is missing, enable **OpenSSH Client** in Windows Optional Features, or copy the three files with a VMware shared folder.

On the VM:

```bash
sudo cp ~/pjsip.conf /etc/asterisk/pjsip.conf
sudo cp ~/extensions.conf /etc/asterisk/extensions.conf
sudo cp ~/rtp.conf /etc/asterisk/rtp.conf
```

Ubuntu’s default `rtp.conf` is **10000–20000** (same range as sip-edge). The lab file is **30000–40000**. Copying the file is not enough: RTP ports are applied at Asterisk start. Confirm then restart:

```bash
grep -E '^rtpstart|^rtpend' /etc/asterisk/rtp.conf
sudo systemctl restart asterisk
sudo asterisk -rx "rtp show settings"
```

You want `rtpstart=30000` and `rtpend=40000`. If settings still show 10000–20000, the copy did not land on `/etc/asterisk/rtp.conf`. If `ufw` is enabled and only allows 30000–40000, a default RTP port such as **18804** is dropped — SIP still answers, audio is silent.

Ubuntu sometimes `#include` extra files from `pjsip.conf`. The lab file is **standalone**. Do not concatenate it with Ubuntu’s sample endpoints.

If `/etc/asterisk/pjsip.d/` or `/etc/asterisk/sip.conf` still defines a 5060 bind, disable those includes. After reload, `pjsip show endpoints` must show `labphone`, `labphone2`, `vokit-edge` from the lab file.

### 13.4 Edit the token on the VM

```bash
sudo nano /etc/asterisk/extensions.conf
```

In `[globals]`:

```ini
DJANGO_RESOLVE_URL=http://192.168.56.1:8000/internal/telephony/v1/did-resolve/
VOKIT_INTERNAL_TOKEN=change-me-internal-telephony-secret
```

Replace `__VOKIT_INTERNAL_TOKEN__` with the **same** value as `apps/api/.env` → `VOKIT_INTERNAL_TELEPHONY_TOKEN`. Do not commit that file back to git.

If your Windows IP is not `192.168.56.1`, change `DJANGO_RESOLVE_URL` and the `Dial(...@WINDOWS_IP:5071)` line, and the matching fields in `pjsip.conf` (§2.1).

Confirm `pjsip.conf` still has:

- `external_media_address=192.168.56.100`
- `external_signaling_address=192.168.56.100`
- `local_net=192.168.56.0/24`
- `contact=sip:192.168.56.1:5071`

Do **not** add `match=192.168.56.1` on `vokit-edge`. MicroSIP and edge share that IP; IP identify steals REGISTER (404). Edge consult INVITEs use `match_header=User-Agent: vokit-sip-edge/0.1`.

Asterisk RTP in `lab/rtp.conf` is **30000–40000**. Edge RTP is **10000–20000**. Do not make them the same range.

### 13.5 Reload and verify from the VM

```bash
sudo asterisk -rx "module reload res_pjsip.so"
sudo asterisk -rx "dialplan reload"
sudo asterisk -rx "pjsip show transports"
sudo asterisk -rx "pjsip show endpoints"
sudo asterisk -rx "rtp show settings"
```

Expect transports on **5060** and **5070**, endpoints `labphone` and `vokit-edge`, RTP **30000–40000**.

VM → Windows Django again:

```bash
curl -s -X POST http://192.168.56.1:8000/internal/telephony/v1/did-resolve/ \
  -H "Content-Type: application/json" \
  -H "X-Vokit-Internal-Token: change-me-internal-telephony-secret" \
  -d '{"did":"+15550001001"}'
```

Must be `"routable": true`.

Live CLI while you call later:

```bash
sudo asterisk -rvvv
```

---

## 14. Softphone (Windows)

`deploy/asterisk/lab/pjsip.conf` + `lab/README.md`:

| Setting | Value |
|---|---|
| SIP user / login | `labphone` |
| Password | `labphone123` |
| Domain / server | `192.168.56.100` (VM) |
| Transport | UDP |
| Local / bind IP | **`192.168.56.1` only** (host-only VMnet1). Not the VMware NAT NIC (`192.168.157.x`). |
| Codec | PCMU / μ-law / `ulaw` only (`allow=ulaw`) |

MicroSIP account fields (all of them — empty Username is the usual 404):

| MicroSIP field | Value |
|---|---|
| SIP server / Domain | `192.168.56.100` |
| Username | `labphone` (not blank, not the IP) |
| Login / Auth username | `labphone` |
| Password | `labphone123` |
| Domain | `192.168.56.100` |
| Transport | UDP |
| SIP proxy / port | leave empty (must hit **5060**, not 5070) |
| Network / bind | `192.168.56.1` (disable or ignore VMnet8 NAT) |

Do **not** register `labphone` and `labphone2` in the same MicroSIP process.

Windows Firewall does not need an extra inbound rule for MicroSIP; the phone is the client. Ubuntu `ufw` must allow UDP 5060 from `192.168.56.0/24` (§6.2).

On the VM:

```bash
sudo asterisk -rx "pjsip show contacts"
```

`labphone` should be Reachable. The contact URI host must be **`192.168.56.1`**, not `192.168.157.x`. If it shows the NAT address, MicroSIP bound the wrong NIC: set bind/local IP to `192.168.56.1`, re-register, check contacts again.

Place the call: dial **`+15550001001`** or **`15550001001`**. Dialplan `[from-carrier]` sends either form into `[vokit-resolve]`.

If SIP answers but you hear nothing and Pipecat logs `Generating TTS` then `silence_timeout`, that is RTP, not the agent. Fix §13.3 `rtp.conf` + Windows UDP 10000–20000 (run the firewall script **as Administrator**) + MicroSIP bind IP, then call again. Optional: `PIPECAT_INBOUND_DIAG=1` on Pipecat echoes caller audio and skips LLM — still silent means RTP.

---

## 15. What a successful call looks like

1. Asterisk CLI (`sudo asterisk -rvvv`): `CURL_RESULT` contains `"routable": true`, then `Dial` to `192.168.56.1:5071`.
2. sip-edge answers, opens WS to `ws://127.0.0.1:8100/sip/media`.
3. Pipecat `POST /internal/telephony/v1/voice-session/bootstrap/` with `X-Vokit-Internal-Token`.
4. Bootstrap `admitted: true` and `providers.stt/tts/llm` have `provider_code` plus `api_key` (internal only).
5. You hear the agent greeting; you can speak; STT/LLM/TTS run.
6. Hang up. Agency **Calls** (`GET /api/v1/agency/calls`) shows a row. Django logs `voice.session.bootstrapped` / `voice.session.ended` (no API keys).

This is lab evidence only. It is not Phase 19 production GO.

---

## 16. Troubleshooting

| Symptom | Check |
|---|---|
| No VMnet1 / Windows not `.1` | Virtual Network Editor; enable VMware Network Adapter VMnet1; §3.2 |
| VM has no `192.168.56.100` | Wrong NIC is static; NAT vs Host-only swapped in netplan — §4 |
| Ping/SSH to VM fails | VM powered on; Host-only connected; Windows ICMPv4 rule; ufw allows 22 — §5–§6 |
| Softphone 404 / CLI `AOR '' not found for endpoint 'vokit-edge'` | Windows MicroSIP and sip-edge share `192.168.56.1`. Lab `pjsip.conf` must **not** `match=` that IP. Recopy `deploy/asterisk/lab/pjsip.conf`, `module reload res_pjsip.so`. Username **and** Domain both set. REGISTER `To:` must be `sip:labphone@192.168.56.100`. Stay in `asterisk -rvvv` to see the packet. |
| Call dies immediately, CLI `NOT routable` | DID-resolve from VM; number **assigned** to published inbound-enabled agent; customer Active + subscription; `calling_live` |
| `401` on DID-resolve | Token mismatch; using `Authorization` instead of `X-Vokit-Internal-Token` |
| `400 DisallowedHost` | Windows host-only IP missing from `DJANGO_ALLOWED_HOSTS` |
| VM curl to `:8000` times out | Django not `0.0.0.0:8000`; Windows TCP 8000 rule; VMnet1 profile Public — §6.1 |
| Dial never reaches edge | Windows firewall UDP 5071; `SIP_LOCAL_BIND=0.0.0.0:5071`; `pjsip.conf` contact IP |
| Edge up, no AI / silence | `SIP_NODE_MEDIA_BASE_URL` must be Pipecat `:8100`; Pipecat `/health`; media tokens equal |
| Bootstrap `admitted` but no speech | Platform `telephony.*_provider` empty or keys missing — Pipecat mapper throws `UnsupportedProviderError` / provider ErrorFrame. Confirm `GET /api/v1/platform/tts/voices` and bootstrap `providers.*.api_key` |
| Call answers, Pipecat speaks TTS, phone is silent / `silence_timeout` | RTP, not the LLM. sip-edge `rtp=192.168.56.100:18804` means Ubuntu default RTP (10000–20000) — recopy `lab/rtp.conf` and **restart** Asterisk (`rtp show settings` must be 30000–40000). `From=…@192.168.157.x` means MicroSIP used the NAT NIC — bind `192.168.56.1`. Windows inbound UDP 10000–20000 from `192.168.56.0/24` must exist (Administrator). Match ufw to the range Asterisk actually binds. |
| `CURL` missing in Asterisk | `apt install asterisk-modules`; `core show function CURL` — §13.1 |
| Agency Numbers **Reserve** fails | Confirm `useAgencyNumbers` posts `/reservations` and `/assignments`; Django has no `/reserve` or `/assign` |
| Settings secret not stored | Providers → vendor card stores `voice.*.api_key` masked; empty PATCH is rejected. Optional script in §10.3 |
| `voice_provider` on the agent | Stored but ignored. TTS vendor is `telephony.tts_provider` only |

---

## 17. Process start order (every reboot)

**VM:** power on the Ubuntu VM first (or in parallel). Confirm `192.168.56.100` and `sudo systemctl status asterisk`.

**Windows:**

1. MySQL + Redis  
2. `.\scripts\dev-stack.ps1` (Django `0.0.0.0:8000` + portals)  
3. Confirm DID-resolve `routable` on Windows **and** from the VM  
4. `.\scripts\dev-voice.ps1` (edge + Pipecat)  
5. `curl` edge `:8090/health` and Pipecat `:8100/health`  
6. MicroSIP registered → dial `+15550001001`

Do not start sip-edge with `SIP_EDGE_CONTROL_URL` empty in Django, and do not point edge media at Django `:8000` for this lab.

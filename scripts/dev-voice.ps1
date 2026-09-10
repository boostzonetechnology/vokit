# Vokit voice lab process list (Windows host + VMware Asterisk)
# Usage (from repo root): .\scripts\dev-voice.ps1
# Tokens MUST match apps/api/.env, packages/vokit-sip-edge/.env, packages/pipecat-voice/.env

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

Write-Host @"
=== Windows processes (this machine) ===
1) Django API          :8000   (.\scripts\dev-stack.ps1 or manage.py runserver)
2) vokit-sip-edge      :5071 SIP + :8090 HTTP control
3) pipecat-voice       :8100 /sip/media

=== VMware Ubuntu Asterisk (lab VM) ===
4) Asterisk            :5060 UDP (+ RTP)
   Config: deploy/asterisk/lab/
   DJANGO_RESOLVE_URL -> http://<WINDOWS_HOST_IP>:8000/internal/telephony/v1/did-resolve/
   Dial edge on Windows :5071 when DID is routable

Required env alignment:
  VOKIT_INTERNAL_TELEPHONY_TOKEN  (Django + Pipecat + Asterisk curl)
  VOKIT_MEDIA_WS_TOKEN            (edge media_token query + Pipecat)
  SIP_EDGE_CONTROL_URL=http://127.0.0.1:8090
  SIP_NODE_MEDIA_BASE_URL=ws://127.0.0.1:8100/sip/media?media_token=...
  SIP_TRUNK_HOST=<VM_IP>  SIP_LOCAL_BIND=0.0.0.0:5071

Firewall: allow UDP 5071 and RTP 10000-20000 from the VM to Windows.
Docs: docs/execution/27-LAB-VOICE-WIRING.md
"@

$EdgeExe = Join-Path $Root "packages\vokit-sip-edge\target\release\vokit-sip-edge.exe"
$PipecatDir = Join-Path $Root "packages\pipecat-voice"

if (Test-Path $EdgeExe) {
  Write-Host "Starting sip-edge ..."
  Start-Process -FilePath $EdgeExe -WorkingDirectory (Join-Path $Root "packages\vokit-sip-edge") `
    -WindowStyle Minimized
} else {
  Write-Host "Build edge first: cargo build --release (in packages/vokit-sip-edge)"
}

$Py = Join-Path $PipecatDir ".venv\Scripts\python.exe"
if (-not (Test-Path $Py)) { $Py = "python" }
if (Test-Path (Join-Path $PipecatDir "pyproject.toml")) {
  Write-Host "Starting Pipecat on :8100 ..."
  Start-Process -FilePath $Py -ArgumentList "-m","uvicorn","app.main:app","--host","0.0.0.0","--port","8100" `
    -WorkingDirectory $PipecatDir -WindowStyle Minimized
} else {
  Write-Host "Pipecat package not ready — see packages/pipecat-voice/README.md"
}

Write-Host "Asterisk remains on the VMware VM — start it there after copying deploy/asterisk/lab."

# Vokit local stack — API + three Vite portals (Windows PowerShell)
# Usage (from repo root):
#   .\scripts\dev-stack.ps1
# Requires: apps/api/.venv, Node, Laragon/MySQL+Redis as needed.

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

$ApiDir = Join-Path $Root "apps\api"
$VenvPython = Join-Path $ApiDir ".venv\Scripts\python.exe"
if (-not (Test-Path $VenvPython)) {
  Write-Error "Missing $VenvPython — create the API venv first."
}

Write-Host "Starting Django API on :8000 ..."
Start-Process -FilePath $VenvPython -ArgumentList "manage.py","runserver","0.0.0.0:8000" `
  -WorkingDirectory $ApiDir -WindowStyle Minimized

function Start-Portal($RelPath, $Port) {
  $Dir = Join-Path $Root $RelPath
  Write-Host "Starting $RelPath on :$Port ..."
  Start-Process -FilePath "npm" -ArgumentList "run","dev","--","--host","0.0.0.0","--port",$Port `
    -WorkingDirectory $Dir -WindowStyle Minimized
}

Start-Portal "apps\web-platform" 5173
Start-Portal "apps\web-agency" 5174
Start-Portal "apps\web-customer" 5175

Write-Host ""
Write-Host "Portals: http://127.0.0.1:5173  http://127.0.0.1:5174  http://127.0.0.1:5175"
Write-Host "API:     http://127.0.0.1:8000/api/v1/health/"
Write-Host "Voice lab (separate): .\scripts\dev-voice.ps1"

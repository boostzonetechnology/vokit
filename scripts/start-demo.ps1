# Vokit local demo: cleanup (if needed) + MySQL/Redis + migrate + seed + servers
# Run from: H:\laragon\www\vokit
#   powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\start-demo.ps1

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
if (-not (Test-Path "$Root\apps\api\manage.py")) {
  $Root = "H:\laragon\www\vokit"
}
$Api = Join-Path $Root "apps\api"
$Py = Join-Path $Api ".venv\Scripts\python.exe"

Write-Host "`n=== Disk space ===" -ForegroundColor Cyan
Get-PSDrive -PSProvider FileSystem | ForEach-Object {
  "{0}: Free={1:N2} GB" -f $_.Name, ($_.Free / 1GB)
}

# Safe cleanup of known large temp trees
$cleanup = @(
  "$env:LOCALAPPDATA\Temp\vokit-old-inspect",
  "$env:LOCALAPPDATA\Temp\pytest-of-cz 3",
  "$env:LOCALAPPDATA\pip\Cache",
  "$Api\.pytest_cache",
  "$Api\.ruff_cache"
)
foreach ($t in $cleanup) {
  if (Test-Path $t) {
    Write-Host "Removing $t"
    Remove-Item -LiteralPath $t -Recurse -Force -ErrorAction SilentlyContinue
  }
}

if (-not (Test-Path $Py)) {
  throw "Missing venv at $Py — run: cd apps\api; python -m venv .venv; .\.venv\Scripts\python.exe -m pip install -e `".[dev]`""
}

# Prefer Docker compose; if Docker unavailable, assume Laragon MySQL/Redis already running
$compose = Join-Path $Root "deploy\compose\docker-compose.yml"
$dockerOk = $false
try {
  docker info 2>$null | Out-Null
  if ($LASTEXITCODE -eq 0) { $dockerOk = $true }
} catch { $dockerOk = $false }

if ($dockerOk) {
  Write-Host "`n=== Starting MySQL + Redis (Docker) ===" -ForegroundColor Cyan
  docker compose -f $compose up -d
  Write-Host "Waiting for MySQL healthy..."
  $deadline = (Get-Date).AddMinutes(2)
  do {
    Start-Sleep -Seconds 3
    $health = docker inspect --format='{{.State.Health.Status}}' (docker compose -f $compose ps -q mysql) 2>$null
    Write-Host "  mysql: $health"
  } while ($health -ne "healthy" -and (Get-Date) -lt $deadline)
} else {
  Write-Host "`n=== Docker not available — using local MySQL/Redis on 127.0.0.1 ===" -ForegroundColor Yellow
}

Push-Location $Api
try {
  Write-Host "`n=== Migrate + seed demo data ===" -ForegroundColor Cyan
  & $Py manage.py migrate
  & $Py manage.py seed_phase2_demo
  & $Py manage.py seed_phase3_tenants
  & $Py manage.py seed_phase4_lifecycle
} finally {
  Pop-Location
}

Write-Host "`n=== Starting API (port 8000) ===" -ForegroundColor Cyan
Start-Process -FilePath $Py -ArgumentList @("manage.py","runserver","0.0.0.0:8000") -WorkingDirectory $Api -WindowStyle Minimized

if (-not (Test-Path (Join-Path $Root "node_modules"))) {
  Write-Host "`n=== npm install (workspaces) ===" -ForegroundColor Cyan
  Push-Location $Root
  npm install
  Pop-Location
}

Write-Host "`n=== Starting React portals ===" -ForegroundColor Cyan
Start-Process powershell -ArgumentList @("-NoProfile","-Command","cd '$Root'; npm run dev:platform") -WindowStyle Minimized
Start-Process powershell -ArgumentList @("-NoProfile","-Command","cd '$Root'; npm run dev:agency") -WindowStyle Minimized
Start-Process powershell -ArgumentList @("-NoProfile","-Command","cd '$Root'; npm run dev:customer") -WindowStyle Minimized

Start-Sleep -Seconds 4
Write-Host "`n=== Health check ===" -ForegroundColor Cyan
try {
  (Invoke-WebRequest -Uri "http://127.0.0.1:8000/health" -UseBasicParsing).Content
} catch {
  Write-Host "API not ready yet: $_" -ForegroundColor Yellow
}

Write-Host @"

Demo ready (password for all: Phase2-Demo!ok)
  platform@vokit.test  -> http://localhost:5173
  agency@vokit.test    -> http://localhost:5174
  customer@vokit.test  -> http://localhost:5175
  API                  -> http://127.0.0.1:8000

"@ -ForegroundColor Green

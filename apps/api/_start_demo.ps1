$ErrorActionPreference = 'Stop'
$out = 'H:\laragon\www\vokit\apps\api\_start_demo_log.txt'
function Log($m) { $line = "$(Get-Date -Format o) $m"; Add-Content -Path $out -Value $line; Write-Host $line }

Remove-Item $out -Force -ErrorAction SilentlyContinue
Log '=== START DEMO ==='

Log '=== DISK ==='
Get-PSDrive -PSProvider FileSystem | ForEach-Object {
  Log ("{0}: Free={1:N2}GB" -f $_.Name, ($_.Free/1GB))
}

Log '=== CLEANUP ==='
@(
  "$env:LOCALAPPDATA\Temp\vokit-old-inspect",
  "$env:LOCALAPPDATA\Temp\pytest-of-cz 3",
  "$env:LOCALAPPDATA\pip\Cache",
  'H:\laragon\www\vokit\apps\api\.pytest_cache',
  'H:\laragon\www\vokit\apps\api\.ruff_cache'
) | ForEach-Object {
  if (Test-Path $_) {
    Log "Removing $_"
    Remove-Item -LiteralPath $_ -Recurse -Force -ErrorAction SilentlyContinue
  }
}

Log '=== DISK AFTER CLEANUP ==='
Get-PSDrive -PSProvider FileSystem | ForEach-Object {
  Log ("{0}: Free={1:N2}GB" -f $_.Name, ($_.Free/1GB))
}

Set-Location 'H:\laragon\www\vokit\apps\api'

# Prefer Docker compose for MySQL+Redis; fall back if Laragon already serves them
Log '=== INFRA ==='
$compose = 'H:\laragon\www\vokit\deploy\compose\docker-compose.yml'
try {
  docker compose -f $compose up -d 2>&1 | ForEach-Object { Log $_ }
} catch {
  Log "docker compose failed: $_"
}

# Wait for MySQL port
for ($i = 0; $i -lt 30; $i++) {
  try {
    $c = Test-NetConnection -ComputerName 127.0.0.1 -Port 3306 -WarningAction SilentlyContinue
    if ($c.TcpTestSucceeded) { Log 'MySQL port 3306 open'; break }
  } catch {}
  Start-Sleep -Seconds 2
}

$py = '.\.venv\Scripts\python.exe'
if (-not (Test-Path $py)) {
  Log 'Creating venv...'
  python -m venv .venv
  & $py -m pip install -e '.[dev]'
}

Log '=== MIGRATE ==='
& $py manage.py migrate 2>&1 | ForEach-Object { Log $_ }

Log '=== SEED ==='
& $py manage.py seed_phase2_demo 2>&1 | ForEach-Object { Log $_ }
& $py manage.py seed_phase3_tenants 2>&1 | ForEach-Object { Log $_ }
& $py manage.py seed_phase4_lifecycle 2>&1 | ForEach-Object { Log $_ }

Log '=== START API ==='
Start-Process -FilePath $py -ArgumentList 'manage.py','runserver','0.0.0.0:8000' -WorkingDirectory 'H:\laragon\www\vokit\apps\api' -WindowStyle Minimized

Set-Location 'H:\laragon\www\vokit'
if (-not (Test-Path 'H:\laragon\www\vokit\node_modules')) {
  Log 'npm install...'
  npm install 2>&1 | ForEach-Object { Log $_ }
}

Log '=== START PORTALS ==='
Start-Process powershell -ArgumentList '-NoProfile','-Command','cd H:\laragon\www\vokit; npm run dev:platform' -WindowStyle Minimized
Start-Process powershell -ArgumentList '-NoProfile','-Command','cd H:\laragon\www\vokit; npm run dev:agency' -WindowStyle Minimized
Start-Process powershell -ArgumentList '-NoProfile','-Command','cd H:\laragon\www\vokit; npm run dev:customer' -WindowStyle Minimized

Start-Sleep -Seconds 5
try {
  $h = Invoke-WebRequest -Uri 'http://127.0.0.1:8000/health' -UseBasicParsing -TimeoutSec 5
  Log ("health status={0} body={1}" -f $h.StatusCode, $h.Content)
} catch { Log "health check failed: $_" }

Log '=== DONE ==='
Log 'API http://127.0.0.1:8000'
Log 'Platform http://localhost:5173'
Log 'Agency http://localhost:5174'
Log 'Customer http://localhost:5175'
Log 'Password Phase2-Demo!ok'
Log 'Users platform@vokit.test agency@vokit.test customer@vokit.test'

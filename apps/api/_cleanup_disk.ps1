$ErrorActionPreference = 'Continue'
Write-Host "=== FREE SPACE BEFORE ==="
Get-PSDrive -PSProvider FileSystem | ForEach-Object {
  "{0}: Free={1:N2} GB Used={2:N2} GB" -f $_.Name, ($_.Free/1GB), ($_.Used/1GB)
}

# Aggressive safe cleanup
$targets = @(
  "$env:LOCALAPPDATA\Temp\vokit-old-inspect",
  "$env:LOCALAPPDATA\Temp\pytest-of-cz 3",
  "$env:LOCALAPPDATA\pip\Cache",
  "H:\laragon\www\vokit\apps\api\.pytest_cache",
  "H:\laragon\www\vokit\apps\api\.ruff_cache"
)
foreach ($t in $targets) {
  if (Test-Path $t) {
    Write-Host "Removing $t"
    Remove-Item -LiteralPath $t -Recurse -Force -ErrorAction SilentlyContinue
  }
}

Get-ChildItem -Path "H:\laragon\www\vokit\apps\api" -Filter __pycache__ -Recurse -Directory -Force -ErrorAction SilentlyContinue |
  Remove-Item -Recurse -Force -ErrorAction SilentlyContinue

# Clear Windows temp leftovers matching vokit/pytest/pip
Get-ChildItem "$env:LOCALAPPDATA\Temp" -ErrorAction SilentlyContinue |
  Where-Object { $_.Name -match '^(pip-|pytest|vokit|tmp|npm-)' } |
  ForEach-Object {
    Remove-Item -LiteralPath $_.FullName -Recurse -Force -ErrorAction SilentlyContinue
  }

Write-Host "=== FREE SPACE AFTER ==="
Get-PSDrive -PSProvider FileSystem | ForEach-Object {
  "{0}: Free={1:N2} GB Used={2:N2} GB" -f $_.Name, ($_.Free/1GB), ($_.Used/1GB)
}

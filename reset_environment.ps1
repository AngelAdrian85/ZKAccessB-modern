# Reset Environment Script
# Creates a backup archive of current virtual environments and key modified files,
# then rebuilds a clean venv, installs dependencies, migrates DB, and launches services.
# Usage: powershell -ExecutionPolicy Bypass -File .\reset_environment.ps1

$ErrorActionPreference = 'Stop'
$ts = (Get-Date).ToString('yyyyMMdd_HHmmss')
$backupRoot = Join-Path $PSScriptRoot 'env_backups'
if (-not (Test-Path $backupRoot)) { New-Item -ItemType Directory -Path $backupRoot | Out-Null }
$archivePath = Join-Path $backupRoot "env_backup_$ts.zip"

Write-Host "[1/7] Archiving existing environment..." -ForegroundColor Cyan
$items = @('.venv','.altvenv','fresh_auto','auto_run.ps1','auto_run_debug.ps1','reset_environment.ps1','zkeco_modern\tray_agent.py','DIAGNOSTICS.md','sitecustomize.py') | Where-Object { Test-Path $_ }
if ($items.Count -gt 0) {
  Try {
    Compress-Archive -Path $items -DestinationPath $archivePath -Force
    Write-Host "Archive created: $archivePath" -ForegroundColor Green
  } Catch {
    Write-Host "Compression failed; falling back to folder copy" -ForegroundColor Yellow
    $fallbackDir = Join-Path $backupRoot "env_backup_$ts"
    New-Item -ItemType Directory -Path $fallbackDir | Out-Null
    foreach ($i in $items) { Copy-Item $i -Destination (Join-Path $fallbackDir (Split-Path $i -Leaf)) -Recurse -Force }
    Write-Host "Fallback backup directory: $fallbackDir" -ForegroundColor Green
  }
} else {
  Write-Host "No existing items to archive." -ForegroundColor Yellow
}

Write-Host "[2/7] Removing old venv directories (without deleting archive)..." -ForegroundColor Cyan
foreach ($d in @('.venv','.altvenv','fresh_auto')) { if (Test-Path $d) { try { Remove-Item -Recurse -Force $d } catch { Write-Host "Could not remove $d" -ForegroundColor Red } } }

Write-Host "[3/7] Creating fresh virtual environment (.venv) ..." -ForegroundColor Cyan
$pyLauncher = Get-Command py -ErrorAction SilentlyContinue
if (-not $pyLauncher) { Write-Host 'Python launcher py not found; install Python 3.' -ForegroundColor Red; exit 1 }
& py -3 -m venv .venv
if (-not (Test-Path '.\.venv\Scripts\python.exe')) { Write-Host 'venv creation failed (python.exe missing).' -ForegroundColor Red; exit 1 }

Write-Host "[4/7] Bootstrapping pip (ensurepip) ..." -ForegroundColor Cyan
& .\.venv\Scripts\python.exe -m ensurepip --upgrade
& .\.venv\Scripts\python.exe -m pip install --upgrade pip

Write-Host "[5/7] Installing project requirements ..." -ForegroundColor Cyan
if (Test-Path '.\requirements.txt') {
  & .\.venv\Scripts\python.exe -m pip install -r .\requirements.txt
} else {
  Write-Host 'requirements.txt missing; skipping dependency install.' -ForegroundColor Yellow
}

Write-Host "[6/7] Running Django migrations ..." -ForegroundColor Cyan
if (Test-Path '.\zkeco_modern\manage.py') {
  & .\.venv\Scripts\python.exe .\zkeco_modern\manage.py migrate --noinput
} else { Write-Host 'manage.py not found; skipping migrations.' -ForegroundColor Yellow }

Write-Host "[7/7] Launching services (CommCenter + server + tray headless) ..." -ForegroundColor Cyan
Start-Process -WindowStyle Hidden .\.venv\Scripts\python.exe -ArgumentList '.\zkeco_modern\manage.py','run_commcenter','--interval','2.0','--driver','auto'
Start-Process -WindowStyle Hidden .\.venv\Scripts\python.exe -ArgumentList '.\zkeco_modern\manage.py','runserver','0.0.0.0:8000'
& .\.venv\Scripts\python.exe .\zkeco_modern\tray_agent.py --headless --auto --run-server --backup-interval=30 --set=server_port=8000

Write-Host "Reset complete. Monitor at http://localhost:8000/agent/monitor" -ForegroundColor Green

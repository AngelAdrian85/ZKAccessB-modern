Param(
  [int]$Port = 8000,
  [string]$Settings = 'zkeco_config.settings',
  [string]$Venv = '.venv_new',
  [switch]$SelfTest,
  [switch]$NoCommCenter,
  [switch]$WSGI
)
# Ensure no stale python/uvicorn/daphne process is already bound to this port
Write-Host "[TRAY] Killing old processes on port $Port (if any)"
try {
  $pids = netstat -ano | Select-String ":$Port" | ForEach-Object { ($_ -split " +")[-1] } | Sort-Object -Unique
  foreach($pid in $pids){
    if($pid -match '^[0-9]+$'){
      try { Stop-Process -Id [int]$pid -Force -ErrorAction SilentlyContinue } catch {}
    }
  }
} catch {}
# Prefer existing .venv if present and target venv python missing
if( (Test-Path '.venv') -and -not (Test-Path "$Venv\Scripts\python.exe") ) { $Venv = '.venv' }
Write-Host "[TRAY] Preparing environment (quiet pip)"
if(!(Test-Path "$Venv\Scripts\python.exe")){
  py -3 -m venv $Venv; if($LASTEXITCODE -ne 0){ Write-Error 'venv failed'; exit 1 }
}
$py = Join-Path $Venv 'Scripts/python.exe'

# Upgrade pip quietly (suppress normal output, keep errors)
Write-Host "[TRAY] Upgrading pip (quiet)"
& $py -m pip install --upgrade pip -q 2> pip_upgrade_errors.log

# Install requirements quietly; capture a minimal summary
Write-Host "[TRAY] Installing requirements (quiet)"
& $py -m pip install -r requirements.txt -q 2> pip_install_errors.log
if($LASTEXITCODE -ne 0){ Write-Warning "pip install reported errors; see pip_install_errors.log" }
Write-Host "[TRAY] Pip install complete"

# Automatic Django migration check & apply
Write-Host "[TRAY] Checking migrations"
$manage = "zkeco_modern/manage.py"
if (Test-Path $manage) {
  Write-Host "[TRAY] Dry-run migration check (makemigrations --dry-run --check)"
  & $py $manage makemigrations --dry-run --check > $null 2> migration_dryrun_errors.log
  if ($LASTEXITCODE -ne 0) {
    Write-Host "[TRAY] Model changes without migrations detected; creating migrations"
    & $py $manage makemigrations 2>> migration_dryrun_errors.log
    if ($LASTEXITCODE -ne 0) { Write-Error "[TRAY] makemigrations (post dry-run) failed"; exit 11 }
  } else {
    Write-Host "[TRAY] Dry-run OK (no new migrations needed)"
  }
  Write-Host "[TRAY] Verifying schema (migrate --check)"
  & $py $manage migrate --check > $null 2> migration_check_errors.log
  if ($LASTEXITCODE -ne 0) {
    Write-Host "[TRAY] Pending migrations detected; applying"
    & $py $manage makemigrations 2> migration_make_errors.log
    if ($LASTEXITCODE -ne 0) { Write-Error "[TRAY] makemigrations failed"; exit 2 }
    & $py $manage migrate 2> migration_run_errors.log
    if ($LASTEXITCODE -ne 0) { Write-Error "[TRAY] migrate failed"; exit 3 }
    Write-Host "[TRAY] Migrations applied successfully"
    Add-Content -Path migration_auto.log -Value ((Get-Date).ToString() + " Applied migrations successfully")
  }
  else {
    Write-Host "[TRAY] No pending migrations"
    Add-Content -Path migration_auto.log -Value ((Get-Date).ToString() + " No migrations needed")
  }
} else {
  Write-Warning "[TRAY] manage.py not found at $manage; skipping migrations"
  Add-Content -Path migration_auto.log -Value ((Get-Date).ToString() + " manage.py missing; skipped migrations")
}

Write-Host "[TRAY] Launching tray agent"
$trayArgs = @()
if($SelfTest){ $trayArgs += '--self-test' }
if($NoCommCenter){ $trayArgs += '--no-commcenter' }
# ASGI only if not explicitly requesting WSGI
if(-not $WSGI){ $trayArgs += '--asgi' }
$trayArgs += @('--driver','auto','--port',"$Port")
& $py zkeco_modern/manage.py tray_agent @trayArgs
if($LASTEXITCODE -ne 0){ Write-Error "[TRAY] tray_agent exited with code $LASTEXITCODE"; exit $LASTEXITCODE }

Param(
  [int]$Port = 8000,
  [string]$Settings = 'zkeco_config.settings',
  [string]$Venv = '.venv_new',
  [switch]$SelfTest,
  [switch]$NoCommCenter,
  [switch]$WSGI
)
# Kill any process bound to desired port or persisted tray port (config file may override)
Write-Host "[TRAY] Killing old processes on port(s) (requested=$Port, config)"
try {
  $configFile = Join-Path 'zkeco_modern' 'zkeco_tray_config.ini'
  $cfgPort = $null
  if(Test-Path $configFile){
    try {
      $raw = Get-Content $configFile -ErrorAction SilentlyContinue | Select-String -Pattern '^port\s*=\s*(\d+)' | ForEach-Object { $_.Matches[0].Groups[1].Value } | Select-Object -First 1
      if($raw){ $cfgPort = [int]$raw }
    } catch {}
  }
  $portsToKill = @($Port)
  if($cfgPort -and ($cfgPort -ne $Port)){ $portsToKill += $cfgPort }
  foreach($p in ($portsToKill | Sort-Object -Unique)){
    Write-Host "[TRAY] Scanning port $p"
    $pids = netstat -ano | Select-String ":$p" | ForEach-Object { ($_ -split " +")[-1] } | Sort-Object -Unique
    foreach($pid in $pids){
      if($pid -match '^[0-9]+$'){
        try { Stop-Process -Id [int]$pid -Force -ErrorAction SilentlyContinue; Write-Host "[TRAY] Killed PID $pid on port $p" } catch {}
      }
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
Write-Host "[TRAY] Collecting static files"
& $py $manage collectstatic --noinput > $null 2> collectstatic_errors.log
if($LASTEXITCODE -ne 0){ Write-Warning "[TRAY] collectstatic reported errors; see collectstatic_errors.log" }
Write-Host "[TRAY] Starting tray agent"
& $py zkeco_modern/manage.py tray_agent @trayArgs
$exitCode = $LASTEXITCODE

# Cleanup after tray agent exits (regardless of exit code)
Write-Host "[TRAY] Tray agent exited with code $exitCode, cleaning up..."
Write-Host "[TRAY] Killing remaining processes on configured ports"
try {
  $conf
  igFile = Join-Path 'zkeco_modern' 'agent_controller.ini'
  $cfgPort = $Port
  if(Test-Path $configFile){
    try {
      $raw = Get-Content $configFile -ErrorAction SilentlyContinue | Select-String -Pattern '^server_port\s*=\s*(\d+)' | ForEach-Object { $_.Matches[0].Groups[1].Value } | Select-Object -First 1
      if($raw){ $cfgPort = [int]$raw }
    } catch {}
  }
  Write-Host "[TRAY] Scanning and killing processes on port $cfgPort"
  $pids = netstat -ano 2>$null | Select-String ":$cfgPort" | ForEach-Object { ($_ -split " +")[-1] } | Sort-Object -Unique
  foreach($pid in $pids){
    if($pid -match '^[0-9]+$'){
      try { 
        taskkill /PID $pid /F /T 2>$null
        Write-Host "[TRAY] Killed PID $pid on port $cfgPort" 
      } catch {}
    }
  }
} catch {}

Write-Host "[TRAY] Cleanup complete"
if($exitCode -ne 0){ Write-Error "[TRAY] tray_agent exited with code $exitCode"; exit $exitCode }

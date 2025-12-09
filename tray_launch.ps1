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

# Start Card Reader Services (ACP & Elatec) if available
Write-Host "[TRAY] Starting card reader services (ACP, Elatec)"
$global:TrayChildPids = @()
function Write-TrayStatusJson {
  param(
    [bool]$AcpOn,
    [bool]$ElatecOn,
    [string]$ServerState
  )
  $status = [ordered]@{
    acp      = if($AcpOn){'ON'}else{'OPRIT'}
    elatec   = if($ElatecOn){'ON'}else{'OPRIT'}
    server   = $ServerState  # PORNESTE | OPRIT | PORNIT
  }
  $color = 'red'
  if($status.acp -eq 'ON' -and $status.elatec -eq 'ON' -and $status.server -eq 'PORNIT'){
    $color = 'green'
  } elseif($status.acp -eq 'ON' -or $status.elatec -eq 'ON' -or $status.server -eq 'PORNIT'){
    $color = 'yellow'
  }
  $status.color = $color
  try {
    $json = $status | ConvertTo-Json -Depth 3
    Set-Content -Path (Join-Path $PWD 'tray_status.json') -Value $json -Encoding UTF8
  } catch {}
}
try {
  # Optional config: scripts/card_readers.json
  $readerCfgPath = Join-Path 'scripts' 'card_readers.json'
  $ReaderCfg = $null
  if (Test-Path $readerCfgPath) {
    try { $ReaderCfg = Get-Content $readerCfgPath -Raw | ConvertFrom-Json } catch {}
  }
  $acpScript = Join-Path 'scripts' 'card_reader_acp.py'
  if (Test-Path $acpScript) {
    $acpEnabled = $true
    $acpPort = '9001'
    if ($ReaderCfg -and $ReaderCfg.acp) {
      if ($ReaderCfg.acp.enabled -eq $false) { $acpEnabled = $false }
      if ($ReaderCfg.acp.port) { $acpPort = [string]$ReaderCfg.acp.port }
    }
    if ($acpEnabled) {
      Write-Host "[TRAY] Starting ACP listener on port $acpPort"
      $p = Start-Process -FilePath $py -ArgumentList $acpScript, $acpPort -PassThru -WindowStyle Minimized
      if ($p) { $global:TrayChildPids += $p.Id }
    } else {
      Write-Host "[TRAY] ACP listener disabled via config"
    }
  }
  $elatecScript = Join-Path 'scripts' 'card_reader_elatec.py'
  if (Test-Path $elatecScript) {
    # Attempt to ensure pyserial is present quietly
    & $py -m pip show pyserial > $null 2> $null
    if ($LASTEXITCODE -ne 0) { & $py -m pip install pyserial -q > $null 2> $null }
    $elatecEnabled = $true
    $elatecPort = 'COM3'
    if ($ReaderCfg -and $ReaderCfg.elatec) {
      if ($ReaderCfg.elatec.enabled -eq $false) { $elatecEnabled = $false }
      if ($ReaderCfg.elatec.port) { $elatecPort = [string]$ReaderCfg.elatec.port }
    }
    # Auto-disable if COM port not present
    try {
      $ports = (Get-CimInstance Win32_SerialPort | Select-Object -ExpandProperty DeviceID) 2> $null
    } catch { $ports = @() }
    if ($elatecEnabled -and (-not $ports -or ($ports -notcontains $elatecPort))) {
      Write-Warning "[TRAY] Elatec port '$elatecPort' not found; disabling Elatec"
      $elatecEnabled = $false
    }
    if ($elatecEnabled) {
      Write-Host "[TRAY] Starting Elatec serial listener on $elatecPort"
      try {
        $p2 = Start-Process -FilePath $py -ArgumentList $elatecScript, $elatecPort -PassThru -WindowStyle Minimized
        if ($p2) { $global:TrayChildPids += $p2.Id }
      } catch {
        Write-Warning "[ELATEC] Failed to start on '$elatecPort': $_"; $elatecEnabled = $false
      }
    } else {
      Write-Host "[TRAY] Elatec listener disabled (no valid port or config)"
    }
  }
} catch {
  Write-Warning "[TRAY] Could not start card reader services: $_"
}

# Initial status: readers based on enable flags, server getting ready
try { Write-TrayStatusJson -AcpOn:$acpEnabled -ElatecOn:$elatecEnabled -ServerState 'PORNESTE' } catch {}

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
  $configFile = Join-Path 'zkeco_modern' 'agent_controller.ini'
  $cfgPort = $Port
  if(Test-Path $configFile){
    try {
      $raw = Get-Content $configFile -ErrorAction SilentlyContinue | Select-String -Pattern '^server_port\s*=\s*(\d+)' | ForEach-Object { $_.Matches[0].Groups[1].Value } | Select-Object -First 1
      if($raw){ $cfgPort = [int]$raw }
    } catch {}
  }
  Write-Host "[TRAY] Scanning and killing processes on port $cfgPort"
  $pids = netstat -ano 2>$null | Select-String ":$cfgPort" | ForEach-Object { ($_ -split " +")[-1] } | Sort-Object -Unique
  # Stop card reader services
  if ($global:TrayChildPids) {
    Write-Host "[TRAY] Stopping card reader services"
    foreach($pid in $global:TrayChildPids){
      try { Stop-Process -Id $pid -Force -ErrorAction SilentlyContinue } catch {}
    }
  }
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
# Final status: readers off, server off after cleanup
try { Write-TrayStatusJson -AcpOn:$false -ElatecOn:$false -ServerState 'OPRIT' } catch {}
# Exit code 15 is normal (user quit); exit codes 1-11 are errors, others are unexpected
if($exitCode -eq 15){
  Write-Host "[TRAY] tray_agent exited normally (exit code 15)"
  exit 0
} elseif($exitCode -gt 0 -and $exitCode -lt 12){
  Write-Error "[TRAY] tray_agent exited with error code $exitCode"
  exit $exitCode
} elseif($exitCode -ne 0){
  Write-Warning "[TRAY] tray_agent exited with unexpected code $exitCode"
  exit 0
}

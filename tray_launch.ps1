Param(
  [int]$Port = 8000,
  [string]$Settings = 'zkeco_config.settings',
  [string]$Venv = '.venv',
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

# Extra cleanup: kill any leftover card reader scripts started outside this session
try {
  Write-Host "[TRAY] Cleaning up leftover card reader listeners"
  $targets = @('card_reader_acp.py','card_reader_elatec.py')
  foreach($name in $targets){
    try {
      Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -like "*$name*" } | ForEach-Object { try { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue } catch {} }
    } catch {}
  }
} catch {}
# Prefer the standard .venv if present; else fallback to .venv_new
if( -not (Test-Path $Venv) ){
  if(Test-Path '.venv') { $Venv = '.venv' }
  elseif(Test-Path '.venv_new') { $Venv = '.venv_new' }
}
Write-Host "[TRAY] Preparing environment (quiet pip)"
if(!(Test-Path "$Venv\Scripts\python.exe")){
  py -3 -m venv $Venv; if($LASTEXITCODE -ne 0){ Write-Error 'venv failed'; exit 1 }
}
$py = Join-Path $Venv 'Scripts/python.exe'

# Ensure virtual environment is activated for the current session
try {
  $activate = Join-Path $Venv 'Scripts/Activate.ps1'
  if (Test-Path $activate) {
    Write-Host "[TRAY] Activating virtual environment: $Venv"
    . $activate
    # Robust activation: set PATH and VIRTUAL_ENV explicitly
    try {
      $env:VIRTUAL_ENV = (Resolve-Path $Venv).Path
      $scriptsPath = (Join-Path (Resolve-Path $Venv).Path 'Scripts')
      if($env:Path -notlike "*$scriptsPath*"){
        $env:Path = "$scriptsPath;" + $env:Path
      }
    } catch {}
    # Guard: kill any non-venv tray_agent/daphne/runserver processes
    try {
      Write-Host "[TRAY] Guarding against non-venv processes"
      $venvPy = Join-Path $scriptsPath 'python.exe'
      $procList = Get-CimInstance Win32_Process
      $toKill = @()
      $workspaceRoot = (Resolve-Path $PWD).Path
      foreach($p in $procList){
        $cmd = $p.CommandLine
        if([string]::IsNullOrEmpty($cmd)){ continue }
        $isAgent = ($cmd -like "*manage.py* tray_agent*")
        $isDaphne = ($cmd -like "*-m daphne*")
        $isRunserver = ($cmd -like "*manage.py* runserver*")
        $isLegacyAgent = ($cmd -like "*zkeco_modern*tray_agent.py*") -or ($cmd -like "* tray_agent.py*")
        if($isAgent -or $isDaphne -or $isRunserver){
          $usesVenv = ($cmd -like "*$venvPy*")
          if(-not $usesVenv){ $toKill += $p.ProcessId }
        }
        # Always kill legacy standalone tray_agent.py started anywhere under this workspace
        if($isLegacyAgent){
          try {
            if($cmd -like "*$workspaceRoot*"){
              $toKill += $p.ProcessId
            }
          } catch {}
        }
      }
      foreach($pid in ($toKill | Sort-Object -Unique)){
        try { Stop-Process -Id $pid -Force -ErrorAction SilentlyContinue; Write-Host "[TRAY] Killed non-venv PID $pid" } catch {}
      }
    } catch {}
  } else {
    Write-Warning "[TRAY] Activate.ps1 not found in $Venv; continuing with direct python path"
  }
} catch {
  Write-Warning "[TRAY] Failed to activate venv: $_"
}

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
    acp_enabled    = $true
    elatec_enabled = $true
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
  # Read existing tray_status.json to respect UI blocked flags
  $trayStatusPath = Join-Path $PWD 'tray_status.json'
  $trayStatus = $null
  if (Test-Path $trayStatusPath) {
    try { $trayStatus = Get-Content $trayStatusPath -Raw | ConvertFrom-Json } catch {}
  }
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
      # Respect UI block flag if present
      if ($trayStatus -and $trayStatus.acp_blocked -eq $true) { Write-Host "[TRAY] ACP start suppressed: acp_blocked flag set"; $acpEnabled = $false } 
      $p = Start-Process -FilePath $py -ArgumentList $acpScript, $acpPort -PassThru -WindowStyle Hidden
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
    $elatecMode = 'serial'
    if ($ReaderCfg -and $ReaderCfg.elatec) {
      if ($ReaderCfg.elatec.enabled -eq $false) { $elatecEnabled = $false }
      if ($ReaderCfg.elatec.port) { $elatecPort = [string]$ReaderCfg.elatec.port }
      if ($ReaderCfg.elatec.mode) { $elatecMode = [string]$ReaderCfg.elatec.mode }
    }
    # Auto-disable if COM port not present (only for non-virtual mode)
    if ($elatecMode -ne 'virtual') {
      try {
        $ports = (Get-CimInstance Win32_SerialPort | Select-Object -ExpandProperty DeviceID) 2> $null
      } catch { $ports = @() }
      if ($elatecEnabled -and (-not $ports -or ($ports -notcontains $elatecPort))) {
        Write-Warning "[TRAY] Elatec port '$elatecPort' not found; disabling Elatec"
        $elatecEnabled = $false
      }
    } else {
      Write-Host "[TRAY] Elatec in virtual mode; skipping COM port check"
    }
    if ($elatecEnabled) {
      if ($elatecMode -eq 'virtual') {
        Write-Host "[TRAY] Starting Elatec virtual listener"
      } else {
        Write-Host "[TRAY] Starting Elatec serial listener on $elatecPort"
      }
      # Respect UI block flag if present
      if ($trayStatus -and $trayStatus.elatec_blocked -eq $true) { Write-Host "[TRAY] Elatec start suppressed: elatec_blocked flag set"; $elatecEnabled = $false }
      try {
        $p2 = Start-Process -FilePath $py -ArgumentList $elatecScript, $elatecPort -PassThru -WindowStyle Hidden
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
try {
  # Persist enabled flags into status for tray_agent to respect
  $statusInit = [ordered]@{
    acp            = if($acpEnabled){'ON'}else{'OPRIT'}
    elatec         = if($elatecEnabled){'ON'}else{'OPRIT'}
    server         = 'PORNESTE'
    acp_enabled    = $acpEnabled
    elatec_enabled = $elatecEnabled
    commcenter     = 'PORNESTE'
  }
  # Color: treat disabled readers as satisfied
  $allReadersOk = (($statusInit.acp_enabled -eq $false) -or ($statusInit.acp -eq 'ON')) -and (($statusInit.elatec_enabled -eq $false) -or ($statusInit.elatec -eq 'ON'))
  $colorInit = if(($statusInit.server -eq 'PORNIT') -and $allReadersOk){ 'green' } elseif(($statusInit.server -eq 'PORNIT') -or $allReadersOk){ 'yellow' } else { 'red' }
  $statusInit.color = $colorInit
  # Preserve any existing blocked flags so UI STOP isn't clobbered
  if ($trayStatus) {
    if ($trayStatus.acp_blocked -eq $true) { $statusInit.acp_blocked = $true }
    if ($trayStatus.elatec_blocked -eq $true) { $statusInit.elatec_blocked = $true }
    if ($trayStatus.cmd_stop_acp -ne $null) { $statusInit.cmd_stop_acp = $trayStatus.cmd_stop_acp }
    if ($trayStatus.cmd_stop_elatec -ne $null) { $statusInit.cmd_stop_elatec = $trayStatus.cmd_stop_elatec }
  }
  Set-Content -Path (Join-Path $PWD 'tray_status.json') -Value ($statusInit | ConvertTo-Json -Depth 3) -Encoding UTF8
} catch {}

# Automatic Django migration check & apply
Write-Host "[TRAY] Checking migrations"
$manage = "zkeco_modern/manage.py"
if (Test-Path $manage) {
  Write-Host "[TRAY] Dry-run migration check (makemigrations --dry-run --check)"
  & $py $manage makemigrations --dry-run --check > $null 2> migration_dryrun_errors.log
  if ($LASTEXITCODE -ne 0) {
    Write-Host "[TRAY] Model changes without migrations detected; attempting to create migrations"
    & $py $manage makemigrations 2>> migration_dryrun_errors.log
    if ($LASTEXITCODE -ne 0) {
      Write-Warning "[TRAY] makemigrations (post dry-run) failed; continuing startup without applying migrations. See migration_dryrun_errors.log"
      Add-Content -Path migration_auto.log -Value ((Get-Date).ToString() + " makemigrations post-dryrun failed; startup continued")
    } else {
      Write-Host "[TRAY] makemigrations generated new migration files"
    }
  } else {
    Write-Host "[TRAY] Dry-run OK (no new migrations needed)"
  }
  Write-Host "[TRAY] Verifying schema (migrate --check)"
  & $py $manage migrate --check > $null 2> migration_check_errors.log
  if ($LASTEXITCODE -ne 0) {
    Write-Host "[TRAY] Pending migrations detected; attempting to apply"
    & $py $manage makemigrations 2> migration_make_errors.log
    if ($LASTEXITCODE -ne 0) {
      Write-Warning "[TRAY] makemigrations failed; skipping automatic migration apply. See migration_make_errors.log"
      Add-Content -Path migration_auto.log -Value ((Get-Date).ToString() + " makemigrations failed; skipped automatic apply")
    } else {
      & $py $manage migrate 2> migration_run_errors.log
      if ($LASTEXITCODE -ne 0) {
        Write-Warning "[TRAY] migrate failed; continuing startup. See migration_run_errors.log"
        Add-Content -Path migration_auto.log -Value ((Get-Date).ToString() + " migrate failed; startup continued")
      } else {
        Write-Host "[TRAY] Migrations applied successfully"
        Add-Content -Path migration_auto.log -Value ((Get-Date).ToString() + " Applied migrations successfully")
      }
    }
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
if(-not $WSGI){ $trayArgs += '--asgi' }
$trayArgs += @('--driver','auto','--port',"$Port")
Write-Host "[TRAY] Collecting static files"
& $py $manage collectstatic --noinput > $null 2> collectstatic_errors.log
if($LASTEXITCODE -ne 0){ Write-Warning "[TRAY] collectstatic reported errors; see collectstatic_errors.log" }
Write-Host "[TRAY] Starting tray agent"
# Run tray_agent in the foreground so actions are visible in terminal
try {
  # Write initial running status before handing off
  $statusRun = [ordered]@{
    acp            = if($acpEnabled){'ON'}else{'OPRIT'}
    elatec         = if($elatecEnabled){'ON'}else{'OPRIT'}
    server         = 'PORNIT'
    acp_enabled    = $acpEnabled
    elatec_enabled = $elatecEnabled
    commcenter     = 'PORNESTE'
  }
  $allReadersOk = (($statusRun.acp_enabled -eq $false) -or ($statusRun.acp -eq 'ON')) -and (($statusRun.elatec_enabled -eq $false) -or ($statusRun.elatec -eq 'ON'))
  $statusRun.color = if(($statusRun.server -eq 'PORNIT') -and $allReadersOk){ 'green' } elseif(($statusRun.server -eq 'PORNIT') -or $allReadersOk){ 'yellow' } else { 'red' }
  # Preserve blocked flags if present so a UI STOP remains effective
  if ($trayStatus) {
    if ($trayStatus.acp_blocked -eq $true) { $statusRun.acp_blocked = $true }
    if ($trayStatus.elatec_blocked -eq $true) { $statusRun.elatec_blocked = $true }
    if ($trayStatus.cmd_stop_acp -ne $null) { $statusRun.cmd_stop_acp = $trayStatus.cmd_stop_acp }
    if ($trayStatus.cmd_stop_elatec -ne $null) { $statusRun.cmd_stop_elatec = $trayStatus.cmd_stop_elatec }
  }
  Set-Content -Path (Join-Path $PWD 'tray_status.json') -Value ($statusRun | ConvertTo-Json -Depth 3) -Encoding UTF8
} catch {}
& $py @('zkeco_modern/manage.py','tray_agent') @trayArgs
 
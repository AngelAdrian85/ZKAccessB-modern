Param(
  [int]$Port = 0,
  [int]$AdmsPort = 0,
  [string]$Settings = 'zkeco_config.settings',
  [string]$Venv = '.venv',
  [string]$WebUser = '',
  [string]$WebPassword = '',
  [switch]$SaveWebCreds,
  [switch]$Detach,
  [switch]$SelfTest,
  [switch]$SelfTestFull,
  [switch]$NoCommCenter,
  [switch]$WSGI
)

# Force Django settings module for this session.
# Legacy installations may have DJANGO_SETTINGS_MODULE=mysite.settings in the system env.
$env:DJANGO_SETTINGS_MODULE = $Settings

# Optional Redis channel layer (recommended for cross-process WebSocket events).
# Safe behavior: only enable if a local Redis is already listening.
function Test-TcpPort {
  param(
    [string]$HostName = '127.0.0.1',
    [int]$Port = 6379,
    [int]$TimeoutMs = 250
  )
  try {
    $client = New-Object System.Net.Sockets.TcpClient
    $iar = $client.BeginConnect($HostName, $Port, $null, $null)
    $ok = $iar.AsyncWaitHandle.WaitOne($TimeoutMs, $false)
    if(-not $ok){ try{ $client.Close() }catch{}; return $false }
    $client.EndConnect($iar)
    try{ $client.Close() }catch{}
    return $true
  } catch {
    try{ if($client){ $client.Close() } }catch{}
    return $false
  }
}

try {
  if((-not $env:REDIS_URL) -or [string]::IsNullOrWhiteSpace([string]$env:REDIS_URL)){
    if(Test-TcpPort -HostName '127.0.0.1' -Port 6379 -TimeoutMs 250){
      $env:REDIS_URL = 'redis://127.0.0.1:6379/0'
      Write-Host "[TRAY] REDIS_URL set ($($env:REDIS_URL)) - WS cross-process enabled"
    } else {
      Write-Host "[TRAY] Redis not detected on 127.0.0.1:6379 - using in-memory Channels (polling fallback still works)"
    }
  } else {
    Write-Host "[TRAY] REDIS_URL already set (keeping existing value)"
  }
} catch {}

# Optional: controller web UI credentials (used only for diagnostics / config scraping).
# NOTE: We do NOT hard-code defaults here; operators can pass -WebUser/-WebPassword and
# optionally persist them to USERPROFILE\zkeco_tray_config.ini via -SaveWebCreds.

# Helper: read/write minimal INI values
function Get-IniValue {
  param(
    [string[]]$Lines,
    [string]$Section,
    [string]$Key
  )
  try {
    $inSec = $false
    foreach($ln in ($Lines | ForEach-Object { [string]$_ })){
      if($ln -match '^\s*\[(.+)\]\s*$'){
        $inSec = ($Matches[1] -ieq $Section)
        continue
      }
      if(-not $inSec){ continue }
      $rx = '^\s*' + [regex]::Escape($Key) + '\s*=\s*(.*)\s*$'
      if($ln -match $rx){
        return [string]($Matches[1])
      }
    }
  } catch {}
  return ''
}

# Determine config file path early (used by multiple sections)
$configFile = $null
try {
  if($env:USERPROFILE){
    $configFile = Join-Path $env:USERPROFILE 'zkeco_tray_config.ini'
  }
} catch { $configFile = $null }

# If -Port was not explicitly passed (0 = sentinel), read port from INI config.
# This ensures that after changing the port via Server Configuration dialog, the
# next tray_launch (without -Port) automatically uses the saved port.
if($Port -eq 0){
  $iniPort = 0
  try {
    if($configFile -and (Test-Path $configFile)){
      $iniPortRaw = Get-IniValue -Lines (Get-Content $configFile -ErrorAction SilentlyContinue) -Section 'tray' -Key 'port'
      if($iniPortRaw){ $iniPort = [int]$iniPortRaw }
    }
  } catch {}
  if($iniPort -gt 0){ $Port = $iniPort; Write-Host "[TRAY] Using port $Port from saved config" }
  else { $Port = 15437; Write-Host "[TRAY] No saved port found, using default 15437" }
}

if($AdmsPort -eq 0){
  $iniAdmsPort = 0
  try {
    if($configFile -and (Test-Path $configFile)){
      $iniAdmsPortRaw = Get-IniValue -Lines (Get-Content $configFile -ErrorAction SilentlyContinue) -Section 'tray' -Key 'adms_port'
      if($iniAdmsPortRaw){ $iniAdmsPort = [int]$iniAdmsPortRaw }
    }
  } catch {}
  if($iniAdmsPort -gt 0){ $AdmsPort = $iniAdmsPort; Write-Host "[TRAY] Using ADMS port $AdmsPort from saved config" }
  else { $AdmsPort = 8091; Write-Host "[TRAY] No saved ADMS port found, using default 8091" }
}

function Get-ConfiguredListenerPorts {
  param(
    [int]$ServerPort,
    [int]$AdmsPort
  )

  $ports = @()
  if($ServerPort -gt 0){ $ports += [int]$ServerPort }
  if($AdmsPort -gt 0){ $ports += [int]$AdmsPort }

  try {
    $readerCfgPath = Join-Path $PWD 'scripts\card_readers.json'
    if(Test-Path $readerCfgPath){
      $readerCfg = Get-Content $readerCfgPath -Raw | ConvertFrom-Json
      if($null -ne $readerCfg -and $null -ne $readerCfg.acp -and $readerCfg.acp.enabled -ne $false -and $null -ne $readerCfg.acp.port){
        $ports += [int]([string]$readerCfg.acp.port)
      }
      if($null -ne $readerCfg -and $null -ne $readerCfg.wiegand -and $readerCfg.wiegand.enabled -ne $false -and $null -ne $readerCfg.wiegand.port){
        $ports += [int]([string]$readerCfg.wiegand.port)
      }
    }
  } catch {}

  return @($ports | Where-Object { $_ -gt 0 } | Sort-Object -Unique)
}

# Load any existing stored web creds
$cfgLines = @()
try {
  if($configFile -and (Test-Path $configFile)){
    try { $cfgLines = Get-Content $configFile -ErrorAction SilentlyContinue } catch { $cfgLines = @() }
  }
} catch { $cfgLines = @() }

$storedWebUser = ''
$storedWebPassword = ''
try {
  if($cfgLines -and $cfgLines.Count -gt 0){
    $storedWebUser = (Get-IniValue -Lines $cfgLines -Section 'controller_web' -Key 'web_user')
    $storedWebPassword = (Get-IniValue -Lines $cfgLines -Section 'controller_web' -Key 'web_password')
  }
} catch {
  $storedWebUser = ''
  $storedWebPassword = ''
}

# Expose to env (for optional tooling) only if not already set.
try {
  if((-not $env:ZKACCESS_WEB_USER) -or [string]::IsNullOrWhiteSpace([string]$env:ZKACCESS_WEB_USER)){
    $wu = [string]$WebUser
    if([string]::IsNullOrWhiteSpace($wu)){ $wu = [string]$storedWebUser }
    if(-not [string]::IsNullOrWhiteSpace($wu)){
      $env:ZKACCESS_WEB_USER = $wu
      Write-Host "[TRAY] ZKACCESS_WEB_USER set (from param/ini)"
    }
  }
} catch {}
try {
  if((-not $env:ZKACCESS_WEB_PASSWORD) -or [string]::IsNullOrWhiteSpace([string]$env:ZKACCESS_WEB_PASSWORD)){
    $wp = [string]$WebPassword
    if([string]::IsNullOrWhiteSpace($wp)){ $wp = [string]$storedWebPassword }
    if(-not [string]::IsNullOrWhiteSpace($wp)){
      $env:ZKACCESS_WEB_PASSWORD = $wp
      Write-Host "[TRAY] ZKACCESS_WEB_PASSWORD set (from param/ini)"
    }
  }
} catch {}

# Default controller communication password/key for plcommpro (passwd=...).
# Only set if missing so operators (or a future Admin UI tab) can override.
if(-not $env:ZKACCESS_DEFAULT_COMM_PASSWORD -or [string]::IsNullOrWhiteSpace([string]$env:ZKACCESS_DEFAULT_COMM_PASSWORD)){
  # TODO (Admin tab): load/save this value from SystemSettings/DB.
  $env:ZKACCESS_DEFAULT_COMM_PASSWORD = 'Zk@123'
  Write-Host "[TRAY] ZKACCESS_DEFAULT_COMM_PASSWORD set (default)"
} else {
  Write-Host "[TRAY] ZKACCESS_DEFAULT_COMM_PASSWORD already set (keeping existing value)"
}
# Kill any process bound to desired port or persisted tray port.
# NOTE: tray_agent persists config to HOME\zkeco_tray_config.ini.
Write-Host "[TRAY] Killing old processes on port(s) (requested=$Port, config)"
try {
  $cfgPort = $null
  if(Test-Path $configFile){
    try {
      $raw = Get-Content $configFile -ErrorAction SilentlyContinue | Select-String -Pattern '^port\s*=\s*(\d+)' | ForEach-Object { $_.Matches[0].Groups[1].Value } | Select-Object -First 1
      if($null -ne $raw){ $cfgPort = [int]$raw }
    } catch {}
  }
  $portsToKill = @(Get-ConfiguredListenerPorts -ServerPort $Port -AdmsPort $AdmsPort)
  if($null -ne $cfgPort -and ($cfgPort -ne $Port)){ $portsToKill += $cfgPort }
  foreach($p in ($portsToKill | Sort-Object -Unique)){
    Write-Host "[TRAY] Scanning port $p"
    $pids = netstat -ano | Select-String ":$p" | ForEach-Object { ($_ -split " +")[-1] } | Sort-Object -Unique
    foreach($proc_id in $pids){
      if($proc_id -match '^[0-9]+$'){
        try { Stop-Process -Id [int]$proc_id -Force -ErrorAction SilentlyContinue; Write-Host "[TRAY] Killed PID $proc_id on port $p" } catch {}
      }
    }
  }
} catch {}

# Ensure tray_agent will use the port/mode requested by this launch.
try {
  if($env:USERPROFILE){
    $cfgPath = Join-Path $env:USERPROFILE 'zkeco_tray_config.ini'
    $mode = if($WSGI){ 'wsgi' } else { 'asgi' }
    $lines = @()
    if(Test-Path $cfgPath){
      try { $lines = Get-Content $cfgPath -ErrorAction SilentlyContinue } catch { $lines = @() }
    }
    # Minimal INI update: ensure [tray] exists, update port and server_mode
    $out = @()
    $inTray = $false
    $seenTray = $false
    $wrotePort = $false
    $wroteAdmsPort = $false
    $wroteMode = $false

    $inWeb = $false
    $seenWeb = $false
    $wroteWebUser = $false
    $wroteWebPassword = $false

    $wantSaveWeb = $false
    try {
      $wantSaveWeb = [bool]$SaveWebCreds
    } catch { $wantSaveWeb = $false }
    $webUserToSave = ''
    $webPasswordToSave = ''
    try {
      $webUserToSave = [string]($WebUser)
      $webPasswordToSave = [string]($WebPassword)
      if([string]::IsNullOrWhiteSpace($webUserToSave)){ $webUserToSave = [string]($env:ZKACCESS_WEB_USER) }
      if([string]::IsNullOrWhiteSpace($webPasswordToSave)){ $webPasswordToSave = [string]($env:ZKACCESS_WEB_PASSWORD) }
    } catch {
      $webUserToSave = ''
      $webPasswordToSave = ''
    }
    foreach($ln in $lines){
      if($ln -match '^\s*\[(.+)\]\s*$'){
        if($inTray -and (-not $wrotePort)) { $out += "port=$Port"; $wrotePort = $true }
        if($inTray -and (-not $wroteAdmsPort)) { $out += "adms_port=$AdmsPort"; $wroteAdmsPort = $true }
        if($inTray -and (-not $wroteMode)) { $out += "server_mode=$mode"; $wroteMode = $true }

        if($inWeb -and $wantSaveWeb){
          if((-not $wroteWebUser) -and (-not [string]::IsNullOrWhiteSpace($webUserToSave))) { $out += "web_user=$webUserToSave"; $wroteWebUser = $true }
          if((-not $wroteWebPassword) -and (-not [string]::IsNullOrWhiteSpace($webPasswordToSave))) { $out += "web_password=$webPasswordToSave"; $wroteWebPassword = $true }
        }
        $section = $Matches[1]
        $inTray = ($section -ieq 'tray')
        if($inTray){ $seenTray = $true }

        $inWeb = ($section -ieq 'controller_web')
        if($inWeb){ $seenWeb = $true }
        $out += $ln
        continue
      }
      if($inTray){
        if($ln -match '^\s*port\s*='){ if(-not $wrotePort){ $out += "port=$Port"; $wrotePort = $true }; continue }
        if($ln -match '^\s*adms_port\s*='){ if(-not $wroteAdmsPort){ $out += "adms_port=$AdmsPort"; $wroteAdmsPort = $true }; continue }
        if($ln -match '^\s*server_mode\s*='){ if(-not $wroteMode){ $out += "server_mode=$mode"; $wroteMode = $true }; continue }
      }

      if($inWeb -and $wantSaveWeb){
        if($ln -match '^\s*web_user\s*='){ if(-not $wroteWebUser -and (-not [string]::IsNullOrWhiteSpace($webUserToSave))){ $out += "web_user=$webUserToSave"; $wroteWebUser = $true }; continue }
        if($ln -match '^\s*web_password\s*='){ if(-not $wroteWebPassword -and (-not [string]::IsNullOrWhiteSpace($webPasswordToSave))){ $out += "web_password=$webPasswordToSave"; $wroteWebPassword = $true }; continue }
      }
      $out += $ln
    }
    if(-not $seenTray){
      $out += ''
      $out += '[tray]'
    }
    if(-not $wrotePort){ $out += "port=$Port" }
    if(-not $wroteAdmsPort){ $out += "adms_port=$AdmsPort" }
    if(-not $wroteMode){ $out += "server_mode=$mode" }

    # Optionally persist controller web creds (diagnostics only)
    if($wantSaveWeb -and ((-not [string]::IsNullOrWhiteSpace($webUserToSave)) -or (-not [string]::IsNullOrWhiteSpace($webPasswordToSave)))){
      if(-not $seenWeb){
        $out += ''
        $out += '[controller_web]'
      }
      if((-not $wroteWebUser) -and (-not [string]::IsNullOrWhiteSpace($webUserToSave))){ $out += "web_user=$webUserToSave" }
      if((-not $wroteWebPassword) -and (-not [string]::IsNullOrWhiteSpace($webPasswordToSave))){ $out += "web_password=$webPasswordToSave" }
    }
    Set-Content -Path $cfgPath -Value $out -Encoding UTF8
    if($wantSaveWeb){
      Write-Host "[TRAY] Persisted tray config (+web creds if provided): port=$Port, adms_port=$AdmsPort, server_mode=$mode ($cfgPath)"
    } else {
      Write-Host "[TRAY] Persisted tray config: port=$Port, adms_port=$AdmsPort, server_mode=$mode ($cfgPath)"
    }
  }
} catch {}

# Extra cleanup: kill any leftover card reader scripts started outside this session
try {
  Write-Host "[TRAY] Cleaning up leftover card reader listeners"
  $targets = @('card_reader_acp.py','card_reader_elatec.py','wiegand_listener.py','zkemkeeper_event_bridge.ps1','zkemkeeper_event_bridge.vbs')
  foreach($name in $targets){
    try {
      Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -like "*$name*" } | ForEach-Object { try { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue } catch {} }
    } catch {}
  }
} catch {}

# Extra cleanup: ensure we don't run duplicate python system/venv processes.
# If multiple tray_agent/daphne/run_commcenter/readers exist, status becomes inconsistent.
try {
  Write-Host "[TRAY] Cleaning up old tray/server/reader processes (any Python)"
  $root = (Resolve-Path $PWD).Path
  $patterns = @(
    '*manage.py* tray_agent*',
    '*manage.py* run_commcenter*',
    '*-m daphne*',
    '*manage.py* runserver*',
    '*card_reader_acp.py*',
    '*card_reader_elatec.py*',
    '*wiegand_listener.py*',
    '*zkemkeeper_event_bridge.ps1*',
    '*zkemkeeper_event_bridge.vbs*'
  )
  $procs = Get-CimInstance Win32_Process | Where-Object {
    try {
      $_.CommandLine -and ($_.CommandLine -like "*$root*")
    } catch { $false }
  }
  $toKill = @()
  foreach($p in $procs){
    foreach($pat in $patterns){
      try {
        if($p.CommandLine -like $pat){ $toKill += $p.ProcessId; break }
      } catch {}
    }
  }
  foreach($pid in ($toKill | Sort-Object -Unique)){
    try { Stop-Process -Id [int]$pid -Force -ErrorAction SilentlyContinue; Write-Host "[TRAY] Killed PID $pid" } catch {}
  }
} catch {}

try {
  Write-Host "[TRAY] Cleaning up old tray_launch shells"
  $root = (Resolve-Path $PWD).Path
  Get-CimInstance Win32_Process | Where-Object {
    try {
      $_.ProcessId -ne $PID -and
      $_.CommandLine -and
      ($_.CommandLine -like '*tray_launch.ps1*') -and
      ($_.CommandLine -like "*$root*")
    } catch {
      $false
    }
  } | ForEach-Object {
    try {
      Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue
      Write-Host "[TRAY] Killed old launcher PID $($_.ProcessId)"
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

function Get-ManagedRuntimeProcesses {
  param(
    [string[]]$RoleFilter = @()
  )

  $venvPy = ''
  try { $venvPy = (Resolve-Path $py).Path } catch {}

  $items = @()
  try {
    foreach($proc in (Get-CimInstance Win32_Process)){
      $cmd = [string]$proc.CommandLine
      if([string]::IsNullOrWhiteSpace($cmd)){ continue }

      $role = ''
      if($cmd -like '*manage.py* tray_agent*'){
        $role = 'tray_agent'
      } elseif($cmd -like '*manage.py* run_commcenter*'){
        $role = 'run_commcenter'
      } elseif(($cmd -like '*-m daphne*') -and ($cmd -like "*-p $Port*")){
        $role = 'daphne'
      } elseif(($cmd -like '*manage.py* runserver*') -and ($cmd -like "*0.0.0.0:$AdmsPort*")){
        $role = 'adms_runserver'
      } elseif($cmd -like '*card_reader_acp.py*'){
        $role = 'card_reader_acp'
      } elseif($cmd -like '*card_reader_elatec.py*'){
        $role = 'card_reader_elatec'
      } elseif($cmd -like '*wiegand_listener.py*'){
        $role = 'wiegand_listener'
      } elseif($cmd -like '*zkemkeeper_event_bridge.ps1*' -or $cmd -like '*zkemkeeper_event_bridge.vbs*'){
        $role = 'zkemkeeper_bridge'
      } elseif(($cmd -like '*zkeco_modern*tray_agent.py*') -or ($cmd -like '* tray_agent.py*')){
        $role = 'tray_agent_legacy'
      }

      if([string]::IsNullOrWhiteSpace($role)){ continue }
      if($RoleFilter.Count -gt 0 -and ($RoleFilter -notcontains $role)){ continue }

      $usesVenv = $false
      try {
        if($venvPy){
          $usesVenv = ($cmd -like "*$venvPy*")
        }
      } catch {}

      $items += [pscustomobject]@{
        ProcessId = [int]$proc.ProcessId
        Role = $role
        UsesVenv = [bool]$usesVenv
        Name = [string]$proc.Name
        CommandLine = $cmd
      }
    }
  } catch {}
  return @($items)
}

function Stop-ManagedRuntimeNonVenv {
  param(
    [string[]]$RoleFilter = @(),
    [int[]]$KeepPids = @()
  )

  foreach($proc in @(Get-ManagedRuntimeProcesses -RoleFilter $RoleFilter)){
    if($KeepPids -contains [int]$proc.ProcessId){ continue }
    if($proc.UsesVenv){ continue }
    try {
      Stop-Process -Id $proc.ProcessId -Force -ErrorAction SilentlyContinue
      Write-Host "[TRAY] Killed non-venv PID $($proc.ProcessId) role=$($proc.Role)"
    } catch {}
  }
}

function Stop-ManagedRuntimeDuplicates {
  param(
    [string[]]$RoleFilter = @(),
    [int[]]$KeepPids = @(),
    [switch]$PreferVenv
  )

  $snapshot = @(Get-ManagedRuntimeProcesses -RoleFilter $RoleFilter)
  foreach($group in @($snapshot | Group-Object Role)){
    $groupItems = @($group.Group | Sort-Object ProcessId -Descending)
    if($groupItems.Count -le 1){ continue }

    $keep = $null
    if($PreferVenv){
      $keep = @($groupItems | Where-Object { $_.UsesVenv } | Select-Object -First 1)
      if($keep.Count -gt 0){ $keep = $keep[0] } else { $keep = $null }
    }
    if($null -eq $keep){
      $keep = $groupItems[0]
    }

    foreach($item in $groupItems){
      if($KeepPids -contains [int]$item.ProcessId){ continue }
      if([int]$item.ProcessId -eq [int]$keep.ProcessId){ continue }
      try {
        Stop-Process -Id $item.ProcessId -Force -ErrorAction SilentlyContinue
        Write-Host "[TRAY] Killed duplicate PID $($item.ProcessId) role=$($item.Role)"
      } catch {}
    }
  }
}

# -----------------------------------------------------------------------------
# QUICK SELF-TEST (non-blocking)
# -----------------------------------------------------------------------------
# Historical note: -SelfTest previously launched tray_agent with --self-test,
# which keeps running and can look like a "hang". To avoid blocking operators,
# -SelfTest is now a quick diagnostic that exits. Use -SelfTestFull to run the
# old long-running behavior.
if($SelfTest -and (-not $SelfTestFull)){
  Write-Host "[TRAY] Quick self-test (no migrations, no tray agent)"

  $manage = "zkeco_modern/manage.py"
  if(-not (Test-Path $manage)){
    Write-Error "[TRAY] manage.py not found at $manage"
    exit 1
  }

  # 1) Basic imports (fast)
  try {
    $importsProc = Start-Process -FilePath $py -ArgumentList @('-c',"import django, channels; import channels_redis; import redis; print('imports:ok')") -NoNewWindow -Wait -PassThru -RedirectStandardOutput 'selftest_imports.log' -RedirectStandardError 'selftest_imports_errors.log'
    if($importsProc.ExitCode -ne 0){ throw "python imports failed" }
  } catch {
    Write-Warning "[TRAY] Python imports check failed (channels_redis/redis). WS will fall back to polling if Redis layer isn't available."
  }

  # 2) Django config check (fast, no migrate)
  try {
    $checkProc = Start-Process -FilePath $py -ArgumentList @($manage,'check',"--settings=$Settings") -NoNewWindow -Wait -PassThru -RedirectStandardOutput 'selftest_django_check.log' -RedirectStandardError 'selftest_django_check_errors.log'
    if($checkProc.ExitCode -ne 0){
      Write-Warning "[TRAY] Django check reported issues (exit=$($checkProc.ExitCode))"
    } else {
      Write-Host "[TRAY] Django check OK"
    }
  } catch {
    Write-Warning "[TRAY] Django check threw: $_"
  }

  # 3) Redis status hint
  try {
    if($env:REDIS_URL){
      Write-Host "[TRAY] REDIS_URL=$($env:REDIS_URL)"
    } else {
      Write-Host "[TRAY] REDIS_URL not set; if Redis runs locally it will be auto-enabled on normal launch"
    }
  } catch {}

  Write-Host "[TRAY] Quick self-test complete"
  exit 0
}

# Optional: configure plcommpro.dll bridge runner
# Preferred modern path: x64 .NET bridge EXE on 64-bit Windows.
# Fallback path: x86 .NET bridge EXE or 32-bit Python 3 bridge runner.

function Resolve-ZkAccessBridgeExe {
  try {
    if($env:ZKACCESS_BRIDGE_EXE -and (Test-Path $env:ZKACCESS_BRIDGE_EXE)){
      return $env:ZKACCESS_BRIDGE_EXE
    }
    # Repo-local default (published output)
    $cand = Join-Path $PWD 'zkeco_modern\agent\bridge_dotnet\PlcommproBridgeRunner\bin\Release\net8.0\win-x86\publish\PlcommproBridgeRunner.exe'
    if(Test-Path $cand){
      return $cand
    }
  } catch {}
  return $null
}

function Resolve-ZkAccessBridgeExeX64 {
  try {
    # Repo-local default (published output)
    $cand = Join-Path $PWD 'zkeco_modern\agent\bridge_dotnet\PlcommproBridgeRunner\bin\Release\net8.0\win-x64\publish\PlcommproBridgeRunner.exe'
    if(Test-Path $cand){
      return $cand
    }
  } catch {}
  return $null
}

function Resolve-StandaloneSdkRoot {
  try {
    $resurseRoot = Join-Path $PWD 'Resurse'
    if(-not (Test-Path $resurseRoot)){
      return $null
    }
    $candidates = Get-ChildItem -Path $resurseRoot -Directory -Filter 'Standalone SDK-*' -ErrorAction SilentlyContinue |
      Sort-Object Name -Descending
    foreach($candidate in $candidates){
      if($candidate -and (Test-Path (Join-Path $candidate.FullName 'SDK'))){
        return $candidate.FullName
      }
    }
  } catch {}
  return $null
}

function Resolve-ZkemkeeperSdkDirX64 {
  try {
    if($env:ZKACCESS_ZKEMKEEPER_SDK_DIR -and (Test-Path $env:ZKACCESS_ZKEMKEEPER_SDK_DIR)){
      return $env:ZKACCESS_ZKEMKEEPER_SDK_DIR
    }
    $resurseRoot = Join-Path $PWD 'Resurse'
    if(Test-Path $resurseRoot){
      $dllMatch = Get-ChildItem -Path $resurseRoot -Recurse -Filter 'zkemkeeper.dll' -ErrorAction SilentlyContinue |
        Where-Object { $_.FullName -match '[\\/](x64|64bits)[\\/]zkemkeeper\.dll$' } |
        Sort-Object FullName |
        Select-Object -First 1
      if($dllMatch){
        return $dllMatch.DirectoryName
      }
    }
  } catch {}
  return $null
}

function Resolve-PlcommproDllX86 {
  try {
    if($env:ZKACCESS_PLCOMMPRO_DLL -and (Test-Path $env:ZKACCESS_PLCOMMPRO_DLL)){
      return $env:ZKACCESS_PLCOMMPRO_DLL
    }
    $sdkRoot = Resolve-StandaloneSdkRoot
    $cands = @(
      $(if($sdkRoot){ Join-Path $sdkRoot 'PullSDK\plcommpro.dll' }),
      (Join-Path $PWD 'Resurse\ZKEUBioAccessSetup\Dependencies\ZKAccess3.5\NewSDK\plcommpro.dll'),
      $(if($sdkRoot){ Join-Path $sdkRoot 'SDK\x86\plcommpro.dll' })
    )
    foreach($c in $cands){
      if($c -and (Test-Path $c)) { return $c }
    }
  } catch {}
  return $null
}

function Resolve-PlcommproDllX64 {
  try {
    if($env:ZKACCESS_PLCOMMPRO_DLL -and (Test-Path $env:ZKACCESS_PLCOMMPRO_DLL)){
      return $env:ZKACCESS_PLCOMMPRO_DLL
    }
    $sdkRoot = Resolve-StandaloneSdkRoot
    $cands = @(
      $(if($sdkRoot){ Join-Path $sdkRoot 'SDK\x64\plcommpro.dll' })
    )
    foreach($c in $cands){
      if($c -and (Test-Path $c)) { return $c }
    }
  } catch {}
  return $null
}

# Optional: prefer x64 SDK bundle by default on this deployment target.
try {
  if(-not $env:ZKACCESS_PLCOMMPRO_ARCH){
    $env:ZKACCESS_PLCOMMPRO_ARCH = 'x64'
    Write-Host "[TRAY] plcommpro arch defaulted to x64"
  }
} catch {}

try {
  if(($env:ZKACCESS_PLCOMMPRO_ARCH -as [string]).ToLower() -eq 'x64'){
    if(-not $env:ZKACCESS_BRIDGE_EXE){
      $bridge64 = Resolve-ZkAccessBridgeExeX64
      if($bridge64){
        $env:ZKACCESS_BRIDGE_EXE = $bridge64
        Write-Host "[TRAY] Bridge runner set (x64 EXE): $bridge64"
      }
    }
    if(-not $env:ZKACCESS_PLCOMMPRO_DLL){
      $dll64 = Resolve-PlcommproDllX64
      if($dll64){
        $env:ZKACCESS_PLCOMMPRO_DLL = $dll64
        Write-Host "[TRAY] plcommpro.dll set (x64): $dll64"
      }
    }
  }
} catch {}

try {
  if(-not $env:ZKACCESS_BRIDGE_EXE){
    $bridgeExe = Resolve-ZkAccessBridgeExeX64
    if(-not $bridgeExe){
      $bridgeExe = Resolve-ZkAccessBridgeExe
    }
    if($bridgeExe){
      $env:ZKACCESS_BRIDGE_EXE = $bridgeExe
      Write-Host "[TRAY] Bridge runner set: $bridgeExe"
    }
  }
} catch {}

try {
  if(-not $env:ZKACCESS_PLCOMMPRO_DLL){
    $dll = Resolve-PlcommproDllX86
    if($dll){
      $env:ZKACCESS_PLCOMMPRO_DLL = $dll
      Write-Host "[TRAY] plcommpro.dll set (x86): $dll"
    }
  }
} catch {}

try {
  if(-not $env:ZKACCESS_ZKEMKEEPER_SDK_DIR){
    $zkemSdk64 = Resolve-ZkemkeeperSdkDirX64
    if(Test-Path $zkemSdk64){
      $env:ZKACCESS_ZKEMKEEPER_SDK_DIR = $zkemSdk64
      Write-Host "[TRAY] zkemkeeper SDK dir set (x64): $zkemSdk64"
    }
  }
} catch {}

try {
  # Controller 22 defaults for the x64 zkemkeeper bridge. These can still be overridden
  # externally, but tray_launch now boots a real integration path by default.
  if(-not $env:ZKACCESS_ZKEMKEEPER_ENABLE){ $env:ZKACCESS_ZKEMKEEPER_ENABLE = '1' }
  if(-not $env:ZKACCESS_ZKEMKEEPER_IP){ $env:ZKACCESS_ZKEMKEEPER_IP = '192.168.1.235' }
  if(-not $env:ZKACCESS_ZKEMKEEPER_PORT){ $env:ZKACCESS_ZKEMKEEPER_PORT = '14370' }
  if(-not $env:ZKACCESS_ZKEMKEEPER_MACHINE){ $env:ZKACCESS_ZKEMKEEPER_MACHINE = '1' }
  if(-not $env:ZKACCESS_ZKEMKEEPER_DEVICE_ID){ $env:ZKACCESS_ZKEMKEEPER_DEVICE_ID = '22' }
  if(-not $env:ZKACCESS_ZKEMKEEPER_DOOR_ID){ $env:ZKACCESS_ZKEMKEEPER_DOOR_ID = '1' }
  if(-not $env:ZKACCESS_ZKEMKEEPER_DOOR_PK){ $env:ZKACCESS_ZKEMKEEPER_DOOR_PK = '27' }
  if(-not $env:ZKACCESS_ZKEMKEEPER_SOURCE){ $env:ZKACCESS_ZKEMKEEPER_SOURCE = 'zkemkeeper-c22' }
  if(-not $env:ZKACCESS_ZKEMKEEPER_AUTOREG){ $env:ZKACCESS_ZKEMKEEPER_AUTOREG = '1' }
  if(-not $env:ZKACCESS_ZKEMKEEPER_ENGINE){ $env:ZKACCESS_ZKEMKEEPER_ENGINE = 'vbs' }
  if((-not $env:ZKACCESS_ZKEMKEEPER_COMM_PASSWORD) -and $env:ZKACCESS_DEFAULT_COMM_PASSWORD){
    $env:ZKACCESS_ZKEMKEEPER_COMM_PASSWORD = [string]$env:ZKACCESS_DEFAULT_COMM_PASSWORD
  }
  if(-not $env:ZKACCESS_ZKEMKEEPER_DUMP_FILE){
    $env:ZKACCESS_ZKEMKEEPER_DUMP_FILE = (Join-Path $PWD 'zkemkeeper_event_dump_controller22.jsonl')
  }
  if(-not $env:ZKACCESS_ICLOCK_CAPTURE_FILE){
    $env:ZKACCESS_ICLOCK_CAPTURE_FILE = (Join-Path $PWD 'iclock_push_capture.jsonl')
    Write-Host "[TRAY] iClock capture file set: $($env:ZKACCESS_ICLOCK_CAPTURE_FILE)"
  }
  if(-not $env:ZKACCESS_ICLOCK_CAPTURE_ALL){
    $env:ZKACCESS_ICLOCK_CAPTURE_ALL = '1'
    Write-Host "[TRAY] iClock capture-all enabled for ADMS debugging"
  }
} catch {}

# If we don't have the EXE bridge, try to locate a Python 32-bit runner.
function Resolve-ZkAccessBridgePython32 {
  try {
    if($env:ZKACCESS_PYBRIDGE -and (Test-Path $env:ZKACCESS_PYBRIDGE)){
      return $env:ZKACCESS_PYBRIDGE
    }

    # Preferred: portable (non-installed) Python 3.x 32-bit shipped/extracted in repo
    try {
      $portable = Join-Path $PWD 'tools\python32\python.exe'
      if(Test-Path $portable){
        return $portable
      }
    } catch {}

    $candidates = @()
    # Common 32-bit installs
    $candidates += @(
      "C:\\Program Files (x86)\\Python311-32\\python.exe",
      "C:\\Program Files (x86)\\Python310-32\\python.exe",
      "C:\\Program Files (x86)\\Python39-32\\python.exe"
    )
    # Per-user installs
    if($env:LocalAppData){
      $candidates += (Get-ChildItem -Path (Join-Path $env:LocalAppData 'Programs\Python') -Filter 'python.exe' -Recurse -ErrorAction SilentlyContinue | ForEach-Object { $_.FullName })
    }
    # System-wide installs
    $candidates += (Get-ChildItem -Path 'C:\\Program Files (x86)' -Filter 'python.exe' -Recurse -ErrorAction SilentlyContinue | ForEach-Object { $_.FullName })

    # De-dupe + exclude legacy ZKAccessB Python 2.6 bundles
    $candidates = $candidates | Where-Object { $_ -and ($_ -notmatch 'ZKTeco\\ZKAccessB\\Python26') -and ($_ -notmatch 'Python26') } | Sort-Object -Unique

    foreach($cand in $candidates){
      try {
        if(-not (Test-Path $cand)) { continue }
        # Validate 32-bit + Python 3
        $out = & $cand -S -c "import struct,sys; print(struct.calcsize('P')*8); print(sys.version_info[0])" 2>$null
        if($LASTEXITCODE -ne 0) { continue }
        $lines = @($out)
        $bits = 0
        $major = 0
        if($lines.Count -ge 1){ $bits = [int]($lines[0]) }
        if($lines.Count -ge 2){ $major = [int]($lines[1]) }
        if($bits -eq 32 -and $major -ge 3){
          return $cand
        }
      } catch {}
    }
  } catch {}
  return $null
}

try {
  if((-not $env:ZKACCESS_BRIDGE_EXE) -and (-not $env:ZKACCESS_PYBRIDGE)){
    $bridgePy = Resolve-ZkAccessBridgePython32
    if($bridgePy){
      $env:ZKACCESS_PYBRIDGE = $bridgePy
      Write-Host "[TRAY] Bridge runner set (Python 32-bit): $bridgePy"
    } else {
      Write-Warning "[TRAY] plcommpro bridge not configured. Hardware ops (plcommpro.dll) unavailable until either ZKACCESS_BRIDGE_EXE (preferred) or ZKACCESS_PYBRIDGE is set."
    }
  }
} catch {}

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
    # Guard: kill any non-venv tray_agent/run_commcenter/daphne/runserver processes
    try {
      Write-Host "[TRAY] Guarding against non-venv processes"
      Stop-ManagedRuntimeNonVenv -RoleFilter @('tray_agent','tray_agent_legacy','run_commcenter','daphne','adms_runserver','card_reader_acp','card_reader_elatec','wiegand_listener')
      Stop-ManagedRuntimeDuplicates -RoleFilter @('tray_agent','tray_agent_legacy','run_commcenter','daphne','adms_runserver','card_reader_acp','card_reader_elatec','wiegand_listener') -PreferVenv
    } catch {}
  } else {
    Write-Warning "[TRAY] Activate.ps1 not found in $Venv; continuing with direct python path"
  }
} catch {
  Write-Warning "[TRAY] Failed to activate venv: $_"
}

# Upgrade pip quietly (suppress normal output, keep stderr in a file)
Write-Host "[TRAY] Upgrading pip (quiet)"
$pipUpgradeProc = Start-Process -FilePath $py -ArgumentList @('-m','pip','install','--upgrade','pip','-q') -NoNewWindow -Wait -PassThru -RedirectStandardOutput 'pip_upgrade_output.log' -RedirectStandardError 'pip_upgrade_errors.log'
if($pipUpgradeProc.ExitCode -ne 0){ Write-Warning "pip upgrade reported errors; see pip_upgrade_errors.log" }

# Install requirements quietly; capture a minimal summary
Write-Host "[TRAY] Installing requirements (quiet)"
$pipInstallProc = Start-Process -FilePath $py -ArgumentList @('-m','pip','install','-r','requirements.txt','-q') -NoNewWindow -Wait -PassThru -RedirectStandardOutput 'pip_install_output.log' -RedirectStandardError 'pip_install_errors.log'
if($pipInstallProc.ExitCode -ne 0){ Write-Warning "pip install reported errors; see pip_install_errors.log" }
Write-Host "[TRAY] Pip install complete"

# Start Card Reader Services (ACP, Elatec, Wiegand) if available
Write-Host "[TRAY] Starting card reader services (ACP, Elatec, Wiegand)"
$global:TrayChildPids = @()
$acpEnabled = $false
$elatecEnabled = $false
$wiegandEnabled = $false

function Get-ReaderProcess {
  param(
    [Parameter(Mandatory=$true)][string]$ScriptName
  )
  try {
    $workspaceRoot = (Resolve-Path $PWD).Path
    return Get-CimInstance Win32_Process | Where-Object {
      try {
        $_.CommandLine -and ($_.CommandLine -like "*${ScriptName}*") -and (($_.CommandLine -like "*$workspaceRoot*") -or ($_.CommandLine -like "*scripts\\${ScriptName}*") -or ($_.CommandLine -like "*scripts/${ScriptName}*"))
      } catch {
        $false
      }
    }
  } catch {
    return @()
  }
}

function Start-ReaderIfNotRunning {
  param(
    [Parameter(Mandatory=$true)][string]$ScriptPath,
    [Parameter(Mandatory=$true)][string[]]$Args,
    [Parameter(Mandatory=$true)][string]$Tag,
    [int]$StartupPort = 0,
    [int]$StartupTimeoutMs = 2500
  )
  try {
    $scriptLeaf = Split-Path $ScriptPath -Leaf
    $running = @(Get-ReaderProcess -ScriptName $scriptLeaf)
    if($running.Count -gt 0){
      Write-Host "[TRAY] ${Tag} already running (count=$($running.Count)); skipping duplicate start"
      return $null
    }
    $argumentList = @()
    foreach($item in @($ScriptPath) + $Args){
      $arg = [string]$item
      if($arg -match '[\s"]'){
        $argumentList += '"' + ($arg -replace '"', '\"') + '"'
      } else {
        $argumentList += $arg
      }
    }
    $p = Start-Process -FilePath $py -ArgumentList $argumentList -PassThru -WindowStyle Hidden -WorkingDirectory $PWD
    Start-Sleep -Milliseconds 300
    try {
      if($p.HasExited){
        Write-Warning "[TRAY] ${Tag} exited immediately with code $($p.ExitCode)"
        return $null
      }
    } catch {}
    if($StartupPort -gt 0){
      $deadline = (Get-Date).AddMilliseconds([math]::Max(500, $StartupTimeoutMs))
      $ready = $false
      while((Get-Date) -lt $deadline){
        if(Test-TcpPort -HostName '127.0.0.1' -Port $StartupPort -TimeoutMs 200){
          $ready = $true
          break
        }
        try {
          if($p.HasExited){ break }
        } catch {}
        Start-Sleep -Milliseconds 200
      }
      if(-not $ready){
        try {
          if($p.HasExited){
            Write-Warning "[TRAY] ${Tag} failed to bind port $StartupPort and exited with code $($p.ExitCode)"
            return $null
          }
        } catch {}
      }
    }
    return $p
  } catch {
    Write-Warning "[TRAY] Failed to start ${Tag}: $_"
    return $null
  }
}

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
  Merge-TrayStatusFields -Target $status -Updates (Get-ZkemkeeperTrayFields)
  try {
    $json = $status | ConvertTo-Json -Depth 3
    Set-Content -Path (Join-Path $PWD 'tray_status.json') -Value $json -Encoding UTF8
  } catch {}
}

function Merge-TrayStatusFields {
  param(
    $Target,
    $Updates
  )
  if ($null -eq $Target -or $null -eq $Updates) { return }
  if ($Updates -is [System.Collections.IDictionary]) {
    foreach ($entry in $Updates.GetEnumerator()) {
      $Target[$entry.Key] = $entry.Value
    }
    return
  }
  foreach ($prop in $Updates.PSObject.Properties) {
    $Target[$prop.Name] = $prop.Value
  }
}

function Get-ZkemkeeperTrayFields {
  $enabled = $false
  try {
    $enabledRaw = [string]($env:ZKACCESS_ZKEMKEEPER_ENABLE)
    $enabled = $enabledRaw -and $enabledRaw.ToLower() -in @('1','true','yes','on')
  } catch {}
  $ip = [string]($env:ZKACCESS_ZKEMKEEPER_IP)
  $port = [string]($env:ZKACCESS_ZKEMKEEPER_PORT)
  if([string]::IsNullOrWhiteSpace($port)){ $port = '14370' }
  $status = if($enabled){ 'PORNESTE' } else { 'OPRIT' }
  [ordered]@{
    zkemkeeper_enabled = $enabled
    zkemkeeper = $status
    zkemkeeper_target = if([string]::IsNullOrWhiteSpace($ip)){ '' } else { "${ip}:$port" }
    zkemkeeper_device_id = [string]($env:ZKACCESS_ZKEMKEEPER_DEVICE_ID)
    zkemkeeper_door_id = [string]($env:ZKACCESS_ZKEMKEEPER_DOOR_ID)
    zkemkeeper_door_pk = [string]($env:ZKACCESS_ZKEMKEEPER_DOOR_PK)
    zkemkeeper_dump_file = [string]($env:ZKACCESS_ZKEMKEEPER_DUMP_FILE)
    zkemkeeper_registration = 'PENDING'
  }
}

function Update-TrayStatusFields {
  param($Updates)
  try {
    $trayStatusPath = Join-Path $PWD 'tray_status.json'
    $current = [ordered]@{}
    if (Test-Path $trayStatusPath) {
      try {
        $loaded = Get-Content $trayStatusPath -Raw | ConvertFrom-Json
        if ($loaded) {
          foreach ($prop in $loaded.PSObject.Properties) {
            $current[$prop.Name] = $prop.Value
          }
        }
      } catch {}
    }
    if ($Updates -is [System.Collections.IDictionary]) {
      foreach ($entry in $Updates.GetEnumerator()) {
        $current[$entry.Key] = $entry.Value
      }
    } elseif ($Updates) {
      foreach ($entry in $Updates.GetEnumerator()) {
        $current[$entry.Key] = $entry.Value
      }
    }
    Set-Content -Path $trayStatusPath -Value ($current | ConvertTo-Json -Depth 6) -Encoding UTF8
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
    if ($null -ne $ReaderCfg -and $null -ne $ReaderCfg.acp) {
      if ($ReaderCfg.acp.enabled -eq $false) { $acpEnabled = $false }
      if ($null -ne $ReaderCfg.acp.port) { $acpPort = [string]$ReaderCfg.acp.port }
    }
    
    if ($acpEnabled) {
      Write-Host "[TRAY] Starting ACP listener on port $acpPort"
      # Respect UI block flag if present
      if ($null -ne $trayStatus -and $trayStatus.acp_blocked -eq $true) {
        Write-Host "[TRAY] ACP start suppressed: acp_blocked flag set"
        $acpEnabled = $false
      }
      if($acpEnabled){
        $p = Start-ReaderIfNotRunning -ScriptPath $acpScript -Args @($acpPort) -Tag 'ACP listener' -StartupPort ([int]$acpPort)
        if ($p) { $global:TrayChildPids += $p.Id }
      }
    } else {
      Write-Host "[TRAY] ACP listener disabled via config"
    }
  }
  $elatecScript = Join-Path 'scripts' 'card_reader_elatec.py'
  if (Test-Path $elatecScript) {
    # Attempt to ensure pyserial is present quietly
    $pyserialShowProc = Start-Process -FilePath $py -ArgumentList @('-m','pip','show','pyserial') -NoNewWindow -Wait -PassThru -RedirectStandardOutput 'pyserial_show.log' -RedirectStandardError 'pyserial_show_errors.log'
    if ($pyserialShowProc.ExitCode -ne 0) {
      $pyserialInstallProc = Start-Process -FilePath $py -ArgumentList @('-m','pip','install','pyserial','-q') -NoNewWindow -Wait -PassThru -RedirectStandardOutput 'pyserial_install.log' -RedirectStandardError 'pyserial_install_errors.log'
      if($pyserialInstallProc.ExitCode -ne 0){
        Write-Warning "[TRAY] pyserial install reported errors; see pyserial_install_errors.log"
      }
    }
    $elatecEnabled = $true
    $elatecPort = 'COM3'
    $elatecMode = 'serial'
    if ($null -ne $ReaderCfg -and $null -ne $ReaderCfg.elatec) {
      if ($ReaderCfg.elatec.enabled -eq $false) { $elatecEnabled = $false }
      if ($null -ne $ReaderCfg.elatec.port) { $elatecPort = [string]$ReaderCfg.elatec.port }
      if ($null -ne $ReaderCfg.elatec.mode) { $elatecMode = [string]$ReaderCfg.elatec.mode }
    }
    # Warn if COM port not present (only for non-virtual mode), but keep listener enabled.
    # Elatec must still start as an independent reader service and may recover later.
    if ($elatecMode -ne 'virtual') {
      try {
        $ports = (Get-CimInstance Win32_SerialPort | Select-Object -ExpandProperty DeviceID) 2> $null
      } catch { $ports = @() }
      if ($elatecEnabled -and ($null -eq $ports -or ($ports -notcontains $elatecPort))) {
        Write-Warning "[TRAY] Elatec port '$elatecPort' not found; starting listener anyway (independent reader mode)"
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
      if ($null -ne $trayStatus -and $trayStatus.elatec_blocked -eq $true) {
        Write-Host "[TRAY] Elatec start suppressed: elatec_blocked flag set"
        $elatecEnabled = $false
      }
      if($elatecEnabled){
        $p2 = Start-ReaderIfNotRunning -ScriptPath $elatecScript -Args @($elatecPort) -Tag 'Elatec listener'
        if ($p2) {
          $global:TrayChildPids += $p2.Id
        } else {
          $elatecEnabled = $false
        }
      }
    } else {
      Write-Host "[TRAY] Elatec listener disabled (no valid port or config)"
    }
  }
  $wiegandScript = Join-Path 'scripts' 'wiegand_listener.py'
  if (Test-Path $wiegandScript) {
    $wiegandEnabled = $true
    $wiegandHost = '0.0.0.0'
    $wiegandPort = '9002'
    $wiegandFormatName = 'Wiegand 26'
    $wiegandFormatId = ''
    $wiegandDeviceId = ''
    $wiegandDoorId = ''
    $wiegandDoorPk = ''
    $wiegandSource = 'w26-hardware-tap'
    if ($null -ne $ReaderCfg -and $null -ne $ReaderCfg.wiegand) {
      if ($ReaderCfg.wiegand.enabled -eq $false) { $wiegandEnabled = $false }
      if ($null -ne $ReaderCfg.wiegand.listen_host) { $wiegandHost = [string]$ReaderCfg.wiegand.listen_host }
      if ($null -ne $ReaderCfg.wiegand.port) { $wiegandPort = [string]$ReaderCfg.wiegand.port }
      if ($null -ne $ReaderCfg.wiegand.format_name) { $wiegandFormatName = [string]$ReaderCfg.wiegand.format_name }
      if ($null -ne $ReaderCfg.wiegand.format_id) { $wiegandFormatId = [string]$ReaderCfg.wiegand.format_id }
      if ($null -ne $ReaderCfg.wiegand.device_id) { $wiegandDeviceId = [string]$ReaderCfg.wiegand.device_id }
      if ($null -ne $ReaderCfg.wiegand.door_id) { $wiegandDoorId = [string]$ReaderCfg.wiegand.door_id }
      if ($null -ne $ReaderCfg.wiegand.door_pk) { $wiegandDoorPk = [string]$ReaderCfg.wiegand.door_pk }
      if ($null -ne $ReaderCfg.wiegand.source) { $wiegandSource = [string]$ReaderCfg.wiegand.source }
    }
    if ([string]::IsNullOrWhiteSpace($wiegandDeviceId) -and $null -ne $ReaderCfg -and $null -ne $ReaderCfg.acp -and $null -ne $ReaderCfg.acp.device_id) { $wiegandDeviceId = [string]$ReaderCfg.acp.device_id }
    if ([string]::IsNullOrWhiteSpace($wiegandDoorId) -and $null -ne $ReaderCfg -and $null -ne $ReaderCfg.acp -and $null -ne $ReaderCfg.acp.door_id) { $wiegandDoorId = [string]$ReaderCfg.acp.door_id }
    if ([string]::IsNullOrWhiteSpace($wiegandDoorPk) -and $null -ne $ReaderCfg -and $null -ne $ReaderCfg.acp -and $null -ne $ReaderCfg.acp.door_pk) { $wiegandDoorPk = [string]$ReaderCfg.acp.door_pk }
    if ($wiegandEnabled) {
      Write-Host "[TRAY] Starting Wiegand listener on $wiegandHost`:$wiegandPort"
      if ($null -ne $trayStatus -and $trayStatus.wiegand_blocked -eq $true) {
        Write-Host "[TRAY] Wiegand start suppressed: wiegand_blocked flag set"
        $wiegandEnabled = $false
      }
      if($wiegandEnabled){
        $wgArgs = @('--server-url', "http://127.0.0.1:$Port", '--listen-host', $wiegandHost, '--listen-port', $wiegandPort, '--source', $wiegandSource)
        if (-not [string]::IsNullOrWhiteSpace($wiegandFormatName)) { $wgArgs += @('--format-name', $wiegandFormatName) }
        if (-not [string]::IsNullOrWhiteSpace($wiegandFormatId)) { $wgArgs += @('--format-id', $wiegandFormatId) }
        if (-not [string]::IsNullOrWhiteSpace($wiegandDeviceId)) { $wgArgs += @('--device-id', $wiegandDeviceId) }
        if (-not [string]::IsNullOrWhiteSpace($wiegandDoorId)) { $wgArgs += @('--door-id', $wiegandDoorId) }
        if (-not [string]::IsNullOrWhiteSpace($wiegandDoorPk)) { $wgArgs += @('--door-pk', $wiegandDoorPk) }
        $p3 = Start-ReaderIfNotRunning -ScriptPath $wiegandScript -Args $wgArgs -Tag 'Wiegand listener' -StartupPort ([int]$wiegandPort)
        if ($p3) {
          $global:TrayChildPids += $p3.Id
        } else {
          $wiegandEnabled = $false
        }
      }
    } else {
      Write-Host "[TRAY] Wiegand listener disabled via config"
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
    wiegand        = if($wiegandEnabled){'ON'}else{'OPRIT'}
    server         = 'PORNESTE'
    acp_enabled    = $acpEnabled
    elatec_enabled = $elatecEnabled
    wiegand_enabled = $wiegandEnabled
    commcenter     = 'PORNESTE'
    commcenter_driver  = 'auto'
  }
  # Color: treat disabled readers as satisfied
  $allReadersOk = (($statusInit.acp_enabled -eq $false) -or ($statusInit.acp -eq 'ON')) -and (($statusInit.elatec_enabled -eq $false) -or ($statusInit.elatec -eq 'ON')) -and (($statusInit.wiegand_enabled -eq $false) -or ($statusInit.wiegand -eq 'ON'))
  $colorInit = if(($statusInit.server -eq 'PORNIT') -and $allReadersOk){ 'green' } elseif(($statusInit.server -eq 'PORNIT') -or $allReadersOk){ 'yellow' } else { 'red' }
  $statusInit.color = $colorInit
  Merge-TrayStatusFields -Target $statusInit -Updates (Get-ZkemkeeperTrayFields)
  # Preserve any existing blocked flags so UI STOP isn't clobbered
  if ($trayStatus) {
    if ($true -eq $trayStatus.acp_blocked) { $statusInit.acp_blocked = $true }
    if ($true -eq $trayStatus.elatec_blocked) { $statusInit.elatec_blocked = $true }
    if ($true -eq $trayStatus.wiegand_blocked) { $statusInit.wiegand_blocked = $true }
    if (($trayStatus.cmd_stop_acp | Measure-Object).Count -gt 0) { $statusInit.cmd_stop_acp = $trayStatus.cmd_stop_acp }
    if (($trayStatus.cmd_stop_elatec | Measure-Object).Count -gt 0) { $statusInit.cmd_stop_elatec = $trayStatus.cmd_stop_elatec }
    if (($trayStatus.cmd_stop_wiegand | Measure-Object).Count -gt 0) { $statusInit.cmd_stop_wiegand = $trayStatus.cmd_stop_wiegand }
  }
  Set-Content -Path (Join-Path $PWD 'tray_status.json') -Value ($statusInit | ConvertTo-Json -Depth 3) -Encoding UTF8
} catch {}

# Automatic Django migration check & apply
Write-Host "[TRAY] Checking migrations"
$manage = "zkeco_modern/manage.py"
if (Test-Path $manage) {
  # IMPORTANT: Do NOT auto-generate migrations in an automatic startup script.
  # This script should only apply existing migrations.
  Write-Host "[TRAY] Applying migrations (migrate --noinput)"
  $migrateOut = Join-Path $PWD 'migration_run.log'
  $migrateErr = Join-Path $PWD 'migration_run_errors.log'
  try {
    $migrateProc = Start-Process -FilePath $py -ArgumentList @($manage,'migrate','--noinput',"--settings=$Settings") -NoNewWindow -Wait -PassThru -RedirectStandardOutput $migrateOut -RedirectStandardError $migrateErr
  } catch {
    Write-Error "[TRAY] migrate threw an exception: $_"
    Add-Content -Path migration_auto.log -Value ((Get-Date).ToString() + " migrate exception; startup aborted")
    exit 1
  }
  if ($migrateProc.ExitCode -ne 0) {
    Write-Error "[TRAY] migrate failed (exit=$($migrateProc.ExitCode)). See migration_run_errors.log"
    Add-Content -Path migration_auto.log -Value ((Get-Date).ToString() + " migrate failed; startup aborted")
    exit 1
  }
  Write-Host "[TRAY] Migrations OK"
  Add-Content -Path migration_auto.log -Value ((Get-Date).ToString() + " Migrations OK")
} else {
  Write-Warning "[TRAY] manage.py not found at $manage; skipping migrations"
  Add-Content -Path migration_auto.log -Value ((Get-Date).ToString() + " manage.py missing; skipped migrations")
}

# Best-effort: allow inbound UI and ADMS/iClock push to the configured ports.
# (Requires admin; failures are non-fatal.)
try {
  foreach($rule in @(
    @{ Name = "ZKAccessB UI Port $Port"; LocalPort = $Port },
    @{ Name = "ZKAccessB ADMS Port $AdmsPort"; LocalPort = $AdmsPort }
  )){
    $existing = $null
    try { $existing = Get-NetFirewallRule -DisplayName $rule.Name -ErrorAction SilentlyContinue } catch { $existing = $null }
    if(-not $existing){
      try {
        New-NetFirewallRule -DisplayName $rule.Name -Direction Inbound -Action Allow -Protocol TCP -LocalPort $rule.LocalPort -Profile Any -ErrorAction SilentlyContinue | Out-Null
        Write-Host "[TRAY] Firewall rule added: $($rule.Name)"
      } catch {
        Write-Warning "[TRAY] Could not add firewall rule (needs admin): $_"
      }
    }
  }
} catch {}

Write-Host "[TRAY] Launching tray agent"
$trayArgs = @()
if($SelfTestFull){ $trayArgs += '--self-test' }
if($NoCommCenter){ $trayArgs += '--no-commcenter' }
if(-not $WSGI){ $trayArgs += '--asgi' }
$commDriver = ''
try { $commDriver = [string]($env:ZKACCESS_COMMCENTER_DRIVER) } catch { $commDriver = '' }
if([string]::IsNullOrWhiteSpace($commDriver)){ $commDriver = 'auto' }
Write-Host "[TRAY] CommCenter driver: $commDriver"
$trayArgs += @('--driver',"$commDriver",'--port',"$Port")
$trayArgs += @('--adms-port',"$AdmsPort")
Write-Host "[TRAY] Collecting static files"
$collectstaticProc = Start-Process -FilePath $py -ArgumentList @($manage,'collectstatic','--noinput',"--settings=$Settings") -NoNewWindow -Wait -PassThru -RedirectStandardOutput 'collectstatic_output.log' -RedirectStandardError 'collectstatic_errors.log'
if($collectstaticProc.ExitCode -ne 0){ Write-Warning "[TRAY] collectstatic reported errors; see collectstatic_errors.log" }
Write-Host "[TRAY] Starting tray agent"
# Run tray_agent detached so it keeps running even if this launcher session ends.
try {
  # Keep ADMS auto-config in sync with the dedicated push port.
  $env:ZKACCESS_ADMS_PORT = [string]$AdmsPort
} catch {}

try {
  # Write initial running status before handing off
  $statusRun = [ordered]@{
    acp            = if($acpEnabled){'ON'}else{'OPRIT'}
    elatec         = if($elatecEnabled){'ON'}else{'OPRIT'}
    wiegand        = if($wiegandEnabled){'ON'}else{'OPRIT'}
    server         = 'PORNIT'
    acp_enabled    = $acpEnabled
    elatec_enabled = $elatecEnabled
    wiegand_enabled = $wiegandEnabled
    commcenter     = 'PORNESTE'
    commcenter_driver  = 'auto'
  }
  $allReadersOk = (($statusRun.acp_enabled -eq $false) -or ($statusRun.acp -eq 'ON')) -and (($statusRun.elatec_enabled -eq $false) -or ($statusRun.elatec -eq 'ON')) -and (($statusRun.wiegand_enabled -eq $false) -or ($statusRun.wiegand -eq 'ON'))
  $statusRun.color = if(($statusRun.server -eq 'PORNIT') -and $allReadersOk){ 'green' } elseif(($statusRun.server -eq 'PORNIT') -or $allReadersOk){ 'yellow' } else { 'red' }
  Merge-TrayStatusFields -Target $statusRun -Updates (Get-ZkemkeeperTrayFields)
  # Preserve blocked flags if present so a UI STOP remains effective
  if ($trayStatus) {
    if ($true -eq $trayStatus.acp_blocked) { $statusRun.acp_blocked = $true }
    if ($true -eq $trayStatus.elatec_blocked) { $statusRun.elatec_blocked = $true }
    if ($true -eq $trayStatus.wiegand_blocked) { $statusRun.wiegand_blocked = $true }
    if (($trayStatus.cmd_stop_acp | Measure-Object).Count -gt 0) { $statusRun.cmd_stop_acp = $trayStatus.cmd_stop_acp }
    if (($trayStatus.cmd_stop_elatec | Measure-Object).Count -gt 0) { $statusRun.cmd_stop_elatec = $trayStatus.cmd_stop_elatec }
    if (($trayStatus.cmd_stop_wiegand | Measure-Object).Count -gt 0) { $statusRun.cmd_stop_wiegand = $trayStatus.cmd_stop_wiegand }
  }
  Set-Content -Path (Join-Path $PWD 'tray_status.json') -Value ($statusRun | ConvertTo-Json -Depth 3) -Encoding UTF8
} catch {}

try {
  $selfPid = $PID
  $existingTray = Get-CimInstance Win32_Process | Where-Object {
    try {
      $_.ProcessId -ne $selfPid -and $_.CommandLine -and ($_.CommandLine -like '*manage.py* tray_agent*')
    } catch {
      $false
    }
  }
  foreach($proc in $existingTray){
    try {
      Stop-Process -Id $proc.ProcessId -Force -ErrorAction SilentlyContinue
      Write-Host "[TRAY] Stopped previous tray_agent PID $($proc.ProcessId)"
    } catch {}
  }
} catch {
  Write-Warning "[TRAY] Could not pre-clean tray_agent processes: $_"
}

$trayHealthy = $false

try {
  $stdout = Join-Path $PWD 'tray_agent_stdout.log'
  $stderr = Join-Path $PWD 'tray_agent_stderr.log'
  $argList = @('zkeco_modern/manage.py','tray_agent',"--settings=$Settings") + $trayArgs
  if($Detach){
    $argList += '--headless'
    $trayProc = Start-Process -FilePath $py -ArgumentList $argList -WindowStyle Hidden -RedirectStandardOutput $stdout -RedirectStandardError $stderr -PassThru
    Write-Host "[TRAY] tray_agent launched (detached)"
    Write-Host "[TRAY] Logs: $stdout ; $stderr"
    try {
      $healthDeadline = (Get-Date).AddSeconds(15)
      do {
        Start-Sleep -Seconds 1
        $trayProcLive = @(Get-ManagedRuntimeProcesses -RoleFilter @('tray_agent','tray_agent_legacy'))
        $serverLive = Test-TcpPort -HostName '127.0.0.1' -Port $Port -TimeoutMs 500
        $admsLive = $true
        if($AdmsPort -and ([int]$AdmsPort) -gt 0 -and ([int]$AdmsPort) -ne ([int]$Port)){
          $admsLive = Test-TcpPort -HostName '127.0.0.1' -Port $AdmsPort -TimeoutMs 500
        }
        $trayHealthy = ($trayProcLive.Count -gt 0) -and $serverLive -and $admsLive
      } until($trayHealthy -or ((Get-Date) -ge $healthDeadline))
      if($trayHealthy){
        Write-Host "[TRAY] tray_agent health check OK (ui=$Port adms=$AdmsPort)"
      } else {
        Write-Warning "[TRAY] tray_agent health check failed (tray=$($trayProcLive.Count) ui=$serverLive adms=$admsLive)"
        try {
          Update-TrayStatusFields @{
            server = 'OPRIT'
            commcenter = 'OPRIT'
            color = 'red'
          }
        } catch {}
      }
    } catch {
      Write-Warning "[TRAY] tray_agent health check error: $_"
    }
    } else {
      Write-Host "[TRAY] tray_agent launching in this console"
      & $py @($argList)
      if($LASTEXITCODE -ne 0){
        Write-Warning "[TRAY] tray_agent exited with code $LASTEXITCODE"
      }
      return
    }
} catch {
  Write-Warning "[TRAY] Failed to launch tray_agent detached: $_"
  throw
}

# Optional: start x64 zkemkeeper bridge for real-time controller events.
# Enable with:
#   $env:ZKACCESS_ZKEMKEEPER_ENABLE=1
#   $env:ZKACCESS_ZKEMKEEPER_IP=192.168.1.235
# Optional:
#   $env:ZKACCESS_ZKEMKEEPER_PORT=4370
#   $env:ZKACCESS_ZKEMKEEPER_MACHINE=1
#   $env:ZKACCESS_ZKEMKEEPER_DEVICE_ID=22
#   $env:ZKACCESS_ZKEMKEEPER_DOOR_ID=1
#   $env:ZKACCESS_ZKEMKEEPER_DOOR_PK=<db door id>
#   $env:ZKACCESS_ZKEMKEEPER_AUTOREG=1
try {
  $zkemEnable = [string]($env:ZKACCESS_ZKEMKEEPER_ENABLE)
  if((-not $trayHealthy)){
    Write-Warning "[TRAY] Skipping zkemkeeper bridge launch because tray/web stack is not healthy"
  }
  elseif($zkemEnable -and $zkemEnable.ToLower() -in @('1','true','yes','on')){
    $zkemEngine = [string]($env:ZKACCESS_ZKEMKEEPER_ENGINE)
    if([string]::IsNullOrWhiteSpace($zkemEngine)){ $zkemEngine = 'vbs' }
    $zkemEngine = $zkemEngine.ToLowerInvariant()
    $zkemPsScript = Join-Path $PWD 'scripts\zkemkeeper_event_bridge.ps1'
    $zkemVbsScript = Join-Path $PWD 'scripts\zkemkeeper_event_bridge.vbs'
    $zkemScript = if($zkemEngine -eq 'ps1'){ $zkemPsScript } else { $zkemVbsScript }
    $zkemRegisterScript = Join-Path $PWD 'scripts\register_zkemkeeper_sdk_x64.ps1'
    $zkemIp = [string]($env:ZKACCESS_ZKEMKEEPER_IP)
    if((Test-Path $zkemScript) -and (-not [string]::IsNullOrWhiteSpace($zkemIp))){
      $zkemPort = [string]($env:ZKACCESS_ZKEMKEEPER_PORT)
      if([string]::IsNullOrWhiteSpace($zkemPort)){ $zkemPort = '14370' }
      $zkemMachine = [string]($env:ZKACCESS_ZKEMKEEPER_MACHINE)
      if([string]::IsNullOrWhiteSpace($zkemMachine)){ $zkemMachine = '1' }
      $zkemSdkDir = [string]($env:ZKACCESS_ZKEMKEEPER_SDK_DIR)
      if([string]::IsNullOrWhiteSpace($zkemSdkDir)){
        $zkemSdkDir = Resolve-ZkemkeeperSdkDirX64
      }
      $zkemDumpFile = [string]($env:ZKACCESS_ZKEMKEEPER_DUMP_FILE)
      if([string]::IsNullOrWhiteSpace($zkemDumpFile)){
        $zkemDumpFile = Join-Path $PWD 'zkemkeeper_event_dump_controller22.jsonl'
      }
      $serverUrl = "http://127.0.0.1:$Port"
      $regState = 'SKIPPED'
      $regMessage = ''
      $regProgId = ''
      $canLaunch = $true
      if(Test-Path $zkemRegisterScript){
        try {
          $regOutput = & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $zkemRegisterScript -SdkDir $zkemSdkDir -Json 2>&1
          $regExit = $LASTEXITCODE
          $regText = (($regOutput | ForEach-Object { $_.ToString() }) -join [Environment]::NewLine).Trim()
          $regObj = $null
          if(-not [string]::IsNullOrWhiteSpace($regText)){
            try { $regObj = $regText | ConvertFrom-Json } catch {}
          }
          if($regObj){
            $regMessage = [string]$regObj.message
            $regProgId = [string]$regObj.prog_id
            if([bool]$regObj.ok){
              $regState = if([bool]$regObj.already_registered){ 'REGISTERED' } else { 'REGISTERED_NOW' }
            } else {
              $regState = if([bool]$regObj.needs_admin){ 'NEEDS_ADMIN' } else { 'ERROR' }
            }
          } elseif($regExit -eq 0) {
            $regState = 'REGISTERED'
            $regMessage = 'Registration helper completed successfully.'
          } else {
            $regState = 'ERROR'
            $regMessage = if($regText){ $regText } else { 'Registration helper failed.' }
          }
          if($regExit -ne 0 -and $regState -eq 'NEEDS_ADMIN'){
            $canLaunch = $false
          }
        } catch {
          $regState = 'ERROR'
          $regMessage = $_.Exception.Message
          $canLaunch = $false
        }
      }
      Update-TrayStatusFields @{
        zkemkeeper = if($canLaunch){ 'PORNESTE' } else { 'ADMIN' }
        zkemkeeper_enabled = $true
        zkemkeeper_target = "${zkemIp}:$zkemPort"
        zkemkeeper_engine = $zkemEngine
        zkemkeeper_registration = $regState
        zkemkeeper_registration_message = $regMessage
        zkemkeeper_prog_id = $regProgId
        zkemkeeper_dump_file = $zkemDumpFile
        zkemkeeper_device_id = [string]($env:ZKACCESS_ZKEMKEEPER_DEVICE_ID)
        zkemkeeper_door_id = [string]($env:ZKACCESS_ZKEMKEEPER_DOOR_ID)
        zkemkeeper_door_pk = [string]($env:ZKACCESS_ZKEMKEEPER_DOOR_PK)
      }
      if(-not $canLaunch){
        Write-Warning "[TRAY] zkemkeeper registration requires Administrator rights before bridge launch. $regMessage"
        return
      }
      $zkemStdout = Join-Path $PWD 'zkemkeeper_bridge_stdout.log'
      $zkemStderr = Join-Path $PWD 'zkemkeeper_bridge_stderr.log'
      try { Remove-Item (Join-Path $env:USERPROFILE 'zkeco_reader_heartbeat_zkemkeeper.json') -ErrorAction SilentlyContinue } catch {}
      if($zkemEngine -eq 'ps1'){
        $zkemArgTokens = @(
          '-NoProfile',
          '-ExecutionPolicy', 'Bypass',
          '-File', ('"{0}"' -f $zkemScript),
          '-Ip', ('"{0}"' -f $zkemIp),
          '-Port', ('"{0}"' -f $zkemPort),
          '-MachineNumber', ('"{0}"' -f $zkemMachine),
          '-ServerUrl', ('"{0}"' -f $serverUrl),
          '-SdkDir', ('"{0}"' -f $zkemSdkDir),
          '-DumpFile', ('"{0}"' -f $zkemDumpFile)
        )
        if($env:ZKACCESS_ZKEMKEEPER_DEVICE_ID){ $zkemArgTokens += @('-DeviceId', ('"{0}"' -f [string]$env:ZKACCESS_ZKEMKEEPER_DEVICE_ID)) }
        if($env:ZKACCESS_ZKEMKEEPER_DOOR_ID){ $zkemArgTokens += @('-DoorId', ('"{0}"' -f [string]$env:ZKACCESS_ZKEMKEEPER_DOOR_ID)) }
        if($env:ZKACCESS_ZKEMKEEPER_DOOR_PK){ $zkemArgTokens += @('-DoorPk', ('"{0}"' -f [string]$env:ZKACCESS_ZKEMKEEPER_DOOR_PK)) }
        if($env:ZKACCESS_ZKEMKEEPER_SOURCE){ $zkemArgTokens += @('-Source', ('"{0}"' -f [string]$env:ZKACCESS_ZKEMKEEPER_SOURCE)) }
        if($env:ZKACCESS_ZKEMKEEPER_COMM_PASSWORD){ $zkemArgTokens += @('-CommPassword', ('"{0}"' -f [string]$env:ZKACCESS_ZKEMKEEPER_COMM_PASSWORD)) }
        $autoReg = [string]($env:ZKACCESS_ZKEMKEEPER_AUTOREG)
        if($autoReg -and $autoReg.ToLower() -in @('1','true','yes','on')){ $zkemArgTokens += '-AutoRegister' }
        $zkemArgs = $zkemArgTokens -join ' '
        Start-Process -FilePath 'powershell.exe' -ArgumentList $zkemArgs -WindowStyle Hidden -RedirectStandardOutput $zkemStdout -RedirectStandardError $zkemStderr | Out-Null
      } else {
        $zkemArgTokens = @(
          '//nologo',
          ('"{0}"' -f $zkemScript),
          ('/Ip:{0}' -f ('"{0}"' -f $zkemIp)),
          ('/Port:{0}' -f ('"{0}"' -f $zkemPort)),
          ('/MachineNumber:{0}' -f ('"{0}"' -f $zkemMachine)),
          ('/ServerUrl:{0}' -f ('"{0}"' -f $serverUrl)),
          ('/SdkDir:{0}' -f ('"{0}"' -f $zkemSdkDir)),
          ('/DumpFile:{0}' -f ('"{0}"' -f $zkemDumpFile))
        )
        if($env:ZKACCESS_ZKEMKEEPER_DEVICE_ID){ $zkemArgTokens += ('/DeviceId:{0}' -f ('"{0}"' -f [string]$env:ZKACCESS_ZKEMKEEPER_DEVICE_ID)) }
        if($env:ZKACCESS_ZKEMKEEPER_DOOR_ID){ $zkemArgTokens += ('/DoorId:{0}' -f ('"{0}"' -f [string]$env:ZKACCESS_ZKEMKEEPER_DOOR_ID)) }
        if($env:ZKACCESS_ZKEMKEEPER_DOOR_PK){ $zkemArgTokens += ('/DoorPk:{0}' -f ('"{0}"' -f [string]$env:ZKACCESS_ZKEMKEEPER_DOOR_PK)) }
        if($env:ZKACCESS_ZKEMKEEPER_SOURCE){ $zkemArgTokens += ('/Source:{0}' -f ('"{0}"' -f [string]$env:ZKACCESS_ZKEMKEEPER_SOURCE)) }
        if($env:ZKACCESS_ZKEMKEEPER_COMM_PASSWORD){ $zkemArgTokens += ('/CommPassword:{0}' -f ('"{0}"' -f [string]$env:ZKACCESS_ZKEMKEEPER_COMM_PASSWORD)) }
        if($env:ZKACCESS_ZKEMKEEPER_AUTOREG){ $zkemArgTokens += ('/AutoRegister:{0}' -f ('"{0}"' -f [string]$env:ZKACCESS_ZKEMKEEPER_AUTOREG)) }
        Start-Process -FilePath 'cscript.exe' -ArgumentList $zkemArgTokens -WindowStyle Hidden -RedirectStandardOutput $zkemStdout -RedirectStandardError $zkemStderr | Out-Null
      }
      Write-Host "[TRAY] zkemkeeper bridge launched for ${zkemIp}:$zkemPort"
      Write-Host "[TRAY] Logs: $zkemStdout ; $zkemStderr"
      Update-TrayStatusFields @{
        zkemkeeper = 'PORNESTE'
        zkemkeeper_message = 'Bridge launched by tray_launch.'
        zkemkeeper_stdout = $zkemStdout
        zkemkeeper_stderr = $zkemStderr
        zkemkeeper_last_launch = (Get-Date).ToString('s')
      }
    } else {
      Update-TrayStatusFields @{
        zkemkeeper = 'EROARE'
        zkemkeeper_enabled = $true
        zkemkeeper_message = 'Missing script or controller IP for zkemkeeper bridge.'
      }
      Write-Warning "[TRAY] ZKEMKEEPER enabled but script/ip missing. Set ZKACCESS_ZKEMKEEPER_IP and ensure scripts\zkemkeeper_event_bridge.ps1 or scripts\zkemkeeper_event_bridge.vbs exists."
    }
  }
} catch {
  Update-TrayStatusFields @{
    zkemkeeper = 'EROARE'
    zkemkeeper_message = $_.Exception.Message
  }
  Write-Warning "[TRAY] Failed to launch zkemkeeper bridge: $_"
}
 
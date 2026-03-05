Param(
  [int]$Port = 0,
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
    [string]$Host = '127.0.0.1',
    [int]$Port = 6379,
    [int]$TimeoutMs = 250
  )
  try {
    $client = New-Object System.Net.Sockets.TcpClient
    $iar = $client.BeginConnect($Host, $Port, $null, $null)
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
    if(Test-TcpPort -Host '127.0.0.1' -Port 6379 -TimeoutMs 250){
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
      $iniPortRaw = Get-Content $configFile -ErrorAction SilentlyContinue |
        Select-String '^\s*port\s*=\s*(\d+)' |
        ForEach-Object { $_.Matches[0].Groups[1].Value } |
        Select-Object -First 1
      if($iniPortRaw){ $iniPort = [int]$iniPortRaw }
    }
  } catch {}
  if($iniPort -gt 0){ $Port = $iniPort; Write-Host "[TRAY] Using port $Port from saved config" }
  else { $Port = 8000; Write-Host "[TRAY] No saved port found, using default 8000" }
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
  $portsToKill = @($Port)
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

# Kill ALL duplicate ZKAccessB processes (both venv and system Python) to avoid
# port conflicts and inconsistent status reporting.
Write-Host "[TRAY] Cleaning up duplicate tray_agent / daphne / CommCenter processes"
try {
  $selfPid = $PID
  $stalePatterns = @('tray_agent', 'daphne', 'run_commcenter', 'card_reader_acp', 'card_reader_elatec')
  $allProcs = Get-CimInstance Win32_Process -ErrorAction SilentlyContinue | Where-Object { $_.ProcessId -ne $selfPid }
  foreach($proc in $allProcs){
    try {
      $cmdLine = [string]($proc.CommandLine)
      if(-not $cmdLine){ continue }
      $isZkProcess = $false
      foreach($pat in $stalePatterns){
        if($cmdLine -like "*$pat*"){
          $isZkProcess = $true
          break
        }
      }
      if($isZkProcess){
        try {
          Stop-Process -Id $proc.ProcessId -Force -ErrorAction SilentlyContinue
          Write-Host "[TRAY] Stopped duplicate process PID=$($proc.ProcessId): $($cmdLine.Substring(0, [Math]::Min(80, $cmdLine.Length)))"
        } catch {}
      }
    } catch {}
  }
} catch {
  Write-Warning "[TRAY] Process cleanup error: $_"
}

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
      Write-Host "[TRAY] Persisted tray config (+web creds if provided): port=$Port, server_mode=$mode ($cfgPath)"
    } else {
      Write-Host "[TRAY] Persisted tray config: port=$Port, server_mode=$mode ($cfgPath)"
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

# Extra cleanup: ensure we don't run duplicate python system/venv processes.
# If multiple tray_agent/daphne/readers exist, status becomes inconsistent and CommCenter appears offline.
try {
  Write-Host "[TRAY] Cleaning up old tray/server/reader processes (any Python)"
  $root = (Resolve-Path $PWD).Path
  $patterns = @(
    '*manage.py* tray_agent*',
    '*-m daphne*',
    '*manage.py* runserver*',
    '*card_reader_acp.py*',
    '*card_reader_elatec.py*'
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
    & $py -c "import django, channels; import channels_redis; import redis; print('imports:ok')" 2>$null
    if($LASTEXITCODE -ne 0){ throw "python imports failed" }
  } catch {
    Write-Warning "[TRAY] Python imports check failed (channels_redis/redis). WS will fall back to polling if Redis layer isn't available."
  }

  # 2) Django config check (fast, no migrate)
  try {
    & $py $manage 'check' "--settings=$Settings" 1>$null
    if($LASTEXITCODE -ne 0){
      Write-Warning "[TRAY] Django check reported issues (exit=$LASTEXITCODE)"
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
# Preferred modern path: x86 .NET bridge EXE (no Python 32-bit required).
# Fallback path: 32-bit Python 3 bridge runner.

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

function Resolve-PlcommproDllX86 {
  try {
    if($env:ZKACCESS_PLCOMMPRO_DLL -and (Test-Path $env:ZKACCESS_PLCOMMPRO_DLL)){
      return $env:ZKACCESS_PLCOMMPRO_DLL
    }
    $cands = @(
      (Join-Path $PWD 'Resurse\Standalone SDK-6.3.1.55\PullSDK\plcommpro.dll'),
      (Join-Path $PWD 'Resurse\ZKEUBioAccessSetup\Dependencies\ZKAccess3.5\NewSDK\plcommpro.dll'),
      (Join-Path $PWD 'Resurse\Standalone SDK-6.3.1.55\SDK\x86\plcommpro.dll')
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
    $cands = @(
      (Join-Path $PWD 'Resurse\Standalone SDK-6.3.1.55\SDK\x64\plcommpro.dll')
    )
    foreach($c in $cands){
      if($c -and (Test-Path $c)) { return $c }
    }
  } catch {}
  return $null
}

# Optional: prefer x64 SDK bundle if explicitly requested.
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
    $bridgeExe = Resolve-ZkAccessBridgeExe
    if($bridgeExe){
      $env:ZKACCESS_BRIDGE_EXE = $bridgeExe
      Write-Host "[TRAY] Bridge runner set (x86 EXE): $bridgeExe"
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
      foreach($proc_id in ($toKill | Sort-Object -Unique)){
        try { Stop-Process -Id $proc_id -Force -ErrorAction SilentlyContinue; Write-Host "[TRAY] Killed non-venv PID $proc_id" } catch {}
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
$acpEnabled = $false
$elatecEnabled = $false

function Get-ReaderProcess {
  param(
    [Parameter(Mandatory=$true)][string]$ScriptName
  )
  try {
    return Get-CimInstance Win32_Process | Where-Object {
      try {
        $_.CommandLine -and ($_.CommandLine -like "*${ScriptName}*")
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
    [Parameter(Mandatory=$true)][string]$Tag
  )
  try {
    $scriptLeaf = Split-Path $ScriptPath -Leaf
    $running = @(Get-ReaderProcess -ScriptName $scriptLeaf)
    if($running.Count -gt 0){
      Write-Host "[TRAY] ${Tag} already running (count=$($running.Count)); skipping duplicate start"
      return $null
    }
    $p = Start-Process -FilePath $py -ArgumentList (@($ScriptPath) + $Args) -PassThru -WindowStyle Hidden
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
        $p = Start-ReaderIfNotRunning -ScriptPath $acpScript -Args @($acpPort) -Tag 'ACP listener'
        if ($p) { $global:TrayChildPids += $p.Id }
      }
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
    commcenter_driver  = 'auto'
  }
  # Color: treat disabled readers as satisfied
  $allReadersOk = (($statusInit.acp_enabled -eq $false) -or ($statusInit.acp -eq 'ON')) -and (($statusInit.elatec_enabled -eq $false) -or ($statusInit.elatec -eq 'ON'))
  $colorInit = if(($statusInit.server -eq 'PORNIT') -and $allReadersOk){ 'green' } elseif(($statusInit.server -eq 'PORNIT') -or $allReadersOk){ 'yellow' } else { 'red' }
  $statusInit.color = $colorInit
  # Preserve any existing blocked flags so UI STOP isn't clobbered
  if ($trayStatus) {
    if ($true -eq $trayStatus.acp_blocked) { $statusInit.acp_blocked = $true }
    if ($true -eq $trayStatus.elatec_blocked) { $statusInit.elatec_blocked = $true }
    if (($trayStatus.cmd_stop_acp | Measure-Object).Count -gt 0) { $statusInit.cmd_stop_acp = $trayStatus.cmd_stop_acp }
    if (($trayStatus.cmd_stop_elatec | Measure-Object).Count -gt 0) { $statusInit.cmd_stop_elatec = $trayStatus.cmd_stop_elatec }
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
    & $py $manage 'migrate' '--noinput' "--settings=$Settings" 1> $migrateOut 2> $migrateErr
  } catch {
    Write-Error "[TRAY] migrate threw an exception: $_"
    Add-Content -Path migration_auto.log -Value ((Get-Date).ToString() + " migrate exception; startup aborted")
    exit 1
  }
  if ($LASTEXITCODE -ne 0) {
    Write-Error "[TRAY] migrate failed (exit=$LASTEXITCODE). See migration_run_errors.log"
    Add-Content -Path migration_auto.log -Value ((Get-Date).ToString() + " migrate failed; startup aborted")
    exit 1
  }
  Write-Host "[TRAY] Migrations OK"
  Add-Content -Path migration_auto.log -Value ((Get-Date).ToString() + " Migrations OK")
} else {
  Write-Warning "[TRAY] manage.py not found at $manage; skipping migrations"
  Add-Content -Path migration_auto.log -Value ((Get-Date).ToString() + " manage.py missing; skipped migrations")
}

# Best-effort: allow inbound ADMS/iClock push to this server port.
# (Requires admin; failures are non-fatal.)
try {
  $ruleName = "ZKAccessB ADMS Port $Port"
  $existing = $null
  try { $existing = Get-NetFirewallRule -DisplayName $ruleName -ErrorAction SilentlyContinue } catch { $existing = $null }
  if(-not $existing){
    try {
      New-NetFirewallRule -DisplayName $ruleName -Direction Inbound -Action Allow -Protocol TCP -LocalPort $Port -Profile Any -ErrorAction SilentlyContinue | Out-Null
      Write-Host "[TRAY] Firewall rule added: $ruleName"
    } catch {
      Write-Warning "[TRAY] Could not add firewall rule (needs admin): $_"
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
if([string]::IsNullOrWhiteSpace($commDriver)){ $commDriver = 'plcommpro' }
Write-Host "[TRAY] CommCenter driver: $commDriver"
$trayArgs += @('--driver',"$commDriver",'--port',"$Port")
Write-Host "[TRAY] Collecting static files"
& $py $manage 'collectstatic' '--noinput' "--settings=$Settings" > $null 2> collectstatic_errors.log
if($LASTEXITCODE -ne 0){ Write-Warning "[TRAY] collectstatic reported errors; see collectstatic_errors.log" }
Write-Host "[TRAY] Starting tray agent"
# Run tray_agent detached so it keeps running even if this launcher session ends.
try {
  # Write initial running status before handing off
  $statusRun = [ordered]@{
    acp            = if($acpEnabled){'ON'}else{'OPRIT'}
    elatec         = if($elatecEnabled){'ON'}else{'OPRIT'}
    server         = 'PORNIT'
    acp_enabled    = $acpEnabled
    elatec_enabled = $elatecEnabled
    commcenter     = 'PORNESTE'
    commcenter_driver  = 'auto'
  }
  $allReadersOk = (($statusRun.acp_enabled -eq $false) -or ($statusRun.acp -eq 'ON')) -and (($statusRun.elatec_enabled -eq $false) -or ($statusRun.elatec -eq 'ON'))
  $statusRun.color = if(($statusRun.server -eq 'PORNIT') -and $allReadersOk){ 'green' } elseif(($statusRun.server -eq 'PORNIT') -or $allReadersOk){ 'yellow' } else { 'red' }
  # Preserve blocked flags if present so a UI STOP remains effective
  if ($trayStatus) {
    if ($true -eq $trayStatus.acp_blocked) { $statusRun.acp_blocked = $true }
    if ($true -eq $trayStatus.elatec_blocked) { $statusRun.elatec_blocked = $true }
    if (($trayStatus.cmd_stop_acp | Measure-Object).Count -gt 0) { $statusRun.cmd_stop_acp = $trayStatus.cmd_stop_acp }
    if (($trayStatus.cmd_stop_elatec | Measure-Object).Count -gt 0) { $statusRun.cmd_stop_elatec = $trayStatus.cmd_stop_elatec }
  }
  Set-Content -Path (Join-Path $PWD 'tray_status.json') -Value ($statusRun | ConvertTo-Json -Depth 3) -Encoding UTF8
} catch {}

try {
  $stdout = Join-Path $PWD 'tray_agent_stdout.log'
  $stderr = Join-Path $PWD 'tray_agent_stderr.log'
  $argList = @('zkeco_modern/manage.py','tray_agent',"--settings=$Settings") + $trayArgs
  if($Detach){
    Start-Process -FilePath $py -ArgumentList $argList -WindowStyle Hidden -RedirectStandardOutput $stdout -RedirectStandardError $stderr | Out-Null
    Write-Host "[TRAY] tray_agent launched (detached)"
    Write-Host "[TRAY] Logs: $stdout ; $stderr"
  } else {
    Write-Host "[TRAY] tray_agent launching in this console (Ctrl+C stops only this console, tray stays managed by OS)"
    & $py @($argList)
  }
} catch {
  Write-Warning "[TRAY] Failed to launch tray_agent detached: $_"
  throw
}
 
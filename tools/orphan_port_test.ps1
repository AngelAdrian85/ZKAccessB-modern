param(
  [int]$Port = 18080
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Continue'

$root = "C:\Users\AngelAdrian\Desktop\Acces\ZKAccessB"
Set-Location $root

$logDir = Join-Path $root 'runtime_logs'
New-Item -ItemType Directory -Force -Path $logDir | Out-Null
$logPath = Join-Path $logDir ("orphan_port_test_{0}.log" -f (Get-Date -Format 'yyyyMMdd_HHmmss'))

function Log([string]$msg) {
  $line = "[{0}] {1}" -f (Get-Date -Format 'HH:mm:ss'), $msg
  Add-Content -Path $logPath -Value $line -Encoding utf8
}

$cfg = Join-Path $HOME 'zkeco_tray_config.ini'
$cfgBackup = Join-Path $logDir ("zkeco_tray_config_backup_{0}.ini" -f (Get-Date -Format 'yyyyMMdd_HHmmss'))
$py = ".\\.venv\\Scripts\\python.exe"

function Get-ProcCmd([int]$procId) {
  try { return [string](Get-CimInstance Win32_Process -Filter "ProcessId=$procId").CommandLine } catch { return '' }
}
function Is-OurServerCmd([string]$cmd) {
  if (-not $cmd) { return $false }
  $cl = $cmd.ToLower()
  if ($cl.Contains('daphne') -and $cl.Contains('zkeco_config.asgi:application')) { return $true }
  if ($cl.Contains('manage.py') -and $cl.Contains('runserver') -and $cl.Contains('zkeco_config')) { return $true }
  return $false
}
function PortListeningPids([int]$p) {
  $pids = @()
  $lines = netstat -ano -p TCP | Select-String (":$p\s+.*LISTENING")
  foreach ($ln in $lines) {
    $procIdStr = (($ln -split "\s+")[-1]).Trim()
    if ($procIdStr -match '^\d+$') { $pids += [int]$procIdStr }
  }
  return ($pids | Sort-Object -Unique)
}
function Show-PortOwners([int]$p) {
  Log "--- LISTENING on port $p ---"
  $pids = @(PortListeningPids $p)
  if ($pids.Count -eq 0) { Log "(none)"; return @() }
  foreach ($procId in $pids) {
    $cmdLine = [string](Get-ProcCmd $procId)
    $short = $cmdLine
    if ($short.Length -gt 160) { $short = $short.Substring(0, 160) + '…' }
    Log ("PID={0} CMD={1}" -f $procId, $short)
  }
  return $pids
}

Log "[0] Preparing config port=$Port (manual port)"
try {
  if (Test-Path $cfg) {
    Copy-Item -Path $cfg -Destination $cfgBackup -Force
    Log "Backed up config to $cfgBackup"
  }
} catch {}

# Important: write a clean INI to avoid duplicate keys which make Python configparser fail.
@(
  '[tray]'
  "port=$Port"
  'server_mode=asgi'
) -join "`n" | Out-File -FilePath $cfg -Encoding utf8
Log "Config overwritten (clean): $cfg"

Log "[1] Cleanup any prior tray_agent and OUR server on port"
Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -like '*manage.py*tray_agent*' } | ForEach-Object {
  try { Log ("Stopping tray_agent PID {0}" -f $_.ProcessId); Stop-Process -Id $_.ProcessId -Force } catch {}
}
Start-Sleep -Milliseconds 300
$pre = Show-PortOwners $Port
foreach ($procId in @($pre)) {
  $cmdLine = [string](Get-ProcCmd $procId)
  if (Is-OurServerCmd $cmdLine) { Log "Stopping existing OUR server PID $procId"; try { Stop-Process -Id $procId -Force } catch {} }
}
Start-Sleep -Milliseconds 300
Show-PortOwners $Port | Out-Null

Log "[2] Start tray_agent (run #1)"
$p1 = Start-Process -FilePath $py -ArgumentList "manage.py tray_agent --host 127.0.0.1 --asgi --no-commcenter" -PassThru -WindowStyle Hidden
Log ("tray_agent #1 PID={0}" -f $p1.Id)
Start-Sleep -Seconds 4
$mid = Show-PortOwners $Port

Log "[3] Kill only tray_agent #1 (server may remain orphaned)"
try { Stop-Process -Id $p1.Id -Force; Log "tray_agent #1 killed" } catch { Log "Failed to kill tray_agent #1" }
Start-Sleep -Seconds 2
$orphan = Show-PortOwners $Port

Log "[4] Start tray_agent (run #2) -> should stop orphan and reclaim port"
$p2 = Start-Process -FilePath $py -ArgumentList "manage.py tray_agent --host 127.0.0.1 --asgi --no-commcenter" -PassThru -WindowStyle Hidden
Log ("tray_agent #2 PID={0}" -f $p2.Id)
Start-Sleep -Seconds 4
$after = Show-PortOwners $Port

$orphanList = @($orphan)
$afterList = @($after)
$still = @(); foreach ($procId in $orphanList) { if ($afterList -contains $procId) { $still += $procId } }
if ($orphanList.Count -gt 0 -and $still.Count -eq 0) {
  Log "RESULT: orphan server PID(s) were stopped on restart."
} elseif ($orphanList.Count -eq 0) {
  Log "RESULT: no orphan detected (port not listening after tray_agent kill)."
} else {
  Log ("RESULT: orphan PID(s) still present: {0}" -f ($still -join ', '))
}

Log "[5] Show persisted last_server_state.json"
$state = Join-Path $root 'runtime_logs\\last_server_state.json'
if (Test-Path $state) {
  $txt = Get-Content $state -Raw
  if ($txt.Length -gt 300) { $txt = $txt.Substring(0, 300) + '…' }
  Log ("STATE: {0}" -f $txt)
} else {
  Log "STATE: (no state file)"
}

Log "[6] Cleanup: stop tray_agent #2 and OUR server on port"
try { Stop-Process -Id $p2.Id -Force; Log "tray_agent #2 killed" } catch { Log "Failed to kill tray_agent #2" }
Start-Sleep -Seconds 1
$final = Show-PortOwners $Port
foreach ($procId in @($final)) {
  $cmdLine = [string](Get-ProcCmd $procId)
  if (Is-OurServerCmd $cmdLine) { Log "Stopping OUR server PID $procId"; try { Stop-Process -Id $procId -Force } catch {} }
}
Start-Sleep -Milliseconds 500
Show-PortOwners $Port | Out-Null

try {
  if (Test-Path $cfgBackup) {
    Copy-Item -Path $cfgBackup -Destination $cfg -Force
    Log "Restored original config from $cfgBackup"
  }
} catch {}

Log "DONE"
Write-Output $logPath

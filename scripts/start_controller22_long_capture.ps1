param(
  [int]$Seconds = 900,
  [string]$Ip = '192.168.1.235',
  [int]$Port = 14370,
  [int]$MachineNumber = 1,
  [int]$DeviceId = 22,
  [string]$DoorId = '1',
  [string]$DoorPk = '27',
  [int]$AdmsPort = 15437,
  [string]$CommPassword = 'Zk@123'
)

$ErrorActionPreference = 'Stop'

$root = Split-Path -Parent $PSScriptRoot
$python = Join-Path $root '.venv\Scripts\python.exe'
$listenerOut = Join-Path $root 'tmp_adms_listener.out.log'
$listenerErr = Join-Path $root 'tmp_adms_listener.err.log'
$vbsOut = Join-Path $root 'tmp_zkem_vbs.out.log'
$vbsErr = Join-Path $root 'tmp_zkem_vbs.err.log'
$dumpFile = Join-Path $root 'zkemkeeper_event_dump_controller22.jsonl'
$heartbeat = Join-Path $env:USERPROFILE 'zkeco_reader_heartbeat_zkemkeeper.json'
$pidFile = Join-Path $root 'tmp_controller22_capture_pids.json'

Get-CimInstance Win32_Process | Where-Object {
  ($_.Name -eq 'python.exe' -and $_.CommandLine -match 'push_listener.py') -or
  ($_.Name -eq 'cscript.exe' -and $_.CommandLine -match 'zkemkeeper_event_bridge.vbs')
} | ForEach-Object {
  Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue
}

Remove-Item $listenerOut,$listenerErr,$vbsOut,$vbsErr,$dumpFile,$heartbeat,$pidFile -ErrorAction SilentlyContinue

$listener = Start-Process -FilePath $python `
  -ArgumentList @('scripts/push_listener.py','--host','0.0.0.0','--port',"$AdmsPort") `
  -WorkingDirectory $root `
  -WindowStyle Hidden `
  -RedirectStandardOutput $listenerOut `
  -RedirectStandardError $listenerErr `
  -PassThru

Start-Sleep -Seconds 2

$listenerOwner = ''
try {
  $listenerOwner = (netstat -ano | Select-String ":$AdmsPort\s+.*LISTENING").ToString()
} catch {}

$vbsArgs = @(
  '//nologo',
  (Join-Path $root 'scripts/zkemkeeper_event_bridge.vbs'),
  "/Ip:$Ip",
  "/Port:$Port",
  "/MachineNumber:$MachineNumber",
  "/ServerUrl:http://127.0.0.1:$AdmsPort",
  "/DeviceId:$DeviceId",
  "/DoorId:$DoorId",
  "/DoorPk:$DoorPk",
  '/Source:zkemkeeper-c22-long',
  "/CommPassword:$CommPassword"
)

$vbs = Start-Process -FilePath 'cscript.exe' `
  -ArgumentList $vbsArgs `
  -WorkingDirectory $root `
  -WindowStyle Hidden `
  -RedirectStandardOutput $vbsOut `
  -RedirectStandardError $vbsErr `
  -PassThru

$pidInfo = [ordered]@{
  started_at = (Get-Date).ToString('s')
  listener_pid = $listener.Id
  vbs_pid = $vbs.Id
  listener_owner = $listenerOwner
  listener_out = $listenerOut
  listener_err = $listenerErr
  vbs_out = $vbsOut
  vbs_err = $vbsErr
  dump_file = $dumpFile
  heartbeat = $heartbeat
}
$pidInfo | ConvertTo-Json | Set-Content -Path $pidFile -Encoding UTF8

Write-Host "Capture armed for controller $DeviceId"
Write-Host "Seconds=$Seconds"
Write-Host "Listener PID=$($listener.Id)"
Write-Host "VBS PID=$($vbs.Id)"
Write-Host "Listener owner: $listenerOwner"
Write-Host "Logs:"
Write-Host "  $listenerOut"
Write-Host "  $listenerErr"
Write-Host "  $vbsOut"
Write-Host "  $vbsErr"
Write-Host "  $dumpFile"
Write-Host "  $heartbeat"

if ($Seconds -gt 0) {
  $deadline = (Get-Date).AddSeconds($Seconds)
  while ((Get-Date) -lt $deadline) {
    $vbsAlive = Get-Process -Id $vbs.Id -ErrorAction SilentlyContinue
    $listenerAlive = Get-Process -Id $listener.Id -ErrorAction SilentlyContinue
    $hb = Get-Item $heartbeat -ErrorAction SilentlyContinue
    $dump = Get-Item $dumpFile -ErrorAction SilentlyContinue
    $hbStamp = if ($hb) { $hb.LastWriteTime.ToString('HH:mm:ss') } else { '-' }
    $dumpSize = if ($dump) { $dump.Length } else { 0 }
    Write-Host ((Get-Date).ToString('HH:mm:ss') + " listener=" + [bool]$listenerAlive + " vbs=" + [bool]$vbsAlive + " hb=" + $hbStamp + " dump=" + $dumpSize)
    Start-Sleep -Seconds 5
  }
}
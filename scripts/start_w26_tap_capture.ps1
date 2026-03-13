param(
  [string]$ServerUrl = 'http://127.0.0.1:8000',
  [string]$ListenHost = '0.0.0.0',
  [int]$ListenPort = 9002,
  [string]$FormatName = 'Wiegand 26',
  [string]$DeviceId = '22',
  [string]$DoorId = '1',
  [string]$DoorPk = '27',
  [string]$Source = 'w26-hardware-tap'
)

$ErrorActionPreference = 'Stop'

$root = Split-Path -Parent $PSScriptRoot
$python = Join-Path $root '.venv\Scripts\python.exe'
$logFile = Join-Path $root 'tmp_w26_tap_capture.log'
$errFile = Join-Path $root 'tmp_w26_tap_capture.err.log'

Get-CimInstance Win32_Process | Where-Object {
  $_.Name -match 'python|powershell' -and $_.CommandLine -match 'wiegand_listener.py'
} | ForEach-Object {
  Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue
}

Remove-Item $logFile,$errFile -ErrorAction SilentlyContinue

$args = @(
  'scripts/wiegand_listener.py',
  '--server-url', $ServerUrl,
  '--listen-host', $ListenHost,
  '--listen-port', "$ListenPort",
  '--format-name', $FormatName,
  '--device-id', $DeviceId,
  '--door-id', $DoorId,
  '--door-pk', $DoorPk,
  '--source', $Source
)

$proc = Start-Process -FilePath $python `
  -ArgumentList $args `
  -WorkingDirectory $root `
  -WindowStyle Hidden `
  -RedirectStandardOutput $logFile `
  -RedirectStandardError $errFile `
  -PassThru

Start-Sleep -Seconds 2

Write-Host "W26 tap capture armed"
Write-Host "PID=$($proc.Id)"
Write-Host "TCP target: $ListenHost:$ListenPort"
Write-Host "Log: $logFile"
Write-Host "Err: $errFile"
Write-Host "Accepted frame examples:"
Write-Host "  BITS:10101010101010101010101010"
Write-Host "  HEX:123456"
Write-Host "  INT:1193046"
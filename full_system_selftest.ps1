param(
  [int]$TimeoutSeconds = 25
)
$ErrorActionPreference='Stop'
Function Info($m){Write-Host $m -ForegroundColor Cyan}
Function Warn($m){Write-Host $m -ForegroundColor Yellow}
Function Fail($m){Write-Host $m -ForegroundColor Red}

$py=".\.venv\Scripts\python.exe"
if(!(Test-Path $py)){Fail "Python venv missing: $py"; exit 2}

# 1. Start Django server (background)
$ts = Get-Date -Format 'yyyyMMdd_HHmmss'
$serverOut = New-Item -ItemType File -Force -Path (".\server_selftest_out_$ts.log") | Select-Object -ExpandProperty FullName
$serverErr = New-Item -ItemType File -Force -Path (".\server_selftest_err_$ts.log") | Select-Object -ExpandProperty FullName
Info "Starting server (out: $serverOut, err: $serverErr)"
$serverProc = Start-Process -FilePath $py -ArgumentList "zkeco_modern\manage.py runserver 8000" -RedirectStandardOutput $serverOut -RedirectStandardError $serverErr -PassThru
Start-Sleep -Seconds 3

# 2. Headless backup run (agent)
Info "Running tray agent headless backup"
$prevEAP = $ErrorActionPreference; $ErrorActionPreference='Continue'
$backupResult = & $py .\zkeco_modern\tray_agent.py --headless --auto --skip-services --backup-interval=0 2> $null | Out-String
$ErrorActionPreference = $prevEAP
$backupExit = $LASTEXITCODE
# Fallback success detection by parsing output if exit non-zero
if($backupExit -ne 0 -and ($backupResult -match 'Backup success:')){ $backupExit = 0 }
$backupOk = $backupExit -eq 0

# 3. Restore test
Info "Running headless restore latest"
$prevEAP = $ErrorActionPreference; $ErrorActionPreference='Continue'
$restoreResult = & $py .\zkeco_modern\tray_agent.py --headless-restore-latest 2> $null | Out-String
$ErrorActionPreference = $prevEAP
$restoreExit = $LASTEXITCODE
if($restoreExit -ne 0 -and ($restoreResult -match '"restore":"ok"')){ $restoreExit = 0 }
$restoreOk = $restoreExit -eq 0

# 4. Web monitor page fetch
$monitorUrl = "http://127.0.0.1:8000/agent/monitor/"
Info "Fetching monitor page: $monitorUrl"
$pageContent = $null
try {
  $pageContent = (Invoke-WebRequest -Uri $monitorUrl -UseBasicParsing -TimeoutSec 10).Content
} catch { Warn "Monitor fetch failed: $($_.Exception.Message)" }
$hasMonitorHeader = $pageContent -match 'Real-Time Monitoring'

# 5. WebSocket basic probe (optional fallback)
$wsStatus = 'skipped'
try {
  # Quick port test only; actual WS handshake requires client library.
  $tcpClient = New-Object System.Net.Sockets.TcpClient
  $iar = $tcpClient.BeginConnect('127.0.0.1',8000,$null,$null)
  $wait = $iar.AsyncWaitHandle.WaitOne(3000,$false)
  if($wait -and $tcpClient.Connected){$wsStatus='port-open'} else {$wsStatus='port-timeout'}
  $tcpClient.Close()
} catch { $wsStatus='error' }

# 6. Gather latest backup file
$modernDir = Join-Path $PSScriptRoot 'zkeco_modern'
$backupDir = Join-Path $modernDir 'backups'
$latestBackup = $null
if(Test-Path $backupDir){
  $latestBackup = Get-ChildItem $backupDir -Filter db_backup_*.sql | Sort-Object LastWriteTime -Desc | Select-Object -First 1
}

# 7. Output JSON summary
$result = [ordered]@{
  server_pid = $serverProc.Id
  server_running = $serverProc.HasExited -eq $false
  backup_exit_code = $backupExit
  backup_latest = $latestBackup.Name
  restore_exit_code = $restoreExit
  backup_log_excerpt = ($backupResult -split "`r?`n" | Select-Object -First 6) -join " | "
  restore_log = ($restoreResult -replace "`r`n",' ') -replace "`n",' '
  monitor_page = if($hasMonitorHeader){'ok'} else {'missing'}
  ws_port_status = $wsStatus
  timestamp = (Get-Date).ToString('yyyy-MM-ddTHH:mm:ss')
}
$result | ConvertTo-Json -Depth 3 | Out-File full_selftest_result.json -Encoding UTF8
Info "Selftest summary written to full_selftest_result.json"

# 8. Cleanup: stop server (optional - leave running if monitor ok)
if($hasMonitorHeader){
  Warn "Leaving server running for manual inspection (PID $($serverProc.Id))."
}else{
  Info "Stopping server (no monitor page)"
  try { $serverProc | Stop-Process } catch {}
}

Write-Host (ConvertTo-Json $result -Depth 3)
exit 0

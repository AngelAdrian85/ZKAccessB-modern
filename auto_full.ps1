param(
  [switch]$SkipReset,
  [switch]$EnableRoutinesEvents,
  [switch]$SkipServices,
  [switch]$LeaveServer,
  [int]$Retention=5
)
$ErrorActionPreference='Stop'
Function Info($m){Write-Host $m -ForegroundColor Cyan}
Function Warn($m){Write-Host $m -ForegroundColor Yellow}
Function Fail($m){Write-Host $m -ForegroundColor Red}

if(-not $SkipReset){
  if(Test-Path .\.venv){ Info 'Resetting environment (calling reset_environment.ps1)'; powershell -ExecutionPolicy Bypass -File .\reset_environment.ps1 } else { Info 'Fresh env: skipping archive step' }
}

# Ensure mysqldump integration
if($EnableRoutinesEvents){
  Info 'Running install_mysql_tools.ps1 with routines/events'
  powershell -ExecutionPolicy Bypass -File .\install_mysql_tools.ps1 -EnableRoutinesEvents
} else {
  Info 'Running install_mysql_tools.ps1 basic'
  powershell -ExecutionPolicy Bypass -File .\install_mysql_tools.ps1
}

# Adjust retention if requested
$ini = 'zkeco_modern/agent_controller.ini'
if(Test-Path $ini){
  (Get-Content $ini) | ForEach-Object { if($_ -match '^backup_retention\s*='){ 'backup_retention='+$Retention } else { $_ } } | Set-Content $ini -Encoding UTF8
  Info "Set backup_retention=$Retention"
}

# Run full self-test
Info 'Launching full_system_selftest.ps1'
$testJson = powershell -ExecutionPolicy Bypass -File .\full_system_selftest.ps1 | Out-String
$summaryPath = 'auto_full_summary.json'
# Extract final JSON object (last line)
$lastLine = ($testJson -split "`r?`n" | Where-Object { $_ -match '{' } | Select-Object -Last 1)
if($lastLine){ $lastLine | Out-File $summaryPath -Encoding UTF8; Info "Summary written: $summaryPath" } else { Warn 'Selftest produced no JSON summary.' }

# Optionally stop server
if(-not $LeaveServer){
  if(Test-Path server_selftest_out_*.log){
    $pids = Get-Process | Where-Object { $_.Path -like "*python*" -and $_.StartInfo.Arguments -match 'runserver 8000' } | Select-Object -ExpandProperty Id -ErrorAction SilentlyContinue
    foreach($pid in $pids){ try{ Stop-Process -Id $pid -ErrorAction SilentlyContinue; Info "Stopped server PID $pid" } catch {} }
  }
}

Info 'Automation complete.'

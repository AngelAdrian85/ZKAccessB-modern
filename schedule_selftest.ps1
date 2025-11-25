<#!
.SYNOPSIS
  Registers or removes a scheduled task to run full_system_selftest.ps1 periodically.
.DESCRIPTION
  Creates a Windows Scheduled Task that executes the self-test script at a fixed interval.
.PARAMETER TaskName
  Name of the scheduled task (default: ZKAccessB-SelfTest)
.PARAMETER IntervalMinutes
  Repetition interval in minutes (default: 60)
.PARAMETER Remove
  If specified, removes the existing task instead of creating it.
.EXAMPLE
  powershell -ExecutionPolicy Bypass -File .\schedule_selftest.ps1 -IntervalMinutes 30
.EXAMPLE
  powershell -ExecutionPolicy Bypass -File .\schedule_selftest.ps1 -Remove
#>
param(
  [string]$TaskName = 'ZKAccessB-SelfTest',
  [int]$IntervalMinutes = 60,
  [int]$DurationDays = 365,
  [switch]$Remove
)

$script = Join-Path $PSScriptRoot 'full_system_selftest.ps1'
if(-not (Test-Path $script)) {
    Write-Error "Self-test script not found at $script"; exit 1
}

if($Remove) {
    if(Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue) {
        Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
        Write-Host "Removed scheduled task $TaskName"
    } else {
        Write-Host "Task $TaskName not found (nothing to remove)"
    }
    exit 0
}

if($IntervalMinutes -lt 5) { Write-Warning 'Interval <5 minutes may be too frequent.' }

# Trigger: start 2 minutes from now, repeat for configurable duration (avoid MaxValue serialization error)
$start = (Get-Date).AddMinutes(2)
$repetition = New-TimeSpan -Minutes $IntervalMinutes
if($DurationDays -le 0) { $DurationDays = 365 }
$duration = New-TimeSpan -Days $DurationDays
$trigger = New-ScheduledTaskTrigger -Once -At $start -RepetitionInterval $repetition -RepetitionDuration $duration

# Action: run PowerShell self-test script and append JSON summary to a dated log
$logDir = Join-Path $PSScriptRoot 'selftest_logs'
if(-not (Test-Path $logDir)) { New-Item -ItemType Directory -Path $logDir | Out-Null }
$actionArgs = "-NoProfile -ExecutionPolicy Bypass -File `"$script`" | Out-File -FilePath `"$logDir\selftest_$(Get-Date -Format yyyyMMdd).log`" -Append"
$action = New-ScheduledTaskAction -Execute 'powershell.exe' -Argument $actionArgs

# Principal creation: Adjust RunLevel enumerator (Valid: Limited, Highest). Fallback if creation fails.
try {
  # Use Limited to avoid elevation prompt; switch to Highest if needed for privileged ops
  $principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType S4U -RunLevel Limited
} catch {
  Write-Warning "Could not create principal with S4U Limited. Falling back to Interactive.";
  try {
    $principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive -RunLevel Limited
  } catch {
    Write-Warning "Principal creation failed; will register task without explicit principal.";
    $principal = $null
  }
}

if(Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue) {
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
}
if($principal) {
  Register-ScheduledTask -TaskName $TaskName -Trigger $trigger -Action $action -Principal $principal -Description 'Periodic full_system_selftest.ps1 to validate backup & restore.'
} else {
  Register-ScheduledTask -TaskName $TaskName -Trigger $trigger -Action $action -Description 'Periodic full_system_selftest.ps1 to validate backup & restore.'
}
Write-Host "Registered scheduled task $TaskName (interval $IntervalMinutes min)"

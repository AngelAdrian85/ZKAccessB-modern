# Registers a Windows Scheduled Task to run auto_run.ps1 at user logon.
# Usage (elevated or user context): powershell -ExecutionPolicy Bypass -File .\register_scheduled_task.ps1

$taskName = 'ZKAccessAutoRun'
$scriptPath = (Resolve-Path '.\auto_run.ps1').Path
$action = New-ScheduledTaskAction -Execute 'powershell.exe' -Argument "-ExecutionPolicy Bypass -File `"$scriptPath`""
$trigger = New-ScheduledTaskTrigger -AtLogOn
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries

try {
    Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger -Settings $settings -Description 'Auto start ZKAccess modern services and agent'
    Write-Host "Scheduled Task '$taskName' registered."
} catch {
    Write-Host "Failed to register task: $($_.Exception.Message)" -ForegroundColor Red
}

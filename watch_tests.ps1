Param(
  [string]$Venv = '.venv_new',
  [string]$TestPath = 'zkeco_modern/tests',
  [int]$DebounceMs = 800
)
Write-Host "[WATCH] Starting test watch on $TestPath"
if(!(Test-Path "$Venv\Scripts\python.exe")){
  Write-Error "Virtual env $Venv missing. Run tray_launch.ps1 first."; exit 1
}
$py = Join-Path $Venv 'Scripts/python.exe'
$full = Resolve-Path $TestPath

# FileSystemWatcher setup
$watcher = New-Object System.IO.FileSystemWatcher
$watcher.Path = $full.Path
$watcher.Filter = '*.py'
$watcher.IncludeSubdirectories = $true
$watcher.EnableRaisingEvents = $true

$script:pending = $false
$script:lastRun = Get-Date

function Invoke-Tests {
  if($script:pending -eq $false){ return }
  $script:pending = $false
  Write-Host "[WATCH] Running tests..." -ForegroundColor Cyan
  & $py zkeco_modern/manage.py test --verbosity 1 2>&1 | ForEach-Object {
    if($_ -match 'FAILED' -or $_ -match 'ERROR'){ Write-Host $_ -ForegroundColor Red }
    elseif($_ -match 'OK'){ Write-Host $_ -ForegroundColor Green }
    elseif($_ -match 'Ran \d+ tests'){ Write-Host $_ -ForegroundColor Yellow }
  }
  Write-Host "[WATCH] Cycle complete." -ForegroundColor Cyan
}

$action = {
  $script:pending = $true
  $script:lastChange = Get-Date
}

Register-ObjectEvent $watcher Changed -Action $action | Out-Null
Register-ObjectEvent $watcher Created -Action $action | Out-Null
Register-ObjectEvent $watcher Deleted -Action $action | Out-Null
Register-ObjectEvent $watcher Renamed -Action $action | Out-Null

Write-Host "[WATCH] Ready. Initial test run starting..." -ForegroundColor Green
& $py zkeco_modern/manage.py test --verbosity 1 2>&1 | ForEach-Object {
  if($_ -match 'FAILED' -or $_ -match 'ERROR'){ Write-Host $_ -ForegroundColor Red }
  elseif($_ -match 'OK'){ Write-Host $_ -ForegroundColor Green }
  elseif($_ -match 'Ran \d+ tests'){ Write-Host $_ -ForegroundColor Yellow }
}
Write-Host "[WATCH] Initial test cycle complete. Monitoring for changes." -ForegroundColor Cyan

try {
  while($true){
    if($script:pending){
      $since = (Get-Date) - $script:lastChange
      if($since.TotalMilliseconds -ge $DebounceMs){ Invoke-Tests }
    }
    Start-Sleep -Milliseconds 250
  }
} catch {
  Write-Warning "[WATCH] Stopping watch: $_"
} finally {
  Get-EventSubscriber | Where-Object { $_.SourceIdentifier -like '*FileSystemWatcher*' } | Unregister-Event
  $watcher.Dispose()
}

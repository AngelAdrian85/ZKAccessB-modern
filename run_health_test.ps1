<#!
.SYNOPSIS
  Starts Django server briefly and fetches /agent/health/ JSON.
.DESCRIPTION
  Launches manage.py runserver on a chosen port, waits until health endpoint is reachable or timeout, prints JSON then stops process.
.PARAMETER Port
  Port to bind (default 8000)
.PARAMETER TimeoutSeconds
  Max seconds to wait for server readiness (default 40)
.EXAMPLE
  powershell -ExecutionPolicy Bypass -File .\run_health_test.ps1 -Port 8010
#>
param(
  [int]$Port = 8000,
  [int]$TimeoutSeconds = 40
)
$manage = Join-Path $PSScriptRoot 'zkeco_modern' 'manage.py'
if(-not (Test-Path $manage)) { Write-Error "manage.py not found at $manage"; exit 1 }

Write-Host "Starting Django server on port $Port..."
$python = (Get-Command python).Source
$proc = Start-Process -FilePath $python -ArgumentList "`"$manage`" runserver $Port" -PassThru -WindowStyle Hidden

$healthUrl = "http://127.0.0.1:$Port/agent/health/"
$deadline = (Get-Date).AddSeconds($TimeoutSeconds)
$ready = $false
while((Get-Date) -lt $deadline) {
  try {
    $resp = Invoke-WebRequest -Uri $healthUrl -UseBasicParsing -TimeoutSec 5
    if($resp.StatusCode -eq 200) { $ready = $true; break }
  } catch { }
  Start-Sleep -Seconds 2
}
if(-not $ready) {
  Write-Warning "Health endpoint not reachable within $TimeoutSeconds seconds"
} else {
  Write-Host "Health endpoint reached. Raw JSON:";
  Write-Output $resp.Content
}
Write-Host "Stopping server (PID $($proc.Id))..."
try { Stop-Process -Id $proc.Id -Force } catch { }

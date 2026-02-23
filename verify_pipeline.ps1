param(
  [int]$DeviceId = 22,
  [string]$SN = "",
  [string]$DeviceIP = "192.168.1.235",
  [int[]]$Ports = @(14370, 4370),
  [string]$InjectCard = "999999",
  [string]$EnqueueAdmsRaw = "PING_FROM_SERVER",
  [switch]$RunPytest,
  [switch]$SkipTcpTest,
  [bool]$SimulateGetRequest = $true,
  [bool]$ShowAudit = $true
)

$ErrorActionPreference = 'Stop'

function Resolve-Python {
  $p = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
  if(Test-Path $p){ return $p }
  $p = Join-Path $PSScriptRoot '.venv_clean\Scripts\python.exe'
  if(Test-Path $p){ return $p }
  return 'python'
}

function Run-Step([string]$Title, [string]$CommandLine){
  Write-Host "`n=== $Title ===" -ForegroundColor Cyan
  Write-Host $CommandLine
  Invoke-Expression $CommandLine
  if($LASTEXITCODE -ne 0){
    throw "Step failed ($Title) exit=$LASTEXITCODE"
  }
}

$py = Resolve-Python
Write-Host "Using Python: $py" -ForegroundColor Green

# Mandatory override (legacy systems often have mysite.settings in env)
$env:DJANGO_SETTINGS_MODULE = 'zkeco_config.settings'

if(-not $SkipTcpTest){
  if($DeviceIP){
    Write-Host "`n=== TCP Reachability ===" -ForegroundColor Cyan
    foreach($port in $Ports){
      try{
        $r = Test-NetConnection -ComputerName $DeviceIP -Port $port -WarningAction SilentlyContinue
        $ok = [bool]$r.TcpTestSucceeded
        $status = 'FAIL'
        if($ok){ $status = 'OK' }
        Write-Host ("{0}:{1} -> {2}" -f $DeviceIP, $port, $status)
      } catch {
        Write-Host "${DeviceIP}:${port} -> ERROR: $($_.Exception.Message)" -ForegroundColor Yellow
      }
    }
  } else {
    Write-Host "Skipping TCP test (DeviceIP empty)" -ForegroundColor Yellow
  }
}

if($RunPytest){
  Run-Step "Pytest (iClock push + getrequest queue)" (
    "$py -m pytest -q zkeco_modern/agent/tests/test_iclock_push_ingest.py zkeco_modern/agent/tests/test_iclock_getrequest_queue.py"
  )
}

# Build pipeline_selftest args
$argsList = @()
if($DeviceId -gt 0){
  $argsList += "--device-id $DeviceId"
}
if($SN){
  $argsList += "--sn `"$SN`""
}
if($InjectCard){
  $argsList += "--inject-card `"$InjectCard`""
}
if($EnqueueAdmsRaw){
  $argsList += "--enqueue-adms-raw `"$EnqueueAdmsRaw`""
}
if($SimulateGetRequest){
  $argsList += "--simulate-getrequest"
}
if($ShowAudit){
  $argsList += "--show-audit"
}

$cmd = "$py zkeco_modern/manage.py pipeline_selftest " + ($argsList -join ' ')
Run-Step "Django pipeline self-test" $cmd

Write-Host "`nAll verification steps completed." -ForegroundColor Green

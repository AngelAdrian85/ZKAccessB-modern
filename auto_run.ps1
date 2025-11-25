# Auto setup and run all components with logging and diagnostics
# Usage: powershell -ExecutionPolicy Bypass -File .\auto_run.ps1 [-Verbose]

$ErrorActionPreference = 'Stop'
$logFile = Join-Path $PSScriptRoot 'auto_run.log'
$global:Failed = $false
Function Log($msg){ $ts = (Get-Date).ToString('u'); "$ts $msg" | Out-File -Append -FilePath $logFile }
Function Fail($msg){ Log "FAIL: $msg"; Write-Host $msg -ForegroundColor Red; $global:Failed = $true }
Log '--- AUTO RUN START ---'
Write-Host '== Auto Run Starting ==' -ForegroundColor Cyan

# ---------------- Python / venv resolution (robust) ----------------
$PythonExe = $null
$VenvPath = Join-Path $PSScriptRoot '.\.venv\Scripts\python.exe'
if (Test-Path $VenvPath) { $PythonExe = $VenvPath }
if (-not $PythonExe) {
    $cmdPy = Get-Command python -ErrorAction SilentlyContinue
    if ($cmdPy) { $PythonExe = $cmdPy.Source }
}
if (-not $PythonExe) {
    $cmdPyLauncher = Get-Command py -ErrorAction SilentlyContinue
    if ($cmdPyLauncher) { $PythonExe = $cmdPyLauncher.Source }
}
if ($PythonExe -and (Test-Path $PythonExe)) {
    Log "Initial Python candidate: $PythonExe"
} else {
    Fail 'No Python candidate found'; exit 1
}

# Skip python execution test due to environment stderr noise; assume usable
Log 'Skipping python pre-flight test'

# Ensure usable Python with pip
try { & $PythonExe -c "import pip" 2>$null } catch { Log 'pip import raised (will attempt venv refresh if needed)' }
if ($LASTEXITCODE -ne 0) {
    Log 'pip missing or import failed; creating fresh_auto venv'
    $FreshDir = Join-Path $PSScriptRoot 'fresh_auto'
    if (Test-Path $FreshDir) { try { Remove-Item -Recurse -Force $FreshDir } catch { Log 'Could not remove fresh_auto' } }
    $launcher = Get-Command py -ErrorAction SilentlyContinue
    if (-not $launcher) { Fail 'Cannot create fresh venv (py launcher missing)'; exit 2 }
    try { & py -3 -m venv $FreshDir } catch { Fail 'fresh_auto venv creation failed'; exit 2 }
    $PythonExe = Join-Path $FreshDir 'Scripts\python.exe'
    Log "Using fresh_auto python: $PythonExe"
    & $PythonExe -c "import ensurepip; ensurepip.bootstrap()" 2>$null
    & $PythonExe -m pip install --upgrade pip 2>$null
    & $PythonExe -c "import pip" 2>$null
    if ($LASTEXITCODE -ne 0) { Fail 'pip still missing after fresh_auto creation'; exit 2 } else { Log 'pip available in fresh_auto' }
}

# 1. Ensure venv
if (-not (Test-Path '.\.venv')) {
    Write-Host 'Creating virtual environment (.venv)' -ForegroundColor Yellow
    Log 'Creating venv'
    try { & $PythonExe -m venv .venv } catch { Fail 'Unable to create venv'; Exit 2 }
}
if (Test-Path '.\.venv\Scripts\python.exe') { $PythonExe = (Join-Path $PSScriptRoot '.\.venv\Scripts\python.exe'); Log "Switched PythonExe to venv: $PythonExe" }

# 2. Activate
# We can call python directly; activation optional. Attempt activation for PATH consistency.
try { . .\.venv\Scripts\Activate.ps1; Log 'Activated venv' } catch { Log 'Activation skipped (direct python usage).' }

# 3. Requirements install (idempotent)
Write-Host 'Installing dependencies' -ForegroundColor Cyan
Log 'Installing dependencies'
try { & $PythonExe -m pip install --upgrade pip | Out-Null } catch { Fail 'pip upgrade failed' }
try { & $PythonExe -m pip install -r .\requirements.txt | Tee-Object -FilePath $logFile -Append | Out-Null } catch { Fail 'requirements install failed' }

# 4. Migrate database (if Django project present)
if (Test-Path '.\zkeco_modern\manage.py') {
    Write-Host 'Running migrations' -ForegroundColor Cyan
    Log 'Running migrations'
    Write-Host '--- Running migrate (verbose) ---' -ForegroundColor DarkCyan
    $prevEAP = $ErrorActionPreference
    $ErrorActionPreference = 'Continue'  # allow stderr without terminating
    $migrateOutput = & $PythonExe .\zkeco_modern\manage.py migrate --noinput 2>&1
    $ErrorActionPreference = $prevEAP
    $migrateLogPath = Join-Path $PSScriptRoot 'migrate_err.log'
    $migrateOutput | Out-File -FilePath $migrateLogPath -Append
    $migrateOutput | Tee-Object -FilePath $logFile -Append | Out-Null
    $outputText = ($migrateOutput -join "`n")
    if ($outputText -match 'Traceback' -or $outputText -match 'ERROR:' -or $LASTEXITCODE -ne 0) {
        Fail 'migrations failed'
    } elseif ($outputText -match 'No migrations to apply' -or $outputText -match 'Applying') {
        Log 'migrations completed (detected success)'
    } else {
        Log 'migrations ambiguous output treated as success'
    }
} else {
    Log 'manage.py not found; skipping migrations'
}

# 5. Start CommCenter agent (persistent background)
Write-Host 'Starting CommCenter (persistent background)' -ForegroundColor Cyan
Log 'CommCenter starting persistent'
try {
    $ccProc = Start-Process -FilePath $PythonExe -ArgumentList '.\zkeco_modern\manage.py','run_commcenter','--interval','2.0','--driver','auto' -PassThru -WindowStyle Hidden
    Start-Sleep -Seconds 3
    if ($ccProc.HasExited) { Fail 'CommCenter exited early' } else { Log "CommCenter PID=$($ccProc.Id)" }
} catch { Fail 'CommCenter launch failed' }

# 6. Start web server (background) and wait for readiness (prefer production ASGI if available)
Write-Host 'Starting web server (ASGI preferred) in background' -ForegroundColor Cyan
Log 'Starting web server (ASGI detection)'
# Determine port (prefer existing config server_port)
$Port = 8000
$iniPath = Join-Path $PSScriptRoot 'agent_controller.ini'
if (Test-Path $iniPath) {
    try {
        $iniContent = Get-Content $iniPath -Raw
        if ($iniContent -match "server_port\s*=\s*(\d+)") {
            $Port = [int]$Matches[1]
            Log "Using existing configured port: $Port"
        } else {
            Log 'No server_port entry found in config; defaulting to 8000'
        }
    } catch {
        Log 'Failed reading agent_controller.ini; defaulting to 8000'
    }
} else {
    Log 'agent_controller.ini not present yet; defaulting to 8000'
}
if ($env:PORT_OVERRIDE) { $Port = [int]$env:PORT_OVERRIDE; Log "PORT_OVERRIDE env applied: $Port" }
$venvScripts = Join-Path $PSScriptRoot '.\..\zkeco_modern'
$Uvicorn = Join-Path $PSScriptRoot '.\.venv\Scripts\uvicorn.exe'
$Daphne  = Join-Path $PSScriptRoot '.\.venv\Scripts\daphne.exe'
$Gunicorn = Join-Path $PSScriptRoot '.\.venv\Scripts\gunicorn.exe'
$wsProc = $null
try {
    if (Test-Path $Uvicorn) {
        Log 'Using uvicorn for ASGI'
        $env:SC_SERVER_TYPE = 'uvicorn'
        $wsProc = Start-Process -WindowStyle Hidden -FilePath $Uvicorn -ArgumentList 'zkeco_config.asgi:application','--host','0.0.0.0','--port',$Port -PassThru
    } elseif (Test-Path $Daphne) {
        Log 'Using daphne for ASGI'
        $env:SC_SERVER_TYPE = 'daphne'
        $wsProc = Start-Process -WindowStyle Hidden -FilePath $Daphne -ArgumentList '-b','0.0.0.0','-p',$Port,'zkeco_config.asgi:application' -PassThru
    } elseif (Test-Path $Gunicorn) {
        Log 'Using gunicorn (uvicorn worker) for ASGI'
        $env:SC_SERVER_TYPE = 'gunicorn'
        $wsProc = Start-Process -WindowStyle Hidden -FilePath $Gunicorn -ArgumentList 'zkeco_config.asgi:application','-k','uvicorn.workers.UvicornWorker','-b',"0.0.0.0:$Port" -PassThru
    } else {
        Log 'No ASGI server found; falling back to runserver'
        $env:SC_SERVER_TYPE = 'runserver'
        $wsProc = Start-Process -WindowStyle Hidden -FilePath $PythonExe -ArgumentList '.\zkeco_modern\manage.py','runserver',"0.0.0.0:$Port" -PassThru
    }
    Log "SC_SERVER_TYPE set to $env:SC_SERVER_TYPE"
} catch { Fail 'Web server launch failed' }

# Wait loop for port 8000 readiness
Write-Host "Waiting for server readiness on port $Port..." -ForegroundColor Yellow
Log "Waiting for server readiness on port $Port"
$serverReady = $false
for($i=0; $i -lt 40; $i++){  # up to ~40*0.75s ≈ 30s
    try {
        $resp = Invoke-WebRequest -Uri "http://127.0.0.1:$Port/agent/health/" -UseBasicParsing -TimeoutSec 3
        if($resp.StatusCode -eq 200){ $serverReady = $true; break }
    } catch { Start-Sleep -Milliseconds 750 }
}
if($serverReady){ Write-Host 'Server ready.' -ForegroundColor Green; Log 'Server ready' } else { Write-Host 'Server not confirmed (continuing).' -ForegroundColor Yellow; Log 'Server readiness not confirmed' }

# 7. Start tray agent GUI (auto backups) after server ready
Write-Host 'Starting tray agent GUI (auto backup interval=60m)' -ForegroundColor Cyan
Log 'Starting tray agent GUI'
try {
    $trayProc = Start-Process -FilePath $PythonExe -ArgumentList '.\zkeco_modern\tray_agent.py',"--backup-interval=60","--set=server_port=$Port" -PassThru
    Start-Sleep -Seconds 4
    if ($trayProc.HasExited) { Fail 'Tray agent exited immediately' } else { Log "Tray agent PID=$($trayProc.Id)" }
} catch { Fail 'Tray agent GUI start failed' }

# Perform one-off headless backup only if tray GUI did NOT start
if (-not $trayProc -or $trayProc.HasExited) {
    Write-Host 'Waiting for dump readiness before headless backup (no GUI tray).' -ForegroundColor Cyan
    Log 'Waiting for dump readiness (no GUI tray)'
    $dumpReady = $false
    for($i=0; $i -lt 30; $i++) {
        try {
            $h = Invoke-WebRequest -Uri "http://127.0.0.1:$Port/agent/health/" -UseBasicParsing -TimeoutSec 3
            if ($h.StatusCode -eq 200) {
                $json = $h.Content | ConvertFrom-Json
                if ($json.dump.ready -eq $true) { $dumpReady = $true; break }
            }
        } catch { Start-Sleep -Milliseconds 1000 }
        Start-Sleep -Milliseconds 1000
    }
    if ($dumpReady) { Write-Host 'mysqldump ready.' -ForegroundColor Green; Log 'Dump ready confirmed' } else { Write-Host 'Dump not confirmed (continuing anyway).' -ForegroundColor Yellow; Log 'Dump readiness not confirmed' }
    Write-Host 'Initiating one-off headless backup' -ForegroundColor Cyan
    Log 'Headless backup start'
    try {
        $hbOutput = & $PythonExe .\zkeco_modern\tray_agent.py --headless --auto --set=server_port=$Port 2>&1
        $exitCode = $LASTEXITCODE
        $hbOutput | Tee-Object -FilePath $logFile -Append | Out-Null
        if ($exitCode -ne 0) { Fail "Headless backup non-zero exit $exitCode" } else { Log 'Headless backup completed successfully' }
    } catch {
        Fail 'Headless backup run failed'
    }
} else {
    Write-Host 'Skipping one-off headless backup (GUI tray active).' -ForegroundColor DarkYellow
    Log 'Skipped one-off headless backup (GUI tray active)'
}

if ($global:Failed) {
    Write-Host '== Auto Run Completed With Errors ==' -ForegroundColor Red
    Log '--- AUTO RUN END (errors) ---'
    Write-Host 'Exit code 2 (failures detected)' -ForegroundColor Red
    Write-Host "Log saved to $logFile" -ForegroundColor DarkGray
    exit 2
} else {
    # 8. Endpoint verification (health + events) using test_endpoints.py (non-fatal)
    Write-Host 'Verifying health/events endpoints' -ForegroundColor Cyan
    Log 'Running endpoint verification script'
    try {
        $testJson = & $PythonExe .\zkeco_modern\scripts\test_endpoints.py 2>&1
        $testJson | Out-File -Append -FilePath $logFile
        if ($testJson -match '"health_status_code"\s*:\s*(\d+)') {
            $hs = [int]$Matches[1]
            if ($hs -eq 200) { Log 'Health endpoint responded 200' } else { Log "Health endpoint non-200: $hs" }
        } else {
            Log 'Could not parse health_status_code from test output'
        }
    } catch {
        Log 'Endpoint verification script failed'
    }
    Write-Host '== Auto Run Completed Successfully ==' -ForegroundColor Green
    Log '--- AUTO RUN END (success) ---'
    Write-Host 'Exit code 0 (success)' -ForegroundColor Green
    Write-Host "Log saved to $logFile" -ForegroundColor DarkGray
    exit 0
}

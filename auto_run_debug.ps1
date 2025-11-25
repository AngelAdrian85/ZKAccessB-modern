# Debug variant: verbose transcript, step timing, extended diagnostics
# Usage: powershell -ExecutionPolicy Bypass -File .\auto_run_debug.ps1

$ErrorActionPreference = 'Stop'
$logRoot = $PSScriptRoot
$logFile = Join-Path $logRoot 'auto_run_debug.log'
$transcript = Join-Path $logRoot 'auto_run_debug_transcript.txt'
Start-Transcript -Path $transcript -Force | Out-Null
Function Log($msg){ $ts=(Get-Date).ToString('u'); "$ts $msg" | Out-File -Append -FilePath $logFile }
Function Stamp($label){ Log "STEP [$label] start"; return [DateTime]::UtcNow }
Function Done($label,$start){ $dur=([DateTime]::UtcNow - $start).TotalSeconds; Log "STEP [$label] end (${dur}s)" }
$global:Failed=$false
Function Fail($msg){ Log "FAIL: $msg"; Write-Host $msg -ForegroundColor Red; $global:Failed=$true }
Log '=== DEBUG AUTO RUN START ==='

$pythonVersion = ''
try { $pythonVersion = & python -c "import sys;print(sys.version)"; Log "Python: $pythonVersion" } catch { Fail 'Python missing' }

$st=Stamp 'venv'
if (-not (Test-Path '.\.venv')) { try { python -m venv .venv } catch { Fail 'venv creation failed' } }
. .\.venv\Scripts\Activate.ps1
Done 'venv' $st

$st=Stamp 'deps'
try { pip install --upgrade pip } catch { Fail 'pip upgrade failed' }
try { pip install -r .\requirements.txt } catch { Fail 'requirements install failed' }
Done 'deps' $st

$st=Stamp 'migrate'
if (Test-Path '.\zkeco_modern\manage.py') { try { python .\zkeco_modern\manage.py migrate --noinput } catch { Fail 'migrations failed' } } else { Log 'manage.py missing' }
Done 'migrate' $st

$st=Stamp 'commcenter.once'
try { python .\zkeco_modern\manage.py run_commcenter --interval 1.0 --driver auto --once } catch { Fail 'commcenter once failed' }
Done 'commcenter.once' $st

$st=Stamp 'webserver'
try { Start-Process -WindowStyle Hidden -FilePath .\.venv\Scripts\python.exe -ArgumentList '.\zkeco_modern\manage.py','runserver','0.0.0.0:8000' } catch { Fail 'web server launch failed' }
Done 'webserver' $st

$st=Stamp 'tray.headless'
try { python .\zkeco_modern\tray_agent.py --headless --auto --run-server --backup-interval=30 --set=server_port=8000 } catch { Fail 'tray automation failed' }
Done 'tray.headless' $st

# Diagnostics summary
Log '--- SUMMARY ---'
try { Log "Backups: $(Get-ChildItem (Join-Path $PSScriptRoot 'zkeco_modern\backups') -Filter db_backup_*.sql | Measure-Object | Select -ExpandProperty Count)" } catch { Log 'Backups dir read failed' }
try { Log "mysqldump PATH: $(Get-Command mysqldump -ErrorAction SilentlyContinue | Select -ExpandProperty Source)" } catch { Log 'mysqldump not in PATH' }

if ($global:Failed) { Log 'DEBUG RUN END (errors)'; Write-Host 'Debug run completed with errors' -ForegroundColor Red; Stop-Transcript | Out-Null; exit 3 } else { Log 'DEBUG RUN END (success)'; Write-Host 'Debug run successful' -ForegroundColor Green; Stop-Transcript | Out-Null; exit 0 }

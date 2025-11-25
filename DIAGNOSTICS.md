# Diagnostics & Operations Guide

## Quick Start
1. Create/activate venv:
   powershell -ExecutionPolicy Bypass -File .\auto_run.ps1
2. Debug (verbose):
   powershell -ExecutionPolicy Bypass -File .\auto_run_debug.ps1

## Individual Component Launch
powershell
. .\.venv\Scripts\Activate.ps1
python .\zkeco_modern\manage.py migrate --noinput
python .\zkeco_modern\manage.py run_commcenter --interval 2.0 --driver auto
# In new terminal
python .\zkeco_modern\manage.py runserver 0.0.0.0:8000
# Tray (GUI)
python .\zkeco_modern\tray_agent.py
# Tray (headless automation)
python .\zkeco_modern\tray_agent.py --headless --auto --run-server --backup-interval=30 --set=server_port=8000

Open monitor UI:
http://localhost:8000/agent/monitor

## Backup Verification
Get latest backups:
Get-ChildItem .\zkeco_modern\backups -Filter db_backup_*.sql | Sort-Object LastWriteTime -Descending | Select-Object -First 5

Force manual backup (GUI if not headless):
python .\zkeco_modern\tray_agent.py --headless

## MySQL Tools Installation (mysqldump)
Run helper script to locate/install mysqldump and update configuration:
powershell -ExecutionPolicy Bypass -File .\install_mysql_tools.ps1

If already installed but want to force refresh:
powershell -ExecutionPolicy Bypass -File .\install_mysql_tools.ps1 -ForceReinstall

After success tray tooltip shows: "Dump OK". If "Dump NOT READY" appears, check:
- Path in `agent_controller.ini` key `mysql_bin`
- Binaries exist: `Get-ChildItem "$((Get-Content .\zkeco_modern\agent_controller.ini | Select-String 'mysql_bin' | % { ($_ -split '=')[1].Trim() }))" -Filter mysqldump.exe`
- Architecture match (64-bit on 64-bit OS)

Exit codes (tray headless):
0 = success (backup ok)
2 = backup failed

## mysqldump Detection
Check configured path:
(Get-Content .\zkeco_modern\agent_controller.ini | Select-String 'mysql_bin')
Test mysqldump:
& (Join-Path (Select-String 'mysql_bin' .\zkeco_modern\agent_controller.ini | ForEach-Object { ($_ -split '=')[1].Trim() }) 'mysqldump.exe') --version
PATH search:
Get-Command mysqldump -ErrorAction SilentlyContinue

## Self-Test Mode
python .\zkeco_modern\tray_agent.py --selftest
Returns JSON including dummy backup creation details.

## Logs
Main automation log: auto_run.log
Debug transcript: auto_run_debug_transcript.txt
Debug log: auto_run_debug.log

## Retention
Configured in `agent_controller.ini` key `backup_retention` (default 10). Old backups pruned automatically after each successful backup.

## Event Monitoring
WebSocket batches with descriptions and codes are displayed. Alarm events colored red. Other events blue.

## Common Issues
- Python missing: Install Python 3.x and ensure in PATH.
- mysqldump missing: Install MySQL tools; update `mysql_bin` path or place mysqldump.exe in PATH.
- Backup fails with header error: Replace invalid mysqldump.exe with proper architecture (match system 64-bit).
- WebSocket not updating: Ensure `run_commcenter` is running continuously (omit --once).

## Continuous Agent Loop
To keep CommCenter running:
python .\zkeco_modern\manage.py run_commcenter --interval 2.0 --driver auto
(Leave process active; tray can still perform backups.)

## Prometheus Metrics
Basic metrics endpoint (if routed) accessible at:
http://localhost:8000/agent/metrics

## Scheduled Task Registration
powershell -ExecutionPolicy Bypass -File .\register_scheduled_task.ps1

## Updating SDK DLL
python .\zkeco_modern\tray_agent.py --set=sdk_dll_path=C:\path\to\dll --headless --auto

## Override Config Keys
python .\zkeco_modern\tray_agent.py --set=backup_retention=20 --set=server_port=8001 --headless --auto

## Unattended Environment Refresh
powershell -ExecutionPolicy Bypass -File .\auto_run.ps1


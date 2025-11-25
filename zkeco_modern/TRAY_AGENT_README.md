# Services Controller Tray Agent

Modern replacement for legacy Windows taskbar "Services Controller" menu.

## Features
- Configure server port & paths (database, backup, video, picture)
- Secure MySQL credential storage via Windows Credential Manager (keyring) fallback to ini
- Start Django Web UI at configured port
- Start / Stop / Restart backend services (memcached + legacy python services)
- Dynamic status icon (green=all services, yellow=partial, red=none) + tooltip
- Database backup (mysqldump) and restore (mysql import) with tray notifications
- Scheduled automatic backups (interval configurable; 0 disables)
- SDK DLL path selection & load test
- License activation shortcut (opens admin site)

## Running (Development)
```powershell
python zkeco_modern\tray_agent.py
```
To enable scheduled backups: Tray menu -> Configure Backup Interval.

## Packaging (Single EXE)
```powershell
pip install pystray pillow pyinstaller keyring
pyinstaller -F -w zkeco_modern\tray_agent.py --name ServicesController
```
## Automation
Scripts provided for full automatic setup and run:

1. `auto_run.ps1` – creates venv, installs dependencies from `requirements.txt`, runs migrations, seeds CommCenter, starts server, executes tray agent in headless auto mode (backup interval 60 mins).
2. `register_scheduled_task.ps1` – registers a Scheduled Task to run `auto_run.ps1` at user logon.

Run manually:
```powershell
powershell -ExecutionPolicy Bypass -File .\auto_run.ps1
```
Register task:
```powershell
powershell -ExecutionPolicy Bypass -File .\register_scheduled_task.ps1
```

Tray agent CLI automation flags:
```powershell
python zkeco_modern\tray_agent.py --headless --auto --run-server --backup-interval=30 --set=server_port=8000 --sdk-dll=C:\path\to\sdk.dll
```
Flags:
- `--headless` : no GUI icon.
- `--auto` : run services + one backup then continue (GUI if not headless).
- `--run-server` : start Django server.
- `--backup-interval=N` : set scheduled backup interval minutes.
- `--set=key=value` : persist configuration key.
- `--sdk-dll=PATH` : set and load SDK DLL.
- `--selftest` : JSON diagnostic run (backup only) and exit.
Optionally provide an ICO file with `--icon icon.ico`.

## Configuration File
Stored at `agent_controller.ini` next to the script. Keys:
- server_port
- database_path
- backup_path
- video_path
- picture_path
- mysql_bin
- mysql_user
- mysql_password (legacy plaintext; superseded by keyring if installed)
- backup_interval_minutes (0 = disabled)
- sdk_dll_path

## Database Backup
Creates `db_backup_<timestamp>.sql` inside `backup_path` using `mysqldump.exe`.
Requires `mysql_bin` to point at folder containing `mysqldump.exe`.
Tray notification indicates success/failure.

## Database Restore
Prompts for an `.sql` file and imports into `zkeco_db` via `mysql.exe`.
Tray notification indicates success/failure.

## Service Control
Uses existing batch script `install_services.bat` for starting services and `net stop` for stopping.
Adjust service names or batch logic as needed. Status icon updates every 30s.

## Extending
- Replace stub service names with actual Windows service names.
- Add dialogs for advanced settings (e.g. Redis URL, SDK DLL path).
- Integrate signed license activation logic if available.

## Safety
If `keyring` is installed, password stored securely in Windows Credential Manager. Otherwise credentials are stored in plain text `agent_controller.ini` (protect ACLs).

## Next Ideas
- Retention policy (keep last N backups)
- Automatic cleanup of old backups
- Encrypt ini fallback password
- Multi-database selection / maintenance tasks

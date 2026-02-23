# ZKAccessB Modern - AI Coding Agent Instructions

## Project Overview

Django 4.2 access control system wrapping legacy ZKTeco hardware/software. **Critical**: System has Python 2.6 vendor paths that inject incompatible `.pyc` files—aggressive `sys.path` filtering is mandatory in all entry points.

**Primary codebase**: `zkeco_modern/` (other variants are legacy/experimental)

## Architecture

### Core Django Apps
- **agent**: Main access control logic (devices, doors, employees, events, WebSockets)
- **iaccess_port**: Legacy UI compatibility layer providing old template routes
- **legacy_models**: Reconstructed models from original MySQL schema (optional)

### Key Components
1. **Tray Agent** ([tray_agent.py](zkeco_modern/agent/management/commands/tray_agent.py)): Windows system tray controller managing Django server, card readers (ACP/Elatec), and CommCenter via `pystray`
2. **ModernCommCenter** ([modern_comm_center.py](zkeco_modern/agent/modern_comm_center.py)): Device polling engine collecting rtlogs and event logs
3. **WebSocket Consumers** ([consumers.py](zkeco_modern/agent/consumers.py)): Real-time updates for monitor, events, access-levels via Channels
4. **ETL Module** ([etl/](zkeco_modern/etl/)): Import legacy employee/device data with state-file resume capability
5. **Card Readers**: External Python scripts (`card_reader_acp.py`, `card_reader_elatec.py`) launched as subprocesses by tray agent

### Data Models ([agent/models.py](zkeco_modern/agent/models.py))
- `Device`: Access panels (TCP/RS485), links to card scanners
- `Door`: Physical doors with time segments, normal-open/multi-card rules  
- `Employee`: Personnel with card numbers, access levels, photos
- `EmployeeCard`: Multi-card support per employee
- `AccessLevel`: Groups of doors + time segments for access control
- `DeviceEventLog`, `DeviceRealtimeLog`: Collected from hardware
- `CommandLog`: Async command queue for device operations

## Critical Setup Requirements

### 1. Environment Variable Override
**MANDATORY**: Legacy system has `DJANGO_SETTINGS_MODULE=mysite.settings` in system environment. Override **every time**:
```powershell
$env:DJANGO_SETTINGS_MODULE = "zkeco_config.settings"
```
[manage.py](zkeco_modern/manage.py) forces this, but terminals/scripts need explicit override.

### 2. Virtual Environment Isolation
Use `.venv` or `.venv_clean` **only**. Never use system Python or `.venv_corrupt`:
```powershell
python -m venv .venv --clear --without-pip
.venv\Scripts\python.exe -m ensurepip --default-pip
.venv\Scripts\pip.exe install -r requirements.txt
```

### 3. sys.path Filtering Pattern
**Copy this to all entry points** ([settings.py](zkeco_modern/zkeco_config/settings.py), [manage.py](zkeco_modern/manage.py)):
```python
bad_path_markers = ("ZKTeco", "python-support", "Python26")
sys.path[:] = [p for p in sys.path if not (p and any(marker in p for marker in bad_path_markers))]
```

## Development Workflows

### Running the Server
```powershell
# Quick launch (PowerShell)
.\tray_launch.ps1  # Handles migrations, collectstatic, starts tray agent + server

# Manual (from zkeco_modern/)
python manage.py migrate
python manage.py runserver 0.0.0.0:8000

# ASGI (WebSockets enabled)
daphne -b 0.0.0.0 -p 8000 zkeco_config.asgi:application
```

### Testing
```powershell
# All tests (note: conftest.py adjusts sys.path)
pytest

# Specific app
python zkeco_modern/manage.py test zkeco_modern.agent.test_core

# Single test
python zkeco_modern/manage.py test zkeco_modern.agent.test_core.CoreAccessTests.test_access_cache
```

### Tray Agent Commands
```powershell
# Standard launch (auto-starts server + CommCenter)
python zkeco_modern/manage.py tray_agent

# Options
--no-server          # Skip Django server
--asgi              # Use Daphne instead of runserver
--no-commcenter     # Skip device polling
--host 0.0.0.0      # Bind address
--port 8000         # Server port
--status-interval 1.0  # Tray tooltip update frequency
```

### CommCenter (Device Polling)
```powershell
python zkeco_modern/manage.py run_commcenter --interval 1.0 --driver stub
# --driver options: stub, socket, zk (ZKTech native), sdk, auto
# --redis --redis-url redis://localhost:6379/0  # Enable Redis queue

# ZKTech Example (real hardware)
python zkeco_modern/manage.py run_commcenter --interval 5.0 --driver zk
```

## Project-Specific Patterns

### 1. URL Routing Structure
- `/agent/*` - Main app (dashboard, monitor, CRUD)
- `/iaccess/*` - Legacy UI routes (templates from old system)
- Admin at `/admin/` (standard Django)
- WebSockets: `/ws/monitor/`, `/ws/events/`, `/ws/access-levels/`

### 2. Template System
Two-layer approach:
- Modern: `agent/templates/agent/*.html` (GitHub dark theme styling)
- Legacy: `iaccess_port/templates/legacy/*.html` (compatibility layer)

### 3. Device Communication
**Never use blocking SDK calls in views**. Pattern:
1. Create `CommandLog` entry with queued status
2. CommCenter processes queue asynchronously
3. Update status to `completed`/`failed`
4. Frontend polls or uses WebSocket for updates

### 4. Card Reader Integration
Launched as subprocesses by tray agent:
```python
# Example from tray_agent.py
subprocess.Popen([sys.executable, 'card_reader_acp.py'], 
                 creationflags=subprocess.CREATE_NO_WINDOW)
```
Heartbeat tracking via `tray_status.json` file.

### 5. Time Zone Handling
Custom middleware ([middleware.py](zkeco_modern/agent/middleware.py)):
- `SystemTimeZoneMiddleware`: Activates system-wide timezone from `SystemSettings`
- `AuditMiddleware`: Tracks user for audit logging

### 6. Migration Testing
**Always test migrations before commit**:
```powershell
python manage.py makemigrations --check --dry-run
python manage.py migrate --plan
```

## Common Issues & Solutions

### Import Errors / "bad magic number"
**Cause**: Python loading `.pyc` from legacy vendor paths.
**Fix**: Add sys.path filter (see Critical Setup #3), ensure using `.venv` not system Python.

### "ModuleNotFoundError: No module named 'mysite'"
**Cause**: Wrong `DJANGO_SETTINGS_MODULE`.
**Fix**: `$env:DJANGO_SETTINGS_MODULE = "zkeco_config.settings"` before running commands.

### WebSocket 404 at /ws/*
**Cause**: Running under `runserver` (doesn't support WebSockets).
**Fix**: Use Daphne: `daphne zkeco_config.asgi:application` or `tray_agent --asgi`.

### Port 8000 Already in Use
**Fix**: `tray_launch.ps1` auto-kills orphaned processes. Manual:
```powershell
netstat -ano | findstr :8000
Stop-Process -Id <PID> -Force
```

### Device Not Polling
1. Check `Device.enabled = True` in DB
2. Verify CommCenter running: `tray_agent.py` menu → CommCenter → Status
3. Check [server.log](zkeco_modern/server.log) for connection errors

## File Conventions

### Naming
- Models: `PascalCase` (e.g., `DeviceEventLog`)
- Views functions: `snake_case` (e.g., `access_dashboard`)
- Templates: `snake_case.html` (e.g., `access_dashboard.html`)
- Management commands: `snake_case.py` (e.g., `run_commcenter.py`)

### Code Organization
```
zkeco_modern/
├── agent/                    # Main app
│   ├── management/commands/  # Django commands
│   ├── templates/agent/      # Modern templates
│   ├── static/agent/         # CSS, JS, images
│   ├── tests/               # pytest tests
│   ├── models.py            # 19 models (see grep output)
│   ├── views.py             # 100+ view functions
│   ├── consumers.py         # 3 WebSocket consumers
│   ├── routing.py           # WebSocket URL routing
│   └── modern_comm_center.py  # Device polling engine
├── zkeco_config/            # Django settings
│   ├── settings.py          # Main config (sys.path filter!)
│   ├── urls.py              # URL routing
│   └── asgi.py              # ASGI config (Channels)
├── iaccess_port/            # Legacy UI app
├── etl/                     # Data import
└── manage.py                # CLI entry (sys.path filter!)
```

## Testing Patterns

### Fixture Usage ([conftest.py](conftest.py))
Custom pytest config adjusts `sys.path` before Django setup. **Don't modify** without understanding import resolution.

### Transaction Management
Tests use Django's `TransactionTestCase` when testing signals or multi-DB operations. Use `TestCase` for simple model tests.

### WebSocket Testing
```python
from channels.testing import WebsocketCommunicator
communicator = WebsocketCommunicator(application, "/ws/monitor/")
connected, _ = await communicator.connect()
```

## External Dependencies

### Hardware SDKs (Optional)
- `plcommpro.dll` - Legacy RS485 protocol
- ZKTeco SDK DLL - Set via `AGENT_SDK_DLL` environment variable
- See [driver_ctypes.py](zkeco_modern/agent/driver_ctypes.py) for loading pattern
### ZKTech Device Socket Driver (NEW)
- Pure Python TCP socket driver: [zk_socket_driver.py](zkeco_modern/agent/drivers/zk_socket_driver.py)
- Supports ZKAccess C3/F3/G series panels
- Protocol: plcommpro binary (proprietary ZKTech protocol)
- No external DLLs required - direct TCP/IP communication
### Card Readers
- ACP: USB HID reader (Windows device)
- Elatec TWN4: USB serial (pyserial communication)

## Key Files to Reference

| Question | Reference File |
|----------|----------------|
| Model definitions | [agent/models.py](zkeco_modern/agent/models.py) |
| URL routing | [agent/urls.py](zkeco_modern/agent/urls.py), [zkeco_config/urls.py](zkeco_modern/zkeco_config/urls.py) |
| Device polling | [modern_comm_center.py](zkeco_modern/agent/modern_comm_center.py) |
| Tray implementation | [tray_agent.py](zkeco_modern/agent/management/commands/tray_agent.py) |
| WebSocket handlers | [consumers.py](zkeco_modern/agent/consumers.py) |
| Settings/config | [settings.py](zkeco_modern/zkeco_config/settings.py) |
| Setup instructions | [README.md](README.md) |
| Migration guide | [MIGRATION.md](MIGRATION.md) |

## When Making Changes

### Adding Models
1. Define in [agent/models.py](zkeco_modern/agent/models.py)
2. `python manage.py makemigrations agent`
3. Review migration file carefully (legacy DB constraints!)
4. Test migration: `python manage.py migrate --plan`
5. Update admin.py if model should appear in admin interface

### Adding Views
1. Add function to [agent/views.py](zkeco_modern/agent/views.py)
2. Add URL route to [agent/urls.py](zkeco_modern/agent/urls.py)
3. Create template in `agent/templates/agent/`
4. Add permission checks: `@login_required`, `@staff_member_required`

### Adding WebSocket Consumers
1. Define consumer in [consumers.py](zkeco_modern/agent/consumers.py)
2. Add route to [routing.py](zkeco_modern/agent/routing.py)
3. Update [asgi.py](zkeco_modern/zkeco_config/asgi.py) if needed
4. Test with `--asgi` flag (Daphne required)

### Modifying Tray Agent
**High impact area**: Changes affect production deployment.
1. Test with `--no-server --no-commcenter` first
2. Verify config persistence ([zkeco_tray_config.ini](zkeco_modern/zkeco_tray_config.ini))
3. Check [tray_status.json](tray_status.json) handling
4. Test shutdown cleanup (port release, process termination)

## Performance Considerations

- **Bulk Operations**: Use `bulk_create()`, `bulk_update()` for >100 records
- **Device Queries**: Index on `enabled`, `scanner_linked` fields (already configured)
- **Event Logs**: Regularly purge old `DeviceRealtimeLog` entries (no auto-cleanup yet)
- **WebSocket Broadcasting**: Use Channels' group messaging, not individual sends

## Security Notes

- **Card Numbers**: Treat as sensitive data, log access attempts
- **Device Passwords**: Encrypted in `Device.comm_password` (placeholder—implement crypto)
- **Admin Access**: All CRUD operations require `is_staff=True`
- **CSRF**: Exempt only specific API endpoints (check `@csrf_exempt` usage)

## Questions to Ask User When Context is Unclear

1. **Deployment target**: Development (SQLite) or production (MySQL)?
2. **Hardware availability**: Real ZKTeco panels or stub/test mode?
3. **WebSocket requirement**: Real-time updates needed or polling acceptable?
4. **Legacy compatibility**: Must support old templates or modern UI only?
5. **Windows-specific**: Need cross-platform or Windows-only solution?

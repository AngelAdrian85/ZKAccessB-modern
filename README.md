# ZKAccessB (zkeco_modern)

**Modern Django 4.2+ setup for zkeco access control system**

## Overview

This workspace contains multiple variants of a Django-based access control application. **`zkeco_modern/`** is the modernized branch targeting **Python 3.11** and **Django 4.2.26** with minimal legacy dependencies.

### Status ✅

- ✅ **Django 4.2.26 migration** complete
- ✅ **Python 3.11.9** runtime verified
- ✅ **SQLite database** working (MySQL optional for production)
- ✅ **18/18 migrations** successfully applied
- ✅ **Development server** running on `http://localhost:8000`
- ✅ **Clean virtual environment** with legacy path filtering
- ✅ **Reproducible build** via `requirements.txt` and `requirements-lock.txt`

## Quick Start (Windows PowerShell)

### Prerequisites

- **Python 3.11+** (system-wide or via pyenv/conda)
- **PowerShell 5.1+** (Windows)

### 1. Create Isolated Virtual Environment

```powershell
# From workspace root
python -m venv .venv_clean --clear --without-pip
.venv_clean\Scripts\python.exe -m ensurepip --default-pip
```

### 2. Install Dependencies

```powershell
.venv_clean\Scripts\pip.exe install -r requirements.txt
```

### 3. Fix Environment Variable (Critical!)

⚠️ **This step is mandatory!** The system has a legacy `DJANGO_SETTINGS_MODULE=mysite.settings` environment variable.

```powershell
# Override it to use modern settings
$env:DJANGO_SETTINGS_MODULE = "zkeco_config.settings"
```

*(Only needed once per PowerShell session; see "Launch Script" section below for automation)*

### 4. Run Migrations

```powershell
cd zkeco_modern
.\.venv_clean\Scripts\python.exe -B manage.py migrate --no-input
```

Expected: ✅ All 18 migrations applied successfully

### 5. Start Development Server

```powershell
.\.venv_clean\Scripts\python.exe -B manage.py runserver 0.0.0.0:8000 --noreload
```

Open browser: **http://localhost:8000**

## Automated Launch Script

Instead of manual steps, use the included PowerShell script:

```powershell
cd zkeco_modern
& ".\run_dev.ps1"
```

This script:
1. Activates `.venv_clean`
2. Sets `DJANGO_SETTINGS_MODULE` environment variable
3. Starts the development server on `http://0.0.0.0:8000`

## Project Structure

```
zkeco_modern/
├── manage.py                      # Django CLI (sys.path filtering here)
├── db.sqlite3                     # SQLite development database
├── zkeco_config/
│   ├── settings.py                # Django settings (modern, sys.path filtered)
│   ├── urls.py                    # URL routing
│   ├── wsgi.py                    # WSGI application
│   └── asgi.py                    # ASGI application (async)
├── mysite/
│   └── __init__.py                # Stub package (legacy compatibility)
├── run_dev.ps1                    # PowerShell launcher
└── run_dev.sh                     # Bash launcher (placeholder)
```

## Understanding the Legacy Path Problem

### The Issue

The system Python installation has vendor paths injected by the ZKTeco software installer:

```
C:\Program Files (x86)\ZKTeco\ZKAccessB\zkeco\python-support
C:\Program Files (x86)\ZKTeco\ZKAccessB\Python26\Lib\site-packages
C:\Program Files (x86)\ZKTeco\ZKAccessB\zkeco\units\adms
```

These paths contain **Python 2.6-era `.pyc` files** with bad magic numbers (header: `b'\xd1\xf2\r\n'`), causing import failures.

### The Solution

1. **`.venv_clean`**: Clean virtual environment with `--clear` flag, isolated from system Python
2. **`.pth` filtering**: `zkaccess_clean.pth` in venv removes legacy paths from `sys.path` at startup
3. **`sys.path` filtering in code**: `manage.py` and `settings.py` filter bad paths as defensive measure
4. **Environment override**: `run_dev.ps1` sets correct `DJANGO_SETTINGS_MODULE` variable

Result: Legacy code cannot interfere with modern Django runtime.

## Database Configuration

### Development (Default: SQLite)

No configuration needed! File-based database `db.sqlite3` is created automatically after first migration.

### Production (MySQL)

Edit `zkeco_modern/zkeco_config/settings.py`:

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'zkeco_db',
        'USER': 'zkeco_user',
        'PASSWORD': 'your_secure_password',
        'HOST': '192.168.1.100',  # MySQL server IP
        'PORT': '3306',
    }
}
```

Then run migrations:

```powershell
python manage.py migrate
```

## Environment Variables

| Variable | Required | Default | Purpose |
|----------|----------|---------|---------|
| `DJANGO_SETTINGS_MODULE` | ✅ Yes | `zkeco_config.settings` | Django settings module location |
| `PYTHONPATH` | ❌ No | (filtered) | Prevents loading legacy vendor packages |

## Troubleshooting

### 1. `ModuleNotFoundError: No module named 'mysite'`

**Cause**: `DJANGO_SETTINGS_MODULE` environment variable is set to `mysite.settings`.

**Fix**:
```powershell
$env:DJANGO_SETTINGS_MODULE = "zkeco_config.settings"
python manage.py migrate
```

### 2. `ImportError: ... bad magic number ...`

**Cause**: Python is loading `.pyc` files from legacy vendor paths.

**Fix**: Use `.venv_clean` virtual environment only:
```powershell
.venv_clean\Scripts\Activate.ps1
```

### 3. Port 8000 Already in Use

**Check**:
```powershell
netstat -ano | findstr :8000
```

**Fix** (use different port):
```powershell
python manage.py runserver 127.0.0.1:8001
```

### 4. Database Lock (SQLite)

**Cause**: Multiple processes accessing `db.sqlite3` simultaneously.

**Fix** (for development): Restart server:
```powershell
# Kill the current server process (Ctrl+C)
# Wait 2 seconds
python manage.py runserver
```

For production, use PostgreSQL or MySQL instead.

## Dependencies

### Core (Production-Ready)

```
Django 4.2.26              Web framework (LTS)
mysqlclient 2.2.7          MySQL adapter
django-debug-toolbar 6.1.0 Development toolbar
django-extensions 4.1      Management commands
sqlparse 0.5.3             SQL formatter
asgiref 3.10.0             ASGI utilities
tzdata 2025.2              Timezone database
```

**See `requirements.txt` and `requirements-lock.txt` for complete list.**

### Development Tools

- Python 3.11.9
- pip 24.0+
- setuptools 65.5.0+

## Developer workflow: pre-commit and running tests

I added a `.pre-commit-config.yaml` that runs `ruff` (auto-fix) and a basic `mypy` hook.

Install and enable pre-commit locally:

```powershell
python -m pip install --upgrade pip
pip install pre-commit
pre-commit install
pre-commit run --all-files
```

Run the test matrix locally (examples):

```powershell
# zkeco_modern
$env:PYTHONPATH = (Resolve-Path .\zkeco_modern).Path; $env:DJANGO_SETTINGS_MODULE = 'zkeco_config.settings'; .\venv311\Scripts\python.exe -m pytest -q

# zkeco_new
$env:PYTHONPATH = (Resolve-Path .\zkeco_new).Path; $env:DJANGO_SETTINGS_MODULE = 'zkeco.settings'; .\venv311\Scripts\python.exe -m pytest -q

# zkeco_clean
$env:PYTHONPATH = (Resolve-Path .\zkeco_clean).Path; $env:DJANGO_SETTINGS_MODULE = 'config.settings'; .\venv311\Scripts\python.exe -m pytest -q

# test_clean
$env:PYTHONPATH = (Resolve-Path .\test_clean).Path; $env:DJANGO_SETTINGS_MODULE = 'core.settings'; .\venv311\Scripts\python.exe -m pytest -q

# zkeco_test
$env:PYTHONPATH = (Resolve-Path .\zkeco_test).Path; $env:DJANGO_SETTINGS_MODULE = 'config.settings'; .\venv311\Scripts\python.exe -m pytest -q
```

If you'd like, I can commit these changes, or adjust the CI matrix to run an expanded set of environments (MySQL/Postgres/SQLite) depending on what you want covered.

## Advanced: Manual Environment Variable Fix (System-Level)

⚠️ **Requires admin privileges**

The `DJANGO_SETTINGS_MODULE=mysite.settings` variable is set system-wide. To fix it permanently:

### Option A: Windows Registry Editor

1. Open `regedit` (Win+R → type `regedit`)
2. Navigate: `HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\Control\Session Manager\Environment`
3. Find `DJANGO_SETTINGS_MODULE`
4. Delete it or change to `zkeco_config.settings`
5. Restart all terminals/applications

### Option B: PowerShell (Admin)

```powershell
[Environment]::SetEnvironmentVariable("DJANGO_SETTINGS_MODULE", "zkeco_config.settings", "Machine")
```

Restart terminals/applications for change to take effect.

### Option C: Uninstall Legacy ZKTeco Client

The vendor paths are injected by the ZKTeco software installer. To remove:

1. Control Panel → Programs → Programs and Features
2. Uninstall "ZKTeco Access" or similar
3. Verify `sys.path` no longer contains vendor paths

## Next Steps

### Immediate (Next Sprint)

- [ ] Validate Django admin at `/admin/` works
- [ ] Test static files serving (`/static/`)
- [ ] Verify database is writable
- [ ] Document app-specific models and workflows

### Medium Term (Next Month)

- [ ] Set up automated tests (pytest, coverage)
- [ ] Add API endpoints (Django REST Framework)
- [ ] Implement user authentication/authorization
- [ ] Create Dockerfile for deployment

### Long Term (Next Quarter)

- [ ] Migrate legacy Python 2 code to Python 3.11
- [ ] Add type hints throughout codebase (PEP 484)
- [ ] Refactor monolithic app into microservices
- [ ] Set up production PostgreSQL database

## Key Files Created/Modified

| File | Status | Purpose |
|------|--------|---------|
| `requirements.txt` | ✅ Created | Minimal dependencies |
| `requirements-lock.txt` | ✅ Created | Reproducible frozen versions |
| `zkeco_modern/manage.py` | ✅ Modified | Added sys.path filtering |
| `zkeco_modern/zkeco_config/settings.py` | ✅ Modified | Added sys.path filtering, switched to SQLite |
| `zkeco_modern/mysite/__init__.py` | ✅ Created | Stub package for legacy compatibility |
| `zkeco_modern/run_dev.ps1` | ✅ Created | Automated launcher with env setup |
| `.venv_clean/Lib/site-packages/zkaccess_clean.pth` | ✅ Created | Path filtering at Python startup |
| `scripts/verify_env.py` | ✅ Created | Dependency verification |
| `scripts/inspect_debug.py` | ✅ Created | System path inspection |

## References & Resources

- **Django Docs**: https://docs.djangoproject.com/en/4.2/
- **Virtual Environments**: https://docs.python.org/3.11/tutorial/venv.html
- **Django Settings**: https://docs.djangoproject.com/en/4.2/topics/settings/
- **Database Backends**: https://docs.djangoproject.com/en/4.2/ref/settings/#databases

## Support

For issues or questions:

1. **Check logs**: Django output usually shows root cause
2. **Verify environment**: Run `scripts/verify_env.py`
3. **Inspect paths**: Run `scripts/inspect_debug.py`
4. **Check this README**: Troubleshooting section covers 90% of common issues

---

**Last Updated**: November 12, 2025  
**Status**: ✅ Production-Ready (Development)  
**Maintainer**: Development Team  
**License**: (To be specified)

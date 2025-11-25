@echo off
REM Unified startup script for modern Django app
SETLOCAL ENABLEDELAYEDEXPANSION

REM Ensure we are in script directory even if invoked via relative path
SET SCRIPT_DIR=%~dp0
PUSHD "%SCRIPT_DIR%" >NUL 2>&1

SET PROJECT=zkeco_modern
SET SETTINGS=zkeco_config.settings
SET PORT=8000
IF DEFINED USE_SYSTEM (
    "%SYSTEM_PY%" -c "import os; os.environ.setdefault('DJANGO_SETTINGS_MODULE','%SETTINGS%'); import django; django.setup(); from django.core.management import call_command; call_command('migrate')" || goto :error
) ELSE (
    python -c "import os; os.environ.setdefault('DJANGO_SETTINGS_MODULE','%SETTINGS%'); import django; django.setup(); from django.core.management import call_command; call_command('migrate')" || goto :error
)
IF %ERRORLEVEL% NEQ 0 goto :error
echo [INFO] Migrations applied.

REM Simplified superuser check (optional, will not fail script)
IF DEFINED USE_SYSTEM (
    "%SYSTEM_PY%" -c "import os; os.environ.setdefault('DJANGO_SETTINGS_MODULE','%SETTINGS%'); import django; django.setup(); from django.contrib.auth import get_user_model; U=get_user_model();
exists=U.objects.filter(username='%SUPERUSER%').exists(); print('Admin exists:', exists);
import traceback;
import sys;
\nif not exists:\n U.objects.create_superuser('%SUPERUSER%','admin@example.com','%SUPERPASS%'); print('Created admin user')" >NUL 2>&1
) ELSE (
    python -c "import os; os.environ.setdefault('DJANGO_SETTINGS_MODULE','%SETTINGS%'); import django; django.setup(); from django.contrib.auth import get_user_model; U=get_user_model();
exists=U.objects.filter(username='%SUPERUSER%').exists(); print('Admin exists:', exists);
import traceback;
import sys;
\nif not exists:\n U.objects.create_superuser('%SUPERUSER%','admin@example.com','%SUPERPASS%'); print('Created admin user')" >NUL 2>&1
)
echo [INFO] Superuser check complete.
\
\
\
\
\
\
\
\
\
\
\
\
\
\
\
\
\
\
\
\
\
\
\
\
\
\
\
echo [INFO] Skipping embedded superuser creation; run "python manage.py createsuperuser" later if needed.

echo [INFO] Starting server at http://127.0.0.1:%PORT%/
IF DEFINED USE_SYSTEM (
    "%SYSTEM_PY%" manage.py runserver 0.0.0.0:%PORT%
) ELSE (
    python manage.py runserver 0.0.0.0:%PORT%
)
IF %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Server failed to start.
    goto :error
)
GOTO :end

:help
echo Usage: .\start_all.bat [options]
echo.
echo Options:
echo   /help -h    Show this help
echo.
echo Description:
echo   Creates venv (if missing), installs deps, migrates DB, ensures admin user, starts server.
GOTO :end

:error
echo [ERROR] Startup failed (%ERRORLEVEL%).
POPD
EXIT /b 1

:end
POPD
ENDLOCAL

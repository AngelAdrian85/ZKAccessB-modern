@echo off
REM Minimal startup script
SETLOCAL
SET SETTINGS=zkeco_config.settings
SET PORT=8000

IF EXIST .venv\Scripts\activate.bat (
  CALL .venv\Scripts\activate.bat
) ELSE (
  echo [WARN] .venv missing, using system Python
)

IF EXIST requirements.txt (
  echo [INFO] Installing dependencies
  python -m pip install --upgrade pip >NUL 2>&1
  python -m pip install -r requirements.txt || goto :error
) ELSE (
  echo [WARN] requirements.txt not found; skipping dependency install
)

echo [INFO] Applying migrations
python -c "import os; os.environ.setdefault('DJANGO_SETTINGS_MODULE','%SETTINGS%'); import django; django.setup(); from django.core.management import call_command; call_command('migrate')" || goto :error

echo [INFO] Starting server at http://127.0.0.1:%PORT%/
python manage.py runserver 0.0.0.0:%PORT%
IF %ERRORLEVEL% NEQ 0 goto :error
GOTO :end

:error
echo [ERROR] Startup failed (%ERRORLEVEL%).
EXIT /b 1

:end
ENDLOCAL
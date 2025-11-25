@echo off
REM Minimal clean startup (use this instead of start_all.bat)
SETLOCAL
SET SETTINGS=zkeco_config.settings
SET PORT=8000
SET VENV=.venv_new
REM Force ignoring legacy .venv if present
IF EXIST .venv (
  echo [INFO] Detected legacy .venv (ignored, using %VENV%)
)

IF NOT EXIST %VENV%\Scripts\activate.bat (
  echo [INFO] Creating virtual environment %VENV%
  py -3 -m venv %VENV% || goto :error
)
CALL %VENV%\Scripts\activate.bat || goto :error

IF EXIST requirements.txt (
  echo [INFO] Installing dependencies (first run only)
  python -m pip install --upgrade pip >NUL 2>&1
  python -m pip install -r requirements.txt || goto :error
) ELSE (
  echo [WARN] requirements.txt missing; skipping install
)

echo [INFO] Applying migrations
python -c "import os; os.environ.setdefault('DJANGO_SETTINGS_MODULE','%SETTINGS%'); import django; django.setup(); from django.core.management import call_command; call_command('migrate')" || goto :error

echo [INFO] Running agent tests (smoke)
python zkeco_modern\manage.py test zkeco_modern.agent.test_core --verbosity=1 || echo [WARN] Tests failed (continuing) 

echo [INFO] Ensuring admin user
python -c "import os; os.environ.setdefault('DJANGO_SETTINGS_MODULE','%SETTINGS%'); import django; django.setup(); from django.contrib.auth import get_user_model; U=get_user_model(); u=U.objects.filter(username='admin').exists(); print('Admin exists:',u);\nimport traceback;\nif not u: U.objects.create_superuser('admin','admin@example.com','adminpass'); print('Created admin: admin / adminpass')" || echo [WARN] Superuser skipped

echo [INFO] Starting server http://127.0.0.1:%PORT%/
REM Use root shim manage.py if exists else fallback to zkeco_modern/manage.py
IF EXIST manage.py (
  python manage.py runserver 0.0.0.0:%PORT% || goto :error
) ELSE (
  python zkeco_modern\manage.py runserver 0.0.0.0:%PORT% || goto :error
)
GOTO :end

:error
echo [ERROR] Startup failed (%ERRORLEVEL%). Possible causes:
echo   - Missing dependencies (re-run to install)
echo   - Port %PORT% already in use
echo   - Invalid DJANGO_SETTINGS_MODULE (%SETTINGS%)
echo   - Database locked or inaccessible
EXIT /b 1

:end
ENDLOCAL

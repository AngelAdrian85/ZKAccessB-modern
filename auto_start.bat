@echo off
SETLOCAL ENABLEDELAYEDEXPANSION
SET SETTINGS=zkeco_config.settings
SET PORT=8000
SET VENV=.venv_new
SET TEST_MODULE=zkeco_modern.agent.test_core

REM Force usage of new environment even if old .venv exists
IF EXIST .venv (
  echo [INFO] Ignoring legacy .venv (corrupt) in favor of %VENV%
)
IF NOT EXIST %VENV%\Scripts\python.exe (
  echo [INFO] Creating virtual environment %VENV%
  py -3 -m venv %VENV% || goto :error
)

REM Use direct python path; avoid activate to prevent PATH confusion if old venv auto-activates
SET PY_BIN=%VENV%\Scripts\python.exe

IF EXIST requirements.txt (
  echo [INFO] Ensuring dependencies
  %PY_BIN% -m pip install --upgrade pip >NUL 2>&1
  %PY_BIN% -m pip install -r requirements.txt || goto :error
)

echo [INFO] Applying migrations
%PY_BIN% -c "import os; os.environ.setdefault('DJANGO_SETTINGS_MODULE','%SETTINGS%'); import django; django.setup(); from django.core.management import call_command; call_command('migrate')" || goto :error

echo [INFO] Skipping admin auto-create (manual creation recommended: manage.py createsuperuser)

echo [INFO] Running tests (%TEST_MODULE%)
%PY_BIN% zkeco_modern\manage.py test %TEST_MODULE% --verbosity=1 || goto :error

echo [INFO] Starting server on port %PORT%
%PY_BIN% zkeco_modern\manage.py runserver 0.0.0.0:%PORT%
GOTO :end

:error
echo [ERROR] Automation failed (%ERRORLEVEL%).
EXIT /b 1

:end
ENDLOCAL

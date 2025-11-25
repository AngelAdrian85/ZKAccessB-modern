@echo off
setlocal ENABLEDELAYEDEXPANSION
REM Ensure modern virtual environment
if not exist .venv_new (
  echo [setup] Creating .venv_new virtual environment...
  python -m venv .venv_new || goto :fail
  echo [setup] Installing dependencies...
  .\.venv_new\Scripts\python.exe -m pip install -r requirements.txt || goto :fail
)
call .\.venv_new\Scripts\activate
set DJANGO_SETTINGS_MODULE=zkeco_config.settings
echo [tests] Running agent test suite...
python zkeco_modern\manage.py test zkeco_modern.agent.test_core --verbosity=2
set EXITCODE=%ERRORLEVEL%
if %EXITCODE% NEQ 0 goto :fail
echo [tests] Completed successfully.
endlocal
exit /b 0
:fail
echo [tests] FAILED with exit code %EXITCODE%
endlocal
exit /b %EXITCODE%

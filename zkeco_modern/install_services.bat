@echo off
@echo off
echo [modern-services] Starting service scaffold...
REM Elevation check (Administrators SID)
whoami /groups | find "S-1-5-32-544" >NUL
if %ERRORLEVEL% NEQ 0 (
  echo [modern-services] Not elevated: service create operations skipped.
  echo Run this from an Administrator PowerShell / CMD to actually create services.
  goto :SHOWPLAN
)

SETLOCAL ENABLEDELAYEDEXPANSION
set BASE=%~dp0
set PY=%BASE%\.venv\Scripts\python.exe
if not exist "%PY%" set PY=python

echo [modern-services] Using Python: %PY%

REM Optional: create a wrapper script for Django server service
set SERVER_WRAP=%BASE%run_server_service.cmd
(
  echo @echo off
  echo set DJANGO_SETTINGS_MODULE=zkeco_config.settings
  echo set PORT=%%1
  echo if "%%PORT%%"=="" set PORT=8000
  echo rem Prefer uvicorn -> daphne -> gunicorn -> fallback runserver
  echo if exist "%BASE%\.venv\Scripts\uvicorn.exe" (
  echo.  "%BASE%\.venv\Scripts\uvicorn.exe" zkeco_config.asgi:application --host 0.0.0.0 --port %%PORT%%
  echo ) else if exist "%BASE%\.venv\Scripts\daphne.exe" (
  echo.  "%BASE%\.venv\Scripts\daphne.exe" -b 0.0.0.0 -p %%PORT%% zkeco_config.asgi:application
  echo ) else if exist "%BASE%\.venv\Scripts\gunicorn.exe" (
  echo.  "%BASE%\.venv\Scripts\gunicorn.exe" zkeco_config.asgi:application -k uvicorn.workers.UvicornWorker -b 0.0.0.0:%%PORT%%
  echo ) else (
  echo.  "%PY%" "%BASE%zkeco_modern\manage.py" runserver 0.0.0.0:%%PORT%% --settings=zkeco_config.settings
  echo )
) > "%SERVER_WRAP%"

REM Create CommCenter wrapper
set COMM_WRAP=%BASE%run_commcenter_service.cmd
(
  echo @echo off
  echo set DJANGO_SETTINGS_MODULE=zkeco_config.settings
  echo "%PY%" "%BASE%zkeco_modern\manage.py" run_commcenter --interval 2.0 --driver auto
) > "%COMM_WRAP%"

REM Install services using sc (simple type share process). For production use NSSM for better control.
sc query SC_DjangoWeb >NUL 2>&1
if %ERRORLEVEL% NEQ 0 (
  sc create SC_DjangoWeb binPath= "%SERVER_WRAP% 8000" start= auto depend= TCPIP
  echo [modern-services] Created SC_DjangoWeb
) else (
  echo [modern-services] Service SC_DjangoWeb already exists
)

sc query SC_CommCenter >NUL 2>&1
if %ERRORLEVEL% NEQ 0 (
  sc create SC_CommCenter binPath= "%COMM_WRAP%" start= auto depend= TCPIP
  echo [modern-services] Created SC_CommCenter
) else (
  echo [modern-services] Service SC_CommCenter already exists
)

echo Attempting to start services...
net start SC_DjangoWeb >NUL 2>&1 && echo [start] SC_DjangoWeb started || echo [start] SC_DjangoWeb failed
net start SC_CommCenter >NUL 2>&1 && echo [start] SC_CommCenter started || echo [start] SC_CommCenter failed

:SHOWPLAN
echo --------------------------------------------------
echo Service Plan:
echo  SC_DjangoWeb    -> runs production ASGI server (uvicorn/daphne/gunicorn fallback to runserver)
echo  SC_CommCenter   -> runs commcenter event loop
echo For production replace 'runserver' with gunicorn/uvicorn or WSGI service.
echo Remove services: sc stop SC_DjangoWeb ^& sc delete SC_DjangoWeb (same for SC_CommCenter)
echo --------------------------------------------------
exit /b 0

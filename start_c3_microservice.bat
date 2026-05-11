@echo off
REM start_c3_microservice.bat - wrapper to launch c3_microservice in background
setlocal enabledelayedexpansion
set ROOT=%~dp0
set PY=%ROOT%\.venv\Scripts\python.exe
pushd %~dp0
echo [START_MICROSERVICE] launching at %DATE% %TIME% > "%ROOT%c3_microservice_stdout.log"
start "" /B "%PY%" "%~dp0c3_microservice\main.py" >> "%ROOT%c3_microservice_stdout.log" 2>> "%ROOT%c3_microservice_stderr.log"
popd
endlocal

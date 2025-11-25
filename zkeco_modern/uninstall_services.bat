@echo off
setlocal
echo [uninstall-services] Starting removal sequence...
REM Elevation check
whoami /groups | find "S-1-5-32-544" >NUL
if %ERRORLEVEL% NEQ 0 (
  echo [uninstall-services] Not elevated. Re-run from Administrator shell.
  goto :END
)
for %%S in (SC_DjangoWeb SC_CommCenter ZKECOMemCachedService ServiceADMS ServiceBackupDB) do (
  sc query %%S >NUL 2>&1
  if %ERRORLEVEL% EQU 0 (
    echo Stopping %%S...
    net stop %%S >NUL 2>&1
    echo Deleting %%S...
    sc delete %%S >NUL 2>&1 && echo [removed] %%S || echo [skip] %%S delete failed
  ) else (
    echo [missing] %%S not found
  )
)
:END
echo [uninstall-services] Complete.
endlocal
exit /b 0

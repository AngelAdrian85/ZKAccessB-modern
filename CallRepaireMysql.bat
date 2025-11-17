for /f %%i IN ('dir  %2\*.MYI /b /l') DO %1\myisamchk %2\%%i -r


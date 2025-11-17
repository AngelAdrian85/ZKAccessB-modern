@echo off
REM Local server runner for zkeco_modern
set DJANGO_SETTINGS_MODULE=zkeco_config.settings
if not exist logs mkdir logs
..\.venv_clean\Scripts\python.exe -B manage.py runserver 0.0.0.0:8000 >> logs\devserver.log 2>&1
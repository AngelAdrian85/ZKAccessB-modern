# Launch script for zkeco_modern Django development server
# Clears legacy environment variables and starts the server

$env:DJANGO_SETTINGS_MODULE = "zkeco_config.settings"

Push-Location $PSScriptRoot
& ".\.venv_clean\Scripts\python.exe" -B manage.py runserver 0.0.0.0:8000 --noreload

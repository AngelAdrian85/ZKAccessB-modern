#!/bin/bash
# Launch script for zkeco_modern Django development server
# Clears legacy environment variables and starts the server

export DJANGO_SETTINGS_MODULE=zkeco_config.settings
unset DJANGO_SETTINGS_MODULE
export DJANGO_SETTINGS_MODULE=zkeco_config.settings

cd "$(dirname "$0")"
.venv_clean/Scripts/python.exe -B manage.py runserver 0.0.0.0:8000 --noreload

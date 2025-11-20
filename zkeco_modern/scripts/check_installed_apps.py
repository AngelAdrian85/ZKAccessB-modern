#!/usr/bin/env python3
import os
import importlib
import sys
from pathlib import Path
os.environ.setdefault('DJANGO_SETTINGS_MODULE','zkeco_config.settings')
# include legacy
os.environ['INCLUDE_LEGACY'] = '1'

reports = Path(__file__).resolve().parent.parent / 'reports'
reports.mkdir(parents=True, exist_ok=True)
out = reports / 'static_checks.txt'

with out.open('w', encoding='utf-8') as f:
    f.write('STATIC ENV CHECKS\n')
    f.write('=================\n')
    f.write(f'WORKDIR: {Path.cwd()}\n')
    f.write('\nPIP LIST:\n')
    pip_file = Path(__file__).resolve().parent.parent / 'reports' / 'pip_list.txt'
    if pip_file.exists():
        f.write(pip_file.read_text(encoding='utf-8'))
    else:
        f.write('pip list not found\n')

    f.write('\nINSTALLED_APPS IMPORT CHECKS:\n')
    try:
        import django
        django.setup()
        from django.conf import settings
        apps = list(settings.INSTALLED_APPS)
        f.write(f'Found INSTALLED_APPS: {len(apps)} entries\n')
        for app in apps:
            try:
                importlib.import_module(app)
                f.write(f'OK: imported {app}\n')
            except Exception as e:
                # try top-level module
                top = app.split('.')[0]
                try:
                    importlib.import_module(top)
                    f.write(f'WARN: could not import full {app} but top-level {top} imported\n')
                except Exception:
                    f.write(f'ERROR: cannot import {app} (error: {e})\n')
    except Exception as e:
        f.write('Failed to run django.setup(): ' + str(e) + '\n')

print('DONE', out)

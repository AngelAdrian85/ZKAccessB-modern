import os
import sys
BASE = os.path.dirname(os.path.dirname(__file__))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zkeco_config.settings')
sys.path.insert(0, os.path.join(BASE, 'zkeco_modern'))
import django
django.setup()

script = os.path.join(BASE, 'runtime_scripts', 'check_status.py')
with open(script, 'r', encoding='utf-8') as fh:
    code = fh.read()
exec(compile(code, script, 'exec'))

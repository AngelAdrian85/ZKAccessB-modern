import os, socket, time, json
from pathlib import Path

# Ensure Django is configured
os.environ.setdefault('DJANGO_SETTINGS_MODULE','zkeco_config.settings')
import django
try:
    django.setup()
except Exception as e:
    print(json.dumps({'ok': False, 'stage': 'django.setup', 'error': str(e)})); raise

from zkeco_modern.agent.management.commands import tray_agent as T

results = {
    'ok': True,
    'wsgi_started': False,
    'asgi_requested_started': False,
    'persisted_mode': None,
    'error_line_example': None,
}

# Helper to get free port
s = socket.socket(); s.bind(('127.0.0.1',0)); free_port = s.getsockname()[1]; s.close()

# Stop any existing server
try:
    T._stop_server()
except Exception:
    pass

# 1) Start WSGI on a free port
try:
    ok = T._start_server(host='127.0.0.1', port=free_port, asgi=False)
    up = ok and (T._SERVER_PROC is not None) and (T._SERVER_PROC.poll() is None)
    results['wsgi_started'] = bool(up)
finally:
    T._stop_server(); time.sleep(0.5)

# 2) Request ASGI (should start; falls back to WSGI if Daphne missing)
s = socket.socket(); s.bind(('127.0.0.1',0)); free_port2 = s.getsockname()[1]; s.close()
try:
    ok2 = T._start_server(host='127.0.0.1', port=free_port2, asgi=True)
    up2 = ok2 and (T._SERVER_PROC is not None) and (T._SERVER_PROC.poll() is None)
    results['asgi_requested_started'] = bool(up2)
    results['persisted_mode'] = T._CONFIG.get('tray','server_mode', fallback='asgi')
finally:
    T._stop_server(); time.sleep(0.5)

# 3) Log parsing sanity: write a sample traceback and ensure we get the final error line
logp = (Path(getattr(__import__('django').conf.settings, 'BASE_DIR', Path.cwd()))/ 'server.log')
try:
    sample = 'Info: booting\nTraceback (most recent call last):\n  File "x.py", line 1, in <module>\n    boom()\nValueError: bad config\n'
    logp.write_text(sample, encoding='utf-8')
except Exception:
    pass
results['error_line_example'] = T._read_first_error_from_log()

print(json.dumps(results))

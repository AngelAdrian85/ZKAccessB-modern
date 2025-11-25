import os, socket, time, json, hashlib
from pathlib import Path

os.environ.setdefault('DJANGO_SETTINGS_MODULE','zkeco_config.settings')
import django
try:
    django.setup()
except Exception as e:
    print(json.dumps({'ok': False, 'stage': 'django.setup', 'error': str(e)}))
    raise

from zkeco_modern.agent.management.commands import tray_agent as T

results = {
    'ok': True,
    'server_start_stop_cycle': False,
    'asgi_request_fallback_mode': None,
    'restart_services_both_up': False,
    'commcenter_cycle': False,
    'icon_color_mapping': {},
    'license_roundtrip': False,
    'error_popup_logic_simulated': False,
}

def free_port():
    s = socket.socket(); s.bind(('127.0.0.1',0)); p = s.getsockname()[1]; s.close(); return p

# 1) Server start/stop WSGI
try:
    T._stop_server()
    p1 = free_port()
    ok = T._start_server(host='127.0.0.1', port=p1, asgi=False)
    up = ok and T._SERVER_PROC is not None and T._SERVER_PROC.poll() is None
    T._stop_server(); time.sleep(0.4)
    down = T._SERVER_PROC is None
    results['server_start_stop_cycle'] = (up and down)
except Exception as e:
    results['server_start_stop_cycle'] = False

# 2) ASGI request fallback (no daphne) -> should set mode wsgi and still start
try:
    T._stop_server()
    p2 = free_port()
    ok2 = T._start_server(host='127.0.0.1', port=p2, asgi=True)
    up2 = ok2 and T._SERVER_PROC is not None and T._SERVER_PROC.poll() is None
    mode = T._CONFIG.get('tray','server_mode', fallback='asgi')
    T._stop_server(); time.sleep(0.2)
    results['asgi_request_fallback_mode'] = mode if up2 else 'failed'
except Exception:
    results['asgi_request_fallback_mode'] = 'error'

# 3) CommCenter start/stop
try:
    T._stop_comm_center()
    c = T._start_comm_center()
    started = c is not None
    time.sleep(0.6)
    T._stop_comm_center()
    stopped = T._CENTER is None
    results['commcenter_cycle'] = started and stopped
except Exception:
    results['commcenter_cycle'] = False

# 4) Restart Services (simulate lambda): stop -> start server+center
try:
    T._stop_server(); T._stop_comm_center();
    p3 = free_port()
    # force config mode read
    mode_flag = T._CONFIG.get('tray','server_mode', fallback='wsgi') == 'asgi'
    ok_rs = T._start_server(host='127.0.0.1', port=p3, asgi=mode_flag)
    c2 = T._start_comm_center()
    both_up = ok_rs and (T._SERVER_PROC is not None and T._SERVER_PROC.poll() is None) and c2 is not None
    results['restart_services_both_up'] = bool(both_up)
    T._stop_server(); T._stop_comm_center()
except Exception:
    results['restart_services_both_up'] = False

# 5) Icon color mapping logic
try:
    results['icon_color_mapping'] = {
        'none_none': T._choose_icon_color(False, False),
        'srv_only': T._choose_icon_color(True, False),
        'center_only': T._choose_icon_color(False, True),
        'both': T._choose_icon_color(True, True),
    }
except Exception:
    pass

# 6) License encrypt/decrypt + validity stub
try:
    sample_body = 'PROD-STD-20250101-001-XYZ'
    hmac8 = hashlib.sha256((django.conf.settings.SECRET_KEY + sample_body).encode()).hexdigest()[:8].upper()
    license_key = sample_body + '-' + hmac8
    enc = T._encrypt(license_key)
    dec = T._decrypt(enc)
    results['license_roundtrip'] = (dec == license_key and T._license_valid(dec))
except Exception:
    results['license_roundtrip'] = False

# 7) Error popup logic simulation: write fake traceback and capture parsing function result
try:
    logp = Path(django.conf.settings.BASE_DIR)/'server.log'
    logp.write_text('Booting\nTraceback (most recent call last):\n  File "a.py", line 1\n    bad()\nRuntimeError: boom\n', encoding='utf-8')
    parsed = T._read_first_error_from_log()
    results['error_popup_logic_simulated'] = parsed.endswith('RuntimeError: boom')
except Exception:
    results['error_popup_logic_simulated'] = False

print(json.dumps(results))

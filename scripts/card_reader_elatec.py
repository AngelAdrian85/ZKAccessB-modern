import time
import sys
import json
import requests
import os

HEARTBEAT_PATH = os.path.join(os.path.expanduser('~'), 'zkeco_reader_heartbeat_elatec.json')

try:
    import serial  # pyserial
except Exception:
    serial = None

PUSH_URL = None
EVAL_URL = None
ERROR_URL = None
SERIAL_PORT = 'COM3'  # change as needed
BAUDRATE = 9600
CFG = None
INI_PORT = None
try:
    import os, json as _json
    cfg_path = os.path.join(os.path.dirname(__file__), 'card_readers.json')
    if os.path.exists(cfg_path):
        with open(cfg_path,'r',encoding='utf-8') as f:
            CFG = _json.load(f)
    # Read tray port from zkeco_tray_config.ini in user home
    ini_path = os.path.join(os.path.expanduser('~'), 'zkeco_tray_config.ini')
    if os.path.exists(ini_path):
        import configparser
        cp = configparser.ConfigParser(); cp.read(ini_path)
        if cp.has_section('tray') and cp.has_option('tray','port'):
            try:
                INI_PORT = int(cp.get('tray','port'))
            except Exception:
                INI_PORT = None
except Exception:
    CFG = None
    INI_PORT = None

# Build URLs using detected port, default to 8000
BASE = f"http://127.0.0.1:{INI_PORT or 8000}"
PUSH_URL = BASE + '/agent/api/cards/read/push/'
EVAL_URL = BASE + '/agent/api/access/evaluate-open/'
ERROR_URL = BASE + '/agent/api/listeners/error/'

# Elatec readers often output hex or decimal card numbers followed by newline
# Optionally they can be configured to prefix with 'CARD:'

def push_card(card_number: str, source: str='elatec'):
    try:
        payload = { 'card_number': card_number, 'source': source }
        el_cfg = (CFG or {}).get('elatec') or {}
        if 'device_id' in el_cfg: payload['device_id'] = el_cfg['device_id']
        if 'door_id' in el_cfg: payload['door_id'] = el_cfg['door_id']
        if 'door_pk' in el_cfg: payload['door_pk'] = el_cfg['door_pk']
        requests.post(PUSH_URL, json=payload, timeout=2)
        try:
            requests.post(EVAL_URL, json=payload, timeout=2)
        except Exception:
            pass
    except Exception:
        pass

def run_serial():
    if serial is None:
        print('[ELATEC] pyserial not installed. Install with: pip install pyserial')
        return
    failures = 0
    backoff = 0.5
    while True:
        ser = None
        try:
            ser = serial.Serial(SERIAL_PORT, BAUDRATE, timeout=1)
            print(f"[ELATEC] Listening on {SERIAL_PORT} @ {BAUDRATE}")
            backoff = 0.5  # reset backoff after successful open
            buf = b''
            while True:
                data = ser.read(1024)
                if data:
                    buf += data
                    while b'\n' in buf:
                        line, buf = buf.split(b'\n', 1)
                        s = line.decode('utf-8', errors='ignore').strip()
                        if not s:
                            continue
                        if s.upper().startswith('CARD:'):
                            push_card(s.split(':',1)[1].strip(), 'elatec')
                        else:
                            # assume whole line is card number
                            push_card(s.strip(), 'elatec')
                    # Touch heartbeat on data activity
                    try:
                        hb = { 'ts': time.time(), 'source': 'elatec', 'port': SERIAL_PORT }
                        with open(HEARTBEAT_PATH,'w',encoding='utf-8') as f:
                            json.dump(hb, f)
                    except Exception:
                        pass
                else:
                    time.sleep(0.05)
                    # periodic heartbeat even without data
                    try:
                        hb = { 'ts': time.time(), 'source': 'elatec', 'port': SERIAL_PORT }
                        with open(HEARTBEAT_PATH,'w',encoding='utf-8') as f:
                            json.dump(hb, f)
                    except Exception:
                        pass
        except KeyboardInterrupt:
            break
        except Exception as e:
            print('[ELATEC] Error:', e)
            failures += 1
            # Report error to server cache
            try:
                requests.post(ERROR_URL, json={'name':'elatec','message': f'port open failed: {SERIAL_PORT}'}, timeout=2)
            except Exception:
                pass
            # Auto-disable after 3 consecutive failures
            if failures >= 3:
                try:
                    import os, json as _json
                    cfg_path = os.path.join(os.path.dirname(__file__), 'card_readers.json')
                    cfg = {}
                    if os.path.exists(cfg_path):
                        with open(cfg_path,'r',encoding='utf-8') as f:
                            cfg = _json.load(f)
                    el = cfg.get('elatec') or {}
                    el['enabled'] = False
                    cfg['elatec'] = el
                    with open(cfg_path,'w',encoding='utf-8') as f:
                        _json.dump(cfg, f, indent=2)
                    print('[ELATEC] Auto-disabled after repeated failures')
                    # Report disabled state
                    try:
                        requests.post(ERROR_URL, json={'name':'elatec','message': 'auto-disabled after port open failures'}, timeout=2)
                    except Exception:
                        pass
                    break
            # Exponential backoff before retrying open
            time.sleep(backoff)
            backoff = min(backoff * 2, 5.0)
        finally:
            try:
                if ser:
                    ser.close()
            except Exception:
                pass

if __name__ == '__main__':
    if len(sys.argv) > 1:
        SERIAL_PORT = sys.argv[1]
    run_serial()

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
ERROR_URL = None
SERIAL_PORT = 'COM3'  # change as needed
BAUDRATE = 9600
CFG = None
INI_PORT = None
try:
    import os, json as _json
    cfg_path = os.path.join(os.path.dirname(__file__), 'card_readers.json')
    if os.path.exists(cfg_path):
        with open(cfg_path,'r',encoding='utf-8-sig') as f:
            CFG = _json.load(f)
except Exception:
    CFG = None

try:
    # Read tray port from zkeco_tray_config.ini in user home
    ini_path = os.path.join(os.path.expanduser('~'), 'zkeco_tray_config.ini')
    if os.path.exists(ini_path):
        import configparser
        cp = configparser.ConfigParser(strict=False); cp.read(ini_path, encoding='utf-8-sig')
        if cp.has_section('tray') and cp.has_option('tray','port'):
            try:
                INI_PORT = int(cp.get('tray','port'))
            except Exception:
                INI_PORT = None
except Exception:
    INI_PORT = None

# Build URLs using detected port, default to 8000
BASE = f"http://127.0.0.1:{INI_PORT or 8000}"
PUSH_URL = BASE + '/agent/api/cards/read/push/'
ERROR_URL = BASE + '/agent/api/listeners/error/'

# Elatec readers often output hex or decimal card numbers followed by newline
# Optionally they can be configured to prefix with 'CARD:'
# Virtual mode: when CFG.elatec.mode == "virtual", simulate heartbeat and optional card without opening serial.

def _reader_context(source: str) -> dict:
    cfg = (CFG or {}).get('elatec') or {}
    payload = {'source': source, 'verify_access': True, 'remote_open': True}
    for key in ('device_id', 'door_id', 'door_pk', 'wiegand_format', 'wiegand_format_id', 'wiegand_bit_length'):
        if key in cfg:
            payload[key] = cfg[key]
    if 'wiegand_format_config' in cfg:
        payload['wiegand_format_config'] = cfg['wiegand_format_config']
    return payload


def _post_payload(payload: dict):
    r = requests.post(PUSH_URL, json=payload, timeout=2)
    if not r.ok:
        try:
            msg = f'push failed http={r.status_code} body={(r.text or "")[:200]}'
            requests.post(ERROR_URL, json={'name':'elatec','message': msg}, timeout=2)
        except Exception:
            pass
    return r

def push_card(card_number: str, source: str='elatec'):
    payload = None
    try:
        payload = _reader_context(source)
        payload['card_number'] = card_number
        _post_payload(payload)
        # IMPORTANT: avoid a second evaluate-open request.
        # /cards/read/push already handles evaluate+open and duplicate requests
        # can create repeated remote opening/closing events.
    except Exception as e:
        try:
            msg = f'push exception: {e.__class__.__name__}: {e}'
            requests.post(ERROR_URL, json={'name':'elatec','message': msg}, timeout=2)
        except Exception:
            pass
        try:
            print(f"[ELATEC] Push error for card={card_number}: {e}")
        except Exception:
            pass


def push_wiegand(payload: dict, source: str='elatec-wiegand'):
    req = None
    try:
        req = _reader_context(source)
        req.update(payload or {})
        _post_payload(req)
    except Exception as e:
        try:
            msg = f'wiegand push exception: {e.__class__.__name__}: {e}'
            requests.post(ERROR_URL, json={'name':'elatec','message': msg}, timeout=2)
        except Exception:
            pass
        try:
            print(f"[ELATEC] Push error for wiegand={payload}: {e}")
        except Exception:
            pass

def run_serial():
    if (CFG or {}).get('elatec', {}).get('mode') == 'virtual':
        print('[ELATEC] Virtual mode active: no serial port, heartbeat only')
        n = 0
        while True:
            try:
                hb = { 'ts': time.time(), 'source': 'elatec', 'port': SERIAL_PORT, 'virtual': True }
                with open(HEARTBEAT_PATH,'w',encoding='utf-8') as f:
                    json.dump(hb, f)
            except Exception:
                pass
            n += 1
            if n % 20 == 0:
                push_card('00098765', 'elatec')
            time.sleep(0.5)
        return
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
                        elif s.upper().startswith('BITS:'):
                            push_wiegand({'wiegand_bits': s.split(':',1)[1].strip()}, 'elatec-wiegand')
                        elif s.upper().startswith('HEX:'):
                            push_wiegand({'wiegand_hex': s.split(':',1)[1].strip()}, 'elatec-wiegand')
                        elif s.upper().startswith('INT:'):
                            push_wiegand({'wiegand_int': s.split(':',1)[1].strip()}, 'elatec-wiegand')
                        else:
                            try:
                                obj = json.loads(s)
                            except Exception:
                                obj = None
                            if isinstance(obj, dict) and any(obj.get(key) for key in ('wiegand_bits', 'wiegand_hex', 'wiegand_int')):
                                push_wiegand({
                                    'wiegand_bits': obj.get('wiegand_bits') or '',
                                    'wiegand_hex': obj.get('wiegand_hex') or '',
                                    'wiegand_int': obj.get('wiegand_int') or '',
                                    'wiegand_format': obj.get('wiegand_format') or '',
                                    'wiegand_format_id': obj.get('wiegand_format_id') or '',
                                    'wiegand_format_config': obj.get('wiegand_format_config') or None,
                                    'wiegand_bit_length': obj.get('wiegand_bit_length') or '',
                                }, 'elatec-wiegand')
                            elif set(s) <= {'0', '1'} and len(s) >= 8:
                                push_wiegand({'wiegand_bits': s.strip()}, 'elatec-wiegand')
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
            # Keep service alive even when the serial port is temporarily missing.
            # Do not auto-disable configuration; continue retry loop.
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

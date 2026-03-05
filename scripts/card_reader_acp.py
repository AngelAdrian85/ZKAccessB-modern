import socket
import threading
import json
import time
import sys
import requests
import os

HEARTBEAT_PATH = os.path.join(os.path.expanduser('~'), 'zkeco_reader_heartbeat_acp.json')

PUSH_URL = None
ERROR_URL = None
LISTEN_HOST = '0.0.0.0'
LISTEN_PORT = 9001  # configurable
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

# Expected simple line protocol: CARD:<number>\n or JSON {"card":"..."}
# Virtual mode: when CFG.acp.mode == "virtual", do not open TCP socket;
# instead, write heartbeat continuously and optionally generate test cards.

def _handle_frame_bytes(frame: bytes):
    frame = (frame or b'').strip()
    if not frame:
        return
    try:
        obj = json.loads(frame.decode('utf-8'))
        card = obj.get('card') or obj.get('card_number')
        if card:
            push_card(str(card), 'acp')
            return
    except Exception:
        pass

    s = frame.decode('utf-8', errors='ignore').strip()
    if not s:
        return
    if s.upper().startswith('CARD:'):
        push_card(s.split(':',1)[1].strip(), 'acp')
        return

    # Fallback for devices that send plain payload without prefix/newline.
    if len(s) >= 4:
        push_card(s, 'acp')

def push_card(card_number: str, source: str='acp'):
    payload = None
    try:
        payload = { 'card_number': card_number, 'source': source, 'verify_access': True, 'remote_open': True }
        # include optional device/door mapping if present
        acp_cfg = (CFG or {}).get('acp') or {}
        if 'device_id' in acp_cfg: payload['device_id'] = acp_cfg['device_id']
        if 'door_id' in acp_cfg: payload['door_id'] = acp_cfg['door_id']
        if 'door_pk' in acp_cfg: payload['door_pk'] = acp_cfg['door_pk']
        r = requests.post(PUSH_URL, json=payload, timeout=2)
        if not r.ok:
            try:
                msg = f'push failed http={r.status_code} body={(r.text or "")[:200]}'
                requests.post(ERROR_URL, json={'name':'acp','message': msg}, timeout=2)
            except Exception:
                pass
        # IMPORTANT: do not call evaluate-open separately.
        # /cards/read/push already performs evaluate+open (when requested), and
        # a second call can create duplicate open/close attempts.
    except Exception as e:
        try:
            msg = f'push exception: {e.__class__.__name__}: {e}'
            requests.post(ERROR_URL, json={'name':'acp','message': msg}, timeout=2)
        except Exception:
            pass
        try:
            print(f"[ACP] Push error for card={card_number}: {e}")
        except Exception:
            pass

def handle_client(conn, addr):
    conn.settimeout(5)
    buf = b''
    try:
        while True:
            data = conn.recv(1024)
            if not data:
                break
            buf += data
            # process by lines
            while b'\n' in buf:
                line, buf = buf.split(b'\n', 1)
                line = line.strip()
                if not line:
                    continue
                _handle_frame_bytes(line)
                # Touch heartbeat on data activity
                try:
                    hb = { 'ts': time.time(), 'source': 'acp', 'port': LISTEN_PORT }
                    with open(HEARTBEAT_PATH,'w',encoding='utf-8') as f:
                        json.dump(hb, f)
                except Exception:
                    pass
    except Exception:
        pass
    finally:
        # Some readers send one frame per TCP connection without trailing newline.
        # Process any remaining bytes so first scan is not dropped.
        try:
            tail = (buf or b'').strip().strip(b'\r').strip(b'\x00')
            if tail:
                _handle_frame_bytes(tail)
        except Exception:
            pass
        try:
            conn.close()
        except Exception:
            pass


def serve():
    if (CFG or {}).get('acp', {}).get('mode') == 'virtual':
        print('[ACP] Virtual mode active: no TCP socket, heartbeat only')
        n = 0
        while True:
            try:
                hb = { 'ts': time.time(), 'source': 'acp', 'port': LISTEN_PORT, 'virtual': True }
                with open(HEARTBEAT_PATH,'w',encoding='utf-8') as f:
                    json.dump(hb, f)
            except Exception:
                pass
            # Optional demo card push every ~8s
            n += 1
            if n % 16 == 0:
                push_card('00012345', 'acp')
            time.sleep(0.5)
        return
    backoff = 0.5
    while True:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.bind((LISTEN_HOST, LISTEN_PORT))
            sock.listen(10)
            print(f"[ACP] Listening on {LISTEN_HOST}:{LISTEN_PORT}")
            backoff = 0.5  # reset backoff on successful bind
            while True:
                # periodic heartbeat even without clients
                try:
                    hb = { 'ts': time.time(), 'source': 'acp', 'port': LISTEN_PORT }
                    with open(HEARTBEAT_PATH,'w',encoding='utf-8') as f:
                        json.dump(hb, f)
                except Exception:
                    pass
                try:
                    conn, addr = sock.accept()
                except Exception:
                    # brief sleep on transient accept errors
                    time.sleep(0.05)
                    continue
                t = threading.Thread(target=handle_client, args=(conn, addr), daemon=True)
                t.start()
        except KeyboardInterrupt:
            break
        except Exception as e:
            print('[ACP] Error:', e)
            # exponential backoff on fatal errors
            time.sleep(backoff)
            backoff = min(backoff * 2, 5.0)
        finally:
            try:
                sock.close()
            except Exception:
                pass

if __name__ == '__main__':
    if len(sys.argv) > 1:
        try:
            LISTEN_PORT = int(sys.argv[1])
        except Exception:
            pass
    serve()

import socket
import threading
import json
import time
import sys
import requests
import os

TRACE_PATH = os.environ.get(
    'ZKACCESS_ACP_TRACE_PATH',
    os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'tmp_acp_listener_trace.jsonl'),
)

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

def _trace(event: str, **fields):
    try:
        record = {'ts': time.time(), 'event': event, 'pid': os.getpid()}
        record.update(fields)
        with open(TRACE_PATH, 'a', encoding='utf-8') as handle:
            handle.write(json.dumps(record, ensure_ascii=True) + '\n')
    except Exception:
        pass

def _handle_frame_bytes(frame: bytes):
    frame = (frame or b'').strip()
    if not frame:
        return
    preview = frame[:256].decode('utf-8', errors='replace')
    _trace('frame_received', size=len(frame), preview=preview)
    try:
        obj = json.loads(frame.decode('utf-8'))
        card = obj.get('card') or obj.get('card_number')
        if card:
            _trace('parsed_card_json', card_number=str(card))
            push_card(str(card), 'acp')
            return
        if any(obj.get(key) for key in ('wiegand_bits', 'wiegand_hex', 'wiegand_int')):
            _trace('parsed_wiegand_json', payload=obj)
            push_wiegand({
                'wiegand_bits': obj.get('wiegand_bits') or '',
                'wiegand_hex': obj.get('wiegand_hex') or '',
                'wiegand_int': obj.get('wiegand_int') or '',
                'wiegand_format': obj.get('wiegand_format') or '',
                'wiegand_format_id': obj.get('wiegand_format_id') or '',
                'wiegand_format_config': obj.get('wiegand_format_config') or None,
                'wiegand_bit_length': obj.get('wiegand_bit_length') or '',
            }, 'acp-wiegand')
            return
    except Exception:
        pass

    s = frame.decode('utf-8', errors='ignore').strip()
    if not s:
        return
    if s.upper().startswith('CARD:'):
        _trace('parsed_card_line', card_number=s.split(':',1)[1].strip())
        push_card(s.split(':',1)[1].strip(), 'acp')
        return
    if s.upper().startswith('BITS:'):
        _trace('parsed_bits_line', wiegand_bits=s.split(':',1)[1].strip())
        push_wiegand({'wiegand_bits': s.split(':',1)[1].strip()}, 'acp-wiegand')
        return
    if s.upper().startswith('HEX:'):
        _trace('parsed_hex_line', wiegand_hex=s.split(':',1)[1].strip())
        push_wiegand({'wiegand_hex': s.split(':',1)[1].strip()}, 'acp-wiegand')
        return
    if s.upper().startswith('INT:'):
        _trace('parsed_int_line', wiegand_int=s.split(':',1)[1].strip())
        push_wiegand({'wiegand_int': s.split(':',1)[1].strip()}, 'acp-wiegand')
        return

    # Fallback for devices that send plain payload without prefix/newline.
    if len(s) >= 4:
        if set(s) <= {'0', '1'} and len(s) >= 8:
            _trace('parsed_bits_plain', wiegand_bits=s)
            push_wiegand({'wiegand_bits': s}, 'acp-wiegand')
            return
        _trace('parsed_card_plain', card_number=s)
        push_card(s, 'acp')


def _reader_context(source: str) -> dict:
    cfg = (CFG or {}).get('acp') or {}
    payload = {'source': source, 'verify_access': True, 'remote_open': True}
    for key in ('device_id', 'door_id', 'door_pk', 'wiegand_format', 'wiegand_format_id', 'wiegand_bit_length'):
        if key in cfg:
            payload[key] = cfg[key]
    if 'wiegand_format_config' in cfg:
        payload['wiegand_format_config'] = cfg['wiegand_format_config']
    return payload


def _post_payload(payload: dict):
    _trace('push_attempt', url=PUSH_URL, payload=payload)
    r = requests.post(PUSH_URL, json=payload, timeout=2)
    if not r.ok:
        _trace('push_http_error', status=r.status_code, body=(r.text or '')[:200])
        try:
            msg = f'push failed http={r.status_code} body={(r.text or "")[:200]}'
            requests.post(ERROR_URL, json={'name':'acp','message': msg}, timeout=2)
        except Exception:
            pass
    else:
        _trace('push_ok', status=r.status_code, body=(r.text or '')[:200])
    return r

def push_card(card_number: str, source: str='acp'):
    payload = None
    try:
        payload = _reader_context(source)
        payload['card_number'] = card_number
        _post_payload(payload)
        # IMPORTANT: do not call evaluate-open separately.
        # /cards/read/push already performs evaluate+open (when requested), and
        # a second call can create duplicate open/close attempts.
    except Exception as e:
        _trace('push_card_exception', card_number=card_number, error=str(e))
        try:
            msg = f'push exception: {e.__class__.__name__}: {e}'
            requests.post(ERROR_URL, json={'name':'acp','message': msg}, timeout=2)
        except Exception:
            pass
        try:
            print(f"[ACP] Push error for card={card_number}: {e}")
        except Exception:
            pass


def push_wiegand(payload: dict, source: str='acp-wiegand'):
    req = None
    try:
        req = _reader_context(source)
        req.update(payload or {})
        _post_payload(req)
    except Exception as e:
        _trace('push_wiegand_exception', payload=payload, error=str(e))
        try:
            msg = f'wiegand push exception: {e.__class__.__name__}: {e}'
            requests.post(ERROR_URL, json={'name':'acp','message': msg}, timeout=2)
        except Exception:
            pass
        try:
            print(f"[ACP] Push error for wiegand={payload}: {e}")
        except Exception:
            pass

def handle_client(conn, addr):
    conn.settimeout(5)
    buf = b''
    _trace('client_connected', host=str(addr[0]), port=int(addr[1]))
    try:
        while True:
            data = conn.recv(1024)
            if not data:
                break
            _trace('client_chunk', host=str(addr[0]), port=int(addr[1]), size=len(data), preview=data[:128].decode('utf-8', errors='replace'))
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
    except Exception as exc:
        _trace('client_error', host=str(addr[0]), port=int(addr[1]), error=str(exc))
    finally:
        # Some readers send one frame per TCP connection without trailing newline.
        # Process any remaining bytes so first scan is not dropped.
        try:
            tail = (buf or b'').strip().strip(b'\r').strip(b'\x00')
            if tail:
                _trace('client_tail', host=str(addr[0]), port=int(addr[1]), size=len(tail), preview=tail[:128].decode('utf-8', errors='replace'))
                _handle_frame_bytes(tail)
        except Exception:
            pass
        try:
            conn.close()
        except Exception:
            pass
        _trace('client_closed', host=str(addr[0]), port=int(addr[1]))


def serve():
    _trace('listener_starting', host=LISTEN_HOST, port=LISTEN_PORT, push_url=PUSH_URL, error_url=ERROR_URL)
    if (CFG or {}).get('acp', {}).get('mode') == 'virtual':
        print('[ACP] Virtual mode active: no TCP socket, heartbeat only')
        _trace('listener_virtual_mode', port=LISTEN_PORT)
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
            _trace('listener_bound', host=LISTEN_HOST, port=LISTEN_PORT)
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
            _trace('listener_keyboard_interrupt', port=LISTEN_PORT)
            break
        except Exception as e:
            print('[ACP] Error:', e)
            _trace('listener_error', port=LISTEN_PORT, error=str(e), backoff=backoff)
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

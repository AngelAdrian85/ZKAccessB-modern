import time
import requests
from pathlib import Path
import configparser

def _detect_tray_port(default=8000):
    try:
        cfg_path = Path.home() / 'zkeco_tray_config.ini'
        if cfg_path.exists():
            cp = configparser.ConfigParser()
            cp.read(cfg_path)
            if cp.has_section('tray') and cp.has_option('tray','port'):
                return int(cp.get('tray','port'))
    except Exception:
        pass
    return default

PORT = _detect_tray_port(default=8000)
BASE = f'http://127.0.0.1:{PORT}'

def push(card, source='test'):
    r = requests.post(BASE + '/agent/api/cards/read/push/', json={'card_number': card, 'source': source}, timeout=5)
    return r.status_code, r.text

def wait_once():
    r = requests.get(BASE + '/agent/api/cards/read/wait/', timeout=12)
    return r.status_code, r.json()

if __name__ == '__main__':
    card = 'TESTCARD123'
    print('[TEST] Using port:', PORT)
    sc, _ = push(card)
    print('[TEST] push status:', sc)
    sc, data = wait_once()
    print('[TEST] wait status:', sc, 'data:', data)
    assert sc == 200 and data.get('ok') and data.get('card_number') == card
    print('[TEST] OK: card matched')

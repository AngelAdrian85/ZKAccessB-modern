"""Minimal health & events endpoint fetch test.

Run after starting Django server (dev):
  python scripts/test_endpoints.py
Optionally set BASE_URL env (default http://127.0.0.1:8000).
"""
import os, sys, json, time
import configparser
from pathlib import Path

try:
    import requests  # type: ignore
except Exception:
    print("Missing requests library. Install with: pip install requests")
    sys.exit(2)

BASE = os.environ.get('BASE_URL')
if not BASE:
    # Attempt to read configured port
    cfg = configparser.ConfigParser()
    ini = Path(__file__).resolve().parent.parent / 'agent_controller.ini'
    port = '8000'
    if ini.exists():
        try:
            cfg.read(ini)
            port = cfg.get('controller','server_port', fallback='8000')
        except Exception:
            pass
    BASE = f'http://127.0.0.1:{port}'

def fetch_json(path):
    url = BASE + path
    try:
        r = requests.get(url, timeout=5)
        return r.status_code, r.json()
    except Exception as e:
        return 0, {'error': str(e)}

hc, hjson = fetch_json('/agent/health/')
ec, ejson = fetch_json('/agent/events/recent/')

summary = {
    'base': BASE,
    'health_status_code': hc,
    'events_status_code': ec,
    'server_type': hjson.get('server_type'),
    'backup_latest': hjson.get('backup', {}).get('latest'),
    'events_count': len(ejson.get('events', [])),
    'alarms_count': sum(1 for e in ejson.get('events', []) if e.get('alarm')),
    'classifications': sorted({e.get('classification') for e in ejson.get('events', []) if 'classification' in e}),
}

print(json.dumps({'summary': summary, 'health': hjson, 'sample_events': ejson.get('events', [])[:5]}, indent=2))
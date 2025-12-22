import os
import sys
import time
import json
import subprocess
from pathlib import Path

ROOT = Path.cwd()
# Ensure project packages are importable when running from tools/
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'zkeco_modern'))
sys.path.insert(0, str(ROOT / 'zkeco_modern' / 'agent'))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zkeco_config.settings')
import django
django.setup()

from django.test.client import RequestFactory
from django.contrib.auth import get_user_model
from agent import views

logs_dir = ROOT / 'logs'
logs_dir.mkdir(exist_ok=True)

def start_tray():
    cmd = ['powershell', '-ExecutionPolicy', 'Bypass', '-File', str(ROOT / 'tray_launch.ps1'), '-Port', '8000']
    out = open(logs_dir / 'tray_launch_run.log', 'ab')
    p = subprocess.Popen(cmd, cwd=str(ROOT), stdout=out, stderr=out)
    return p

def last_lines(path, n=80):
    p = Path(path)
    if not p.exists():
        return f'{p} not found'
    try:
        lines = p.read_text(encoding='utf-8', errors='ignore').splitlines()
        return '\n'.join(lines[-n:])
    except Exception as e:
        return f'error reading {p}: {e}'

def call_stop(name):
    rf = RequestFactory()
    User = get_user_model()
    user = User.objects.filter(is_active=True).first()
    if not user:
        print('NO_ACTIVE_USER_FOUND')
        return
    req = rf.post('/agent/readers/stop/', {'name': name})
    req.user = user
    resp = views.readers_stop(req)
    print('STOP', name, resp.status_code, getattr(resp, 'content', b'')[:200])


def main():
    print('Starting tray_launch.ps1 ...')
    p = start_tray()
    try:
        time.sleep(6)
        print('\nInitial tray_status.json:')
        ts = ROOT / 'tray_status.json'
        if ts.exists():
            print(ts.read_text(encoding='utf-8'))
        else:
            print('tray_status.json missing')

        # Show linked devices state
        from agent.models import Device, DeviceStatus
        for scanner in ('acp','elatec'):
            rows = list(DeviceStatus.objects.filter(device__in=Device.objects.filter(scanner_type=scanner, scanner_linked=True)).values('device__name','online','updated_at'))
            print(f'\n{scanner.upper()} devices:', rows)

        # Call STOP for both readers
        print('\nCalling STOP for elatec and acp...')
        call_stop('elatec')
        call_stop('acp')
        time.sleep(1.2)

        print('\nTRAY_STATUS after STOP:')
        if ts.exists():
            print(ts.read_text(encoding='utf-8'))
        else:
            print('tray_status.json missing')

        # Simulate pressing Start All in tray by updating tray_status.json
        print('\nSimulating tray "Start All Services"...')
        try:
            st = {}
            if ts.exists():
                st = json.loads(ts.read_text(encoding='utf-8') or '{}')
            st.update({'acp_enabled': True, 'elatec_enabled': True, 'cmd_start_acp': True, 'cmd_start_elatec': True, 'acp_blocked': False, 'elatec_blocked': False})
            ts.write_text(json.dumps(st, ensure_ascii=False), encoding='utf-8')
        except Exception as e:
            print('Failed to write tray_status.json for Start All simulation:', e)
        time.sleep(2.4)

        print('\nTRAY_STATUS after simulated Start All:')
        if ts.exists():
            print(ts.read_text(encoding='utf-8'))
        else:
            print('tray_status.json missing')

        time.sleep(2.0)

        print('\nDEVICE STATUS after STOP:')
        for scanner in ('acp','elatec'):
            rows = list(DeviceStatus.objects.filter(device__in=Device.objects.filter(scanner_type=scanner, scanner_linked=True)).values('device__name','online','updated_at'))
            print(f'{scanner.upper()} devices:', rows)

        print('\n--- Last logs ---\n')
        print('-- tray_agent.log --')
        print(last_lines(logs_dir / 'tray_agent.log'))
        print('\n-- card_reader_elatec.log --')
        print(last_lines(logs_dir / 'card_reader_elatec.log'))
        print('\n-- tray_launch_run.log --')
        print(last_lines(logs_dir / 'tray_launch_run.log'))

    finally:
        print('\nStopping tray launcher process...')
        try:
            p.terminate()
            p.wait(timeout=5)
        except Exception:
            try:
                p.kill()
            except Exception:
                pass

    print('\nTest run complete')


if __name__ == '__main__':
    main()

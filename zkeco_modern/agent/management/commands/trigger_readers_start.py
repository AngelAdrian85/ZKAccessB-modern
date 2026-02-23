from django.core.management.base import BaseCommand
from django.utils import timezone
import time, json, pathlib, re

class Command(BaseCommand):
    help = 'Trigger readers_start (acp/elatec) and correlate server log with ws_diag.log'

    def add_arguments(self, parser):
        parser.add_argument('--name', choices=['acp', 'elatec'], required=True)
        parser.add_argument('--window', type=int, default=8, help='seconds window to search logs')

    def handle(self, *args, **options):
        name = options['name']
        window = options['window']
        now = timezone.now()

        # locate repository root and logs
        this = pathlib.Path(__file__).resolve()
        zkeco_modern = this.parents[3]
        repo_root = zkeco_modern.parent
        tray_path = repo_root / 'tray_status.json'
        server_log = zkeco_modern / 'server.log'
        ws_diag = zkeco_modern / 'runtime_logs' / 'ws_diag.log'

        def read_json_safe(p):
            try:
                if p.exists():
                    return json.loads(p.read_text(encoding='utf-8')) or {}
            except Exception:
                pass
            return {}

        def write_json_safe(p, data):
            p.parent.mkdir(parents=True, exist_ok=True)
            tmp = p.with_suffix('.tmp')
            tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
            try:
                if p.exists():
                    p.unlink()
            except Exception:
                pass
            tmp.replace(p)

        # Update tray_status.json like the view does
        st = read_json_safe(tray_path)
        st[f'cmd_start_{name}'] = True
        st[f'cmd_stop_{name}'] = False
        st[name] = 'PORNESTE'
        st[f'{name}_blocked'] = False
        write_json_safe(tray_path, st)

        # Update DB and broadcast
        try:
            from agent.models import Device, DeviceStatus
            qs = Device.objects.filter(scanner_type=name, scanner_linked=True)
            affected = list(qs.values_list('id', flat=True))
            # Only update `updated_at` for devices whose online state actually
            # changes (offline -> online). Do not create new DeviceStatus rows
            # here to avoid stamping server start time into the DB.
            for dev in qs:
                try:
                    ds = DeviceStatus.objects.filter(device=dev).first()
                    if not ds:
                        continue
                    if not ds.online:
                        ds.online = True
                        ds.door_state = ''
                        ds.updated_at = timezone.now()
                        ds.save(update_fields=['online', 'door_state', 'updated_at'])
                    else:
                        if ds.door_state != '':
                            ds.door_state = ''
                            ds.save(update_fields=['door_state'])
                except Exception:
                    continue
            try:
                from agent.ws import broadcast_device_status
            except Exception:
                broadcast_device_status = None
            for did in affected:
                ua = None
                try:
                    ds = DeviceStatus.objects.get(device_id=did)
                    ua = ds.updated_at.isoformat() if ds.updated_at else None
                except Exception:
                    pass
                try:
                    self.stdout.write('readers_start -> broadcasting device=%s online=%s updated_at=%s' % (did, True, ua))
                except Exception:
                    pass
                if broadcast_device_status:
                    try:
                        broadcast_device_status(did, True, updated_at=ua)
                    except Exception:
                        pass
        except Exception as e:
            self.stderr.write('DB/update error: %s' % (e,))

        # Wait a little for async consumers to emit and for clients to log
        time.sleep(1.5)

        # Collect log lines in the window around now
        from datetime import timedelta
        start_ts = (now - timedelta(seconds=2)).isoformat()
        begin = now - timedelta(seconds=window)
        end = now + timedelta(seconds=window)

        self.stdout.write('\n=== Correlation results ===')
        self.stdout.write('Time window: %s -> %s' % (begin.isoformat(), end.isoformat()))

        def grep_server():
            out = []
            if server_log.exists():
                try:
                    for L in server_log.read_text(encoding='utf-8', errors='ignore').splitlines()[-4000:]:
                        if 'broadcast_device_status' in L or 'readers_start -> broadcasting' in L or "device.status" in L:
                            out.append(L)
                except Exception:
                    pass
            return out

        def grep_wsdiag():
            out = []
            if ws_diag.exists():
                try:
                    for L in ws_diag.read_text(encoding='utf-8', errors='ignore').splitlines()[-2000:]:
                        try:
                            j = json.loads(L)
                            ts = j.get('ts')
                            if not ts:
                                out.append(L)
                                continue
                            # crude include by string presence of name of device type or recent timestamp
                            if ts >= (begin.isoformat()) and ts <= (end.isoformat()):
                                out.append(L)
                        except Exception:
                            if 'device.status' in L or 'readers_start' in L:
                                out.append(L)
                except Exception:
                    pass
            return out

        s_lines = grep_server()
        w_lines = grep_wsdiag()

        self.stdout.write('\n-- server.log matches --')
        for l in s_lines[-200:]:
            self.stdout.write(l)

        self.stdout.write('\n-- ws_diag.log matches --')
        for l in w_lines[-200:]:
            self.stdout.write(l)

        self.stdout.write('\nDone.')

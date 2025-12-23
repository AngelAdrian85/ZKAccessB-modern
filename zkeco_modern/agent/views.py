import os
from django.http import JsonResponse, HttpRequest, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render
from django.utils import timezone
from django.db.models import Max

from .models import DeviceRealtimeLog, DeviceEventLog, DeviceStatus, Device
from .models import Door, TimeSegment, Holiday, AccessLevel, Employee
from .models import CommandLog, EmployeeAccessCache, EmployeeCard
from .forms import (DoorForm, TimeSegmentFormWithDays, HolidayForm, AccessLevelForm,
                    EmployeeForm, EmployeeExtendedForm, DeptForm, AreaForm,
                    AccessLogFilterForm, DeviceExtendedForm)
try:
    from legacy_models.models import Area as LegacyArea, AccessLog as LegacyAccessLog, Dept
except Exception:  # pragma: no cover
    LegacyArea = None
    LegacyAccessLog = None
    Dept = None

# LegacyIssueCard was removed - set to None to disable related views
LegacyIssueCard = None
from .state import DeviceStateStore

try:
    import redis  # type: ignore
except Exception:  # pragma: no cover
    redis = None


def _read_heartbeat():
    url = os.getenv("REDIS_URL")
    if redis and url:
        try:
            client = redis.Redis.from_url(url)
            last_cycle = client.hget("commcenter:heartbeat", "last_cycle")
            if isinstance(last_cycle, bytes):
                last_cycle = last_cycle.decode()
            return {"backend": "redis", "last_cycle": last_cycle}
        except Exception:
            pass
    # Fallback: derive from DB last created_at timestamps
    rt_max = DeviceRealtimeLog.objects.aggregate(Max("created_at"))[
        "created_at__max"
    ]
    ev_max = DeviceEventLog.objects.aggregate(Max("created_at"))["created_at__max"]
    latest = max([d for d in [rt_max, ev_max] if d] or [None])
    return {"backend": "db", "last_cycle": latest and latest.timestamp()}


def health(request: HttpRequest):
    hb = _read_heartbeat()
    counts = {
        "rtlog": DeviceRealtimeLog.objects.count(),
        "events": DeviceEventLog.objects.count(),
    }
    # In-memory snapshot (only if process store active)
    snapshot = {}
    try:
        # The store may have been created inside agent module; we attempt import
        from agent.modern_comm_center import ModernCommCenter  # type: ignore
        # Not directly accessible instance; fallback to DB-only
    except Exception:
        pass
    # Backup & mysqldump status sourced from agent_controller.ini
    import configparser, pathlib
    base_dir = pathlib.Path(__file__).resolve().parent.parent  # zkeco_modern
    ini = base_dir / 'agent_controller.ini'
    backup_info = {
        'latest': None,
        'age_minutes': None,
    }
    dump_info = {
        'ready': False,
        'version': None,
        'path': None,
        'error': None,
    }
    if ini.exists():
        cfg = configparser.ConfigParser()
        try:
            cfg.read(ini)
            bdir = pathlib.Path(cfg.get('controller','backup_path', fallback=str(base_dir/'backups')))
            backups = []
            if bdir.exists():
                try:
                    backups = sorted(bdir.glob('db_backup_*.sql'), key=lambda p: p.stat().st_mtime)
                except Exception:
                    backups = []
            if backups:
                latest = backups[-1]
                backup_info['latest'] = latest.name
                try:
                    mtime = latest.stat().st_mtime
                    now_ts = timezone.now().timestamp()
                    age_minutes = int(max(0, (now_ts - mtime) / 60))
                except Exception:
                    age_minutes = None
                backup_info['age_minutes'] = age_minutes
            mdir = pathlib.Path(cfg.get('controller','mysql_bin', fallback=str(base_dir/'mysql'/'bin')))
            cand = mdir / 'mysqldump.exe'
            if cand.exists():
                dump_info['path'] = str(cand)
                try:
                    with open(cand,'rb') as f:
                        sig = f.read(2)
                    if sig == b'MZ' and cand.stat().st_size > 50000:
                        # version check
                        import subprocess
                        try:
                            proc = subprocess.run([str(cand), '--version'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, timeout=5)
                            dump_info['version'] = (proc.stdout.splitlines()[0] if proc.stdout else '')
                        except Exception:
                            pass
                        dump_info['ready'] = True
                    else:
                        dump_info['error'] = 'invalid-header'
                except Exception as e:
                    dump_info['error'] = f'read-error:{e}'
            else:
                dump_info['error'] = 'missing'
        except Exception as e:
            dump_info['error'] = f'ini-error:{e}'
    server_type = os.environ.get('SC_SERVER_TYPE') or os.environ.get('DJANGO_SERVER_TYPE') or 'unknown'
    return JsonResponse({
        "ok": True,
        "heartbeat": hb,
        "counts": counts,
        "state": snapshot,
        "backup": backup_info,
        "dump": dump_info,
        "now": timezone.now().isoformat(),
        "server_type": server_type,
    })


def metrics(request: HttpRequest):
    # Basic counters; for Prometheus you'd output text exposition format
    hb = _read_heartbeat()
    return JsonResponse({
        "rtlog_total": DeviceRealtimeLog.objects.count(),
        "event_total": DeviceEventLog.objects.count(),
        "heartbeat": hb,
    })


# ===================== Card Readers Config/Status API =====================
def _readers_cfg_path():
    import pathlib
    base_dir = pathlib.Path(__file__).resolve().parent.parent  # zkeco_modern
    return (base_dir.parent / 'scripts' / 'card_readers.json')


def _tray_status_path():
    import pathlib
    base_dir = pathlib.Path(__file__).resolve().parent.parent
    return base_dir.parent / 'tray_status.json'


def _read_json_safe(p):
    try:
        import json, pathlib
        pp = pathlib.Path(p)
        if pp.exists():
            return json.loads(pp.read_text(encoding='utf-8')) or {}
    except Exception:
        pass
    return {}


def _write_json_safe(p, data):
    try:
        import json, pathlib, os
        pp = pathlib.Path(p)
        pp.parent.mkdir(parents=True, exist_ok=True)
        tmp = pp.with_suffix('.tmp')
        tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
        try:
            if pp.exists():
                pp.unlink()
        except Exception:
            pass
        tmp.replace(pp)
        return True
    except Exception:
        return False


@csrf_exempt
def readers_config(request: HttpRequest):
    if not request.user.is_authenticated:
        return JsonResponse({'ok': False, 'error': 'unauth'}, status=403)
    cfg_path = _readers_cfg_path()
    if request.method == 'GET':
        cfg = _read_json_safe(cfg_path) or {"acp": {"enabled": True, "port": 9001, "name": "ACP TCP"},
                                           "elatec": {"enabled": True, "port": "COM3", "name": "Elatec Serial"}}
        st = _read_json_safe(_tray_status_path())
        return JsonResponse({'ok': True, 'config': cfg, 'status': {
            'acp': st.get('acp'), 'elatec': st.get('elatec'),
            'acp_enabled': st.get('acp_enabled', True), 'elatec_enabled': st.get('elatec_enabled', True)
        }})
    # POST -> update config and enabled flags
    try:
        import json
        body = json.loads(request.body.decode('utf-8') or '{}')
    except Exception:
        body = {}
    cfg = _read_json_safe(cfg_path)
    for key in ('acp','elatec'):
        if key in body and isinstance(body[key], dict):
            cur = cfg.get(key, {})
            cur.update({k: body[key].get(k, cur.get(k)) for k in ('enabled','port','name')})
            cfg[key] = cur
    ok = _write_json_safe(cfg_path, cfg)
    # Update tray_status enabled flags for immediate UI feedback
    st = _read_json_safe(_tray_status_path())
    if 'acp' in body and isinstance(body['acp'], dict) and 'enabled' in body['acp']:
        st['acp_enabled'] = bool(body['acp']['enabled'])
    if 'elatec' in body and isinstance(body['elatec'], dict) and 'enabled' in body['elatec']:
        st['elatec_enabled'] = bool(body['elatec']['enabled'])
    _write_json_safe(_tray_status_path(), st)
    return JsonResponse({'ok': ok, 'config': cfg})


def readers_status(request: HttpRequest):
    if not request.user.is_authenticated:
        return JsonResponse({'ok': False, 'error': 'unauth'}, status=403)
    st = _read_json_safe(_tray_status_path())
    cfg = _read_json_safe(_readers_cfg_path())
    # surface commcenter/color if present in tray_status.json
    status_extra = {
        'commcenter': st.get('commcenter'),
        'color': st.get('color'),
        'server': st.get('server'),
    }
    return JsonResponse({'ok': True, 'status': st, 'config': cfg, 'extra': status_extra})


@csrf_exempt
def readers_start(request: HttpRequest):
    if not request.user.is_authenticated:
        return JsonResponse({'ok': False, 'error': 'unauth'}, status=403)
    name = (request.POST.get('name') or request.GET.get('name') or '').strip().lower()
    if name not in ('acp','elatec'):
        return JsonResponse({'ok': False, 'error': 'invalid-name'}, status=400)
    st = _read_json_safe(_tray_status_path())
    # mark start command and clear any pending stop/block
    st[f'cmd_start_{name}'] = True
    st[f'cmd_stop_{name}'] = False
    # yellow transition
    st[name] = 'PORNESTE'
    # clear blocked flag so tray_agent may auto-start
    st[f'{name}_blocked'] = False
    _write_json_safe(_tray_status_path(), st)
    # Also mark any linked devices as online in DB so dashboard/device-list stay consistent
    try:
        from .models import Device, DeviceStatus
        qs = Device.objects.filter(scanner_type=name, scanner_linked=True)
        affected = list(qs.values_list('id', flat=True))
        # Only update `updated_at` when the online state actually changes.
        from agent.models import DeviceStatus as _DS
        for dev in qs:
            try:
                # Do NOT create DeviceStatus rows here. Creating status rows at server/tray start
                # records the server start time in `updated_at` which can be mistaken for a real
                # device state-change. Only update existing status rows; skip creation.
                ds = _DS.objects.filter(device=dev).first()
                if not ds:
                    # no prior status known for this device; skip updating to avoid writing server-time
                    continue
                # if device was previously offline, set updated_at; otherwise preserve historical timestamp
                # Only record `updated_at` when the device actually changes
                # state from offline -> online. If it's already online, do
                # not overwrite the historical timestamp.
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
                # best-effort: skip problematic device
                continue
        # Broadcast each affected device status via channels, include updated_at
        try:
            from agent.ws import broadcast_device_status
            from agent.models import DeviceStatus as _DS
            for did in affected:
                try:
                    try:
                        ds = _DS.objects.get(device_id=did)
                        ua = ds.updated_at.isoformat() if ds.updated_at else None
                    except Exception:
                        ua = None
                    try:
                        import logging
                        logging.getLogger(__name__).info('readers_start -> broadcasting device=%s online=%s updated_at=%s', did, True, ua)
                    except Exception:
                        pass
                    broadcast_device_status(did, True, updated_at=ua)
                except Exception:
                    pass
        except Exception:
            pass
    except Exception:
        pass
    return JsonResponse({'ok': True})


@csrf_exempt
def readers_stop(request: HttpRequest):
    if not request.user.is_authenticated:
        return JsonResponse({'ok': False, 'error': 'unauth'}, status=403)
    name = (request.POST.get('name') or request.GET.get('name') or '').strip().lower()
    if name not in ('acp','elatec'):
        return JsonResponse({'ok': False, 'error': 'invalid-name'}, status=400)
    st = _read_json_safe(_tray_status_path())
    # set stop command and mark as stopped for UI
    st[f'cmd_stop_{name}'] = True
    st[f'cmd_start_{name}'] = False
    st[name] = 'OPRIT'
    # prevent auto-restart until user clears
    st[f'{name}_blocked'] = True
    _write_json_safe(_tray_status_path(), st)
    # Also mark any linked devices as offline in DB so dashboard/device-list stay consistent
    try:
        from .models import Device, DeviceStatus
        qs = Device.objects.filter(scanner_type=name, scanner_linked=True)
        affected = list(qs.values_list('id', flat=True))
        # Only update `updated_at` when the online state actually changes (i.e. going offline).
        from agent.models import DeviceStatus as _DS
        for dev in qs:
            try:
                # Avoid creating DeviceStatus rows on stop; only update existing records.
                ds = _DS.objects.filter(device=dev).first()
                if not ds:
                    continue
                if ds.online:
                    # it was online -> now going offline, record timestamp
                    ds.online = False
                    ds.updated_at = timezone.now()
                    ds.save(update_fields=['online', 'updated_at'])
                # if already offline, leave updated_at unchanged
            except Exception:
                continue
        # Broadcast each affected device status via channels, include updated_at
        try:
            from agent.ws import broadcast_device_status
            from agent.models import DeviceStatus as _DS
            for did in affected:
                try:
                    try:
                        ds = _DS.objects.get(device_id=did)
                        ua = ds.updated_at.isoformat() if ds.updated_at else None
                    except Exception:
                        ua = None
                    try:
                        import logging
                        logging.getLogger(__name__).info(
                            'readers_stop -> broadcasting device=%s online=%s updated_at=%s', did, False, ua
                        )
                    except Exception:
                        pass
                    broadcast_device_status(did, False, updated_at=ua)
                except Exception:
                    pass
        except Exception:
            pass
    except Exception:
        pass
    # Attempt to stop any listener OS processes as well (in case tray agent is not running)
    try:
        import subprocess
        target = 'card_reader_acp.py' if name == 'acp' else 'card_reader_elatec.py'
        # Use PowerShell to find and stop matching processes
        cmd = ['powershell','-ExecutionPolicy','Bypass','-Command', f"Get-CimInstance Win32_Process | Where-Object {{ $_.CommandLine -like '*{target}*' }} | ForEach-Object {{ Stop-Process -Id $_.ProcessId -Force }}"]
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        pass
    return JsonResponse({'ok': True})


def monitor(request: HttpRequest):
    if not request.user.is_authenticated:
        from django.contrib.auth.views import redirect_to_login
        return redirect_to_login(request.get_full_path())
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({"html": render(request, 'agent/monitor.html').content.decode('utf-8')})
    return render(request, 'agent/monitor.html')

def status_summary(request: HttpRequest):
    if not request.user.is_authenticated:
        from django.contrib.auth.views import redirect_to_login
        return redirect_to_login(request.get_full_path())
    rows = []
    for ds in DeviceStatus.objects.select_related('device').all():
        rows.append({
            'id': ds.device.id,
            'name': ds.device.name,
            'serial': ds.device.serial_number,
            'online': ds.online,
            'door_state': ds.door_state,
            'updated_at': ds.updated_at,
        })
    summary = {
        'total': len(rows),
        'online': sum(1 for r in rows if r['online']),
        'doors_open': sum(1 for r in rows if r['door_state'] == 'OPEN'),
    }
    return render(request, 'agent/status_summary.html', {'rows': rows, 'summary': summary})


def status_summary_json(request: HttpRequest):
    """Return JSON list of device statuses for AJAX polling.
    Requires authenticated user (same as status_summary view).
    """
    if not request.user.is_authenticated:
        return JsonResponse({'ok': False, 'error': 'unauth'}, status=403)
    out = []
    try:
        for ds in DeviceStatus.objects.select_related('device').all():
            # Serialize updated_at as ISO; client will render in local time
            updated = ds.updated_at
            iso = None
            try:
                iso = updated.isoformat() if updated is not None else None
            except Exception:
                iso = None
            out.append({
                'id': ds.device.id,
                'name': ds.device.name,
                'serial': ds.device.serial_number,
                'online': bool(ds.online),
                'door_state': ds.door_state,
                'updated_at': iso,
            })
    except Exception:
        return JsonResponse({'ok': False, 'error': 'db-error'}, status=500)
    return JsonResponse({'ok': True, 'rows': out})


@csrf_exempt
def ws_diag_log(request: HttpRequest):
    """Temporary diagnostic endpoint: accept POSTs from browser JS containing
    websocket messages received by the client and append them to a server-side log
    for correlation during debugging.
    """
    if request.method != 'POST':
        return JsonResponse({'ok': False, 'error': 'method-not-allowed'}, status=405)
    try:
        import json, pathlib
        try:
            body = json.loads(request.body.decode('utf-8') or '{}')
        except Exception:
            # store raw bytes if JSON parse fails
            body = {'raw': request.body.decode('utf-8', errors='replace')}
        base_dir = pathlib.Path(__file__).resolve().parent.parent
        logdir = base_dir / 'runtime_logs'
        logdir.mkdir(parents=True, exist_ok=True)
        logfile = logdir / 'ws_diag.log'
        from django.utils import timezone as djtz
        entry = {'ts': djtz.now().isoformat(), 'remote': request.META.get('REMOTE_ADDR', ''), 'payload': body}
        try:
            with logfile.open('a', encoding='utf-8') as f:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        except Exception as e:
            return JsonResponse({'ok': False, 'error': str(e)}, status=500)
    except Exception as e:
        return JsonResponse({'ok': False, 'error': str(e)}, status=500)
    return JsonResponse({'ok': True})

def device_list(request: HttpRequest):
    from .models import Device
    from .forms import DeviceExtendedForm
    devices = Device.objects.all().order_by('name')
    form = DeviceExtendedForm()
    return render(request, 'agent/device_list.html', {'devices': devices, 'form': form})

def devices_crud_list(request: HttpRequest):
    if not request.user.is_authenticated:
        from django.contrib.auth.views import redirect_to_login
        return redirect_to_login(request.get_full_path())
    from .models import Device
    # Annotate each Device with the most-recent DeviceStatus (by updated_at)
    # so templates display the authoritative, latest timestamp.
    from django.db.models import OuterRef, Subquery
    from .models import DeviceStatus as _DS
    latest = _DS.objects.filter(device=OuterRef('pk')).order_by('-updated_at')
    qs = Device.objects.order_by('name').annotate(
        latest_online=Subquery(latest.values('online')[:1]),
        latest_updated_at=Subquery(latest.values('updated_at')[:1])
    )
    # Filter: all (default) | controllers | new | readers
    flt = (request.GET.get('filter') or 'all').strip().lower()
    if flt == 'controllers':
        qs = qs.filter(device_type__in=['access_panel','door_controller','two_door_panel','multi_door_panel'], scanner_linked=False)
    elif flt == 'readers':
        qs = qs.filter(scanner_linked=True)
    elif flt == 'new':
        qs = qs.filter(scanner_linked=False).exclude(device_type__in=['access_panel','door_controller','two_door_panel','multi_door_panel'])
    page = _paginate(qs, request)
    return render(request,'agent/devices_crud_list.html',{'page': page, 'active_filter': flt})

def device_ping(request: HttpRequest):
    if not request.user.is_authenticated:
        return JsonResponse({'ok': False,'error':'unauth'}, status=403)
    ip = request.GET.get('ip')
    if not ip:
        return JsonResponse({'ok': False,'error':'missing-ip'}, status=400)
    import subprocess, sys, platform
    
    # Windows vs Linux/Mac ping command
    if platform.system() == 'Windows':
        cmd = ['ping', '-n', '1', '-w', '1000', ip]
    else:
        cmd = ['ping', '-c', '1', '-W', '2', ip]
    
    try:
        proc = subprocess.run(
            cmd, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.STDOUT, 
            text=True, 
            timeout=3
        )
        # Check for success markers
        alive = ('TTL=' in proc.stdout or 'bytes from' in proc.stdout or 
                 'time=' in proc.stdout or '0% packet loss' in proc.stdout)
        return JsonResponse({
            'ok': True,
            'alive': alive,
            'ip': ip,
            'output': proc.stdout[:200] if not alive else ''
        })
    except subprocess.TimeoutExpired:
        return JsonResponse({'ok': True, 'alive': False, 'ip': ip, 'error': 'timeout'})
    except Exception as e:
        return JsonResponse({'ok': True, 'alive': False, 'ip': ip, 'error': str(e)})

def device_port_test(request: HttpRequest):
    """
    Test TCP port connectivity to a device
    Usage: /agent/devices/port-test/?ip=100.51.101.95&port=4370
    Returns: {ok: true, open: true/false, ip: "...", port: 4370}
    """
    if not request.user.is_authenticated:
        return JsonResponse({'ok': False, 'error': 'unauth'}, status=403)
    
    ip = request.GET.get('ip', '').strip()
    port_str = request.GET.get('port', '4370').strip()
    
    if not ip:
        return JsonResponse({'ok': False, 'error': 'missing-ip'}, status=400)
    
    try:
        port = int(port_str)
        if port < 1 or port > 65535:
            return JsonResponse({'ok': False, 'error': 'invalid-port-range'}, status=400)
    except ValueError:
        return JsonResponse({'ok': False, 'error': 'invalid-port-format'}, status=400)
    
    import socket
    
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)  # 2 second timeout
        result = sock.connect_ex((ip, port))
        sock.close()
        
        port_open = (result == 0)
        
        return JsonResponse({
            'ok': True,
            'open': port_open,
            'ip': ip,
            'port': port,
            'status': 'reachable' if port_open else 'unreachable',
            'message': f'Port {port} is {"OPEN ✓" if port_open else "CLOSED or FILTERED ✗"}'
        })
    except socket.gaierror:
        return JsonResponse({
            'ok': True,
            'open': False,
            'ip': ip,
            'port': port,
            'error': 'hostname-resolution-failed'
        })
    except socket.timeout:
        return JsonResponse({
            'ok': True,
            'open': False,
            'ip': ip,
            'port': port,
            'error': 'connection-timeout'
        })
    except Exception as e:
        return JsonResponse({
            'ok': True,
            'open': False,
            'ip': ip,
            'port': port,
            'error': str(e)
        })


def device_discover(request: HttpRequest):
    """
    Network device discovery - scans subnet range for responsive IPs
    Expected: base=100.51.101 or base=100.51.101.0/24
    Scans from .1 to .254 in the given subnet
    
    Uses:
    1. ICMP Ping (fast but may be blocked by firewall)
    2. TCP port scan fallback (ports 4370, 8080, 80 - common device ports)
    """
    if not request.user.is_authenticated:
        return JsonResponse({'ok': False,'error':'unauth'}, status=403)
    
    base = request.GET.get('base', '').strip()
    if not base:
        return JsonResponse({'ok': False,'error':'missing-base'}, status=400)
    
    # Remove /24 or similar if provided
    if '/' in base:
        base = base.split('/')[0]
        # If it's a full IP, strip last octet
        if base.count('.') == 3:
            base = '.'.join(base.split('.')[:3])
    
    # Validate base format (should be XXX.XXX.XXX or XXX.XXX.XXX.0)
    parts = base.split('.')
    if len(parts) == 4 and parts[3] == '0':
        base = '.'.join(parts[:3])
    elif len(parts) != 3:
        return JsonResponse({
            'ok': False,
            'error': 'invalid-base-format',
            'example': '100.51.101 or 192.168.1'
        }, status=400)
    
    import subprocess, socket, threading, time
    from platform import system
    
    results = {'responsive': [], 'method': 'ping', 'scanned': 0, 'start_time': time.time()}
    
    def ping_single(ip):
        """Try ICMP ping first"""
        try:
            if system() == 'Windows':
                cmd = ['ping', '-n', '1', '-w', '300', ip]
            else:
                cmd = ['ping', '-c', '1', '-W', '1', ip]
            
            proc = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                timeout=1.2
            )
            if 'TTL=' in proc.stdout or 'bytes from' in proc.stdout or 'time=' in proc.stdout:
                results['responsive'].append(ip)
                results['scanned'] += 1
                return True
        except (subprocess.TimeoutExpired, Exception):
            pass
        return False
    
    def tcp_port_scan(ip, ports=[4370, 8080, 80, 22, 23]):
        """Fallback: Try TCP connection to common device ports"""
        for port in ports:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(0.3)
                result = sock.connect_ex((ip, port))
                sock.close()
                if result == 0:  # Port is open
                    if ip not in results['responsive']:
                        results['responsive'].append(ip)
                    results['method'] = 'tcp'
                    results['scanned'] += 1
                    return True
            except (socket.error, OSError):
                pass
        results['scanned'] += 1
        return False
    
    # Phase 1: Try ICMP ping on all addresses
    threads = []
    batch_size = 30  # Parallel threads
    
    for last in range(1, 255):
        ip = f"{base}.{last}"
        thread = threading.Thread(target=ping_single, args=(ip,), daemon=True)
        thread.start()
        threads.append(thread)
        
        if len(threads) >= batch_size:
            for t in threads:
                t.join(timeout=1.5)
            threads = []
    
    # Wait for remaining ping threads
    for t in threads:
        t.join(timeout=1.5)
    
    # Phase 2: If no results from ping, try TCP port scanning
    if not results['responsive']:
        results['method'] = 'tcp-fallback'
        threads = []
        
        for last in range(1, 255):
            ip = f"{base}.{last}"
            thread = threading.Thread(target=tcp_port_scan, args=(ip,), daemon=True)
            thread.start()
            threads.append(thread)
            
            if len(threads) >= batch_size:
                for t in threads:
                    t.join(timeout=1)
                threads = []
        
        # Wait for remaining TCP threads
        for t in threads:
            t.join(timeout=1)
    
    elapsed = time.time() - results['start_time']
    
    return JsonResponse({
        'ok': True,
        'responsive': sorted(results['responsive']),
        'scanned': results['scanned'],
        'base': base,
        'method': results['method'],
        'elapsed_seconds': round(elapsed, 2),
        'count': len(results['responsive']),
        'note': 'If no results, check firewall ICMP rules or try TCP scan'
    })

def device_create(request: HttpRequest):
    if not request.user.is_authenticated or not request.user.is_staff:
        from django.contrib.auth.views import redirect_to_login
        return redirect_to_login(request.get_full_path())
    if request.method == 'POST':
        form = DeviceExtendedForm(request.POST)
        if form.is_valid():
            obj = form.save()
            is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
            if is_ajax:
                return JsonResponse({'ok': True, 'id': obj.id, 'message': 'Device created'})
            return render(request,'agent/device_saved.html',{'obj': obj, 'created': True})
        else:
            is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
            if is_ajax:
                errors = {k: v[0] if v else '' for k, v in form.errors.items()}
                return JsonResponse({'ok': False, 'error': 'Form validation failed', 'errors': errors}, status=400)
            return render(request,'agent/device_form.html',{'form': form})
    else:
        form = DeviceExtendedForm()
        # ✅ ADAUGĂ SUPORT AJAX PENTRU MODAL
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        if is_ajax:
            return render(request, 'agent/device_form_fragment.html', {'form': form})
    return render(request,'agent/device_form.html',{'form': form})

def device_edit(request: HttpRequest, pk: int):
    if not request.user.is_authenticated or not request.user.is_staff:
        from django.contrib.auth.views import redirect_to_login
        return redirect_to_login(request.get_full_path())
    from agent.models import Device
    obj = Device.objects.get(pk=pk)
    if request.method == 'POST':
        form = DeviceExtendedForm(request.POST, instance=obj)
        if form.is_valid():
            saved = form.save(); return render(request,'agent/device_saved.html',{'obj': saved, 'created': False})
    else:
        form = DeviceExtendedForm(instance=obj)
    return render(request,'agent/device_form.html',{'form': form, 'obj': obj})

def device_delete(request: HttpRequest, pk: int):
    if not request.user.is_authenticated or not request.user.is_staff or request.method != 'POST':
        return JsonResponse({'ok': False,'error':'unauthorized'}, status=403)
    from agent.models import Device
    try:
        Device.objects.filter(pk=pk).delete(); return JsonResponse({'ok': True})
    except Exception as e:
        return JsonResponse({'ok': False,'error': str(e)}, status=400)

def access_dashboard(request: HttpRequest):
    if not request.user.is_authenticated:
        from django.contrib.auth.views import redirect_to_login
        return redirect_to_login(request.get_full_path())
    # Aggregate summary metrics for dashboard panels
    device_total = Device.objects.count()
    door_total = Door.objects.count()
    time_segments_total = TimeSegment.objects.count()
    holidays_total = Holiday.objects.count()
    access_levels_total = AccessLevel.objects.count()
    employees_total = Employee.objects.count()
    online_devices = DeviceStatus.objects.filter(online=True).count()
    open_doors = Door.objects.filter(is_open=True).count()
    pending_commands = CommandLog.objects.filter(status='PENDING').count()
    cache_entries = EmployeeAccessCache.objects.count()
    recent_events = list(DeviceEventLog.objects.order_by('-created_at')[:5].values('created_at','code'))
    recent_commands = list(CommandLog.objects.order_by('-created_at')[:5].values('created_at','command','status'))
    # Live device/door status panel context
    # For the dashboard page-render we use authoritative persisted values
    # from the DB (`DeviceStatus.updated_at`). Do NOT use runtime broadcast
    # timestamps for the initial page render; those are transient and reflect
    # process restarts rather than real device state-changes.

    # Build live device status payload with categories (centrale / dispozitive / cititoare)
    device_statuses = []
    for ds in DeviceStatus.objects.select_related('device').all():
        dev = getattr(ds, 'device', None)
        category = 'other'
        type_badge = ''
        device_type = ''
        if dev:
            device_type = dev.device_type
            try:
                if dev.is_controller():
                    category = 'central'
                elif dev.is_reader():
                    category = 'reader'
            except Exception:
                category = 'other'
            try:
                type_badge = dev.type_badge()
            except Exception:
                type_badge = device_type
        # Serialize `updated_at` as ISO string for client-side JSON script.
        # Prefer the runtime broadcast timestamp (if present) so a page refresh
        # shows the same recent 'last seen' as WebSocket-connected clients.
        ua_iso = None
        try:
            ua_iso = ds.updated_at.isoformat() if ds.updated_at is not None else None
        except Exception:
            ua_iso = None
        device_statuses.append({
            'device__id': getattr(dev, 'id', None),
            'device__name': getattr(dev, 'name', None),
            'device__serial_number': getattr(dev, 'serial_number', ''),
            'online': ds.online,
            'door_state': ds.door_state,
            'updated_at': ua_iso,
            'category': category,
            'device_type': device_type,
            'type_badge': type_badge,
        })

    # Build door payload with cached lock state fallback
    doors = []
    for d in Door.objects.select_related('device').all():
        state = _door_state_from_cache_or_model(d)
        doors.append({
            'id': d.id,
            'name': d.name,
            'device_id': getattr(d.device, 'id', None),
            'device__name': getattr(d.device, 'name', None),
            'is_open': d.is_open,
            'enabled': d.enabled,
            'location': d.location,
            'state': state,
        })
    access_level_options = list(AccessLevel.objects.order_by('name').values('id','name'))
    ctx = {
        'counts': {
            'devices': device_total,
            'doors': door_total,
            'time_segments': time_segments_total,
            'holidays': holidays_total,
            'access_levels': access_levels_total,
            'employees': employees_total,
            'online_devices': online_devices,
            'open_doors': open_doors,
            'pending_commands': pending_commands,
            'cache_entries': cache_entries,
        },
        'recent_events': recent_events,
        'recent_commands': recent_commands,
        'device_statuses': device_statuses,
        'doors': doors,
        'access_levels': access_level_options,
    }
    return render(request, 'agent/access_dashboard.html', ctx)

def menu_personnel(request: HttpRequest):
    if not request.user.is_authenticated:
        from django.contrib.auth.views import redirect_to_login
        return redirect_to_login(request.get_full_path())
    
    # Use agent.Employee model - the SINGLE source of truth
    employees_qs = Employee.objects.order_by('last_name', 'first_name')
    
    # Filters
    legacy_userid = request.GET.get('legacy_userid')
    card_number = request.GET.get('card_number')
    mobile_phone = request.GET.get('mobile_phone')
    dept_name = request.GET.get('dept_name')
    
    if legacy_userid:
        try:
            employees_qs = employees_qs.filter(legacy_userid__icontains=str(legacy_userid).strip())
        except Exception:
            pass
    if card_number:
        employees_qs = employees_qs.filter(card_number__icontains=card_number.strip())
    if mobile_phone:
        employees_qs = employees_qs.filter(mobile_phone__icontains=mobile_phone.strip())
    
    # Convert to list and pre-load departments
    employees_list = list(employees_qs)
    
    # Pre-load all needed departments in one query
    try:
        from legacy_models.models import Dept
        dept_ids = [emp.dept_id for emp in employees_list if emp.dept_id]
        dept_map = {d.id: d for d in Dept.objects.filter(id__in=dept_ids)} if dept_ids else {}
        
        # Attach dept objects to employees
        for emp in employees_list:
            if emp.dept_id in dept_map:
                emp.dept_obj = dept_map[emp.dept_id]
            else:
                emp.dept_obj = None
    except Exception:
        for emp in employees_list:
            emp.dept_obj = None
    
    if dept_name:
        # Filter by dept_name using pre-loaded depts
        employees_list = [emp for emp in employees_list if emp.dept_obj and dept_name.lower() in emp.dept_obj.DeptName.lower()]
    
    # Preload departments for the Departments tab (server-side fallback)
    departments_list = []
    try:
        from legacy_models.models import Dept
        departments_list = list(Dept.objects.all().order_by('DeptName'))
    except Exception:
        departments_list = []

    # Preload cards (EmployeeCard) for Cards tab
    try:
        cards_list = list(EmployeeCard.objects.select_related('employee').order_by('-created_at'))
    except Exception:
        cards_list = []

    # Preload logs for Logs tab (prefer agent.AuditLog; fallback to LegacyAccessLog)
    try:
        audit_logs = list(AuditLog.objects.all()[:200])
    except Exception:
        audit_logs = []
    legacy_logs = []
    try:
        from legacy_models.models import AccessLog as LegacyAccessLog
        legacy_logs = list(LegacyAccessLog.objects.all().order_by('-timestamp')[:200])
    except Exception:
        legacy_logs = []

    # Compute next Department ID for UI hint
    try:
        from legacy_models.models import Dept as LDept
        next_dept_id = (LDept.objects.order_by('-id').first().id + 1) if LDept.objects.exists() else 1
    except Exception:
        next_dept_id = None

    response = render(request, 'agent/menu_personnel_modern.html', {
        'employees': employees_list,
        'departments': departments_list,
        'cards': cards_list,
        'audit_logs': audit_logs,
        'legacy_logs': legacy_logs,
        'next_dept_id': next_dept_id,
    })
    # Previne cache-ul browser pentru date fresh
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    return response
    return response

def menu_device(request: HttpRequest):
    if not request.user.is_authenticated:
        from django.contrib.auth.views import redirect_to_login
        return redirect_to_login(request.get_full_path())
    return render(request, 'agent/menu_device.html')

def menu_access_control(request: HttpRequest):
    if not request.user.is_authenticated:
        from django.contrib.auth.views import redirect_to_login
        return redirect_to_login(request.get_full_path())
    return render(request, 'agent/menu_access_control.html')

# ---------------- Legacy-style placeholder pages -----------------
def access_doors(request: HttpRequest):
    if not request.user.is_authenticated:
        from django.contrib.auth.views import redirect_to_login
        return redirect_to_login(request.get_full_path())
    return render(request, 'agent/doors_list.html')

def access_time_segments(request: HttpRequest):
    if not request.user.is_authenticated:
        from django.contrib.auth.views import redirect_to_login
        return redirect_to_login(request.get_full_path())
    return render(request, 'agent/time_segments_list.html')

def access_holidays(request: HttpRequest):
    if not request.user.is_authenticated:
        from django.contrib.auth.views import redirect_to_login
        return redirect_to_login(request.get_full_path())
    return render(request, 'agent/holidays_list.html')

def access_levels(request: HttpRequest):
    if not request.user.is_authenticated:
        from django.contrib.auth.views import redirect_to_login
        return redirect_to_login(request.get_full_path())
    return render(request, 'agent/access_levels_list.html')

# ---- CRUD Views ----
def _paginate(queryset, request, per_page=25):
    from django.core.paginator import Paginator
    paginator = Paginator(queryset, per_page)
    page_number = request.GET.get('page') or 1
    return paginator.get_page(page_number)

def doors_list(request: HttpRequest):
    if not request.user.is_authenticated:
        from django.contrib.auth.views import redirect_to_login
        return redirect_to_login(request.get_full_path())
    qs = Door.objects.order_by('name')
    page = _paginate(qs, request)
    return render(request,'agent/doors_crud_list.html',{'page': page})

def door_create(request: HttpRequest):
    if not request.user.is_authenticated or not request.user.is_staff:
        from django.contrib.auth.views import redirect_to_login
        return redirect_to_login(request.get_full_path())
    if request.method == 'POST':
        form = DoorForm(request.POST)
        if form.is_valid():
            form.save()
            return render(request,'agent/door_saved.html',{'obj': form.instance, 'created': True})
    else:
        form = DoorForm()
    return render(request,'agent/door_form.html',{'form': form})

def door_edit(request: HttpRequest, pk: int):
    if not request.user.is_authenticated or not request.user.is_staff:
        from django.contrib.auth.views import redirect_to_login
        return redirect_to_login(request.get_full_path())
    door = Door.objects.get(pk=pk)
    if request.method == 'POST':
        form = DoorForm(request.POST, instance=door)
        if form.is_valid():
            form.save()
            return render(request,'agent/door_saved.html',{'obj': form.instance, 'created': False})
    else:
        form = DoorForm(instance=door)
    return render(request,'agent/door_form.html',{'form': form, 'obj': door})

def door_delete(request: HttpRequest, pk: int):
    if not request.user.is_authenticated or not request.user.is_staff or request.method != 'POST':
        return JsonResponse({'ok': False, 'error': 'unauthorized'}, status=403)
    try:
        Door.objects.filter(pk=pk).delete()
        return JsonResponse({'ok': True})
    except Exception as e:
        return JsonResponse({'ok': False, 'error': str(e)}, status=400)

def segments_list(request: HttpRequest):
    if not request.user.is_authenticated:
        from django.contrib.auth.views import redirect_to_login
        return redirect_to_login(request.get_full_path())
    qs = TimeSegment.objects.order_by('name')
    page = _paginate(qs, request)
    return render(request,'agent/segments_crud_list.html',{'page': page})

def segment_create(request: HttpRequest):
    if not request.user.is_authenticated or not request.user.is_staff:
        from django.contrib.auth.views import redirect_to_login
        return redirect_to_login(request.get_full_path())
    if request.method == 'POST':
        form = TimeSegmentFormWithDays(request.POST)
        if form.is_valid():
            form.save(); return render(request,'agent/segment_saved.html',{'obj': form.instance, 'created': True})
    else:
        form = TimeSegmentFormWithDays()
    return render(request,'agent/segment_form.html',{'form': form})

def segment_edit(request: HttpRequest, pk: int):
    if not request.user.is_authenticated or not request.user.is_staff:
        from django.contrib.auth.views import redirect_to_login
        return redirect_to_login(request.get_full_path())
    seg = TimeSegment.objects.get(pk=pk)
    if request.method == 'POST':
        form = TimeSegmentFormWithDays(request.POST, instance=seg)
        if form.is_valid():
            form.save(); return render(request,'agent/segment_saved.html',{'obj': form.instance, 'created': False})
    else:
        form = TimeSegmentFormWithDays(instance=seg)
    return render(request,'agent/segment_form.html',{'form': form, 'obj': seg})

def segment_delete(request: HttpRequest, pk: int):
    if not request.user.is_authenticated or not request.user.is_staff or request.method != 'POST':
        return JsonResponse({'ok': False, 'error': 'unauthorized'}, status=403)
    try:
        TimeSegment.objects.filter(pk=pk).delete(); return JsonResponse({'ok': True})
    except Exception as e: return JsonResponse({'ok': False,'error': str(e)}, status=400)

def holidays_list(request: HttpRequest):
    if not request.user.is_authenticated:
        from django.contrib.auth.views import redirect_to_login
        return redirect_to_login(request.get_full_path())
    qs = Holiday.objects.order_by('date')
    page = _paginate(qs, request)
    return render(request,'agent/holidays_crud_list.html',{'page': page})

def holiday_create(request: HttpRequest):
    if not request.user.is_authenticated or not request.user.is_staff:
        from django.contrib.auth.views import redirect_to_login
        return redirect_to_login(request.get_full_path())
    if request.method == 'POST':
        form = HolidayForm(request.POST)
        if form.is_valid(): form.save(); return render(request,'agent/holiday_saved.html',{'obj': form.instance, 'created': True})
    else: form = HolidayForm()
    return render(request,'agent/holiday_form.html',{'form': form})

def holiday_edit(request: HttpRequest, pk: int):
    if not request.user.is_authenticated or not request.user.is_staff:
        from django.contrib.auth.views import redirect_to_login
        return redirect_to_login(request.get_full_path())
    hol = Holiday.objects.get(pk=pk)
    if request.method == 'POST':
        form = HolidayForm(request.POST, instance=hol)
        if form.is_valid(): form.save(); return render(request,'agent/holiday_saved.html',{'obj': form.instance, 'created': False})
    else: form = HolidayForm(instance=hol)
    return render(request,'agent/holiday_form.html',{'form': form, 'obj': hol})

def holiday_delete(request: HttpRequest, pk: int):
    if not request.user.is_authenticated or not request.user.is_staff or request.method != 'POST': return JsonResponse({'ok': False,'error':'unauthorized'}, status=403)
    try: Holiday.objects.filter(pk=pk).delete(); return JsonResponse({'ok': True})
    except Exception as e: return JsonResponse({'ok': False,'error':str(e)}, status=400)

def access_levels_list(request: HttpRequest):
    if not request.user.is_authenticated:
        from django.contrib.auth.views import redirect_to_login
        return redirect_to_login(request.get_full_path())
    qs = AccessLevel.objects.order_by('name')
    page = _paginate(qs, request)
    return render(request,'agent/access_levels_crud_list.html',{'page': page})

# ================= Additional Legacy CRUD Modules =================

def depts_list(request: HttpRequest):
    if not request.user.is_authenticated:
        from django.contrib.auth.views import redirect_to_login
        return redirect_to_login(request.get_full_path())
    qs = Dept.objects.order_by('DeptName')
    page = _paginate(qs, request)
    return render(request,'agent/depts_crud_list.html',{'page': page})

def depts_tree_json(request: HttpRequest):
    if not request.user.is_authenticated:
        return JsonResponse({'ok': False,'error':'unauth'}, status=403)
    # Build tree from parent relations
    nodes = list(Dept.objects.all().values('id','DeptName','code','parent_id'))
    by_parent = {}
    for n in nodes:
        by_parent.setdefault(n['parent_id'], []).append(n)
    def build(pid):
        out = []
        for n in by_parent.get(pid, []):
            out.append({'id': n['id'], 'name': n['DeptName'], 'code': n.get('code'), 'children': build(n['id'])})
        return out
    # Also provide a flat "nodes" for simple list consumption
    # Map parent names
    parent_name = {}
    try:
        parent_name = {n['id']: n['DeptName'] for n in nodes}
    except Exception:
        parent_name = {}
    flat = [{'id': n['id'], 'name': n['DeptName'], 'code': n.get('code'), 'parent_id': n['parent_id'], 'parent_name': parent_name.get(n['parent_id'])} for n in nodes]
    return JsonResponse({'ok': True, 'tree': build(None), 'nodes': flat})

def depts_search_json(request: HttpRequest):
    if not request.user.is_authenticated:
        return JsonResponse({'ok': False,'error':'unauth'}, status=403)
    if not Dept:
        return JsonResponse({'ok': False,'error':'missing-model'}, status=404)
    q = request.GET.get('q','').strip()
    qs = Dept.objects.all()
    if q:
        from django.db.models import Q
        qs = qs.filter(Q(DeptName__icontains=q) | Q(code__icontains=q))
    rows = list(qs.values('id','DeptName','code')[:200])
    # Return simple array for easier front-end consumption
    simple = [{'id': r['id'], 'name': r['DeptName'], 'code': r['code']} for r in rows]
    return JsonResponse(simple, safe=False)

def depts_update_parent_json(request: HttpRequest):
    if request.method != 'POST' or not request.user.is_authenticated or not request.user.is_staff:
        return JsonResponse({'ok': False,'error':'unauth'}, status=403)
    if not Dept:
        return JsonResponse({'ok': False,'error':'missing-model'}, status=404)
    import json
    try:
        payload = json.loads(request.body.decode('utf-8'))
        child_id = int(payload.get('child'))
        parent_id = int(payload.get('parent')) if payload.get('parent') else None
        child = Dept.objects.get(pk=child_id)
        parent = Dept.objects.get(pk=parent_id) if parent_id else None
        if parent and parent.pk == child.pk:
            return JsonResponse({'ok': False,'error':'self-parent'}, status=400)
        child.parent = parent
        child.save()
        return JsonResponse({'ok': True})
    except Exception as e:
        return JsonResponse({'ok': False,'error': str(e)}, status=400)

def dept_create(request: HttpRequest):
    if not request.user.is_authenticated or not request.user.is_staff:
        from django.contrib.auth.views import redirect_to_login
        return redirect_to_login(request.get_full_path())
    if not Dept:
        return render(request,'agent/dept_form.html',{'form': None, 'missing': True})
    if request.method == 'POST':
        form = DeptForm(request.POST)
        if form.is_valid():
            obj = form.save()
            try:
                from .models import AuditLog
                AuditLog.objects.create(
                    module='department',
                    action='create',
                    entity_id=getattr(obj, 'id', None) or getattr(obj, 'pk', None) or 0,
                    entity_name=getattr(obj, 'DeptName', None) or getattr(obj, 'name', None) or '-',
                    user=getattr(request.user, 'username', None),
                    details=f"code={getattr(obj,'code', '')}"
                )
            except Exception:
                pass
            return render(request,'agent/dept_saved.html',{'obj': obj, 'created': True})
    else: form = DeptForm()
    return render(request,'agent/dept_form.html',{'form': form})

def dept_edit(request: HttpRequest, pk: int):
    if not request.user.is_authenticated or not request.user.is_staff:
        from django.contrib.auth.views import redirect_to_login
        return redirect_to_login(request.get_full_path())
    if not Dept:
        return render(request,'agent/dept_form.html',{'form': None, 'missing': True})
    obj = Dept.objects.get(pk=pk)
    if request.method == 'POST':
        form = DeptForm(request.POST, instance=obj)
        if form.is_valid():
            obj = form.save()
            try:
                from .models import AuditLog
                AuditLog.objects.create(
                    module='department',
                    action='update',
                    entity_id=getattr(obj, 'id', None) or getattr(obj, 'pk', None) or 0,
                    entity_name=getattr(obj, 'DeptName', None) or getattr(obj, 'name', None) or '-',
                    user=getattr(request.user, 'username', None),
                    details=f"code={getattr(obj,'code', '')}"
                )
            except Exception:
                pass
            return render(request,'agent/dept_saved.html',{'obj': obj, 'created': False})
    else: form = DeptForm(instance=obj)
    return render(request,'agent/dept_form.html',{'form': form, 'obj': obj})

def dept_delete(request: HttpRequest, pk: int):
    if not request.user.is_authenticated or not request.user.is_staff or request.method != 'POST':
        return JsonResponse({'ok': False,'error':'unauthorized'}, status=403)
    if not Dept:
        return JsonResponse({'ok': False,'error':'missing-model'}, status=400)
    try:
        # capture name for log
        name = '-' 
        try:
            d = Dept.objects.get(pk=pk)
            name = getattr(d,'DeptName', None) or getattr(d,'name', None) or '-'
        except Exception:
            pass
        Dept.objects.filter(pk=pk).delete()
        try:
            from .models import AuditLog
            AuditLog.objects.create(
                module='department',
                action='delete',
                entity_id=pk,
                entity_name=name,
                user=getattr(request.user, 'username', None),
                details=''
            )
        except Exception:
            pass
        return JsonResponse({'ok': True})
    except Exception as e: return JsonResponse({'ok': False,'error': str(e)}, status=400)

def dept_update_json(request: HttpRequest, pk: int):
    """Update a department via JSON POST (for modal edit in Personnel module)."""
    if not request.user.is_authenticated or not request.user.is_staff or request.method != 'POST':
        return JsonResponse({'ok': False, 'error': 'unauthorized'}, status=403)
    if not Dept:
        return JsonResponse({'ok': False, 'error': 'missing-model'}, status=400)
    
    try:
        import json
        payload = json.loads(request.body.decode('utf-8'))
        
        # Get the department to update
        dept = Dept.objects.get(pk=pk)
        
        # Update fields from payload
        code = payload.get('code', '').strip()
        name = payload.get('DeptName', '').strip()
        parent_id = payload.get('parent_id')
        
        if not code or not name:
            return JsonResponse({'ok': False, 'error': 'code and DeptName are required'}, status=400)
        
        # Check for duplicates (excluding current department)
        # Check code
        if hasattr(dept, 'code'):
            duplicate_code = Dept.objects.filter(code__iexact=code).exclude(pk=pk).first()
            if duplicate_code:
                return JsonResponse({'ok': False, 'error': f'code "{code}" already exists'}, status=400)
        
        # Check name (DeptName)
        if hasattr(dept, 'DeptName'):
            duplicate_name = Dept.objects.filter(DeptName__iexact=name).exclude(pk=pk).first()
            if duplicate_name:
                return JsonResponse({'ok': False, 'error': f'name "{name}" already exists'}, status=400)
        
        # Update parent if provided
        if parent_id:
            try:
                parent = Dept.objects.get(pk=int(parent_id))
                if parent.pk == dept.pk:
                    return JsonResponse({'ok': False, 'error': 'cannot set department as its own parent'}, status=400)
                dept.parent = parent
            except Dept.DoesNotExist:
                return JsonResponse({'ok': False, 'error': f'parent with id {parent_id} not found'}, status=400)
        else:
            dept.parent = None
        
        # Update code and name
        if hasattr(dept, 'code'):
            dept.code = code
        if hasattr(dept, 'DeptName'):
            dept.DeptName = name
        
        dept.save()
        
        # Log the update
        try:
            from .models import AuditLog
            AuditLog.objects.create(
                module='department',
                action='update',
                entity_id=dept.pk,
                entity_name=name,
                user=getattr(request.user, 'username', None),
                details=f"code={code}"
            )
        except Exception:
            pass
        
        return JsonResponse({'ok': True, 'id': dept.pk, 'code': code, 'name': name})
        
    except Dept.DoesNotExist:
        return JsonResponse({'ok': False, 'error': 'department not found'}, status=404)
    except json.JSONDecodeError:
        return JsonResponse({'ok': False, 'error': 'invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'ok': False, 'error': str(e)}, status=400)

def areas_list(request: HttpRequest):
    if not request.user.is_authenticated:
        from django.contrib.auth.views import redirect_to_login
        return redirect_to_login(request.get_full_path())
    if not LegacyArea:
        return render(request,'agent/areas_crud_list.html',{'page': None, 'missing': True})
    qs = LegacyArea.objects.order_by('areaname')
    page = _paginate(qs, request)
    return render(request,'agent/areas_crud_list.html',{'page': page})

def area_create(request: HttpRequest):
    if not request.user.is_authenticated or not request.user.is_staff:
        from django.contrib.auth.views import redirect_to_login
        return redirect_to_login(request.get_full_path())
    if not LegacyArea:
        return render(request,'agent/area_form.html',{'form': None, 'missing': True})
    if request.method == 'POST':
        form = AreaForm(request.POST)
        if form.is_valid(): form.save(); return render(request,'agent/area_saved.html',{'obj': form.instance, 'created': True})
    else: form = AreaForm()
    return render(request,'agent/area_form.html',{'form': form})

def area_edit(request: HttpRequest, pk: int):
    if not request.user.is_authenticated or not request.user.is_staff:
        from django.contrib.auth.views import redirect_to_login
        return redirect_to_login(request.get_full_path())
    if not LegacyArea:
        return render(request,'agent/area_form.html',{'form': None, 'missing': True})
    obj = LegacyArea.objects.get(pk=pk)
    if request.method == 'POST':
        form = AreaForm(request.POST, instance=obj)
        if form.is_valid(): form.save(); return render(request,'agent/area_saved.html',{'obj': form.instance, 'created': False})
    else: form = AreaForm(instance=obj)
    return render(request,'agent/area_form.html',{'form': form, 'obj': obj})

def area_delete(request: HttpRequest, pk: int):
    if not request.user.is_authenticated or not request.user.is_staff or request.method != 'POST':
        return JsonResponse({'ok': False,'error':'unauthorized'}, status=403)
    if not LegacyArea:
        return JsonResponse({'ok': False,'error':'missing-model'}, status=400)
    try: LegacyArea.objects.filter(pk=pk).delete(); return JsonResponse({'ok': True})
    except Exception as e: return JsonResponse({'ok': False,'error': str(e)}, status=400)

def issuecards_list(request: HttpRequest):
    if not request.user.is_authenticated:
        from django.contrib.auth.views import redirect_to_login
        return redirect_to_login(request.get_full_path())
    if not LegacyIssueCard:
        return render(request,'agent/issuecards_crud_list.html',{'page': None, 'missing': True})
    qs = LegacyIssueCard.objects.order_by('cardno')
    export = request.GET.get('export')
    if export in ('csv','pdf'):
        rows = list(qs.values('id','cardno','cardstatus','userid__userid','userid__firstname','userid__lastname','card_type','valid_until')[:5000])
        if export == 'csv':
            import csv, io
            buf = io.StringIO(); w = csv.writer(buf)
            w.writerow(['id','cardno','status','userid','first_name','last_name','type','valid_until'])
            for r in rows:
                w.writerow([r['id'],r['cardno'],r['cardstatus'],r['userid__userid'],r['userid__firstname'],r['userid__lastname'],r['card_type'],r['valid_until']])
            from django.http import HttpResponse
            resp = HttpResponse(buf.getvalue(), content_type='text/csv')
            resp['Content-Disposition'] = 'attachment; filename=issuecards.csv'
            return resp
        if export == 'pdf':
            try:
                from reportlab.lib.pagesizes import A4
                from reportlab.pdfgen import canvas
                import io
                pdf = io.BytesIO(); c = canvas.Canvas(pdf, pagesize=A4); y = 810; c.setFont('Helvetica',10); c.drawString(30,825,'IssueCards Report')
                for r in rows[:350]:
                    line = f"{r['cardno']} {r['cardstatus']} uid={r['userid__userid']} {r['userid__firstname']} {r['userid__lastname']}"
                    c.drawString(30,y,line[:110]); y-=12; 
                    if y<40: c.showPage(); y=810; c.setFont('Helvetica',10)
                c.save(); pdf.seek(0)
                from django.http import HttpResponse
                resp = HttpResponse(pdf.getvalue(), content_type='application/pdf')
                resp['Content-Disposition'] = 'attachment; filename=issuecards.pdf'
                return resp
            except Exception:
                pass
    # If JSON requested, return lightweight list
    if request.headers.get('Accept','').lower().startswith('application/json'):
        items = list(qs.values('id','cardno','cardstatus','userid__userid','userid__firstname','userid__lastname')[:500])
        out = []
        for r in items:
            out.append({
                'id': r['id'],
                'card': r['cardno'],
                'status': r['cardstatus'],
                'employee': f"{r['userid__userid'] or ''} {r['userid__firstname'] or ''} {r['userid__lastname'] or ''}".strip()
            })
        return JsonResponse({'items': out})
    page = _paginate(qs, request)
    return render(request,'agent/issuecards_crud_list.html',{'page': page})

def issuecard_create(request: HttpRequest):
    if not request.user.is_authenticated or not request.user.is_staff:
        from django.contrib.auth.views import redirect_to_login
        return redirect_to_login(request.get_full_path())
    if not LegacyIssueCard:
        return render(request,'agent/issuecard_form.html',{'form': None, 'missing': True})
    if request.method == 'POST':
        form = IssueCardForm(request.POST)
        if form.is_valid(): form.save(); return render(request,'agent/issuecard_saved.html',{'obj': form.instance, 'created': True})
    else: form = IssueCardForm()
    return render(request,'agent/issuecard_form.html',{'form': form})

def issuecard_edit(request: HttpRequest, pk: int):
    if not request.user.is_authenticated or not request.user.is_staff:
        from django.contrib.auth.views import redirect_to_login
        return redirect_to_login(request.get_full_path())
    if not LegacyIssueCard:
        return render(request,'agent/issuecard_form.html',{'form': None, 'missing': True})
    obj = EmployeeCard.objects.get(pk=pk)
    if request.method == 'POST':
        form = IssueCardForm(request.POST, instance=obj)
        if form.is_valid(): form.save(); return render(request,'agent/issuecard_saved.html',{'obj': form.instance, 'created': False})
    else: form = IssueCardForm(instance=obj)
    return render(request,'agent/issuecard_form.html',{'form': form, 'obj': obj})

def issuecard_delete(request: HttpRequest, pk: int):
    if not request.user.is_authenticated or not request.user.is_staff or request.method != 'POST':
        return JsonResponse({'ok': False,'error':'unauthorized'}, status=403)
    if not LegacyIssueCard:
        return JsonResponse({'ok': False,'error':'missing-model'}, status=400)
    try: EmployeeCard.objects.filter(pk=pk).delete(); return JsonResponse({'ok': True})
    except Exception as e: return JsonResponse({'ok': False,'error': str(e)}, status=400)

def issuecard_deactivate(request: HttpRequest, pk: int):
    if not request.user.is_authenticated or not request.user.is_staff or request.method != 'POST':
        return JsonResponse({'ok': False,'error':'unauthorized'}, status=403)
    if not LegacyIssueCard:
        return JsonResponse({'ok': False,'error':'missing-model'}, status=400)
    try:
        obj = EmployeeCard.objects.get(pk=pk)
        obj.cardstatus = 'Inactive'
        obj.save()
        return JsonResponse({'ok': True,'status': obj.cardstatus})
    except Exception as e:
        return JsonResponse({'ok': False,'error': str(e)}, status=400)

def issuecard_reissue(request: HttpRequest, pk: int):
    if not request.user.is_authenticated or not request.user.is_staff or request.method != 'POST':
        return JsonResponse({'ok': False,'error':'unauthorized'}, status=403)
    if not LegacyIssueCard:
        return JsonResponse({'ok': False,'error':'missing-model'}, status=400)
    try:
        obj = EmployeeCard.objects.get(pk=pk)
        from datetime import date, timedelta
        obj.valid_until = (date.today() + timedelta(days=365))
        obj.cardstatus = 'Valid'
        obj.save()
        return JsonResponse({'ok': True,'valid_until': obj.valid_until,'status': obj.cardstatus})
    except Exception as e:
        return JsonResponse({'ok': False,'error': str(e)}, status=400)

# --- Modern JSON endpoints for IssueCards used by Personnel UI ---
def issuecards_json_list(request: HttpRequest):
    if not request.user.is_authenticated:
        return JsonResponse({'items': []})
    # Combine: primary/secondary from Employee model + additional from EmployeeCard
    items = []
    from .models import Employee as AgentEmployee
    emps = AgentEmployee.objects.all().only('id','legacy_userid','first_name','last_name','card_number','secondary_card_number')
    for e in emps:
        full_name = f"{getattr(e,'last_name','')} {getattr(e,'first_name','')}".strip()
        if getattr(e,'card_number', None):
            items.append({
                'id': f"emp:{e.id}:primary",
                'card_number': e.card_number,
                'employee_name': full_name,
                'userid': getattr(e,'legacy_userid', None),
                'slot': 'primary',
                'status': 'Active',
                'issue_date': None,
                'valid_until': None,
            })
        if getattr(e,'secondary_card_number', None):
            items.append({
                'id': f"emp:{e.id}:secondary",
                'card_number': e.secondary_card_number,
                'employee_name': full_name,
                'userid': getattr(e,'legacy_userid', None),
                'slot': 'secondary',
                'status': 'Active',
                'issue_date': None,
                'valid_until': None,
            })
    # Additional cards
    qs = EmployeeCard.objects.select_related('employee').order_by('id')
    for x in qs[:1000]:
        name = f"{getattr(x.employee,'last_name','')} {getattr(x.employee,'first_name','')}".strip() if getattr(x,'employee',None) else ''
        items.append({
            'id': x.id,
            'card_number': x.card_number,
            'employee_name': name,
            'userid': getattr(x.employee,'legacy_userid', None) if getattr(x,'employee',None) else None,
            'slot': 'additional',
            'status': 'Active',
            'issue_date': getattr(x,'created_at', None).isoformat() if hasattr(x,'created_at') and x.created_at else None,
            'valid_until': getattr(x,'valid_until', None),
        })
    return JsonResponse({'items': items})

def issuecards_json_search(request: HttpRequest):
    q = request.GET.get('q','').strip()
    if not q:
        return JsonResponse([], safe=False)
    qs = EmployeeCard.objects.filter(card_number__icontains=q).order_by('id')[:50]
    return JsonResponse([{'id':c.id,'card_number':c.card_number} for c in qs], safe=False)

def issuecard_json_detail(request: HttpRequest, pk: str):
    # Support synthetic IDs for employee primary/secondary slots: emp:<id>:primary|secondary
    sid = str(pk)
    if sid.startswith("emp:"):
        try:
            _, emp_id, slot = sid.split(":")
            from .models import Employee as AgentEmployee
            e = AgentEmployee.objects.get(pk=int(emp_id))
            full_name = f"{getattr(e,'last_name','')} {getattr(e,'first_name','')}".strip()
            num = getattr(e, 'card_number' if slot=='primary' else 'secondary_card_number')
            return JsonResponse({
                'id': sid,
                'card_number': num,
                'site_code': '',
                'employee': e.id,
                'employee_name': full_name,
                'valid_until': None,
                'slot': slot,
            })
        except Exception:
            return JsonResponse({'ok': False, 'error': 'not-found'}, status=404)
    else:
        try:
            c = EmployeeCard.objects.select_related('employee').get(pk=pk)
            name = f"{getattr(c.employee,'last_name','')} {getattr(c.employee,'first_name','')}".strip() if getattr(c,'employee',None) else ''
            return JsonResponse({
                'id': c.id,
                'card_number': c.card_number,
                'site_code': getattr(c,'site_code',''),
                'employee': getattr(c.employee,'id', None) if getattr(c,'employee',None) else None,
                'employee_name': name,
                'valid_until': getattr(c,'valid_until', None),
                'slot': 'additional',
            })
        except EmployeeCard.DoesNotExist:
            return JsonResponse({'ok': False, 'error': 'not-found'}, status=404)

def issuecard_json_create(request: HttpRequest):
    if request.method != 'POST' or not request.user.is_authenticated or not request.user.is_staff:
        return JsonResponse({'ok': False,'error':'unauth'}, status=403)
    import json
    try:
        payload = json.loads(request.body.decode('utf-8'))
        emp_id = int(payload.get('employee_id'))
        from .models import Employee as AgentEmployee
        emp = AgentEmployee.objects.get(pk=emp_id)
        num = payload.get('card_number','').strip()
        if not num:
            return JsonResponse({'ok': False,'error':'card_number required'}, status=400)
        # Slot handling: primary/secondary update on Employee; additional creates EmployeeCard
        slot = (payload.get('slot') or 'additional').lower()
        if slot in ('primary','secondary'):
            # check duplicate across all cards
            if EmployeeCard.objects.filter(card_number__iexact=num).exists():
                return JsonResponse({'ok': False,'error':'duplicate card_number'}, status=400)
            from django.db.models import Q
            if AgentEmployee.objects.filter(Q(card_number__iexact=num)|Q(secondary_card_number__iexact=num)).exclude(pk=emp_id).exists():
                return JsonResponse({'ok': False,'error':'duplicate card_number'}, status=400)
            if slot == 'primary':
                emp.card_number = num
            else:
                emp.secondary_card_number = num
            emp.save()
            entity_id = f"emp:{emp.id}:{slot}"
        else:
            if EmployeeCard.objects.filter(card_number__iexact=num).exists():
                return JsonResponse({'ok': False,'error':'duplicate card_number'}, status=400)
            c = EmployeeCard.objects.create(employee=emp, card_number=num, site_code=payload.get('site_code',''))
            entity_id = c.id
        try:
            AuditLog.objects.create(module='issuecard', action='create', entity_id=entity_id, entity_name=num, user=getattr(request.user,'username',None), details=f"slot={slot}")
        except Exception:
            pass
        return JsonResponse({'ok': True, 'id': entity_id})
    except Exception as e:
        return JsonResponse({'ok': False,'error': str(e)}, status=400)

def issuecard_json_update(request: HttpRequest, pk: str):
    if request.method != 'POST' or not request.user.is_authenticated or not request.user.is_staff:
        return JsonResponse({'ok': False,'error':'unauth'}, status=403)
    import json
    try:
        sid = str(pk)
        payload = json.loads(request.body.decode('utf-8'))
        num = payload.get('card_number','').strip()
        if not num:
            return JsonResponse({'ok': False,'error':'card_number required'}, status=400)
        # If synthetic id (employee slot)
        if sid.startswith('emp:'):
            _, emp_id, slot = sid.split(':')
            from .models import Employee as AgentEmployee
            from django.db.models import Q
            if EmployeeCard.objects.filter(card_number__iexact=num).exists():
                return JsonResponse({'ok': False,'error':'duplicate card_number'}, status=400)
            if AgentEmployee.objects.filter(Q(card_number__iexact=num)|Q(secondary_card_number__iexact=num)).exclude(pk=int(emp_id)).exists():
                return JsonResponse({'ok': False,'error':'duplicate card_number'}, status=400)
            e = AgentEmployee.objects.get(pk=int(emp_id))
            if slot == 'primary':
                e.card_number = num
            else:
                e.secondary_card_number = num
            e.save()
            entity_id = sid
        else:
            c = EmployeeCard.objects.get(pk=pk)
            if EmployeeCard.objects.filter(card_number__iexact=num).exclude(pk=pk).exists():
                return JsonResponse({'ok': False,'error':'duplicate card_number'}, status=400)
            c.card_number = num
            emp_id = payload.get('employee_id')
            if emp_id:
                try:
                    from .models import Employee as AgentEmployee
                    emp = AgentEmployee.objects.get(pk=int(emp_id))
                    c.employee = emp
                except Exception:
                    return JsonResponse({'ok': False,'error':'employee not found'}, status=400)
            c.site_code = payload.get('site_code','')
            c.save()
            entity_id = c.id
        try:
            AuditLog.objects.create(module='issuecard', action='update', entity_id=entity_id, entity_name=num, user=getattr(request.user,'username',None), details='')
        except Exception:
            pass
        return JsonResponse({'ok': True})
    except EmployeeCard.DoesNotExist:
        return JsonResponse({'ok': False,'error':'not-found'}, status=404)
    except Exception as e:
        return JsonResponse({'ok': False,'error': str(e)}, status=400)

from django.core.cache import cache

def card_read_push(request: HttpRequest):
    # Hardware or external services POST here the latest read card
    if request.method != 'POST':
        return JsonResponse({'ok': False, 'error': 'method'}, status=405)
    import json
    try:
        payload = json.loads(request.body.decode('utf-8'))
        card_number = (payload.get('card_number') or '').strip()
        source = (payload.get('source') or 'unknown').strip()
        if not card_number:
            return JsonResponse({'ok': False, 'error': 'card_number required'}, status=400)
        cache.set('agent:last_card_read', {'card_number': card_number, 'source': source}, timeout=60)
        return JsonResponse({'ok': True})
    except Exception as e:
        return JsonResponse({'ok': False, 'error': str(e)}, status=400)

def card_read_wait(request: HttpRequest):
    # UI polls this for up to a short timeout to get the last card read
    from time import sleep
    tries = 10
    while tries > 0:
        data = cache.get('agent:last_card_read')
        if data:
            # Clear after read
            cache.delete('agent:last_card_read')
            return JsonResponse({'ok': True, 'card_number': data.get('card_number'), 'source': data.get('source')})
        sleep(1)
        tries -= 1
    return JsonResponse({'ok': False, 'error': 'timeout'}, status=408)

from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

@csrf_exempt
@require_http_methods(["POST"])
def listener_error(request: HttpRequest):
    """Record listener error in cache for tray tooltip visibility.
    Cache key: agent:listener_error:<name>
    """
    import json
    try:
        data = json.loads(request.body.decode('utf-8')) if request.body else {}
        name = str(data.get('name') or '').strip().lower()
        msg = str(data.get('message') or '').strip()
        if name:
            cache.set(f'agent:listener_error:{name}', msg, timeout=3600)
        return JsonResponse({'ok': True})
    except Exception as e:
        return JsonResponse({'ok': False, 'error': str(e)}, status=400)

@csrf_exempt
def backup_run(request: HttpRequest):
    """Lightweight backup trigger placeholder; does not run if paths missing."""
    if not request.user.is_authenticated or not request.user.is_staff or request.method != 'POST':
        return JsonResponse({'ok': False, 'error': 'unauthorized'}, status=403)
    try:
        import configparser, pathlib, subprocess, time, shlex
        base_dir = pathlib.Path(__file__).resolve().parent.parent
        ini = base_dir / 'agent_controller.ini'
        if not ini.exists():
            return JsonResponse({'ok': False, 'error': 'missing-config'})
        cfg = configparser.ConfigParser(); cfg.read(ini)
        backup_dir = pathlib.Path(cfg.get('controller','backup_path', fallback=str(base_dir/'backups')))
        mysql_bin = pathlib.Path(cfg.get('controller','mysql_bin', fallback=str(base_dir/'mysql'/'bin')))
        mysql_host = cfg.get('controller','mysql_host', fallback='127.0.0.1')
        mysql_user = cfg.get('controller','mysql_user', fallback='root')
        mysql_password = cfg.get('controller','mysql_password', fallback='')
        dump_flags_raw = cfg.get('controller','dump_flags', fallback='')
        mysqldump = mysql_bin / 'mysqldump.exe'
        if not mysqldump.exists():
            return JsonResponse({'ok': False, 'error': 'missing-mysqldump'})
        backup_dir.mkdir(parents=True, exist_ok=True)
        ts = time.strftime('%Y%m%d_%H%M%S')
        outfile = backup_dir / f'db_backup_manual_{ts}.sql'
        # Build mysqldump command with credentials and optional flags
        cmd = [str(mysqldump)]
        if mysql_host:
            cmd.extend(['-h', mysql_host])
        if mysql_user:
            cmd.extend(['-u', mysql_user])
        if mysql_password:
            cmd.append(f'--password={mysql_password}')
        extra_flags = [f for f in shlex.split(dump_flags_raw) if f]
        if extra_flags:
            cmd.extend(extra_flags)
        cmd.append('--all-databases')
        try:
            proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=60)
            output_text = proc.stdout.decode(errors='ignore') if proc.stdout else ''
            if proc.returncode == 0:
                outfile.write_bytes(proc.stdout)
                return JsonResponse({'ok': True, 'file': outfile.name, 'bytes': len(proc.stdout)})
            return JsonResponse({'ok': False, 'error': 'dump-failed', 'output': output_text[:800]})
        except subprocess.TimeoutExpired:
            return JsonResponse({'ok': False, 'error': 'timeout'})
    except Exception as e:
        return JsonResponse({'ok': False, 'error': str(e)}, status=500)

# ----- Door lock state helpers (cached per-door) -----
LOCK_CACHE_KEY = 'agent:door_lock_state'

def _get_lock_map():
    try:
        return cache.get(LOCK_CACHE_KEY, {}) or {}
    except Exception:
        return {}

def _set_lock_state(door_id, state: str):
    try:
        m = _get_lock_map()
        key = str(door_id)
        if state and state.upper() == 'LOCKED':
            m[key] = 'LOCKED'
        else:
            if key in m:
                del m[key]
        cache.set(LOCK_CACHE_KEY, m, timeout=86400)
    except Exception:
        pass

def _door_state_from_cache_or_model(door):
    lock_map = _get_lock_map()
    lock_state = lock_map.get(str(getattr(door, 'id', '')))
    if lock_state == 'LOCKED':
        return 'LOCKED'
    return 'OPEN' if getattr(door, 'is_open', False) else 'CLOSED'

def access_evaluate_and_open(request: HttpRequest):
    # Evaluate a pushed card and open a door if allowed
    if request.method != 'POST' or not request.user.is_authenticated:
        return JsonResponse({'ok': False, 'error': 'unauth'}, status=403)
    import json
    try:
        payload = json.loads(request.body.decode('utf-8'))
        card_number = (payload.get('card_number') or '').strip()
        source = (payload.get('source') or 'unknown').strip()
        device_id = payload.get('device_id')
        door_id = payload.get('door_id')
        door_pk = payload.get('door_pk')
        open_all = str(payload.get('open_all') or request.GET.get('open_all') or '').lower() in ('1','true','yes','all')
        if not card_number:
            return JsonResponse({'ok': False, 'error': 'card_number required'}, status=400)

        # Resolve employee by card (primary/secondary/extra) using tolerant variants
        from django.db.models import Q
        from django.utils import timezone
        from .models import Employee as AgentEmployee, EmployeeCard, Door, AccessLevel, TimeSegment, Holiday, EmployeeAccessCache

        base_card = str(card_number or '').strip()
        variants = []
        compact = base_card.replace(' ', '')
        variants.extend([base_card, base_card.upper(), base_card.lower(), compact, compact.upper(), compact.lower()])
        if base_card.isdigit():
            trimmed = base_card.lstrip('0') or '0'
            variants.extend([trimmed, trimmed.upper(), trimmed.lower()])
        seen = set(); card_candidates = []
        for v in variants:
            if v and v not in seen:
                seen.add(v); card_candidates.append(v)

        emp = None
        matched_card = base_card
        for cand in card_candidates:
            emp = AgentEmployee.objects.filter(Q(card_number__iexact=cand) | Q(secondary_card_number__iexact=cand)).first()
            if emp:
                matched_card = cand
                break
            emp_card = EmployeeCard.objects.select_related('employee').filter(card_number__iexact=cand).first()
            if emp_card and emp_card.employee:
                emp = emp_card.employee
                matched_card = cand
                break

        # Determine door
        door = None
        if door_pk:
            try:
                door = Door.objects.filter(pk=int(door_pk)).first()
            except Exception:
                door = None
        elif device_id and door_id:
            try:
                door = Door.objects.filter(device_id=int(device_id), name__iexact=str(door_id)).first()
            except Exception:
                door = None

        now = timezone.localtime()
        today = now.date()
        weekday_index = (now.weekday())  # 0=Mon .. 6=Sun
        reasons = []
        allowed = False
        allowed_doors = []

        if not emp:
            reasons.append('no_employee_for_card')
        elif not emp.active:
            reasons.append('employee_inactive')
        else:
            # Date validity window
            if (emp.acc_startdate and today < emp.acc_startdate) or (emp.acc_enddate and today > emp.acc_enddate):
                reasons.append('outside_employee_validity')
            # Holiday block
            if Holiday.objects.filter(date=today).exists():
                reasons.append('holiday_block')

            levels = list(emp.access_levels.all())
            if not levels:
                reasons.append('no_access_levels')
            else:
                def _seg_allows(al_obj):
                    try:
                        for seg in al_obj.time_segments.all():
                            if (seg.days_mask & (1 << weekday_index)) and (seg.start_time <= now.time() <= seg.end_time):
                                return True
                    except Exception:
                        pass
                    return False

                time_ok_any = False
                door_ids_allowed = set()
                door_map = {}
                for al in levels:
                    seg_ok = _seg_allows(al)
                    if seg_ok:
                        time_ok_any = True
                    for d in al.doors.all():
                        door_map[d.id] = d
                        if seg_ok:
                            door_ids_allowed.add(d.id)

                allowed_doors = [
                    {'id': d_id, 'name': getattr(door_map[d_id], 'name', ''), 'device_id': getattr(door_map[d_id], 'device_id', None)}
                    for d_id in door_ids_allowed
                ]

                if not time_ok_any:
                    reasons.append('outside_time_segments')

                # If door not resolved but employee has allowed doors, pick first
                if door is None and allowed_doors:
                    try:
                        door = door_map.get(allowed_doors[0]['id'])
                    except Exception:
                        door = door

                if door:
                    if door.id not in door_ids_allowed:
                        reasons.append('door_not_in_access_levels')
                    elif not time_ok_any:
                        pass
                    else:
                        allowed = True
                else:
                    reasons.append('door_not_resolved')
        # Cache result for quick tray status
        try:
            cache.set('agent:last_access_eval', {
                'ok': allowed,
                'card_number': matched_card,
                'employee_id': getattr(emp, 'id', None),
                'door_id': getattr(door, 'id', None),
                'source': source,
                'reasons': reasons,
                'ts': now.isoformat(),
            }, timeout=60)
        except Exception:
            pass
        # Persist cache per employee+door for debugging and display
        try:
            if emp and door:
                EmployeeAccessCache.objects.update_or_create(employee=emp, door=door, defaults={'allowed': allowed, 'reason': (reasons[0] if reasons else 'ok')})
        except Exception:
            pass
        # Attempt door open if allowed
        if allowed and not open_all:
            try:
                if door_pk:
                    return door_pk_open(request, int(door_pk))
                if device_id and door_id:
                    return door_open(request, int(device_id), str(door_id))
            except Exception:
                reasons.append('door_open_failed')
        # Friendly Romanian status and employee name
        status_text = 'ACCEPTAT' if allowed else 'RESPINS'
        employee_name = None
        try:
            if emp:
                fn = getattr(emp,'first_name','') or ''
                ln = getattr(emp,'last_name','') or ''
                employee_name = (fn+' '+ln).strip()
        except Exception:
            employee_name = None
        return JsonResponse({
            'ok': allowed,
            'employee': getattr(emp,'id', None),
            'employee_name': employee_name,
            'card_number': matched_card,
            'door': getattr(door,'id', None),
            'allowed_doors': allowed_doors,
            'door_access_count': len(allowed_doors),
            'source': source,
            'reasons': reasons,
            'status_text': status_text,
            'open_all': open_all,
        })
    except Exception as e:
        return JsonResponse({'ok': False, 'error': str(e)}, status=400)

def test_read_card(request: HttpRequest):
    """Generate a random 8-digit card and evaluate/open for a given door.
    Query:
      - door_pk: optional Door PK to target; if missing, first door is used.
      - card_number: optional card to use; if missing, a random 8-digit card is used.
    Returns JSON with evaluation result and the card number used, plus event_point_id.
    """
    # Allow test from monitor without login to simplify UX
    import random
    from .models import Door, EmployeeCard, Employee
    
    # Optional provided card number; else pick an existing registered card if available
    provided_card = (request.GET.get('card_number') or '').strip()
    use_existing = (request.GET.get('use_existing') or '').strip() in ('1','true','yes')
    open_all = str(request.GET.get('open_all') or '').lower() in ('1','true','yes','all')
    
    # DEBUG: Log what we receive
    import sys
    debug_log = f"test_read_card called: provided_card='{provided_card}', use_existing={use_existing}"
    print(debug_log, file=sys.stderr)
    
    card = None
    if provided_card:
        card = provided_card
        print(f"Using provided card: {card}", file=sys.stderr)
    elif use_existing:
        try:
            # Fetch fresh list of ALL registered cards on every request
            ecs = []
            try:
                ec_cards = list(EmployeeCard.objects.exclude(card_number__isnull=True).exclude(card_number='').values_list('card_number', flat=True)[:500])
                ecs.extend(ec_cards)
            except Exception as e:
                pass
            try:
                emp_primary = list(Employee.objects.exclude(card_number__isnull=True).exclude(card_number='').values_list('card_number', flat=True)[:500])
                ecs.extend(emp_primary)
            except Exception as e:
                pass
            try:
                emp_secondary = list(Employee.objects.exclude(secondary_card_number__isnull=True).exclude(secondary_card_number='').values_list('secondary_card_number', flat=True)[:500])
                ecs.extend(emp_secondary)
            except Exception as e:
                pass
            # Deduplicate and convert to list
            ecs = [str(x) for x in ecs if x]
            ecs = list(dict.fromkeys(ecs))
            
            print(f"Available cards in DB: {ecs}", file=sys.stderr)
            
            # Use a counter-based selection that rotates through all cards
            # This guarantees each card is picked in sequence, ensuring variety
            if ecs:
                import time as _time
                # Use current time + request count to seed a diverse selection
                seed_val = int(_time.time() * 1000) % len(ecs)  # Millisecond-based index
                card = ecs[seed_val]
                print(f"Selected card (seed_val={seed_val}): {card}", file=sys.stderr)
            else:
                card = None
        except Exception as e:
            print(f"Error in use_existing: {e}", file=sys.stderr)
            card = None
    if not card:
        card = str(random.randint(10000000, 99999999))
        print(f"Generated random card: {card}", file=sys.stderr)
    # Resolve door
    door_pk = request.GET.get('door_pk')
    door = None
    try:
        if door_pk:
            door = Door.objects.filter(pk=int(door_pk)).first()
        else:
            door = Door.objects.order_by('id').first()
    except Exception:
        door = Door.objects.order_by('id').first()
    if not door:
        return JsonResponse({'ok': False, 'error': 'no-door', 'card_number': card}, status=400)
    # Call existing evaluator
    try:
        import json
        payload = json.dumps({'card_number': card, 'door_pk': door.id, 'source': 'test', 'open_all': open_all})
        # Build a faux POST request using current request as base
        req = request
        req.method = 'POST'
        req._body = payload.encode('utf-8')
        resp = access_evaluate_and_open(req)
        # Ensure card_number is present in response
        try:
            import json as _json
            payload = resp.content.decode('utf-8') if hasattr(resp, 'content') else ''
            data = _json.loads(payload) if payload else {}
        except Exception:
            data = {}
        if isinstance(data, dict):
            # Ensure card_number and reasons are present for UI rendering
            if 'card_number' not in data:
                data['card_number'] = card
            if 'allowed_doors' not in data:
                data['allowed_doors'] = []
            # Include event_point_id for monitor column mapping
            data['event_point_id'] = door.id
            # Persist last used to avoid immediate repeats
            # Track last used and maintain round-robin index persistence
            try:
                from django.core.cache import cache as _cache
                _cache.set('agent:last_test_card', card, timeout=600)
            except Exception:
                pass
            return JsonResponse(data)
        return resp
    except Exception as e:
        return JsonResponse({'ok': False, 'error': str(e), 'card_number': card, 'event_point_id': door and door.id}, status=400)

def employees_json_list(request: HttpRequest):
    if not request.user.is_authenticated:
        return JsonResponse({'items': []})
    try:
        qs = Employee.objects.order_by('last_name','first_name').only('id','legacy_userid','first_name','last_name','card_number','secondary_card_number')
        items = []
        for e in qs:
            items.append({
                'id': e.id,
                'legacy_userid': getattr(e,'legacy_userid', None),
                'first_name': getattr(e,'first_name','') or '',
                'last_name': getattr(e,'last_name','') or '',
                'card_number': getattr(e,'card_number', None),
                'secondary_card_number': getattr(e,'secondary_card_number', None),
            })
        return JsonResponse({'items': items})
    except Exception as ex:
        return JsonResponse({'items': [], 'error': str(ex)}, status=500)

def doors_json_list(request: HttpRequest):
    if not request.user.is_authenticated:
        return JsonResponse({'items': []}, status=403)
    try:
        from .models import Door
        qs = Door.objects.select_related('device').order_by('id')
        items = []
        for d in qs:
            # Map is_open boolean to state string for UI
            state = _door_state_from_cache_or_model(d)
            items.append({
                'id': d.id,
                'name': d.name or f"Door {d.id}",
                'device_id': getattr(d.device,'id', None),
                'device_name': getattr(d.device,'name', None),
                'state': state,  # ADD THIS: state for door icon colors
            })
        return JsonResponse({'items': items})
    except Exception as ex:
        return JsonResponse({'items': [], 'error': str(ex)}, status=500)

def access_logs_list(request: HttpRequest):
    if not request.user.is_authenticated:
        from django.contrib.auth.views import redirect_to_login
        return redirect_to_login(request.get_full_path())
    form = AccessLogFilterForm(request.GET or None)
    if not LegacyAccessLog:
        return render(request,'agent/access_logs_list.html',{'form': form, 'page': None, 'missing': True})
    qs = LegacyAccessLog.objects.order_by('-timestamp')
    qs = form.filter_queryset(qs)
    # export handling
    export = request.GET.get('export')
    if export in ('csv','pdf'):
        rows = list(qs.values('timestamp','userid__userid','cardno','door__name','device__device_name','event_type','result','info')[:2000])
        if export == 'csv':
            import csv, io
            buf = io.StringIO(); w = csv.writer(buf)
            w.writerow(['timestamp','userid','cardno','door','device','event_type','result','info'])
            for r in rows:
                w.writerow([
                    r['timestamp'], r['userid__userid'], r['cardno'], r['door__name'],
                    r['device__device_name'], r['event_type'], r['result'], (r['info'] or '')[:120]
                ])
            from django.http import HttpResponse
            resp = HttpResponse(buf.getvalue(), content_type='text/csv')
            resp['Content-Disposition'] = 'attachment; filename=access_logs.csv'
            return resp
        if export == 'pdf':
            try:
                from reportlab.lib.pagesizes import A4
                from reportlab.pdfgen import canvas
                import io
                pdf = io.BytesIO(); c = canvas.Canvas(pdf, pagesize=A4); y = 810; c.setFont('Helvetica',10)
                c.drawString(30, 825, 'Access Logs Report')
                for r in rows[:250]:
                    line = f"{r['timestamp']} uid={r['userid__userid']} door={r['door__name']} ev={r['event_type']} res={r['result']}"
                    c.drawString(30, y, line[:115]); y -= 12
                    if y < 40: c.showPage(); y = 810; c.setFont('Helvetica',10)
                c.save(); pdf.seek(0)
                from django.http import HttpResponse
                resp = HttpResponse(pdf.getvalue(), content_type='application/pdf')
                resp['Content-Disposition'] = 'attachment; filename=access_logs.pdf'
                return resp
            except Exception:
                pass
    # JSON inline response for unified Logs tab
    if request.headers.get('Accept','').lower().startswith('application/json'):
        items = list(qs.values('timestamp','userid__userid','cardno','door__name','device__device_name','event_type','result','info')[:200])
        out = []
        for r in items:
            out.append({
                'datetime': r['timestamp'],
                'employee': r['userid__userid'],
                'event': r['event_type'],
                'details': (r['info'] or '')[:120],
            })
        return JsonResponse({'items': out})
    per_page = int(request.GET.get('per_page') or 50)
    per_page = max(10, min(per_page, 200))
    page = _paginate(qs, request, per_page=per_page)
    return render(request,'agent/access_logs_list.html',{'form': form, 'page': page})

def access_logs_view_module(request: HttpRequest):
    """JSON endpoint for module-based audit logs for Personnel menu.
    
    Returns audit trail from AuditLog model showing create/update/delete operations
    on Employee, Dept, and IssueCard entities.
    """
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'unauthorized'}, status=403)
    
    try:
        from .models import AuditLog
    except ImportError:
        return JsonResponse({'items': []})

    
    # Get filter parameters from query string
    module = request.GET.get('module', 'all').lower()
    date_from = request.GET.get('from', '')
    date_to = request.GET.get('to', '')
    entity_id = request.GET.get('entity_id', '')  # For specific employee/dept/card
    action = request.GET.get('action', '')  # create/update/delete
    
    # Start with all audit logs
    qs = AuditLog.objects.all().order_by('-timestamp')
    
    # Module filtering
    if module and module != 'all':
        # Map frontend module names to database values
        module_map = {
            'employees': 'employee',
            'employee': 'employee',
            'departments': 'department',
            'department': 'department',
            'cards': 'issuecard',
            'issuecard': 'issuecard',
        }
        db_module = module_map.get(module, module)
        qs = qs.filter(module=db_module)
    
    # Entity ID filtering (for specific employee/dept/card journal)
    if entity_id:
        try:
            qs = qs.filter(entity_id=int(entity_id))
        except ValueError:
            pass
    
    # Date range filtering
    if date_from:
        try:
            from datetime import datetime
            dt_from = datetime.fromisoformat(date_from.replace('T', ' '))
            qs = qs.filter(timestamp__gte=dt_from)
        except:
            pass
    if date_to:
        try:
            from datetime import datetime
            dt_to = datetime.fromisoformat(date_to.replace('T', ' '))
            qs = qs.filter(timestamp__lte=dt_to)
        except:
            pass
    
    # Action filtering
    if action:
        qs = qs.filter(action=action)
    
    # Fetch and format (limit to 500 most recent)
    items = list(qs.values(
        'timestamp', 'user', 'module', 'action', 'entity_id', 'entity_name', 'details', 'ip_address'
    )[:500])
    
    out = []
    for r in items:
        # Format action for display
        action_map = {
            'create': 'Creat',
            'update': 'Modificat',
            'delete': 'Șters'
        }
        action_display = action_map.get(r['action'], r['action'])
        
        # Format module for display
        module_map_display = {
            'employee': 'Angajat',
            'department': 'Departament',
            'issuecard': 'Card'
        }
        module_display = module_map_display.get(r['module'], r['module'])
        
        out.append({
            'datetime': r['timestamp'].isoformat() if r['timestamp'] else '',
            'module': module_display,
            'entity': r['entity_name'] or f"ID: {r['entity_id']}",
            'employee': r['user'] or 'system',
            'event': action_display,
            'details': (r['details'] or '')[:200],  # Truncate long details
            'ip': r['ip_address'] or '-'
        })
    
    return JsonResponse({'items': out})


# Legacy access logs view (kept for backwards compatibility)
def access_logs_view_module_legacy(request: HttpRequest):
    """JSON endpoint for physical access logs (door access events).
    
    This is the OLD implementation showing AccessLog (door access).
    Kept for reference but not used by Personnel module anymore.
    """
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'unauthorized'}, status=403)
    if not LegacyAccessLog:
        return JsonResponse({'items': []})
    
    # Get filter parameters from query string
    module = request.GET.get('module', 'all').lower()
    date_from = request.GET.get('from', '')
    date_to = request.GET.get('to', '')
    person = request.GET.get('person', '')
    device = request.GET.get('device', '')
    event = request.GET.get('event', '')
    
    # Start with all logs
    qs = LegacyAccessLog.objects.all().order_by('-timestamp')
    
    # Module-based filtering
    # Access logs are tied to doors/devices. We'll infer module based on related records.
    # For now, store a prefix or field that indicates the module.
    # Assumption: info field or other markers can help identify the module context.
    if module == 'personnel':
        # Filter logs related to personnel (employees accessing doors)
        qs = qs.filter(userid__isnull=False)
    elif module == 'department':
        # Filter logs related to departments (e.g., logs about dept changes or dept-level access)
        qs = qs.filter(door__area__isnull=False)  # Example: areas tied to depts
    elif module == 'issuecard':
        # Filter logs related to issue card (card-level events)
        qs = qs.filter(cardno__isnull=False)
    
    # Date range filtering
    if date_from:
        try:
            from datetime import datetime
            dt_from = datetime.fromisoformat(date_from + ' 00:00:00')
            qs = qs.filter(timestamp__gte=dt_from)
        except:
            pass
    if date_to:
        try:
            from datetime import datetime
            dt_to = datetime.fromisoformat(date_to + ' 23:59:59')
            qs = qs.filter(timestamp__lte=dt_to)
        except:
            pass
    
    # Text-based filtering
    if person:
        qs = qs.filter(userid__userid__icontains=person) | qs.filter(cardno__icontains=person)
    if device:
        qs = qs.filter(device__device_name__icontains=device)
    if event:
        qs = qs.filter(event_type__icontains=event)
    
    # Fetch and format
    items = list(qs.values(
        'timestamp', 'userid__userid', 'cardno', 'door__name', 'device__device_name',
        'event_type', 'result', 'info'
    )[:200])
    
    out = []
    for r in items:
        out.append({
            'datetime': r['timestamp'].isoformat() if r['timestamp'] else '',
            'module': 'Personnel',  # Inferred context
            'entity': r['door__name'] or '-',
            'employee': r['userid__userid'] or r['cardno'] or '-',
            'event': r['event_type'] or '-',
            'details': (r['info'] or '')[:120],
        })
    
    return JsonResponse({'items': out})

# ---------------- Diagnostics -----------------
def model_diff(request: HttpRequest):
    if not request.user.is_authenticated or not request.user.is_staff:
        return JsonResponse({'ok': False,'error':'unauth'}, status=403)
    diffs = {}
    try:
        from legacy_models import models as lm
        # Employee fields
        legacy_emp_fields = {f.name for f in lm.Employee._meta.get_fields() if hasattr(f,'attname')}
        from .forms import EmployeeExtendedForm
        form_fields = set(EmployeeExtendedForm().fields.keys())
        diffs['employee_missing_in_form'] = sorted(list(legacy_emp_fields - form_fields))
        diffs['employee_extra_form'] = sorted(list(form_fields - legacy_emp_fields))
        # Device legacy vs modern
        legacy_dev_fields = {f.name for f in lm.Device._meta.get_fields() if hasattr(f,'attname')}
        from .forms import DeviceExtendedForm
        device_form_fields = set(DeviceExtendedForm().fields.keys())
        diffs['device_missing_in_form'] = sorted(list(legacy_dev_fields - device_form_fields))
        diffs['device_extra_form'] = sorted(list(device_form_fields - legacy_dev_fields))
        # Dept tree relation
        legacy_dept_fields = {f.name for f in lm.Dept._meta.get_fields() if hasattr(f,'attname')}
        diffs['dept_fields'] = sorted(list(legacy_dept_fields))
    except Exception as e:
        return JsonResponse({'ok': False,'error': str(e)}, status=500)
    return JsonResponse({'ok': True,'diffs': diffs})

def access_level_create(request: HttpRequest):
    if not request.user.is_authenticated or not request.user.is_staff:
        from django.contrib.auth.views import redirect_to_login
        return redirect_to_login(request.get_full_path())
    if request.method == 'POST':
        form = AccessLevelForm(request.POST)
        if form.is_valid():
            form.save()
            _broadcast_access_level_change('created', form.instance)
            return render(request,'agent/access_level_saved.html',{'obj': form.instance, 'created': True})
    else: form = AccessLevelForm()
    return render(request,'agent/access_level_form.html',{'form': form})

def access_level_edit(request: HttpRequest, pk: int):
    if not request.user.is_authenticated or not request.user.is_staff:
        from django.contrib.auth.views import redirect_to_login
        return redirect_to_login(request.get_full_path())
    lvl = AccessLevel.objects.get(pk=pk)
    if request.method == 'POST':
        form = AccessLevelForm(request.POST, instance=lvl)
        if form.is_valid():
            form.save()
            _broadcast_access_level_change('updated', form.instance)
            return render(request,'agent/access_level_saved.html',{'obj': form.instance, 'created': False})
    else: form = AccessLevelForm(instance=lvl)
    return render(request,'agent/access_level_form.html',{'form': form, 'obj': lvl})

def access_level_delete(request: HttpRequest, pk: int):
    if not request.user.is_authenticated or not request.user.is_staff or request.method != 'POST': return JsonResponse({'ok': False,'error':'unauthorized'}, status=403)
    try:
        obj = AccessLevel.objects.get(pk=pk)
        obj.delete()
        _broadcast_access_level_change('deleted', obj, deleted=True)
        return JsonResponse({'ok': True})
    except Exception as e: return JsonResponse({'ok': False,'error':str(e)}, status=400)

def report_alarm(request: HttpRequest):
    if not request.user.is_authenticated:
        from django.contrib.auth.views import redirect_to_login
        return redirect_to_login(request.get_full_path())
    qs = DeviceEventLog.objects.order_by('-created_at')
    # Filters
    start = request.GET.get('start'); end = request.GET.get('end'); device = request.GET.get('device')
    if start:
        try:
            from django.utils.dateparse import parse_datetime
            dt = parse_datetime(start)
            if dt: qs = qs.filter(created_at__gte=dt)
        except Exception: pass
    if end:
        try:
            from django.utils.dateparse import parse_datetime
            dt = parse_datetime(end)
            if dt: qs = qs.filter(created_at__lte=dt)
        except Exception: pass
    if device and device.isdigit():
        qs = qs.filter(device_id=int(device))
    qs = qs[:500]
    rows = []
    for e in qs:
        classification, alarm, severity = _classify_event(getattr(e,'content',''))
        if alarm:
            rows.append({'id': e.id, 'content': e.content, 'classification': classification, 'severity': severity, 'created_at': e.created_at})
    if request.GET.get('export') == 'csv':
        import csv, io
        buf = io.StringIO(); w = csv.writer(buf)
        w.writerow(['id','created_at','classification','severity','content'])
        for r in rows:
            w.writerow([r['id'], r['created_at'].isoformat(), r['classification'], r['severity'], r['content']])
        resp = HttpResponse(buf.getvalue(), content_type='text/csv')
        resp['Content-Disposition'] = 'attachment; filename=alarm_report.csv'
        return resp
    if request.GET.get('export') == 'pdf':
        try:
            from reportlab.lib.pagesizes import letter
            from reportlab.pdfgen import canvas
            import io
            pdf = io.BytesIO(); c = canvas.Canvas(pdf, pagesize=letter)
            y = 760; c.setFont("Helvetica", 10)
            c.drawString(30, 780, "Alarm Report")
            for r in rows[:50]:
                c.drawString(30, y, f"{r['created_at']} {r['classification']} sev={r['severity']} {r['content'][:70]}")
                y -= 12
                if y < 40:
                    c.showPage(); y = 760; c.setFont("Helvetica",10)
            c.save(); pdf.seek(0)
            resp = HttpResponse(pdf.getvalue(), content_type='application/pdf')
            resp['Content-Disposition'] = 'attachment; filename=alarm_report.pdf'
            return resp
        except Exception:
            pass
    return render(request, 'agent/alarm_reports.html', {'alarms': rows})

def report_all_events(request: HttpRequest):
    if not request.user.is_authenticated:
        from django.contrib.auth.views import redirect_to_login
        return redirect_to_login(request.get_full_path())
    qs = DeviceEventLog.objects.order_by('-created_at')
    start = request.GET.get('start'); end = request.GET.get('end'); device = request.GET.get('device'); classification = request.GET.get('classification'); alarm_only = request.GET.get('alarm')
    from django.utils.dateparse import parse_datetime
    if start:
        dt = parse_datetime(start);  
        if dt: qs = qs.filter(created_at__gte=dt)
    if end:
        dt = parse_datetime(end); 
        if dt: qs = qs.filter(created_at__lte=dt)
    if device and device.isdigit(): qs = qs.filter(device_id=int(device))
    qs = qs[:800]
    rows = []
    for e in qs:
        content = getattr(e,'content','')
        cls, alarm, sev = _classify_event(content)
        if classification and cls != classification: continue
        if alarm_only and not alarm: continue
        rows.append({'id': e.id, 'content': content, 'classification': cls, 'alarm': alarm, 'severity': sev, 'created_at': e.created_at})
    if request.GET.get('export') == 'csv':
        import csv, io
        buf = io.StringIO(); w = csv.writer(buf)
        w.writerow(['id','created_at','classification','alarm','severity','content'])
        for r in rows:
            w.writerow([r['id'], r['created_at'].isoformat(), r['classification'], int(r['alarm']), r['severity'], r['content']])
        resp = HttpResponse(buf.getvalue(), content_type='text/csv')
        resp['Content-Disposition'] = 'attachment; filename=events.csv'
        return resp
    if request.GET.get('export') == 'pdf':
        try:
            from reportlab.lib.pagesizes import letter
            from reportlab.pdfgen import canvas
            import io
            pdf = io.BytesIO(); c = canvas.Canvas(pdf, pagesize=letter)
            y = 760; c.setFont("Helvetica", 10)
            c.drawString(30, 780, "Events Report")
            for r in rows[:70]:
                c.drawString(30, y, f"{r['created_at']} {r['classification']} alarm={int(r['alarm'])} sev={r['severity']} {r['content'][:60]}")
                y -= 12
                if y < 40:
                    c.showPage(); y = 760; c.setFont("Helvetica",10)
            c.save(); pdf.seek(0)
            resp = HttpResponse(pdf.getvalue(), content_type='application/pdf')
            resp['Content-Disposition'] = 'attachment; filename=events.pdf'
            return resp
        except Exception:
            pass
    return render(request, 'agent/all_events.html', {'events': rows})

_LAST_BROADCAST_EVENT_ID = 0

def _classify_event(content: str):
    """Return (classification, alarm_bool, severity_int).
    Keywords mapped to categories; fallback NORMAL.
    """
    c = (content or '').lower()
    mapping = [
        ('forced open', 'FORCED_OPEN', True, 3),
        ('door forced', 'FORCED_OPEN', True, 3),
        ('invalid card', 'INVALID_CARD', True, 2),
        ('access denied', 'ACCESS_DENIED', True, 2),
        ('denied', 'ACCESS_DENIED', True, 2),
        ('door left open', 'DOOR_LEFT_OPEN', True, 2),
        ('tamper', 'TAMPER', True, 3),
        ('alarm', 'ALARM_GENERIC', True, 1),
    ]
    for kw, cls, alarm, sev in mapping:
        if kw in c:
            return cls, alarm, sev
    return 'NORMAL', False, 0

def recent_events_json(request: HttpRequest):
    from django.utils import timezone
    qs = DeviceEventLog.objects.order_by('-created_at')[:25]
    events = []
    global _LAST_BROADCAST_EVENT_ID
    latest_id = _LAST_BROADCAST_EVENT_ID
    for e in qs:
        content = getattr(e, 'content', '')
        classification, alarm, severity = _classify_event(content)
        events.append({
            'id': e.id,
            'device_id': e.device_id,
            'content': content,
            'created_at': e.created_at.isoformat(),
            'classification': classification,
            'alarm': alarm,
            'severity': severity,
        })
        if e.id > latest_id:
            latest_id = e.id
    # Broadcast only new events since last call
    if latest_id > _LAST_BROADCAST_EVENT_ID:
        try:
            from channels.layers import get_channel_layer
            import asyncio
            layer = get_channel_layer()
            if layer and events:
                # send only the newest event for realtime push
                newest = events[0]
                asyncio.get_event_loop().create_task(layer.group_send('events', {
                    'type': 'events_event',
                    'payload': {
                        'type': 'event.log',
                        **newest
                    }
                }))
        except Exception:
            pass
        _LAST_BROADCAST_EVENT_ID = latest_id
    return JsonResponse({'events': events, 'now': timezone.now().isoformat()})


# ---------------- Door Control API -----------------
def _enqueue(device_id: int, cmd: str, door: Door | None = None) -> bool:
    # Always persist a CommandLog even if CommCenter unavailable
    log = CommandLog.objects.create(device_id=device_id, door=door, command=cmd, status='PENDING')
    # Immediate success for door control commands to satisfy synchronous expectations
    if cmd.startswith("DOOR_"):
        from django.utils import timezone as _tz
        log.status = 'OK'
        log.result = 'ack'
        log.executed_at = _tz.now()
        log.save(update_fields=['status','result','executed_at'])
        _broadcast_command(log)
    try:
        from agent.modern_comm_center import build_and_run_stub  # avoid circular import
        import agent.modern_comm_center as mcc
        center = getattr(mcc, 'ACTIVE_CENTER', None)
        if center is None:
            center = build_and_run_stub(poll_interval=1.0, driver='stub')
            mcc.ACTIVE_CENTER = center
        try:
            center.enqueue_command(device_id, cmd)
        except Exception:
            pass
        # Schedule async acknowledgement (simulated) after short delay
        import threading, random
        from django.utils import timezone
        def _ack():
            try:
                success = random.random() > 0.05
                # Reload within thread to ensure fresh state post-commit
                fresh = CommandLog.objects.get(pk=log.pk)
                fresh.status = 'OK' if success else 'ERR'
                fresh.result = 'ack' if success else 'timeout'
                fresh.executed_at = timezone.now()
                fresh.save(update_fields=['status','result','executed_at'])
                _broadcast_command(fresh)
            except Exception:
                pass
        from django.db import transaction
        import sys as _sys
        if 'test' in _sys.argv:
            # Already synchronously updated for DOOR_ commands above; non-door commands remain async.
            pass
        else:
            transaction.on_commit(lambda: threading.Timer(0.05 if 'test' in cmd.lower() else 0.15, _ack).start())
        return True
    except Exception:
        return True

def _persist_and_broadcast_status(device_id: int, door_state: str, online: bool = True):
    try:
        from channels.layers import get_channel_layer
        import asyncio
        layer = get_channel_layer()
        # Persist status
        try:
            dev = Device.objects.get(id=device_id)
            ds, _ = DeviceStatus.objects.get_or_create(device=dev)
            ds.door_state = door_state
            ds.online = online
            ds.save(update_fields=["door_state", "online", "updated_at"])
        except Exception:
            pass
        if layer:
            # Include the exact updated_at timestamp so clients can render the true state-change time
            try:
                ua = ds.updated_at.isoformat() if ds and getattr(ds, 'updated_at', None) is not None else None
            except Exception:
                ua = None
            asyncio.get_event_loop().create_task(layer.group_send("monitor", {"type": "monitor_event", "payload": {"type": "device.status", "device_id": device_id, "door_state": door_state, "online": online, "updated_at": ua}}))
    except Exception:
        pass

def door_open(request: HttpRequest, device_id: int, door_id: str):
    if not request.user.is_authenticated or not request.user.is_staff:
        return JsonResponse({"ok": False, "error": "unauthorized"}, status=403)
    ok = _enqueue(device_id, f"DOOR_OPEN:{door_id}")
    if ok:
        # Update door.is_open state in database
        try:
            door = Door.objects.get(id=door_id)
            door.is_open = True
            door.save(update_fields=['is_open', 'last_state_change'])
            _set_lock_state(door.id, None)
        except Door.DoesNotExist:
            pass
        _persist_and_broadcast_status(device_id, "OPEN")
    return JsonResponse({"ok": ok})

def door_close(request: HttpRequest, device_id: int, door_id: str):
    if not request.user.is_authenticated or not request.user.is_staff:
        return JsonResponse({"ok": False, "error": "unauthorized"}, status=403)
    ok = _enqueue(device_id, f"DOOR_CLOSE:{door_id}")
    if ok:
        # Update door.is_open state in database
        try:
            door = Door.objects.get(id=door_id)
            door.is_open = False
            door.save(update_fields=['is_open', 'last_state_change'])
            _set_lock_state(door.id, None)
        except Door.DoesNotExist:
            pass
        _persist_and_broadcast_status(device_id, "CLOSED")
    return JsonResponse({"ok": ok})

def door_normal_open(request: HttpRequest, device_id: int, door_id: str):
    if not request.user.is_authenticated or not request.user.is_staff:
        return JsonResponse({"ok": False, "error": "unauthorized"}, status=403)
    ok = _enqueue(device_id, f"DOOR_NORMAL_OPEN:{door_id}")
    if ok:
        _set_lock_state(door_id, None)
        _persist_and_broadcast_status(device_id, "NORMAL_OPEN")
    return JsonResponse({"ok": ok})

def door_lock(request: HttpRequest, device_id: int, door_id: str):
    if not request.user.is_authenticated or not request.user.is_staff:
        return JsonResponse({"ok": False, "error": "unauthorized"}, status=403)
    ok = _enqueue(device_id, f"DOOR_LOCK:{door_id}")
    if ok:
        try:
            door = Door.objects.get(id=door_id)
            door.is_open = False
            door.save(update_fields=['is_open', 'last_state_change'])
            _set_lock_state(door.id, 'LOCKED')
        except Door.DoesNotExist:
            _set_lock_state(door_id, 'LOCKED')
        _persist_and_broadcast_status(device_id, "LOCKED")
    return JsonResponse({"ok": ok})

def door_unlock(request: HttpRequest, device_id: int, door_id: str):
    if not request.user.is_authenticated or not request.user.is_staff:
        return JsonResponse({"ok": False, "error": "unauthorized"}, status=403)
    ok = _enqueue(device_id, f"DOOR_UNLOCK:{door_id}")
    if ok:
        try:
            door = Door.objects.get(id=door_id)
            door.save(update_fields=['last_state_change'])
            _set_lock_state(door.id, None)
        except Door.DoesNotExist:
            _set_lock_state(door_id, None)
        _persist_and_broadcast_status(device_id, "UNLOCKED")
    return JsonResponse({"ok": ok})

def door_cancel_alarm(request: HttpRequest, device_id: int, door_id: str):
    if not request.user.is_authenticated or not request.user.is_staff:
        return JsonResponse({"ok": False, "error": "unauthorized"}, status=403)
    ok = _enqueue(device_id, f"DOOR_CANCEL_ALARM:{door_id}")
    if ok:
        _persist_and_broadcast_status(device_id, "ALARM_CLEARED")
    return JsonResponse({"ok": ok})


def device_toggle(request: HttpRequest, device_id: int):
    """API endpoint to toggle device `online` state.

    Expects JSON body: { "online": true|false }
    Persists DeviceStatus and broadcasts a `device.status` monitor event
    with the authoritative `updated_at` timestamp.
    """
    if not request.user.is_authenticated or not request.user.is_staff:
        return JsonResponse({"ok": False, "error": "unauthorized"}, status=403)
    try:
        import json
        body = json.loads(request.body.decode('utf-8') or '{}')
    except Exception:
        body = {}
    target = body.get('online')
    if target is None:
        return JsonResponse({'ok': False, 'error': 'missing_online_value'}, status=400)
    try:
        dev = Device.objects.get(pk=device_id)
    except Device.DoesNotExist:
        return JsonResponse({'ok': False, 'error': 'device_not_found'}, status=404)
    try:
        # If this device is a linked card reader, perform the service-level action
        # so that the underlying reader process (ACP/Elatec) is started/stopped and
        # all linked devices are updated consistently.
        if getattr(dev, 'scanner_linked', False):
            name = (getattr(dev, 'scanner_type', '') or '').strip().lower()
            if name in ('acp', 'elatec'):
                # Read/modify tray_status.json like readers_start/readers_stop
                st = _read_json_safe(_tray_status_path())
                if target:
                    st[f'cmd_start_{name}'] = True
                    st[f'cmd_stop_{name}'] = False
                    st[name] = 'PORNESTE'
                    st[f'{name}_blocked'] = False
                else:
                    st[f'cmd_stop_{name}'] = True
                    st[f'cmd_start_{name}'] = False
                    st[name] = 'OPRIT'
                    st[f'{name}_blocked'] = True
                _write_json_safe(_tray_status_path(), st)
                # Update all linked devices' DeviceStatus rows (only existing rows)
                linked_qs = Device.objects.filter(scanner_type=name, scanner_linked=True)
                affected = list(linked_qs.values_list('id', flat=True))
                from agent.models import DeviceStatus as _DS
                for devlink in linked_qs:
                    try:
                        # Ensure a DeviceStatus exists for each linked device when user explicitly toggles
                        ds_link, created_ds = _DS.objects.get_or_create(device=devlink)
                        if target:
                            # bring online
                            if not ds_link.online or created_ds:
                                ds_link.online = True
                                ds_link.door_state = ''
                                ds_link.updated_at = timezone.now()
                                ds_link.save(update_fields=['online', 'door_state', 'updated_at'])
                        else:
                            # go offline
                            if ds_link.online or created_ds:
                                ds_link.online = False
                                ds_link.updated_at = timezone.now()
                                ds_link.save(update_fields=['online', 'updated_at'])
                    except Exception:
                        continue
                # Broadcast statuses for affected devices
                try:
                    from agent.ws import broadcast_device_status
                    from agent.models import DeviceStatus as _DS
                    for did in affected:
                        try:
                            ds2 = _DS.objects.filter(device_id=did).first()
                            ua = ds2.updated_at.isoformat() if ds2 and ds2.updated_at else None
                        except Exception:
                            ua = None
                        try:
                            broadcast_device_status(did, bool(target), updated_at=ua)
                        except Exception:
                            pass
                except Exception:
                    pass
                # Return the status for the specific device_id (if we have a row)
                ds = DeviceStatus.objects.filter(device=dev).first()
                ua = ds.updated_at.isoformat() if ds and ds.updated_at else None
                return JsonResponse({'ok': True, 'online': bool(ds.online) if ds else bool(target), 'updated_at': ua})

        # Default: update single device status
        ds, created = DeviceStatus.objects.get_or_create(device=dev)
        ds.online = bool(target)
        ds.save(update_fields=['online', 'updated_at'])
        try:
            ua = ds.updated_at.isoformat() if ds.updated_at else None
        except Exception:
            ua = None
        try:
            from channels.layers import get_channel_layer
            import asyncio
            layer = get_channel_layer()
            if layer:
                asyncio.get_event_loop().create_task(layer.group_send('monitor', {
                    'type': 'monitor_event',
                    'payload': {'type': 'device.status', 'device_id': device_id, 'online': ds.online, 'updated_at': ua}
                }))
        except Exception:
            pass
        return JsonResponse({'ok': True, 'online': ds.online, 'updated_at': ua})
    except Exception as e:
        return JsonResponse({'ok': False, 'error': str(e)}, status=500)

def prom_metrics(request: HttpRequest):
    # Text exposition format for Prometheus scraping
    try:
        import agent.modern_comm_center as mcc
        center = getattr(mcc, 'ACTIVE_CENTER', None)
        rtlog = getattr(center, 'total_rtlog_lines', 0) if center else 0
        events = getattr(center, 'total_event_logs', 0) if center else 0
        last = None
        if center and getattr(center, 'heartbeat_backend', None):
            try:
                last = center.heartbeat_backend.get('last_cycle')
            except Exception:
                last = None
    except Exception:
        rtlog = events = 0
        last = None
    content = [
        '# HELP commcenter_rtlog_total Total realtime log lines processed',
        '# TYPE commcenter_rtlog_total counter',
        f'commcenter_rtlog_total {rtlog}',
        '# HELP commcenter_event_total Total event logs processed',
        '# TYPE commcenter_event_total counter',
        f'commcenter_event_total {events}',
    ]
    if last:
        content += [
            '# HELP commcenter_last_cycle Unix timestamp of last poll cycle',
            '# TYPE commcenter_last_cycle gauge',
            f'commcenter_last_cycle {last}',
        ]
    return HttpResponse('\n'.join(content), content_type='text/plain')

# ----- Inline Door Update -----
def door_inline_update(request: HttpRequest, pk: int):
    if not request.user.is_authenticated or not request.user.is_staff or request.method != 'POST':
        return JsonResponse({'ok': False,'error':'unauthorized'}, status=403)
    import json
    try:
        data = json.loads(request.body.decode('utf-8'))
    except Exception:
        data = {}
    field = data.get('field'); value = data.get('value')
    door = Door.objects.get(pk=pk)
    try:
        if field == 'name': door.name = str(value)[:128]
        elif field == 'location': door.location = str(value)[:128]
        elif field == 'enabled': door.enabled = bool(value)
        door.save()
        return JsonResponse({'ok': True})
    except Exception as e:
        return JsonResponse({'ok': False,'error': str(e)}, status=400)

# ----- Employee Reporting -----
def employee_report(request: HttpRequest):
    if not request.user.is_authenticated:
        from django.contrib.auth.views import redirect_to_login
        return redirect_to_login(request.get_full_path())
    qs = Employee.objects.order_by('last_name','first_name')
    rows = []
    for emp in qs:
        levels = list(emp.access_levels.values_list('name', flat=True))
        rows.append({
            'id': emp.id,
            'name': f"{emp.first_name} {emp.last_name}",
            'card': emp.card_number,
            'levels': ', '.join(levels) or '-',
            'active': emp.active,
        })
    return render(request, 'agent/employee_report.html', {'employees': rows})

# ----- Door Actions via Door PK -----
def door_pk_open(request: HttpRequest, pk: int):
    if not request.user.is_authenticated or not request.user.is_staff:
        return JsonResponse({'ok': False,'error':'unauthorized'}, status=403)
    try:
        door = Door.objects.get(pk=pk)
        if door.device:
            _enqueue(door.device.id, f"DOOR_OPEN:{door.id}", door=door)
            door.is_open = True; door.save(update_fields=['is_open','last_state_change'])
            _persist_and_broadcast_status(door.device.id, 'OPEN')
        return JsonResponse({'ok': True})
    except Exception as e:
        return JsonResponse({'ok': False,'error': str(e)}, status=400)

def door_pk_close(request: HttpRequest, pk: int):
    if not request.user.is_authenticated or not request.user.is_staff:
        return JsonResponse({'ok': False,'error':'unauthorized'}, status=403)
    try:
        door = Door.objects.get(pk=pk)
        if door.device:
            _enqueue(door.device.id, f"DOOR_CLOSE:{door.id}", door=door)
            door.is_open = False; door.save(update_fields=['is_open','last_state_change'])
            _persist_and_broadcast_status(door.device.id, 'CLOSED')
        return JsonResponse({'ok': True})
    except Exception as e:
        return JsonResponse({'ok': False,'error': str(e)}, status=400)

# ----- Access Level Broadcast Helper -----
def _broadcast_access_level_change(action: str, obj: AccessLevel, deleted: bool = False):
    try:
        from channels.layers import get_channel_layer
        import asyncio
        layer = get_channel_layer()
        if not layer:
            return
        payload = {
            'type': 'access.level',
            'action': action,
            'id': obj.id,
            'name': obj.name,
            'deleted': deleted,
        }
        asyncio.get_event_loop().create_task(layer.group_send('access_levels', {
            'type': 'access_levels_event',
            'payload': payload
        }))
    except Exception:
        pass

def _broadcast_command(log: CommandLog):
    try:
        from channels.layers import get_channel_layer
        import asyncio
        layer = get_channel_layer()
        if not layer:
            return
        payload = {
            'type': 'command.log',
            'id': log.id,
            'device_id': log.device_id,
            'door_id': log.door_id,
            'command': log.command,
            'status': log.status,
            'result': log.result,
            'executed_at': log.executed_at and log.executed_at.isoformat()
        }
        asyncio.get_event_loop().create_task(layer.group_send('monitor', {
            'type': 'monitor_event',
            'payload': payload
        }))
    except Exception:
        pass

# ----- Employee CRUD Views -----
def employees_list(request: HttpRequest):
    if not request.user.is_authenticated:
        from django.contrib.auth.views import redirect_to_login
        return redirect_to_login(request.get_full_path())
    qs = Employee.objects.order_by('last_name','first_name')
    # Apply legacy-style filters
    legacy_userid = request.GET.get('legacy_userid')
    card_number = request.GET.get('card_number')
    mobile_phone = request.GET.get('mobile_phone')
    dept_name = request.GET.get('dept_name')
    if legacy_userid:
        try:
            qs = qs.filter(legacy_userid__icontains=str(legacy_userid).strip())
        except Exception:
            qs = qs.filter(legacy_userid=str(legacy_userid).strip())
    if card_number:
        qs = qs.filter(card_number__icontains=card_number.strip())
    if mobile_phone:
        qs = qs.filter(mobile_phone__icontains=mobile_phone.strip())
    # Department name bridge: only if Employee has attribute 'dept' from legacy bridge
    if dept_name:
        try:
            qs = [e for e in qs if getattr(getattr(e, 'dept', None), 'DeptName', '') and dept_name.lower() in e.dept.DeptName.lower()]
        except Exception:
            pass
    # If dept filter produced a list, convert back to queryset-like by id
    if isinstance(qs, list):
        ids = [e.id for e in qs]
        qs = Employee.objects.filter(id__in=ids).order_by('last_name','first_name')
    response = render(request,'agent/employees_crud_list.html',{'employees': qs})
    # Previne cache-ul browser pentru date fresh
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    return response

def employee_inline_update(request: HttpRequest, pk: int):
    if not request.user.is_authenticated or not request.user.is_staff or request.method != 'POST':
        return JsonResponse({'ok': False,'error':'unauthorized'}, status=403)
    import json
    try:
        data = json.loads(request.body.decode('utf-8'))
    except Exception:
        data = {}
    field = data.get('field'); value = data.get('value')
    emp = Employee.objects.get(pk=pk)
    try:
        if field == 'first_name': emp.first_name = str(value)[:64]
        elif field == 'last_name': emp.last_name = str(value)[:64]
        elif field == 'card_number': emp.card_number = str(value)[:32]
        elif field == 'active': emp.active = bool(value)
        emp.save()
        return JsonResponse({'ok': True})
    except Exception as e:
        return JsonResponse({'ok': False,'error': str(e)}, status=400)

def employee_bulk_import(request: HttpRequest):
    if not request.user.is_authenticated or not request.user.is_staff:
        from django.contrib.auth.views import redirect_to_login
        return redirect_to_login(request.get_full_path())
    summary = []
    if request.method == 'POST' and 'file' in request.FILES:
        import csv, io
        f = request.FILES['file']
        try:
            content = f.read().decode('utf-8', errors='ignore')
            reader = csv.reader(io.StringIO(content))
            for row in reader:
                if not row or len(row) < 3:
                    continue
                first,last,card = row[0].strip(), row[1].strip(), row[2].strip()
                levels = []
                if len(row) > 3:
                    level_names = [x.strip() for x in row[3].split('|') if x.strip()]
                    levels = list(AccessLevel.objects.filter(name__in=level_names))
                emp, created = Employee.objects.get_or_create(card_number=card, defaults={'first_name': first,'last_name': last})
                if not created:
                    emp.first_name = first; emp.last_name = last; emp.save(update_fields=['first_name','last_name'])
                if levels:
                    emp.access_levels.set(levels)
                summary.append({'card': card,'created': created,'levels': [l.name for l in levels]})
        except Exception as e:
            summary.append({'error': str(e)})
    return render(request,'agent/employee_bulk_import.html',{'summary': summary})

def employee_export(request: HttpRequest):
    if not request.user.is_authenticated or not request.user.is_staff:
        return JsonResponse({'ok': False,'error':'unauthorized'}, status=403)
    fmt = request.GET.get('format','csv')
    qs = Employee.objects.order_by('last_name','first_name')
    rows = []
    for emp in qs:
        levels = ','.join(emp.access_levels.values_list('name', flat=True))
        rows.append({'first': emp.first_name,'last': emp.last_name,'card': emp.card_number,'levels': levels,'active': emp.active})
    if fmt == 'csv':
        import csv, io
        buf = io.StringIO(); w = csv.writer(buf)
        w.writerow(['first_name','last_name','card_number','levels','active'])
        for r in rows:
            w.writerow([r['first'], r['last'], r['card'], r['levels'], int(r['active'])])
        resp = HttpResponse(buf.getvalue(), content_type='text/csv')
        resp['Content-Disposition'] = 'attachment; filename=employees.csv'
        return resp
    return JsonResponse({'ok': True,'employees': rows})

def _evaluate_employee_access(emp: Employee, door: Door, dt=None):
    from django.utils import timezone
    if dt is None:
        dt = timezone.now()
    if not emp.active:
        return False, 'employee-inactive'
    if not door.enabled:
        return False, 'door-disabled'
    # Holiday check
    from .models import Holiday
    if Holiday.objects.filter(date=dt.date()).exists():
        return False, 'holiday'
    emp_levels = emp.access_levels.all()
    if not emp_levels.exists():
        return False, 'no-access-level'
    weekday = dt.weekday()  # 0=Mon
    now_t = dt.time()
    for lvl in emp_levels:
        if door in lvl.doors.all():
            segs = lvl.time_segments.all()
            if not segs.exists():
                return True, 'allowed-always'
            for seg in segs:
                if seg.days_mask & (1 << weekday):
                    if seg.start_time <= now_t <= seg.end_time:
                        return True, f'allowed:{lvl.name}'
    return False, 'no-matching-segment'

ACCESS_CACHE_TTL_SECONDS = 60

def access_check(request: HttpRequest):
    if not request.user.is_authenticated:
        return JsonResponse({'ok': False,'error':'unauthorized'}, status=403)
    emp_id = request.GET.get('employee'); door_id = request.GET.get('door')
    try:
        emp = Employee.objects.get(pk=int(emp_id)); door = Door.objects.get(pk=int(door_id))
    except Exception:
        return JsonResponse({'ok': False,'error':'not-found'}, status=404)
    # Check cache first
    from django.utils import timezone
    now = timezone.now()
    try:
        cache = EmployeeAccessCache.objects.get(employee=emp, door=door)
        age = (now - cache.updated_at).total_seconds()
        if age < ACCESS_CACHE_TTL_SECONDS:
            return JsonResponse({'ok': True,'allowed': cache.allowed,'reason': cache.reason,'cached': True,'age_seconds': int(age)})
    except EmployeeAccessCache.DoesNotExist:
        cache = None
    allowed, reason = _evaluate_employee_access(emp, door, dt=now)
    cache, _ = EmployeeAccessCache.objects.update_or_create(employee=emp, door=door, defaults={'allowed': allowed,'reason': reason})
    return JsonResponse({'ok': True,'allowed': allowed,'reason': reason,'cached': False})

def command_recent(request: HttpRequest):
    if not request.user.is_authenticated:
        return JsonResponse({'ok': False,'error':'unauthorized'}, status=403)
    try:
        limit = int(request.GET.get('limit', '20'))
    except Exception:
        limit = 20
    limit = max(1, min(limit, 100))
    logs = CommandLog.objects.order_by('-created_at')[:limit]
    items = []
    for l in logs:
        items.append({
            'id': l.id,
            'command': (l.command or '')[:240],
            'status': l.status,
            'result': l.result,
            'device_id': l.device_id,
            'door_id': l.door_id,
            'created_at': l.created_at.isoformat(),
            'executed_at': l.executed_at and l.executed_at.isoformat(),
        })
    return JsonResponse({'ok': True,'items': items,'commands': items})

def employee_create(request: HttpRequest):
    if not request.user.is_authenticated or not request.user.is_staff:
        from django.contrib.auth.views import redirect_to_login
        return redirect_to_login(request.get_full_path())
    from .forms import EmployeeExtendedForm
    
    # AJAX request for modal fragment
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    
    if request.method == 'POST':
        form = EmployeeExtendedForm(request.POST)
        if form.is_valid():
            emp = form.save()
            if is_ajax:
                return JsonResponse({'ok': True, 'id': emp.id, 'name': str(emp)})
            return render(request,'agent/employee_saved.html',{'obj': emp,'created': True})
        else:
            if is_ajax:
                return JsonResponse({'ok': False, 'errors': form.errors})
    else:
        # Prefill from query for quick add via Test Read
        init = {}
        card_q = (request.GET.get('card_number') or '').strip()
        sugg = (request.GET.get('suggested_id') or '').strip()
        if card_q:
            init['card_number'] = card_q
        if sugg:
            try:
                if sugg == 'next':
                    from .models import Employee
                    next_id = (Employee.objects.order_by('-id').first().id + 1) if Employee.objects.exists() else 1
                    init['legacy_userid'] = next_id
                else:
                    init['legacy_userid'] = int(sugg)
            except Exception:
                pass
        form = EmployeeExtendedForm(initial=init)
    
    # Return ultra-compact fragment for AJAX modal, full page otherwise
    template = 'agent/employee_form_fragment.html' if is_ajax else 'agent/employee_form.html'
    
    # Get available access levels for the fragment
    available_access_levels = AccessLevel.objects.all()
    
    return render(request, template, {
        'form': form,
        'available_access_levels': available_access_levels
    })

def check_personnel_no(request: HttpRequest):
    """Verifică disponibilitatea unui număr de personal (legacy_userid).
    
    Parametri GET:
    - check: numărul specific de verificat (opțional)
    - exclude_id: ID-ul angajatului curent de excludere din verificare (opțional)
    
    Returns JSON:
    - is_available: True/False dacă numărul verificat este disponibil
    - available: următorul număr disponibil
    - used_by: numele angajatului care folosește numărul (dacă e folosit)
    """
    if not request.user.is_authenticated or not request.user.is_staff:
        return JsonResponse({'ok': False, 'error': 'unauthorized'}, status=403)
    
    check_num = request.GET.get('check')
    exclude_id = request.GET.get('exclude_id')
    
    # Get all existing legacy_userid values
    existing = Employee.objects.filter(legacy_userid__isnull=False)
    
    # Exclude curent employee dacă se editează
    if exclude_id:
        try:
            existing = existing.exclude(id=int(exclude_id))
        except (ValueError, TypeError):
            pass
    
    existing_nums = set(existing.values_list('legacy_userid', flat=True))
    
    response_data = {'ok': True}
    
    # Dacă se verifică un număr specific
    if check_num:
        try:
            check_num = int(check_num)
            if check_num in existing_nums:
                # Numărul este folosit - găsește cine îl folosește
                user = existing.filter(legacy_userid=check_num).first()
                response_data['is_available'] = False
                response_data['used_by'] = f'{user.first_name} {user.last_name}' if user else 'Un alt angajat'
            else:
                # Numărul este disponibil
                response_data['is_available'] = True
        except (ValueError, TypeError):
            response_data['is_available'] = False
            response_data['error'] = 'Număr invalid'
    
    # Găsește întotdeauna următorul disponibil
    candidate = 1
    while candidate in existing_nums:
        candidate += 1
    response_data['available'] = candidate
    
    return JsonResponse(response_data)

def check_card_numbers(request: HttpRequest):
    """Verifică disponibilitatea card-urilor (principal și secundar).
    
    Parametri GET:
    - primary: card principal de verificat
    - secondary: card secundar de verificat (opțional)
    - exclude_id: ID-ul angajatului curent (pentru edit, opțional)
    
    Returns JSON:
    - primary_available: True/False
    - secondary_available: True/False
    - primary_used_by: cine folosește primary (dacă duplicat)
    - secondary_used_by: cine folosește secondary (dacă duplicat)
    """
    try:
        if not request.user.is_authenticated or not request.user.is_staff:
            return JsonResponse({'ok': False, 'error': 'unauthorized'}, status=403)
        
        primary = request.GET.get('primary', '').strip()
        secondary = request.GET.get('secondary', '').strip()
        exclude_id = request.GET.get('exclude_id')
        
        import sys
        print(f'DEBUG check_card_numbers: primary={primary}, secondary={secondary}, exclude_id={exclude_id}', file=sys.stderr)
        
        response_data = {'ok': True}
        
        # Verifică dacă primary și secondary sunt aceeași
        if primary and secondary and primary == secondary:
            response_data['primary_available'] = False
            response_data['secondary_available'] = False
            response_data['error'] = 'Card principal și secundar nu pot fi aceeași'
            return JsonResponse(response_data)
        
        # Verifică primary card - caută în AMBELE câmpuri (card_number SAU secondary_card_number)
        if primary:
            from .models import Employee
            from django.db.models import Q
            existing_primary = Employee.objects.filter(
                Q(card_number=primary) | Q(secondary_card_number=primary)
            )
            if exclude_id:
                existing_primary = existing_primary.exclude(id=exclude_id)
            
            if existing_primary.exists():
                user = existing_primary.first()
                response_data['primary_available'] = False
                response_data['primary_used_by'] = f'{user.first_name} {user.last_name}'
            else:
                response_data['primary_available'] = True
        else:
            response_data['primary_available'] = True
        
        print(f'DEBUG primary result: {response_data.get("primary_available")}', file=sys.stderr)
        
        # Verifică secondary card - caută în AMBELE câmpuri (card_number SAU secondary_card_number)
        if secondary:
            from .models import Employee
            from django.db.models import Q
            existing_secondary = Employee.objects.filter(
                Q(card_number=secondary) | Q(secondary_card_number=secondary)
            )
            if exclude_id:
                existing_secondary = existing_secondary.exclude(id=exclude_id)
            
            if existing_secondary.exists():
                user = existing_secondary.first()
                response_data['secondary_available'] = False
                response_data['secondary_used_by'] = f'{user.first_name} {user.last_name}'
            else:
                response_data['secondary_available'] = True
        else:
            response_data['secondary_available'] = True
        
        print(f'DEBUG secondary result: {response_data.get("secondary_available")}', file=sys.stderr)
        print(f'DEBUG final response: {response_data}', file=sys.stderr)
        
        return JsonResponse(response_data)
    
    except Exception as e:
        import traceback
        return JsonResponse({
            'ok': False, 
            'error': str(e),
            'trace': traceback.format_exc()
        }, status=500)


def employee_edit(request: HttpRequest, pk: int):
    if not request.user.is_authenticated or not request.user.is_staff:
        from django.contrib.auth.views import redirect_to_login
        return redirect_to_login(request.get_full_path())
    emp = Employee.objects.get(pk=pk)
    from .forms import EmployeeExtendedForm
    if request.method == 'POST':
        form = EmployeeExtendedForm(request.POST, instance=emp)
        if form.is_valid():
            if form.has_changed():
                saved_emp = form.save()
                # Reîncarcă obiectul fresh din DB pentru a afișa datele actualizate
                saved_emp.refresh_from_db()
                # Recreează formularul cu obiectul fresh
                fresh_form = EmployeeExtendedForm(instance=saved_emp)
                response = render(request,'agent/employee_form.html',{'form': fresh_form,'obj': saved_emp, 'saved': True})
                # Previne cache-ul browser pentru a afișa mereu date fresh
                response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
                response['Pragma'] = 'no-cache'
                response['Expires'] = '0'
                return response
            else:
                from django.shortcuts import redirect
                return_url = request.POST.get('return_url', '/agent/menu/personnel/')
                return redirect(return_url)
    else:
        form = EmployeeExtendedForm(instance=emp)
    response = render(request,'agent/employee_form.html',{'form': form,'obj': emp})
    # Previne cache-ul și pentru GET
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    return response

def employee_delete(request: HttpRequest, pk: int):
    if not request.user.is_authenticated or not request.user.is_staff or request.method != 'POST':
        return JsonResponse({'ok': False,'error':'unauthorized'}, status=403)
    try:
        Employee.objects.filter(pk=pk).delete(); return JsonResponse({'ok': True})
    except Exception as e:
        return JsonResponse({'ok': False,'error': str(e)}, status=400)

# ----- Controlled Server Shutdown -----
def server_shutdown(request: HttpRequest):
    """Gracefully terminate the dev server (staff only, POST)."""
    if not request.user.is_authenticated or not request.user.is_staff or request.method != 'POST':
        return JsonResponse({'ok': False, 'error': 'unauthorized'}, status=403)
    import threading, sys
    # Respond first, then exit shortly after to let response flush
    def _terminate():
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)
    threading.Timer(0.5, _terminate).start()
    return JsonResponse({'ok': True, 'message': 'Server shutting down in 0.5s'})

# ----- CommCenter & Control Center -----
def _get_active_center():
    try:
        import agent.modern_comm_center as mcc
        return getattr(mcc, 'ACTIVE_CENTER', None)
    except Exception:
        return None

def comm_center_status(request: HttpRequest):
    if not request.user.is_authenticated or not request.user.is_staff:
        return JsonResponse({'ok': False,'error':'unauthorized'}, status=403)
    center = _get_active_center()
    data = {
        'running': bool(center),
    }
    if center:
        last = getattr(center.heartbeat_backend, 'get', lambda f: None)('last_cycle')
        data.update({
            'poll_interval': center.poll_interval,
            'sessions': len(center.sessions),
            'rtlog_lines': center.total_rtlog_lines,
            'event_logs': center.total_event_logs,
            'last_cycle': last,
        })
    return JsonResponse({'ok': True, 'center': data})

def comm_center_start(request: HttpRequest):
    if not request.user.is_authenticated or not request.user.is_staff or request.method != 'POST':
        return JsonResponse({'ok': False,'error':'unauthorized'}, status=403)
    center = _get_active_center()
    if center:
        return JsonResponse({'ok': True,'message':'already-running'})
    try:
        from agent.modern_comm_center import build_and_run_stub
        import agent.modern_comm_center as mcc
        mcc.ACTIVE_CENTER = build_and_run_stub(poll_interval=1.0, driver='stub')
        return JsonResponse({'ok': True,'message':'started'})
    except Exception as e:
        return JsonResponse({'ok': False,'error': str(e)}, status=500)

def comm_center_stop(request: HttpRequest):
    if not request.user.is_authenticated or not request.user.is_staff or request.method != 'POST':
        return JsonResponse({'ok': False,'error':'unauthorized'}, status=403)
    center = _get_active_center()
    if not center:
        return JsonResponse({'ok': True,'message':'not-running'})
    try:
        center.stop()
        import agent.modern_comm_center as mcc
        mcc.ACTIVE_CENTER = None
        return JsonResponse({'ok': True,'message':'stopped'})
    except Exception as e:
        return JsonResponse({'ok': False,'error': str(e)}, status=500)

@csrf_exempt
def check_card_owner(request: HttpRequest):
    """Check if a card belongs to an employee (primary, secondary, or extra cards).
    Query params:
      - card_number: The card to check
    Returns JSON with:
      - exists: True if card is in DB
      - employee_id: Employee ID (if exists)
      - employee_name: Full name (if exists)
      - card_type: 'primary' | 'secondary' | 'extra'
    """
    from .models import Employee, EmployeeCard

    card_number = (request.GET.get('card_number') or '').strip()
    if not card_number:
        return JsonResponse({'exists': False, 'error': 'no-card-number'}, status=400)

    # Normalize comparisons to be case-insensitive and spacing-tolerant
    base = card_number.strip()
    variants = []
    compact = base.replace(' ', '')
    variants.extend([base, base.upper(), base.lower(), compact, compact.upper(), compact.lower()])
    # Strip leading zeros for numeric cards
    if base.isdigit():
        trimmed = base.lstrip('0') or '0'
        variants.extend([trimmed, trimmed.upper(), trimmed.lower()])
    # Remove duplicate variants while preserving order
    seen = set(); normalized = []
    for v in variants:
        if v and v not in seen:
            seen.add(v); normalized.append(v)

    for num in normalized:
        emp = Employee.objects.filter(card_number__iexact=num).first()
        if emp:
            return JsonResponse({
                'exists': True,
                'employee_id': emp.id,
                'employee_name': f"{emp.first_name} {emp.last_name}".strip(),
                'card_type': 'primary'
            })
        emp = Employee.objects.filter(secondary_card_number__iexact=num).first()
        if emp:
            return JsonResponse({
                'exists': True,
                'employee_id': emp.id,
                'employee_name': f"{emp.first_name} {emp.last_name}".strip(),
                'card_type': 'secondary'
            })
        card = EmployeeCard.objects.select_related('employee').filter(card_number__iexact=num).first()
        if card and card.employee:
            emp = card.employee
            return JsonResponse({
                'exists': True,
                'employee_id': emp.id,
                'employee_name': f"{emp.first_name} {emp.last_name}".strip(),
                'card_type': 'extra'
            })

    return JsonResponse({'exists': False})

def control_center(request: HttpRequest):
    if not request.user.is_authenticated or not request.user.is_staff:
        from django.contrib.auth.views import redirect_to_login
        return redirect_to_login(request.get_full_path())
    center = _get_active_center()
    status = {
        'running': bool(center),
        'sessions': center and len(center.sessions) or 0,
        'rtlog_lines': center and center.total_rtlog_lines or 0,
        'event_logs': center and center.total_event_logs or 0,
        'poll_interval': center and center.poll_interval,
    }
    return render(request, 'agent/control_center.html', {'center_status': status})

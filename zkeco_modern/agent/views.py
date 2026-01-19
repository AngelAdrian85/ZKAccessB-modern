import os
from django.http import JsonResponse, HttpRequest, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render
from django.utils import timezone
from django.db.models import Max

from .models import DeviceRealtimeLog, DeviceEventLog, DeviceStatus, Device, DSTime
from .models import Door, TimeSegment, Holiday, AccessLevel, Employee
from .models import CommandLog, EmployeeAccessCache, EmployeeCard
try:
    from .models import AuditLog
except ImportError:
    AuditLog = None
from .forms import (DoorForm, TimeSegmentFormWithDays, HolidayForm, AccessLevelForm,
                    EmployeeForm, EmployeeExtendedForm, DeptForm, AreaForm,
                    AccessLogFilterForm, DeviceExtendedForm, DSTimeForm)
try:
    from .forms import IssueCardForm
except ImportError:
    IssueCardForm = None
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


def _audit_log(request: HttpRequest, *, module: str, action: str, entity_id: int, entity_name: str = '', details: str = '') -> None:
    """Best-effort audit trail writer.

    Writes to agent.AuditLog when available. Never raises.
    """
    if AuditLog is None:
        return
    try:
        AuditLog.objects.create(
            module=(module or '').lower(),
            action=(action or '').lower(),
            entity_id=int(entity_id),
            entity_name=entity_name or '',
            user=getattr(getattr(request, 'user', None), 'username', None),
            ip_address=(request.META.get('REMOTE_ADDR') if hasattr(request, 'META') else None),
            details=details or '',
        )
    except Exception:
        return


def _qs_without_page(request: HttpRequest) -> str:
    """Return current querystring without 'page=' (for pagination links)."""
    try:
        q = request.GET.copy()
        if 'page' in q:
            q.pop('page')
        return q.urlencode()
    except Exception:
        return ''


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
                # This path is invoked by an explicit user action (readers_start).
                # Creating DeviceStatus rows here is acceptable because the operator
                # explicitly requested the readers to start; persist the authoritative
                # online state so the UI and other services can act on it.
                ds, created = _DS.objects.get_or_create(device=dev, defaults={'online': True, 'door_state': ''})
                # If newly created or previously offline -> mark online and record timestamp
                if created or not ds.online:
                    ds.online = True
                    ds.door_state = ''
                    ds.updated_at = timezone.now()
                    ds.save(update_fields=['online', 'door_state', 'updated_at'])
                else:
                    # already online; ensure door_state normalized
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
        # Small cooldown to avoid overwriting a very recent user-initiated toggle.
        COOLDOWN_SECONDS = 5.0
        for dev in qs:
            try:
                # Avoid creating DeviceStatus rows on stop; only update existing records.
                ds = _DS.objects.filter(device=dev).first()
                if not ds:
                    continue
                if ds.online:
                    # If this status was updated very recently (e.g. user pressed Start),
                    # don't immediately flip it to offline to avoid race conditions.
                    try:
                        if ds.updated_at is not None:
                            age = (timezone.now() - ds.updated_at).total_seconds()
                            if age < COOLDOWN_SECONDS:
                                # preserve recent user-initiated state
                                continue
                    except Exception:
                        # if any error computing age, fall back to changing state
                        pass
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
    template = 'agent/monitor.html'
    embedded = request.GET.get('embedded') == '1'
    if embedded:
        template = 'agent/monitor_embed.html'
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({"html": render(request, template).content.decode('utf-8')})
    resp = render(request, template)
    # Allow same-origin framing only for the embedded variant (used inside the Echipamente tab).
    if embedded:
        resp['X-Frame-Options'] = 'SAMEORIGIN'
    return resp


def monitor_device_legacy(request: HttpRequest):
    """Preserve the pre-refactor device form under Monitoring."""
    if not request.user.is_authenticated:
        from django.contrib.auth.views import redirect_to_login
        return redirect_to_login(request.get_full_path())
    from django.db.models import OuterRef, Subquery
    from .models import Device, DeviceStatus as _DS
    latest = _DS.objects.filter(device=OuterRef('pk')).order_by('-updated_at')
    devices = Device.objects.order_by('id').annotate(
        latest_online=Subquery(latest.values('online')[:1]),
        latest_updated_at=Subquery(latest.values('updated_at')[:1])
    )
    return render(request, 'agent/monitor_device_legacy.html', {'devices': devices})

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
    template = 'agent/status_summary.html'
    if request.GET.get('embedded') == '1':
        template = 'agent/status_summary_embed.html'
    return render(request, template, {'rows': rows, 'summary': summary})


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
    template = 'agent/devices_crud_list.html'
    if request.GET.get('embedded') == '1':
        template = 'agent/devices_crud_embed.html'
    return render(request, template, {'page': page, 'active_filter': flt})

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


def device_discover_apply(request: HttpRequest):
    """Create or update devices directly from discovery UI."""
    if not request.user.is_authenticated or request.method != 'POST':
        return JsonResponse({'ok': False, 'error': 'unauthorized'}, status=403)
    import json
    try:
        payload = json.loads(request.body.decode('utf-8'))
    except Exception:
        payload = request.POST.dict()
    action = payload.get('action')
    ip = (payload.get('ip') or '').strip()
    if not ip:
        return JsonResponse({'ok': False, 'error': 'missing-ip'}, status=400)
    port = int(payload.get('port', 4370) or 4370)
    name = (payload.get('name') or f'Centrală {ip}').strip()
    serial = (payload.get('serial_number') or '').strip()
    device_id = payload.get('device_id')

    try:
        if action == 'change_ip':
            target_ip = (payload.get('target_ip') or ip).strip()
            dev = None
            if device_id:
                dev = Device.objects.filter(pk=int(device_id)).first()
            if not dev and serial:
                dev = Device.objects.filter(serial_number=serial).first()
            if not dev:
                dev = Device.objects.filter(ip_address=ip).first()
            if not dev:
                return JsonResponse({'ok': False, 'error': 'device-not-found'}, status=404)
            dev.ip_address = target_ip
            dev.port = port
            dev.save(update_fields=['ip_address', 'port'])
            _audit_log(
                request,
                module='device',
                action='update',
                entity_id=dev.id,
                entity_name=getattr(dev, 'name', '') or '',
                details=f"change_ip {ip} -> {target_ip} port={port}",
            )
            try:
                from legacy_models.models import Device as LegacyDevice  # type: ignore
                legacy = LegacyDevice.objects.filter(sn=dev.serial_number or dev.name).first()
                if legacy:
                    legacy.com_address = target_ip
                    legacy.save(update_fields=['com_address'])
            except Exception:
                pass
            return JsonResponse({'ok': True, 'id': dev.id, 'ip': dev.ip_address, 'updated': True})

        # Default: create or update existing device by IP/serial
        dev, created = Device.objects.get_or_create(
            ip_address=ip,
            defaults={
                'name': name,
                'serial_number': serial or name,
                'port': port,
                'device_type': 'access_panel',
                'comm_mode': 'tcp',
                'enabled': True,
            }
        )
        if not created:
            dev.name = name or dev.name
            if serial:
                dev.serial_number = serial
            dev.port = port
            dev.enabled = True
            dev.save(update_fields=['name','serial_number','port','enabled'])

        _audit_log(
            request,
            module='device',
            action=('create' if created else 'update'),
            entity_id=dev.id,
            entity_name=getattr(dev, 'name', '') or '',
            details=f"discover_apply ip={ip} port={port} sn={getattr(dev, 'serial_number', '')}",
        )

        # Sync minimal legacy device record for migration continuity
        try:
            from legacy_models.models import Device as LegacyDevice, Area as LegacyArea  # type: ignore
            legacy_defaults = {
                'device_name': dev.name,
                'fw_version': dev.firmware_version,
                'com_address': ip,
                'com_port': str(port),
            }
            legacy, _ = LegacyDevice.objects.get_or_create(sn=dev.serial_number or dev.name, defaults=legacy_defaults)
            legacy.device_name = dev.name
            legacy.com_address = ip
            legacy.com_port = str(port)
            if dev.area_name:
                area = LegacyArea.objects.filter(areaname=dev.area_name).first()
                if area:
                    legacy.area = area
            legacy.save()
        except Exception:
            pass

        return JsonResponse({'ok': True, 'id': dev.id, 'ip': dev.ip_address, 'created': created})
    except Exception as e:
        return JsonResponse({'ok': False, 'error': str(e)}, status=400)

def device_create(request: HttpRequest):
    if not request.user.is_authenticated or not request.user.is_staff:
        from django.contrib.auth.views import redirect_to_login
        return redirect_to_login(request.get_full_path())

    def _safe_return_url() -> str:
        from django.urls import reverse
        from django.utils.http import url_has_allowed_host_and_scheme

        default_url = reverse('crud-devices-list')
        candidate = (
            request.POST.get('next')
            or request.GET.get('next')
            or request.META.get('HTTP_REFERER')
        )
        if not candidate:
            return default_url
        if url_has_allowed_host_and_scheme(
            url=candidate,
            allowed_hosts={request.get_host()},
            require_https=request.is_secure(),
        ):
            return candidate
        return default_url

    if request.method == 'POST':
        form = DeviceExtendedForm(request.POST)
        if form.is_valid():
            obj = form.save()
            _audit_log(
                request,
                module='device',
                action='create',
                entity_id=obj.id,
                entity_name=getattr(obj, 'name', '') or '',
                details=f"ip={getattr(obj, 'ip_address', None)} port={getattr(obj, 'port', None)} sn={getattr(obj, 'serial_number', '')}",
            )
            is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
            if is_ajax:
                return JsonResponse(
                    {
                        'ok': True,
                        'id': obj.id,
                        'created': True,
                        'message': 'Dispozitiv creat cu succes!',
                        'redirect_url': _safe_return_url(),
                    }
                )
            from django.shortcuts import redirect
            return redirect(_safe_return_url())
        else:
            is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
            if is_ajax:
                from django.template.loader import render_to_string

                errors = {k: v[0] if v else '' for k, v in form.errors.items()}
                html = render_to_string(
                    'agent/device_form_modal.html',
                    {
                        'form': form,
                        'action_url': request.path,
                        'next_url': _safe_return_url(),
                        'mode': 'create',
                    },
                    request=request,
                )
                return JsonResponse(
                    {
                        'ok': False,
                        'error': 'Form validation failed',
                        'errors': errors,
                        'html': html,
                    },
                    status=400,
                )
            return render(request,'agent/device_form.html',{'form': form})
    else:
        form = DeviceExtendedForm()
        # ✅ ADAUGĂ SUPORT AJAX PENTRU MODAL
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        if is_ajax:
            return render(
                request,
                'agent/device_form_modal.html',
                {
                    'form': form,
                    'action_url': request.path,
                    'next_url': _safe_return_url(),
                    'mode': 'create',
                },
            )
    return render(request,'agent/device_form.html',{'form': form, 'next_url': _safe_return_url()})

def device_edit(request: HttpRequest, pk: int):
    if not request.user.is_authenticated or not request.user.is_staff:
        from django.contrib.auth.views import redirect_to_login
        return redirect_to_login(request.get_full_path())

    def _safe_return_url() -> str:
        from django.urls import reverse
        from django.utils.http import url_has_allowed_host_and_scheme

        default_url = reverse('crud-devices-list')
        candidate = (
            request.POST.get('next')
            or request.GET.get('next')
            or request.META.get('HTTP_REFERER')
        )
        if not candidate:
            return default_url
        if url_has_allowed_host_and_scheme(
            url=candidate,
            allowed_hosts={request.get_host()},
            require_https=request.is_secure(),
        ):
            return candidate
        return default_url

    from agent.models import Device
    obj = Device.objects.get(pk=pk)
    if request.method == 'POST':
        before = {
            'name': obj.name,
            'serial_number': obj.serial_number,
            'device_type': obj.device_type,
            'comm_mode': obj.comm_mode,
            'ip_address': obj.ip_address,
            'port': obj.port,
            'area_name': obj.area_name,
            'time_zone': obj.time_zone,
            'enabled': obj.enabled,
            'auto_sync_time': obj.auto_sync_time,
            'clear_on_add': obj.clear_on_add,
            'scanner_linked': obj.scanner_linked,
            'scanner_type': obj.scanner_type,
        }
        form = DeviceExtendedForm(request.POST, instance=obj)
        if form.is_valid():
            saved = form.save()
            try:
                after = {
                    'name': saved.name,
                    'serial_number': saved.serial_number,
                    'device_type': saved.device_type,
                    'comm_mode': saved.comm_mode,
                    'ip_address': saved.ip_address,
                    'port': saved.port,
                    'area_name': saved.area_name,
                    'time_zone': saved.time_zone,
                    'enabled': saved.enabled,
                    'auto_sync_time': saved.auto_sync_time,
                    'clear_on_add': saved.clear_on_add,
                    'scanner_linked': saved.scanner_linked,
                    'scanner_type': saved.scanner_type,
                }
                changes = []
                for k, v_before in before.items():
                    v_after = after.get(k)
                    if v_before != v_after:
                        changes.append(f"{k}: {v_before} -> {v_after}")
                details = '; '.join(changes)[:2000]
            except Exception:
                details = ''
            _audit_log(
                request,
                module='device',
                action='update',
                entity_id=saved.id,
                entity_name=getattr(saved, 'name', '') or '',
                details=details,
            )
            is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
            if is_ajax:
                return JsonResponse(
                    {
                        'ok': True,
                        'id': saved.id,
                        'created': False,
                        'message': 'Dispozitiv actualizat cu succes!',
                        'redirect_url': _safe_return_url(),
                    }
                )
            from django.shortcuts import redirect
            return redirect(_safe_return_url())
        else:
            is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
            if is_ajax:
                from django.template.loader import render_to_string

                errors = {k: v[0] if v else '' for k, v in form.errors.items()}
                html = render_to_string(
                    'agent/device_form_modal.html',
                    {
                        'form': form,
                        'obj': obj,
                        'action_url': request.path,
                        'next_url': _safe_return_url(),
                        'mode': 'edit',
                    },
                    request=request,
                )
                return JsonResponse(
                    {
                        'ok': False,
                        'error': 'Form validation failed',
                        'errors': errors,
                        'html': html,
                    },
                    status=400,
                )
    else:
        form = DeviceExtendedForm(instance=obj)
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        if is_ajax:
            return render(
                request,
                'agent/device_form_modal.html',
                {
                    'form': form,
                    'obj': obj,
                    'action_url': request.path,
                    'next_url': _safe_return_url(),
                    'mode': 'edit',
                },
            )
    return render(request,'agent/device_form.html',{'form': form, 'obj': obj, 'next_url': _safe_return_url()})

def device_delete(request: HttpRequest, pk: int):
    if not request.user.is_authenticated or not request.user.is_staff or request.method != 'POST':
        return JsonResponse({'ok': False,'error':'unauthorized'}, status=403)
    from agent.models import Device
    try:
        obj = Device.objects.filter(pk=pk).first()
        Device.objects.filter(pk=pk).delete()
        if obj is not None:
            _audit_log(
                request,
                module='device',
                action='delete',
                entity_id=int(pk),
                entity_name=getattr(obj, 'name', '') or '',
            )
        return JsonResponse({'ok': True})
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
    # IMPORTANT: keep PERSONAL Loguri scoped to PERSONAL modules even on first page render.
    # Otherwise non-personnel (e.g. door/device) logs can appear until the JS refresh runs.
    try:
        audit_logs = (
            list(
                AuditLog.objects.filter(module__in=['employee', 'department', 'issuecard'])
                .order_by('-timestamp')[:200]
            )
            if AuditLog
            else []
        )
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
    from .models import Device
    from django.db.models import OuterRef, Subquery
    from .models import DeviceStatus as _DS

    latest = _DS.objects.filter(device=OuterRef('pk')).order_by('-updated_at')
    qs = Device.objects.order_by('name').annotate(
        latest_online=Subquery(latest.values('online')[:1]),
        latest_updated_at=Subquery(latest.values('updated_at')[:1])
    )
    flt = (request.GET.get('filter') or 'all').strip().lower()
    if flt == 'controllers':
        qs = qs.filter(device_type__in=['access_panel','door_controller','two_door_panel','multi_door_panel'], scanner_linked=False)
    elif flt == 'readers':
        qs = qs.filter(scanner_linked=True)
    elif flt == 'new':
        qs = qs.filter(scanner_linked=False).exclude(device_type__in=['access_panel','door_controller','two_door_panel','multi_door_panel'])

    devices_page = _paginate(qs, request)

    # Preload status summary for Monitorizare dispozitive tab
    status_rows = []
    for ds in DeviceStatus.objects.select_related('device').all():
        status_rows.append({
            'id': ds.device.id,
            'name': ds.device.name,
            'serial': ds.device.serial_number,
            'online': ds.online,
            'door_state': ds.door_state,
            'updated_at': ds.updated_at,
        })
    status_summary_data = {
        'total': len(status_rows),
        'online': sum(1 for r in status_rows if r['online']),
        'doors_open': sum(1 for r in status_rows if r['door_state'] == 'OPEN'),
    }

    return render(request, 'agent/menu_device.html', {
        'devices_page': devices_page,
        'devices_filter': flt,
        'status_rows': status_rows,
        'status_summary': status_summary_data,
    })

def menu_access_control(request: HttpRequest):
    if not request.user.is_authenticated:
        from django.contrib.auth.views import redirect_to_login
        return redirect_to_login(request.get_full_path())
    if request.GET.get('embed') == '1':
        resp = render(request, 'agent/menu_access_embed.html')
        resp['X-Frame-Options'] = 'SAMEORIGIN'
        return resp
    return render(request, 'agent/menu_access.html')


def menu_reports(request: HttpRequest):
    if not request.user.is_authenticated:
        from django.contrib.auth.views import redirect_to_login
        return redirect_to_login(request.get_full_path())

    tab = (request.GET.get('tab') or 'accesslog').strip().lower()
    tab = tab if tab in ('accesslog', 'device', 'personal', 'system') else 'accesslog'

    # Shared filters
    user_param_present = 'user' in request.GET
    user_q = (request.GET.get('user') or '').strip() if user_param_present else (getattr(getattr(request, 'user', None), 'username', '') or '').strip()
    action_q = (request.GET.get('action') or '').strip().lower()
    q = (request.GET.get('q') or '').strip()
    date_from = (request.GET.get('from') or '').strip()
    date_to = (request.GET.get('to') or '').strip()

    # Sorting
    sort_key = (request.GET.get('sort') or '').strip().lower()
    sort_dir = (request.GET.get('dir') or 'desc').strip().lower()
    if sort_dir not in ('asc', 'desc'):
        sort_dir = 'desc'

    def _sort_href(field: str, *, default_dir: str = 'desc') -> str:
        """Build a querystring that toggles direction for the same sort field."""
        try:
            qd = request.GET.copy()
            if 'page' in qd:
                qd.pop('page')
            if field == sort_key:
                next_dir = 'asc' if sort_dir == 'desc' else 'desc'
            else:
                next_dir = default_dir
            qd['sort'] = field
            qd['dir'] = next_dir
            return '?' + qd.urlencode()
        except Exception:
            return ''

    def _sort_indicator(field: str) -> str:
        if field != sort_key:
            return ''
        return '▲' if sort_dir == 'asc' else '▼'

    page = None
    page_exists = False
    missing_accesslog = False
    access_rows = []
    system_rows = []

    def _paginate_list(items, request_obj, per_page=50):
        from django.core.paginator import Paginator
        paginator = Paginator(items, per_page)
        page_number = request_obj.GET.get('page') or 1
        return paginator.get_page(page_number)

    def _dedupe_remote_rows(items, window_seconds: int = 3):
        """Drop near-duplicate Remote* entries (typically caused by retries/acks).

        Keeps newest entries because we iterate in already-sorted (desc) order.
        """
        kept = []
        last_seen = {}
        for it in items:
            try:
                desc = str(it.get('event_description') or '')
                if not desc.lower().startswith('remote'):
                    kept.append(it)
                    continue
                ts = it.get('_ts')
                # Best-effort timestamp
                if not ts:
                    kept.append(it)
                    continue
                key = (
                    desc.strip().lower(),
                    str(it.get('door_name') or it.get('event_point') or '').strip().lower(),
                    str(it.get('device_name') or '').strip().lower(),
                    str(it.get('operator') or '').strip().lower(),
                )
                prev = last_seen.get(key)
                if prev and abs((prev - ts).total_seconds()) <= window_seconds:
                    continue
                last_seen[key] = ts
                kept.append(it)
            except Exception:
                kept.append(it)
        return kept

    if tab == 'accesslog':
        # AccessLog is primarily sourced from durable AuditLog (module=accesslog/door)
        # because device event downloads can be unavailable on some firmwares.
        # Fallback to Device RTLog/EventLog persistence if no audit events exist.
        from .models import DeviceRealtimeLog as _RT, DeviceEventLog as _EV, Door as _Door, Device as _Device, Employee as _Employee
        from .event_codes import describe as _describe_code
        from .event_codes import describe_verify_mode as _describe_verify
        from django.utils.dateparse import parse_datetime, parse_date
        from django.db.models import Q
        import json as _json

        # Common filters
        card_q = (request.GET.get('card') or '').strip()
        door_q = (request.GET.get('door') or '').strip()
        status_q = (request.GET.get('status') or '').strip().lower()
        verify_q = (request.GET.get('verify') or '').strip().lower()
        person_q = (request.GET.get('person') or '').strip()  # interpreted as UserID/PIN

        # --- A) AuditLog access events (API/test + door commands) ---
        audit_items = []
        if AuditLog is not None:
            try:
                audit_qs = AuditLog.objects.filter(module__in=['accesslog', 'door']).order_by('-timestamp')
            except Exception:
                audit_qs = None

            if audit_qs is not None:
                # Date range
                if date_from:
                    dt = parse_datetime(date_from)
                    if not dt:
                        d = parse_date(date_from)
                        if d:
                            from datetime import datetime, time
                            dt = timezone.make_aware(datetime.combine(d, time.min))
                    elif timezone.is_naive(dt):
                        dt = timezone.make_aware(dt)
                    if dt:
                        audit_qs = audit_qs.filter(timestamp__gte=dt)
                if date_to:
                    dt = parse_datetime(date_to)
                    if not dt:
                        d = parse_date(date_to)
                        if d:
                            from datetime import datetime, time
                            dt = timezone.make_aware(datetime.combine(d, time.max))
                    elif timezone.is_naive(dt):
                        dt = timezone.make_aware(dt)
                    if dt:
                        audit_qs = audit_qs.filter(timestamp__lte=dt)

                # Apply basic text filters at queryset level (best-effort)
                if card_q:
                    audit_qs = audit_qs.filter(details__icontains=card_q)
                if door_q:
                    audit_qs = audit_qs.filter(Q(details__icontains=door_q) | Q(entity_name__icontains=door_q))
                if person_q:
                    audit_qs = audit_qs.filter(details__icontains=person_q)
                if verify_q:
                    audit_qs = audit_qs.filter(details__icontains=verify_q)
                if status_q in ('accepted', 'acceptat'):
                    audit_qs = audit_qs.exclude(action__in=['denied'])
                elif status_q in ('denied', 'respins'):
                    audit_qs = audit_qs.filter(action__in=['denied'])

                # Limit to keep response fast; merged list is still sorted later.
                audit_rows = list(audit_qs[:500])
                device_ids = set()
                door_ids = set()
                parsed = []
                for a in audit_rows:
                    details_raw = getattr(a, 'details', '') or ''
                    payload = {}
                    try:
                        payload = _json.loads(details_raw) if details_raw and details_raw.strip().startswith('{') else {}
                    except Exception:
                        payload = {}
                    dev_id_val = payload.get('device_id')
                    door_id_val = payload.get('door_id')
                    if dev_id_val is not None:
                        try:
                            device_ids.add(int(dev_id_val))
                        except Exception:
                            pass
                    if door_id_val is not None:
                        try:
                            door_ids.add(int(door_id_val))
                        except Exception:
                            pass
                    parsed.append((a, payload))

                # Bulk backfill department names when missing in payload
                missing_dept_emp_ids = set()
                missing_dept_cards = set()
                for (_a, pl) in parsed:
                    if str(pl.get('department_name') or '').strip():
                        continue
                    ev = pl.get('employee_id')
                    if ev is not None:
                        try:
                            missing_dept_emp_ids.add(int(ev))
                        except Exception:
                            pass
                    cv = str(pl.get('card_number') or '').strip()
                    if cv:
                        missing_dept_cards.add(cv)

                dept_by_emp_id_backfill = {}
                if missing_dept_emp_ids or missing_dept_cards:
                    q_emp = Q()
                    if missing_dept_emp_ids:
                        q_emp |= Q(id__in=sorted(missing_dept_emp_ids))
                    if missing_dept_cards:
                        q_emp |= Q(card_number__in=sorted(missing_dept_cards)) | Q(secondary_card_number__in=sorted(missing_dept_cards))
                    for e in _Employee.objects.filter(q_emp):
                        try:
                            dpt = getattr(e, 'dept', None)
                            dept_name_val = (getattr(dpt, 'DeptName', '') or getattr(dpt, 'deptname', '') or '') if dpt else ''
                        except Exception:
                            dept_name_val = ''
                        dept_by_emp_id_backfill[getattr(e, 'id', 0)] = dept_name_val

                device_map = {d.id: d for d in _Device.objects.filter(id__in=sorted(device_ids))} if device_ids else {}
                door_map_by_id = {d.id: d for d in _Door.objects.filter(id__in=sorted(door_ids)).select_related('device')} if door_ids else {}

                for (a, payload) in parsed:
                    ts = getattr(a, 'timestamp', None)
                    ts_local = timezone.localtime(ts) if ts else timezone.localtime(timezone.now())
                    card = str(payload.get('card_number') or '').strip()
                    emp_name = str(payload.get('employee_name') or '').strip()
                    dept_name = str(payload.get('department_name') or '').strip()
                    emp_pin = payload.get('employee_pin')
                    if emp_pin is None:
                        emp_pin = payload.get('employee_id')
                    emp_pin = '' if emp_pin is None else str(emp_pin)

                    door_id_val = payload.get('door_id')
                    door_name = str(payload.get('door_name') or '').strip()
                    dev_id_val = payload.get('device_id')
                    dev_name = str(payload.get('device_name') or '').strip()
                    area_name = str(payload.get('area_name') or '').strip()
                    ip_addr = ''

                    door_obj = None
                    try:
                        if door_id_val is not None:
                            door_obj = door_map_by_id.get(int(door_id_val))
                    except Exception:
                        door_obj = None
                    if door_obj and not door_name:
                        door_name = getattr(door_obj, 'name', '') or ''

                    dev_obj = None
                    try:
                        if dev_id_val is not None:
                            dev_obj = device_map.get(int(dev_id_val))
                    except Exception:
                        dev_obj = None
                    if dev_obj and not dev_name:
                        dev_name = getattr(dev_obj, 'name', '') or ''
                    if dev_obj and not area_name:
                        area_name = getattr(dev_obj, 'area_name', '') or ''
                    if dev_obj:
                        ip_addr = getattr(dev_obj, 'ip_address', '') or ''

                    # Backfill department from Employee record if missing
                    if not dept_name:
                        try:
                            emp_id_val = payload.get('employee_id')
                            if emp_id_val is not None:
                                try:
                                    dept_name = dept_by_emp_id_backfill.get(int(emp_id_val), '')
                                except Exception:
                                    dept_name = ''
                            if not dept_name and card:
                                emp_obj = _Employee.objects.filter(Q(card_number=card) | Q(secondary_card_number=card)).first()
                                if emp_obj is not None:
                                    dpt = getattr(emp_obj, 'dept', None)
                                    if dpt:
                                        dept_name = getattr(dpt, 'DeptName', '') or getattr(dpt, 'deptname', '') or ''
                        except Exception:
                            pass

                    event_desc = str(payload.get('event_description') or '').strip()
                    verify_label = _describe_verify(str(payload.get('verify_mode') or ''))
                    status_text = str(payload.get('status_text') or '').strip()
                    # Normalize status_text: older records may embed "<ip> - <door> RESPINS".
                    try:
                        st_u = status_text.upper()
                        if 'RESPINS' in st_u or 'DENIED' in st_u or st_u.strip() == 'DENY':
                            status_text = 'RESPINS'
                        elif 'ACCEPTAT' in st_u or 'ACCEPTED' in st_u or st_u.strip() == 'OK':
                            status_text = 'ACCEPTAT'
                    except Exception:
                        pass
                    if not status_text:
                        act = str(getattr(a, 'action', '') or '').lower()
                        status_text = 'ACCEPTAT' if act != 'denied' else 'RESPINS'
                    status_hint = str(ip_addr or '').strip()

                    # Show operator only for remote actions (door commands or accesslog remote_open)
                    operator = ''
                    is_remote = False
                    mod = ''
                    try:
                        mod = str(getattr(a, 'module', '') or '').lower()
                        is_remote = bool(payload.get('remote_open')) or event_desc.lower().startswith('remote')
                        if mod == 'door' or is_remote:
                            operator = (getattr(a, 'user', None) or '')
                    except Exception:
                        operator = ''
                        is_remote = False
                        mod = ''

                    # Access action classification (for the dedicated "Acțiune" column)
                    st_norm = (status_text or '').strip().upper()
                    if mod == 'door':
                        access_action = 'command'
                    elif is_remote or (event_desc.lower().startswith('remote')):
                        access_action = 'remote'
                    elif st_norm in ('ACCEPTAT', 'RESPINS'):
                        access_action = 'scan'
                    else:
                        access_action = 'event'

                    audit_items.append({
                        '_ts': ts_local,
                        'action_time': ts_local.strftime('%Y-%m-%d %H:%M:%S'),
                        'event_point': door_name or '-',
                        'event_description': event_desc,
                        'card_number': card,
                        'door_name': door_name,
                        'device_name': dev_name,
                        'area_name': area_name,
                        'employee_pin': emp_pin,
                        'employee_name': emp_name,
                        'department_name': dept_name,
                        'status_text': status_text,
                        'status_hint': status_hint,
                        'access_action': access_action,
                        'verify_mode': verify_label,
                        'operator': operator,
                        'remarks': '',
                    })

        # --- B) Hardware device logs (RTLog/EventLog persisted) ---
        device_items = []
        raw_field = 'raw_line'
        created_field = 'created_at'
        base_qs = None
        try:
            if _EV.objects.exists():
                base_qs = _EV.objects.all().order_by('-created_at')
                raw_field = 'raw_line'
            else:
                base_qs = _RT.objects.all().order_by('-created_at')
                raw_field = 'raw'
        except Exception:
            base_qs = None

        if base_qs is not None:
            qs = base_qs
            # Drop the noisy keepalive pattern that polluted reports
            try:
                if raw_field == 'raw':
                    qs = qs.exclude(raw__contains=',0,0,200,0,0')
                elif raw_field == 'raw_line':
                    qs = qs.exclude(raw_line__contains=',0,0,200,0,0')
            except Exception:
                pass

            # Filters: from/to (date or datetime-local) apply to created_at
            if date_from:
                dt = parse_datetime(date_from)
                if not dt:
                    d = parse_date(date_from)
                    if d:
                        from datetime import datetime, time
                        dt = timezone.make_aware(datetime.combine(d, time.min))
                elif timezone.is_naive(dt):
                    dt = timezone.make_aware(dt)
                if dt:
                    qs = qs.filter(**{f"{created_field}__gte": dt})
            if date_to:
                dt = parse_datetime(date_to)
                if not dt:
                    d = parse_date(date_to)
                    if d:
                        from datetime import datetime, time
                        dt = timezone.make_aware(datetime.combine(d, time.max))
                elif timezone.is_naive(dt):
                    dt = timezone.make_aware(dt)
                if dt:
                    qs = qs.filter(**{f"{created_field}__lte": dt})

            card_q = (request.GET.get('card') or '').strip()
            door_q = (request.GET.get('door') or '').strip()
            status_q = (request.GET.get('status') or '').strip().lower()
            verify_q = (request.GET.get('verify') or '').strip().lower()
            person_q = (request.GET.get('person') or '').strip()  # interpreted as UserID/PIN

            if card_q:
                qs = qs.filter(**{f"{raw_field}__icontains": card_q})
            if door_q:
                qs = qs.filter(**{f"{raw_field}__icontains": f",{door_q},"})
            if person_q:
                qs = qs.filter(**{f"{raw_field}__icontains": f",{person_q},"})
            if status_q in ('accepted', 'acceptat'):
                qs = qs.filter(**{f"{raw_field}__icontains": ',200,'})
            elif status_q in ('denied', 'respins'):
                qs = qs.filter(**{f"{raw_field}__icontains": ',201,'})
            if verify_q:
                qs = qs.filter(**{f"{raw_field}__icontains": verify_q})

            # Keep it bounded for merge
            rows = list(qs[:800])
            device_ids = sorted({getattr(r, 'device_id', None) for r in rows if getattr(r, 'device_id', None) is not None})
            device_map = {d.id: d for d in _Device.objects.filter(id__in=device_ids)} if device_ids else {}

            door_keys = set()
            card_values = set()
            pin_values = set()
            parsed_lines = []
            for r in rows:
                raw_line = (getattr(r, raw_field, '') or '').strip()
                parts = [p.strip() for p in raw_line.split(',')]
                ts_str = parts[0] if len(parts) > 0 else ''
                pin = parts[1] if len(parts) > 1 else ''
                card = parts[2] if len(parts) > 2 else ''
                door_no = parts[3] if len(parts) > 3 else ''
                code = parts[4] if len(parts) > 4 else ''
                verify_mode = parts[5] if len(parts) > 5 else ''
                dev_id = getattr(r, 'device_id', None)
                # Drop known noisy repeat pattern
                if str(code) == '200' and str(card).strip() in ('', '0', '000000', '00000000') and str(door_no).strip() in ('', '0'):
                    continue
                if dev_id is not None and door_no:
                    door_keys.add((dev_id, door_no))
                if card and card not in ('0', '000000', '00000000'):
                    card_values.add(card)
                if pin and pin not in ('0',):
                    pin_values.add(pin)
                parsed_lines.append((r, ts_str, pin, card, door_no, code, verify_mode))

            door_map = {}
            if door_keys:
                dids = sorted({k[0] for k in door_keys})
                names = sorted({k[1] for k in door_keys})
                for d in _Door.objects.filter(device_id__in=dids, name__in=names).select_related('device'):
                    door_map[(d.device_id, str(getattr(d, 'name', '') or ''))] = d

            emp_by_card = {}
            emp_by_pin = {}
            dept_by_emp_id = {}
            emp_id_by_card = {}
            emp_id_by_pin = {}
            if card_values or pin_values:
                q_emp = Q()
                if card_values:
                    q_emp |= Q(card_number__in=card_values) | Q(secondary_card_number__in=card_values)
                pin_ints = []
                for p in pin_values:
                    try:
                        pin_ints.append(int(str(p)))
                    except Exception:
                        pass
                if pin_ints:
                    q_emp |= Q(legacy_userid__in=pin_ints)
                emps = _Employee.objects.filter(q_emp)
                for e in emps:
                    full = (f"{getattr(e,'first_name','') or ''} {getattr(e,'last_name','') or ''}").strip()
                    eid = getattr(e, 'id', None)
                    if getattr(e, 'card_number', None):
                        emp_by_card[str(e.card_number)] = full
                        if eid is not None:
                            emp_id_by_card[str(e.card_number)] = eid
                    if getattr(e, 'secondary_card_number', None):
                        emp_by_card[str(e.secondary_card_number)] = full
                        if eid is not None:
                            emp_id_by_card[str(e.secondary_card_number)] = eid
                    if getattr(e, 'legacy_userid', None) is not None:
                        emp_by_pin[str(getattr(e, 'legacy_userid'))] = full
                        if eid is not None:
                            emp_id_by_pin[str(getattr(e, 'legacy_userid'))] = eid
                    try:
                        dpt = getattr(e, 'dept', None)
                        dept_name = (getattr(dpt, 'DeptName', '') or getattr(dpt, 'deptname', '') or '') if dpt else ''
                    except Exception:
                        dept_name = ''
                    dept_by_emp_id[getattr(e, 'id', 0)] = dept_name

            for (_r, ts_str, pin, card, door_no, code, verify_mode) in parsed_lines:
                dev_id = getattr(_r, 'device_id', None)
                dev_obj = device_map.get(dev_id)
                dev_name = getattr(dev_obj, 'name', '') if dev_obj else ''
                area_name = getattr(dev_obj, 'area_name', '') if dev_obj else ''
                ip_addr = getattr(dev_obj, 'ip_address', '') if dev_obj else ''
                created_at = getattr(_r, created_field, None) or timezone.now()

                door_obj = door_map.get((dev_id, str(door_no)))
                door_name = getattr(door_obj, 'name', '') if door_obj else (door_no or '')

                verify_label = _describe_verify(str(verify_mode))
                base_desc = _describe_code(str(code)) or (f"Code {code}" if code else '')
                # Legacy-friendly naming for accepted opens
                desc = base_desc
                if str(code) == '200':
                    if verify_label == 'Only Fingerprint':
                        desc = 'Normal Fingerprint Open'
                    else:
                        desc = 'Normal Punch Open'
                elif str(code) == '201':
                    desc = 'Access Denied' if (emp_by_card.get(str(card)) or emp_by_pin.get(str(pin))) else 'Unregistered Card'
                elif str(code) in ('100', '101'):
                    desc = base_desc

                status_text = 'ACCEPTAT' if str(code) == '200' else ('RESPINS' if str(code) == '201' else desc)
                employee_name = emp_by_card.get(str(card), '') or emp_by_pin.get(str(pin), '') or ''
                employee_pin = pin
                dept_name = ''
                try:
                    emp_id = None
                    if card:
                        emp_id = emp_id_by_card.get(str(card))
                    if emp_id is None and pin:
                        emp_id = emp_id_by_pin.get(str(pin))
                    if emp_id is not None:
                        dept_name = dept_by_emp_id.get(int(emp_id), '')
                except Exception:
                    dept_name = ''

                device_items.append({
                    '_ts': timezone.localtime(created_at) if created_at else timezone.localtime(timezone.now()),
                    'action_time': ts_str or (timezone.localtime(created_at).strftime('%Y-%m-%d %H:%M:%S') if created_at else ''),
                    'event_point': door_name or '-',
                    'event_description': desc,
                    'card_number': card,
                    'door_name': door_name,
                    'device_name': dev_name,
                    'area_name': area_name,
                    'employee_pin': employee_pin,
                    'employee_name': employee_name,
                    'department_name': dept_name,
                    'status_text': status_text,
                    'status_hint': str(ip_addr or '').strip(),
                    'access_action': 'scan' if str(status_text).strip().upper() in ('ACCEPTAT', 'RESPINS') else 'event',
                    'verify_mode': verify_label,
                    'operator': '',
                    'remarks': '',
                })

        # Merge + sort
        merged = []
        merged.extend(audit_items)
        merged.extend(device_items)
        if not merged:
            missing_accesslog = True

        access_sort_map = {
            'ts': '_ts',
            'zone': 'area_name',
            'device': 'device_name',
            'point': 'event_point',
            'event': 'event_description',
            'card': 'card_number',
            'pin': 'employee_pin',
            'name': 'employee_name',
            'dept': 'department_name',
            'action': 'access_action',
            'user': 'operator',
            'status': 'status_text',
            'method': 'verify_mode',
        }
        sort_field = access_sort_map.get(sort_key or 'ts', '_ts')
        reverse = (sort_dir != 'asc')
        if sort_field == '_ts':
            merged.sort(key=lambda x: x.get('_ts') or timezone.localtime(timezone.now()), reverse=reverse)
        else:
            merged.sort(key=lambda x: str(x.get(sort_field) or '').lower(), reverse=reverse)

        merged = _dedupe_remote_rows(merged, window_seconds=3)
        page = _paginate_list(merged, request, per_page=50)
        page_exists = True
        access_rows = list(getattr(page, 'object_list', []) or [])

    else:
        # AuditLog-backed tabs
        qs = AuditLog.objects.all().order_by('-timestamp') if AuditLog else None
        if qs is not None:
            if tab == 'device':
                qs = qs.filter(module__in=['device', 'door'])
            elif tab == 'personal':
                qs = qs.filter(module__in=['employee', 'department', 'issuecard'])
            elif tab == 'system':
                # Legacy-like "All Access Control Events": merge audit + hardware logs
                qs = qs.filter(module__in=['accesslog', 'door'])

            if user_q:
                qs = qs.filter(user__icontains=user_q)

            if action_q and action_q != 'all':
                if action_q in ('create', 'update', 'delete'):
                    qs = qs.filter(action=action_q)
                elif action_q == 'others':
                    qs = qs.exclude(action__in=['create', 'update', 'delete'])

            if q:
                from django.db.models import Q
                qs = qs.filter(Q(entity_name__icontains=q) | Q(details__icontains=q) | Q(module__icontains=q))

            # Date range
            from django.utils.dateparse import parse_datetime
            if date_from:
                dt = parse_datetime(date_from)
                if dt:
                    qs = qs.filter(timestamp__gte=dt)
            if date_to:
                dt = parse_datetime(date_to)
                if dt:
                    qs = qs.filter(timestamp__lte=dt)

            if tab == 'system':
                # System Log Events: show access-control events from BOTH audit trail and hardware scans.
                from django.utils.dateparse import parse_datetime, parse_date
                from django.db.models import Q
                import json as _json
                from .event_codes import describe as _describe_code
                from .event_codes import describe_verify_mode as _describe_verify
                from .models import DeviceRealtimeLog as _RT, DeviceEventLog as _EV, Door as _Door, Device as _Device, Employee as _Employee

                # A) Audit-derived rows (bounded)
                audit_rows = []
                audit_src = list(qs[:500])

                parsed_audit = []
                audit_device_ids = set()
                for a in audit_src:
                    details_raw = getattr(a, 'details', '') or ''
                    payload = {}
                    try:
                        payload = _json.loads(details_raw) if details_raw and details_raw.strip().startswith('{') else {}
                    except Exception:
                        payload = {}
                    dev_id_val = payload.get('device_id')
                    if dev_id_val is not None:
                        try:
                            audit_device_ids.add(int(dev_id_val))
                        except Exception:
                            pass
                    parsed_audit.append((a, payload))

                audit_device_map = {d.id: d for d in _Device.objects.filter(id__in=sorted(audit_device_ids))} if audit_device_ids else {}

                for a, payload in parsed_audit:
                    ts = getattr(a, 'timestamp', None)
                    ts_local = timezone.localtime(ts) if ts else timezone.localtime(timezone.now())
                    event_desc = str(payload.get('event_description') or '')

                    dev_name = str(payload.get('device_name') or '').strip()
                    area_name = str(payload.get('area_name') or '').strip()
                    ip_addr = ''
                    try:
                        dev_id_val = payload.get('device_id')
                        if dev_id_val is not None:
                            dev_obj = audit_device_map.get(int(dev_id_val))
                            if dev_obj and not dev_name:
                                dev_name = getattr(dev_obj, 'name', '') or ''
                            if dev_obj and not area_name:
                                area_name = getattr(dev_obj, 'area_name', '') or ''
                            if dev_obj:
                                ip_addr = getattr(dev_obj, 'ip_address', '') or ''
                    except Exception:
                        pass

                    operator = ''
                    try:
                        mod = str(getattr(a, 'module', '') or '').lower()
                        is_remote = bool(payload.get('remote_open')) or event_desc.lower().startswith('remote')
                        if mod == 'door' or is_remote:
                            operator = (getattr(a, 'user', None) or '')
                    except Exception:
                        operator = ''

                    status_text = str(payload.get('status_text') or '').strip()
                    # Normalize status_text: older records may embed "<ip> - <door> RESPINS".
                    try:
                        st_u = status_text.upper()
                        if 'RESPINS' in st_u or 'DENIED' in st_u or st_u.strip() == 'DENY':
                            status_text = 'RESPINS'
                        elif 'ACCEPTAT' in st_u or 'ACCEPTED' in st_u or st_u.strip() == 'OK':
                            status_text = 'ACCEPTAT'
                    except Exception:
                        pass

                    audit_rows.append({
                        '_ts': ts_local,
                        'action_time': ts_local.strftime('%Y-%m-%d %H:%M:%S'),
                        'area_name': area_name,
                        'device_name': dev_name,
                        'event_point': str(payload.get('door_name') or payload.get('door_id') or ''),
                        'event_description': event_desc,
                        'card_number': str(payload.get('card_number') or ''),
                        'employee_pin': str(payload.get('employee_pin') or payload.get('employee_id') or ''),
                        'employee_name': str(payload.get('employee_name') or ''),
                        'department_name': str(payload.get('department_name') or ''),
                        'status_text': status_text,
                        'status_hint': str(ip_addr or '').strip(),
                        'verify_mode': _describe_verify(str(payload.get('verify_mode') or '')),
                        'operator': operator,
                        'action': str(getattr(a, 'action', '') or '').strip().lower(),
                        'remarks': '',
                    })

                # B) Hardware-derived rows (latest, bounded; enriched)
                hw_rows = []
                raw_field = 'raw_line'
                created_field = 'created_at'
                base_qs = None
                try:
                    if _EV.objects.exists():
                        base_qs = _EV.objects.all().order_by('-created_at')
                        raw_field = 'raw_line'
                    else:
                        base_qs = _RT.objects.all().order_by('-created_at')
                        raw_field = 'raw'
                except Exception:
                    base_qs = None

                if base_qs is not None:
                    hw_qs = base_qs

                    # Apply search/date filters (best-effort, same as UI)
                    if q:
                        hw_qs = hw_qs.filter(**{f"{raw_field}__icontains": q})

                    if date_from:
                        dt = parse_datetime(date_from)
                        if not dt:
                            d = parse_date(date_from)
                            if d:
                                from datetime import datetime, time
                                dt = timezone.make_aware(datetime.combine(d, time.min))
                        elif timezone.is_naive(dt):
                            dt = timezone.make_aware(dt)
                        if dt:
                            hw_qs = hw_qs.filter(**{f"{created_field}__gte": dt})
                    if date_to:
                        dt = parse_datetime(date_to)
                        if not dt:
                            d = parse_date(date_to)
                            if d:
                                from datetime import datetime, time
                                dt = timezone.make_aware(datetime.combine(d, time.max))
                        elif timezone.is_naive(dt):
                            dt = timezone.make_aware(dt)
                        if dt:
                            hw_qs = hw_qs.filter(**{f"{created_field}__lte": dt})

                    # Drop the noisy keepalive pattern
                    try:
                        if raw_field == 'raw':
                            hw_qs = hw_qs.exclude(raw__contains=',0,0,200,0,0')
                        else:
                            hw_qs = hw_qs.exclude(raw_line__contains=',0,0,200,0,0')
                    except Exception:
                        pass

                    rows = list(hw_qs[:400])
                    device_ids = sorted({getattr(r, 'device_id', None) for r in rows if getattr(r, 'device_id', None) is not None})
                    device_map = {d.id: d for d in _Device.objects.filter(id__in=device_ids)} if device_ids else {}

                    door_keys = set()
                    card_values = set()
                    pin_values = set()
                    parsed_lines = []
                    for r in rows:
                        raw_line = (getattr(r, raw_field, '') or '').strip()
                        parts = [p.strip() for p in raw_line.split(',')]
                        ts_str = parts[0] if len(parts) > 0 else ''
                        pin = parts[1] if len(parts) > 1 else ''
                        card = parts[2] if len(parts) > 2 else ''
                        door_no = parts[3] if len(parts) > 3 else ''
                        code = parts[4] if len(parts) > 4 else ''
                        verify_mode = parts[5] if len(parts) > 5 else ''
                        dev_id = getattr(r, 'device_id', None)

                        if str(code) == '200' and str(card).strip() in ('', '0', '000000', '00000000') and str(door_no).strip() in ('', '0'):
                            continue
                        if dev_id is not None and door_no:
                            door_keys.add((dev_id, door_no))
                        if card and card not in ('0', '000000', '00000000'):
                            card_values.add(card)
                        if pin and pin not in ('0',):
                            pin_values.add(pin)
                        parsed_lines.append((r, ts_str, pin, card, door_no, code, verify_mode))

                    door_map = {}
                    if door_keys:
                        dids = sorted({k[0] for k in door_keys})
                        names = sorted({k[1] for k in door_keys})
                        for d in _Door.objects.filter(device_id__in=dids, name__in=names).select_related('device'):
                            door_map[(d.device_id, str(getattr(d, 'name', '') or ''))] = d

                    emp_by_card = {}
                    emp_by_pin = {}
                    dept_by_emp_id = {}
                    emp_id_by_card = {}
                    emp_id_by_pin = {}
                    if card_values or pin_values:
                        q_emp = Q()
                        if card_values:
                            q_emp |= Q(card_number__in=card_values) | Q(secondary_card_number__in=card_values)
                        pin_ints = []
                        for p in pin_values:
                            try:
                                pin_ints.append(int(str(p)))
                            except Exception:
                                pass
                        if pin_ints:
                            q_emp |= Q(legacy_userid__in=pin_ints)
                        for e in _Employee.objects.filter(q_emp):
                            full = (f"{getattr(e,'first_name','') or ''} {getattr(e,'last_name','') or ''}").strip()
                            if getattr(e, 'card_number', None):
                                emp_by_card[str(e.card_number)] = full
                                emp_id_by_card[str(e.card_number)] = getattr(e, 'id', None)
                            if getattr(e, 'secondary_card_number', None):
                                emp_by_card[str(e.secondary_card_number)] = full
                                emp_id_by_card[str(e.secondary_card_number)] = getattr(e, 'id', None)
                            if getattr(e, 'legacy_userid', None) is not None:
                                emp_by_pin[str(getattr(e, 'legacy_userid'))] = full
                                emp_id_by_pin[str(getattr(e, 'legacy_userid'))] = getattr(e, 'id', None)
                            try:
                                dpt = getattr(e, 'dept', None)
                                dept_name = (getattr(dpt, 'DeptName', '') or getattr(dpt, 'deptname', '') or '') if dpt else ''
                            except Exception:
                                dept_name = ''
                            dept_by_emp_id[getattr(e, 'id', 0)] = dept_name

                    for (_r, ts_str, pin, card, door_no, code, verify_mode) in parsed_lines:
                        dev_id = getattr(_r, 'device_id', None)
                        dev_obj = device_map.get(dev_id)
                        dev_name = getattr(dev_obj, 'name', '') if dev_obj else ''
                        area_name = getattr(dev_obj, 'area_name', '') if dev_obj else ''
                        created_at = getattr(_r, created_field, None) or timezone.now()

                        door_obj = door_map.get((dev_id, str(door_no)))
                        door_name = getattr(door_obj, 'name', '') if door_obj else (door_no or '')

                        verify_label = _describe_verify(str(verify_mode))
                        base_desc = _describe_code(str(code)) or (f"Code {code}" if code else '')
                        desc = base_desc
                        if str(code) == '200':
                            desc = 'Normal Fingerprint Open' if verify_label == 'Only Fingerprint' else 'Normal Punch Open'
                        elif str(code) == '201':
                            desc = 'Access Denied' if (emp_by_card.get(str(card)) or emp_by_pin.get(str(pin))) else 'Unregistered Card'

                        employee_name = emp_by_card.get(str(card), '') or emp_by_pin.get(str(pin), '') or ''
                        dept_name = ''
                        try:
                            emp_id_val = None
                            if card:
                                emp_id_val = emp_id_by_card.get(str(card))
                            if emp_id_val is None and pin:
                                emp_id_val = emp_id_by_pin.get(str(pin))
                            if emp_id_val is not None:
                                dept_name = dept_by_emp_id.get(int(emp_id_val) or 0, '')
                        except Exception:
                            dept_name = ''

                        hw_rows.append({
                            '_ts': timezone.localtime(created_at),
                            'action_time': ts_str or timezone.localtime(created_at).strftime('%Y-%m-%d %H:%M:%S'),
                            'area_name': area_name,
                            'device_name': dev_name,
                            'event_point': door_name or '-',
                            'event_description': desc,
                            'card_number': card,
                            'employee_pin': pin,
                            'employee_name': employee_name,
                            'department_name': dept_name,
                            'status_text': 'ACCEPTAT' if str(code) == '200' else ('RESPINS' if str(code) == '201' else ''),
                            'status_hint': '',
                            'verify_mode': verify_label,
                            'operator': '',
                            'action': 'others',
                            'remarks': '',
                        })

                combined = []
                combined.extend(audit_rows)
                combined.extend(hw_rows)

                system_sort_map = {
                    'ts': '_ts',
                    'zone': 'area_name',
                    'device': 'device_name',
                    'point': 'event_point',
                    'event': 'event_description',
                    'card': 'card_number',
                    'pin': 'employee_pin',
                    'name': 'employee_name',
                    'dept': 'department_name',
                    'action': 'action',
                    'user': 'operator',
                    'status': 'status_text',
                    'method': 'verify_mode',
                }
                sort_field = system_sort_map.get(sort_key or 'ts', '_ts')
                reverse = (sort_dir != 'asc')
                if sort_field == '_ts':
                    combined.sort(key=lambda x: x.get('_ts') or timezone.localtime(timezone.now()), reverse=reverse)
                else:
                    combined.sort(key=lambda x: str(x.get(sort_field) or '').lower(), reverse=reverse)

                combined = _dedupe_remote_rows(combined, window_seconds=3)
                page = _paginate_list(combined, request, per_page=50)
                page_exists = True
                system_rows = list(getattr(page, 'object_list', []) or [])
            else:
                audit_sort_map = {
                    'ts': 'timestamp',
                    'module': 'module',
                    'object': 'entity_name',
                    'action': 'action',
                    'user': 'user',
                }
                order_field = audit_sort_map.get(sort_key or 'ts', 'timestamp')
                prefix = '' if sort_dir == 'asc' else '-'
                try:
                    qs = qs.order_by(prefix + order_field)
                except Exception:
                    pass
                page = _paginate(qs, request, per_page=50)
                page_exists = True

    embed_full = (request.GET.get('embed') == '1') and ((request.GET.get('mode') or '').strip().lower() == 'full')
    if embed_full:
        resp = render(request, 'agent/menu_reports_embed.html', {
            'tab': tab,
            'page': page,
            'page_exists': page_exists,
            'missing_accesslog': missing_accesslog,
            'access_rows': access_rows,
            'system_rows': system_rows,
            'access_filters': {
                'card': (request.GET.get('card') or '').strip(),
                'door': (request.GET.get('door') or '').strip(),
                'person': (request.GET.get('person') or '').strip(),
                'status': (request.GET.get('status') or '').strip().lower(),
                'verify': (request.GET.get('verify') or '').strip(),
            },
            'query_no_page': _qs_without_page(request),
            'sort': sort_key or 'ts',
            'dir': sort_dir,
            'sort_hrefs': {
                'ts': _sort_href('ts', default_dir='desc'),
                'zone': _sort_href('zone', default_dir='asc'),
                'device': _sort_href('device', default_dir='asc'),
                'point': _sort_href('point', default_dir='asc'),
                'event': _sort_href('event', default_dir='asc'),
                'card': _sort_href('card', default_dir='asc'),
                'pin': _sort_href('pin', default_dir='asc'),
                'name': _sort_href('name', default_dir='asc'),
                'dept': _sort_href('dept', default_dir='asc'),
                'action': _sort_href('action', default_dir='asc'),
                'user': _sort_href('user', default_dir='asc'),
                'status': _sort_href('status', default_dir='asc'),
                'method': _sort_href('method', default_dir='asc'),
                'module': _sort_href('module', default_dir='asc'),
                'object': _sort_href('object', default_dir='asc'),
            },
            'sort_ind': {
                'ts': _sort_indicator('ts'),
                'zone': _sort_indicator('zone'),
                'device': _sort_indicator('device'),
                'point': _sort_indicator('point'),
                'event': _sort_indicator('event'),
                'card': _sort_indicator('card'),
                'pin': _sort_indicator('pin'),
                'name': _sort_indicator('name'),
                'dept': _sort_indicator('dept'),
                'action': _sort_indicator('action'),
                'user': _sort_indicator('user'),
                'status': _sort_indicator('status'),
                'method': _sort_indicator('method'),
                'module': _sort_indicator('module'),
                'object': _sort_indicator('object'),
            },
            'current_username': (getattr(getattr(request, 'user', None), 'username', '') or ''),
            'filters': {
                'user': user_q,
                'action': action_q or 'all',
                'q': q,
                'from_val': date_from,
                'to_val': date_to,
            },
            'embed_full': True,
            'embed_suffix': '&embed=1&mode=full',
        })
        resp['X-Frame-Options'] = 'SAMEORIGIN'
        return resp

    if (request.GET.get('embed') == '1') and (tab == 'accesslog'):
        resp = render(request, 'agent/reports_accesslog_embed.html', {
            'tab': tab,
            'page': page,
            'page_exists': page_exists,
            'missing_accesslog': missing_accesslog,
            'access_rows': access_rows,
            'query_no_page': _qs_without_page(request),
        })
        resp['X-Frame-Options'] = 'SAMEORIGIN'
        return resp

    return render(request, 'agent/menu_reports.html', {
        'tab': tab,
        'page': page,
        'page_exists': page_exists,
        'missing_accesslog': missing_accesslog,
        'access_rows': access_rows,
        'system_rows': system_rows,
        'access_filters': {
            'card': (request.GET.get('card') or '').strip(),
            'door': (request.GET.get('door') or '').strip(),
            'person': (request.GET.get('person') or '').strip(),
            'status': (request.GET.get('status') or '').strip().lower(),
            'verify': (request.GET.get('verify') or '').strip(),
        },
        'query_no_page': _qs_without_page(request),
        'sort': sort_key or 'ts',
        'dir': sort_dir,
        'sort_hrefs': {
            'ts': _sort_href('ts', default_dir='desc'),
            'zone': _sort_href('zone', default_dir='asc'),
            'device': _sort_href('device', default_dir='asc'),
            'point': _sort_href('point', default_dir='asc'),
            'event': _sort_href('event', default_dir='asc'),
            'card': _sort_href('card', default_dir='asc'),
            'pin': _sort_href('pin', default_dir='asc'),
            'name': _sort_href('name', default_dir='asc'),
            'dept': _sort_href('dept', default_dir='asc'),
            'action': _sort_href('action', default_dir='asc'),
            'user': _sort_href('user', default_dir='asc'),
            'status': _sort_href('status', default_dir='asc'),
            'method': _sort_href('method', default_dir='asc'),
            'module': _sort_href('module', default_dir='asc'),
            'object': _sort_href('object', default_dir='asc'),
        },
        'sort_ind': {
            'ts': _sort_indicator('ts'),
            'zone': _sort_indicator('zone'),
            'device': _sort_indicator('device'),
            'point': _sort_indicator('point'),
            'event': _sort_indicator('event'),
            'card': _sort_indicator('card'),
            'pin': _sort_indicator('pin'),
            'name': _sort_indicator('name'),
            'dept': _sort_indicator('dept'),
            'action': _sort_indicator('action'),
            'user': _sort_indicator('user'),
            'status': _sort_indicator('status'),
            'method': _sort_indicator('method'),
            'module': _sort_indicator('module'),
            'object': _sort_indicator('object'),
        },
        'current_username': (getattr(getattr(request, 'user', None), 'username', '') or ''),
        'filters': {
            'user': user_q,
            'action': action_q or 'all',
            'q': q,
            'from_val': date_from,
            'to_val': date_to,
        },
        'embed_full': False,
        'embed_suffix': '',
    })

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
    is_embed = (request.GET.get('embed') == '1')
    if not is_embed:
        from django.shortcuts import redirect
        return redirect('/agent/menu/access/?tab=doors')
    qs = Door.objects.order_by('name')
    page = _paginate(qs, request)
    return render(request, 'agent/access_doors_embed.html', {'page': page, 'can_edit': bool(getattr(request.user, 'is_staff', False))})

def door_create(request: HttpRequest):
    if not request.user.is_authenticated or not request.user.is_staff:
        from django.contrib.auth.views import redirect_to_login
        return redirect_to_login(request.get_full_path())
    is_modal = (request.GET.get('modal') == '1') or (request.headers.get('x-requested-with') == 'XMLHttpRequest')
    if request.method == 'POST':
        form = DoorForm(request.POST)
        if form.is_valid():
            form.save()
            _audit_log(
                request,
                module='door',
                action='create',
                entity_id=form.instance.id,
                entity_name=getattr(form.instance, 'name', '') or '',
            )
            tpl = 'agent/door_saved_inner.html' if is_modal else 'agent/door_saved.html'
            return render(request, tpl, {'obj': form.instance, 'created': True})
    else:
        form = DoorForm()
    tpl = 'agent/door_form_inner.html' if is_modal else 'agent/door_form.html'
    return render(request, tpl, {'form': form})

def door_edit(request: HttpRequest, pk: int):
    if not request.user.is_authenticated or not request.user.is_staff:
        from django.contrib.auth.views import redirect_to_login
        return redirect_to_login(request.get_full_path())
    is_modal = (request.GET.get('modal') == '1') or (request.headers.get('x-requested-with') == 'XMLHttpRequest')
    door = Door.objects.get(pk=pk)
    if request.method == 'POST':
        form = DoorForm(request.POST, instance=door)
        if form.is_valid():
            form.save()
            _audit_log(
                request,
                module='door',
                action='update',
                entity_id=form.instance.id,
                entity_name=getattr(form.instance, 'name', '') or '',
            )
            tpl = 'agent/door_saved_inner.html' if is_modal else 'agent/door_saved.html'
            return render(request, tpl, {'obj': form.instance, 'created': False})
    else:
        form = DoorForm(instance=door)
    tpl = 'agent/door_form_inner.html' if is_modal else 'agent/door_form.html'
    return render(request, tpl, {'form': form, 'obj': door})

def door_delete(request: HttpRequest, pk: int):
    if not request.user.is_authenticated or not request.user.is_staff or request.method != 'POST':
        return JsonResponse({'ok': False, 'error': 'unauthorized'}, status=403)
    try:
        obj = Door.objects.filter(pk=pk).first()
        Door.objects.filter(pk=pk).delete()
        if obj is not None:
            _audit_log(
                request,
                module='door',
                action='delete',
                entity_id=int(pk),
                entity_name=getattr(obj, 'name', '') or '',
            )
        return JsonResponse({'ok': True})
    except Exception as e:
        return JsonResponse({'ok': False, 'error': str(e)}, status=400)

def segments_list(request: HttpRequest):
    if not request.user.is_authenticated:
        from django.contrib.auth.views import redirect_to_login
        return redirect_to_login(request.get_full_path())
    is_embed = (request.GET.get('embed') == '1')
    if not is_embed:
        from django.shortcuts import redirect
        return redirect('/agent/menu/access/?tab=segments')
    qs = TimeSegment.objects.order_by('name')
    page = _paginate(qs, request)
    return render(request, 'agent/access_segments_embed.html', {'page': page, 'can_edit': bool(getattr(request.user, 'is_staff', False))})

def segment_create(request: HttpRequest):
    if not request.user.is_authenticated or not request.user.is_staff:
        from django.contrib.auth.views import redirect_to_login
        return redirect_to_login(request.get_full_path())
    is_modal = (request.GET.get('modal') == '1') or (request.headers.get('x-requested-with') == 'XMLHttpRequest')
    if request.method == 'POST':
        form = TimeSegmentFormWithDays(request.POST)
        if form.is_valid():
            form.save()
            _audit_log(
                request,
                module='time-segment',
                action='create',
                entity_id=form.instance.id,
                entity_name=getattr(form.instance, 'name', '') or '',
            )
            tpl = 'agent/segment_saved_inner.html' if is_modal else 'agent/segment_saved.html'
            return render(request, tpl, {'obj': form.instance, 'created': True})
    else:
        form = TimeSegmentFormWithDays()
    tpl = 'agent/segment_form_inner.html' if is_modal else 'agent/segment_form.html'
    return render(request, tpl, {'form': form})

def segment_edit(request: HttpRequest, pk: int):
    if not request.user.is_authenticated or not request.user.is_staff:
        from django.contrib.auth.views import redirect_to_login
        return redirect_to_login(request.get_full_path())
    is_modal = (request.GET.get('modal') == '1') or (request.headers.get('x-requested-with') == 'XMLHttpRequest')
    seg = TimeSegment.objects.get(pk=pk)
    if request.method == 'POST':
        form = TimeSegmentFormWithDays(request.POST, instance=seg)
        if form.is_valid():
            form.save()
            _audit_log(
                request,
                module='time-segment',
                action='update',
                entity_id=form.instance.id,
                entity_name=getattr(form.instance, 'name', '') or '',
            )
            tpl = 'agent/segment_saved_inner.html' if is_modal else 'agent/segment_saved.html'
            return render(request, tpl, {'obj': form.instance, 'created': False})
    else:
        form = TimeSegmentFormWithDays(instance=seg)
    tpl = 'agent/segment_form_inner.html' if is_modal else 'agent/segment_form.html'
    return render(request, tpl, {'form': form, 'obj': seg})

def segment_delete(request: HttpRequest, pk: int):
    if not request.user.is_authenticated or not request.user.is_staff or request.method != 'POST':
        return JsonResponse({'ok': False, 'error': 'unauthorized'}, status=403)
    try:
        obj = TimeSegment.objects.filter(pk=pk).first()
        TimeSegment.objects.filter(pk=pk).delete()
        if obj is not None:
            _audit_log(
                request,
                module='time-segment',
                action='delete',
                entity_id=int(pk),
                entity_name=getattr(obj, 'name', '') or '',
            )
        return JsonResponse({'ok': True})
    except Exception as e: return JsonResponse({'ok': False,'error': str(e)}, status=400)

def holidays_list(request: HttpRequest):
    if not request.user.is_authenticated:
        from django.contrib.auth.views import redirect_to_login
        return redirect_to_login(request.get_full_path())
    is_embed = (request.GET.get('embed') == '1')
    if not is_embed:
        from django.shortcuts import redirect
        return redirect('/agent/menu/access/?tab=holidays')
    qs = Holiday.objects.order_by('date')
    page = _paginate(qs, request)
    return render(request, 'agent/access_holidays_embed.html', {'page': page, 'can_edit': bool(getattr(request.user, 'is_staff', False))})

def holiday_create(request: HttpRequest):
    if not request.user.is_authenticated or not request.user.is_staff:
        from django.contrib.auth.views import redirect_to_login
        return redirect_to_login(request.get_full_path())
    is_modal = (request.GET.get('modal') == '1') or (request.headers.get('x-requested-with') == 'XMLHttpRequest')
    if request.method == 'POST':
        form = HolidayForm(request.POST)
        if form.is_valid():
            form.save()
            _audit_log(
                request,
                module='holiday',
                action='create',
                entity_id=form.instance.id,
                entity_name=getattr(form.instance, 'name', '') or '',
                details=f"date={getattr(form.instance, 'date', None)}",
            )
            tpl = 'agent/holiday_saved_inner.html' if is_modal else 'agent/holiday_saved.html'
            return render(request, tpl, {'obj': form.instance, 'created': True})
    else: form = HolidayForm()
    tpl = 'agent/holiday_form_inner.html' if is_modal else 'agent/holiday_form.html'
    return render(request, tpl, {'form': form})

def holiday_edit(request: HttpRequest, pk: int):
    if not request.user.is_authenticated or not request.user.is_staff:
        from django.contrib.auth.views import redirect_to_login
        return redirect_to_login(request.get_full_path())
    is_modal = (request.GET.get('modal') == '1') or (request.headers.get('x-requested-with') == 'XMLHttpRequest')
    hol = Holiday.objects.get(pk=pk)
    if request.method == 'POST':
        form = HolidayForm(request.POST, instance=hol)
        if form.is_valid():
            form.save()
            _audit_log(
                request,
                module='holiday',
                action='update',
                entity_id=form.instance.id,
                entity_name=getattr(form.instance, 'name', '') or '',
                details=f"date={getattr(form.instance, 'date', None)}",
            )
            tpl = 'agent/holiday_saved_inner.html' if is_modal else 'agent/holiday_saved.html'
            return render(request, tpl, {'obj': form.instance, 'created': False})
    else: form = HolidayForm(instance=hol)
    tpl = 'agent/holiday_form_inner.html' if is_modal else 'agent/holiday_form.html'
    return render(request, tpl, {'form': form, 'obj': hol})

def holiday_delete(request: HttpRequest, pk: int):
    if not request.user.is_authenticated or not request.user.is_staff or request.method != 'POST': return JsonResponse({'ok': False,'error':'unauthorized'}, status=403)
    try:
        obj = Holiday.objects.filter(pk=pk).first()
        Holiday.objects.filter(pk=pk).delete()
        if obj is not None:
            _audit_log(
                request,
                module='holiday',
                action='delete',
                entity_id=int(pk),
                entity_name=getattr(obj, 'name', '') or '',
                details=f"date={getattr(obj, 'date', None)}",
            )
        return JsonResponse({'ok': True})
    except Exception as e: return JsonResponse({'ok': False,'error':str(e)}, status=400)

def access_levels_list(request: HttpRequest):
    if not request.user.is_authenticated:
        from django.contrib.auth.views import redirect_to_login
        return redirect_to_login(request.get_full_path())
    is_embed = (request.GET.get('embed') == '1')
    if not is_embed:
        from django.shortcuts import redirect
        return redirect('/agent/menu/access/?tab=levels')
    qs = AccessLevel.objects.order_by('name')
    page = _paginate(qs, request)
    return render(request, 'agent/access_levels_embed.html', {'page': page, 'can_edit': bool(getattr(request.user, 'is_staff', False))})

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
    try:
        try:
            from .models import LegacyAreaMeta
            LegacyAreaMeta.objects.filter(area_id=pk).delete()
        except Exception:
            pass
        LegacyArea.objects.filter(pk=pk).delete()
        return JsonResponse({'ok': True})
    except Exception as e: return JsonResponse({'ok': False,'error': str(e)}, status=400)


def areas_json(request: HttpRequest):
    if not request.user.is_authenticated:
        return JsonResponse({'ok': False, 'error': 'unauthorized'}, status=403)
    if not LegacyArea:
        return JsonResponse({'ok': False, 'error': 'missing-model'}, status=400)
    try:
        from .models import LegacyAreaMeta
    except Exception:
        LegacyAreaMeta = None  # type: ignore

    areas = list(LegacyArea.objects.order_by('areaname'))
    name_by_id = {int(a.id): (a.areaname or '') for a in areas}

    meta_by_id = {}
    if LegacyAreaMeta is not None:
        try:
            meta_rows = LegacyAreaMeta.objects.filter(legacy_area_id__in=list(name_by_id.keys()))
            meta_by_id = {int(m.legacy_area_id): m for m in meta_rows}
        except Exception:
            meta_by_id = {}

    items = []
    for a in areas:
        mid = int(a.id)
        m = meta_by_id.get(mid)
        parent_id = None
        try:
            parent_id = int(getattr(m, 'parent_legacy_area_id', None)) if m and getattr(m, 'parent_legacy_area_id', None) else None
        except Exception:
            parent_id = None
        items.append({
            'id': mid,
            'name': a.areaname or '',
            'code': (getattr(m, 'code', None) if m else None) or '',
            'remarks': (getattr(m, 'remarks', None) if m else None) or '',
            'parent_id': parent_id or '',
            'parent_name': (name_by_id.get(parent_id) if parent_id else '') or '',
        })

    return JsonResponse({'ok': True, 'items': items})


def area_save_json(request: HttpRequest):
    if not request.user.is_authenticated or not request.user.is_staff or request.method != 'POST':
        return JsonResponse({'ok': False, 'error': 'unauthorized'}, status=403)
    if not LegacyArea:
        return JsonResponse({'ok': False, 'error': 'missing-model'}, status=400)
    import json
    try:
        payload = json.loads(request.body.decode('utf-8'))
    except Exception:
        payload = request.POST.dict()
    name = (payload.get('name') or '').strip()
    code = (payload.get('code') or '').strip()
    remarks = (payload.get('notes') or payload.get('remarks') or '').strip()
    parent_id_raw = (payload.get('parent_id') or payload.get('parent') or '').strip()
    parent_id = None
    if parent_id_raw:
        try:
            parent_id = int(parent_id_raw)
        except Exception:
            parent_id = None
    pk = payload.get('id')
    if not name:
        return JsonResponse({'ok': False, 'error': 'empty-name'}, status=400)
    if not code:
        return JsonResponse({'ok': False, 'error': 'empty-code'}, status=400)

    try:
        from .models import LegacyAreaMeta
    except Exception:
        LegacyAreaMeta = None  # type: ignore

    try:
        if pk:
            obj = LegacyArea.objects.get(pk=int(pk))
            obj.areaname = name
            obj.save(update_fields=['areaname'])
            created = False
        else:
            obj, created = LegacyArea.objects.get_or_create(areaname=name)

        # Persist metadata (code/parent/remarks) in agent.LegacyAreaMeta
        if LegacyAreaMeta is not None:
            # prevent duplicate codes across different areas
            try:
                dup = LegacyAreaMeta.objects.filter(code=code).exclude(legacy_area_id=int(obj.id)).first()
            except Exception:
                dup = None
            if dup is not None:
                return JsonResponse({'ok': False, 'error': 'duplicate-code'}, status=409)
            try:
                LegacyAreaMeta.objects.update_or_create(
                    legacy_area_id=int(obj.id),
                    defaults={
                        'code': code,
                        'parent_legacy_area_id': parent_id,
                        'remarks': remarks,
                    },
                )
            except Exception:
                # Best-effort: don't block saving the legacy area name
                pass

        try:
            _audit_log(
                request,
                module='area',
                action='create' if created else 'update',
                entity_id=int(getattr(obj, 'id', 0) or 0),
                entity_name=name,
                details=f"code={code} parent_id={parent_id or ''}",
            )
        except Exception:
            pass

        return JsonResponse({'ok': True, 'id': obj.id, 'name': obj.areaname, 'code': code, 'created': created})
    except Exception as e:
        return JsonResponse({'ok': False, 'error': str(e)}, status=400)

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
    if not IssueCardForm:
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
    if not IssueCardForm:
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
    if not IssueCardForm:
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


def dst_list_json(request: HttpRequest):
    if not request.user.is_authenticated:
        return JsonResponse({'ok': False, 'error': 'unauthorized'}, status=403)
    items = []
    for d in DSTime.objects.order_by('name'):
        items.append({
            'id': d.id,
            'name': d.name,
            'start': {
                'month': d.start_month,
                'week': d.start_week,
                'weekday': d.start_weekday,
                'hour': d.start_hour,
                'minute': d.start_minute,
            },
            'end': {
                'month': d.end_month,
                'week': d.end_week,
                'weekday': d.end_weekday,
                'hour': d.end_hour,
                'minute': d.end_minute,
            },
            'offset_minutes': d.offset_minutes,
        })
    return JsonResponse({'ok': True, 'items': items})


def dst_save_json(request: HttpRequest):
    if not request.user.is_authenticated or not request.user.is_staff or request.method != 'POST':
        return JsonResponse({'ok': False, 'error': 'unauthorized'}, status=403)
    import json
    try:
        payload = json.loads(request.body.decode('utf-8'))
    except Exception:
        payload = request.POST.dict()
    name = (payload.get('name') or '').strip()
    if not name:
        return JsonResponse({'ok': False, 'error': 'missing-name'}, status=400)
    try:
        pk = payload.get('id')
        is_update = bool(pk)
        obj = DSTime.objects.get(pk=int(pk)) if pk else DSTime()
        obj.name = name
        obj.start_month = int(payload.get('start_month', 1))
        obj.start_week = payload.get('start_week') or 'last'
        obj.start_weekday = int(payload.get('start_weekday', 0))
        obj.start_hour = int(payload.get('start_hour', 3))
        obj.start_minute = int(payload.get('start_minute', 0))
        obj.end_month = int(payload.get('end_month', 10))
        obj.end_week = payload.get('end_week') or 'last'
        obj.end_weekday = int(payload.get('end_weekday', 0))
        obj.end_hour = int(payload.get('end_hour', 3))
        obj.end_minute = int(payload.get('end_minute', 0))
        obj.offset_minutes = int(payload.get('offset_minutes', 60))
        obj.save()
        try:
            _audit_log(
                request,
                module='dst',
                action='update' if is_update else 'create',
                entity_id=int(obj.id),
                entity_name=obj.name or '',
                details=f"offset_minutes={getattr(obj, 'offset_minutes', '')}",
            )
        except Exception:
            pass
        return JsonResponse({'ok': True, 'id': obj.id, 'name': obj.name})
    except Exception as e:
        return JsonResponse({'ok': False, 'error': str(e)}, status=400)


def dst_delete_json(request: HttpRequest, pk: int):
    if not request.user.is_authenticated or not request.user.is_staff or request.method != 'POST':
        return JsonResponse({'ok': False, 'error': 'unauthorized'}, status=403)
    try:
        obj = DSTime.objects.filter(pk=pk).first()
        DSTime.objects.filter(pk=pk).delete()
        if obj is not None:
            try:
                _audit_log(
                    request,
                    module='dst',
                    action='delete',
                    entity_id=int(pk),
                    entity_name=getattr(obj, 'name', '') or '',
                )
            except Exception:
                pass
        return JsonResponse({'ok': True})
    except Exception as e:
        return JsonResponse({'ok': False, 'error': str(e)}, status=400)

# --- Modern JSON endpoints for IssueCards used by Personnel UI ---
def issuecards_json_list(request: HttpRequest):
    if not request.user.is_authenticated:
        return JsonResponse({'items': []})
    # Always return real EmployeeCard rows (numeric IDs) so UI never shows synthetic emp:* identifiers.
    items = []
    qs = EmployeeCard.objects.select_related('employee').order_by('-created_at')
    for x in qs[:5000]:
        name = f"{getattr(x.employee,'last_name','')} {getattr(x.employee,'first_name','')}".strip() if getattr(x,'employee',None) else ''
        issue_date = None
        try:
            issue_date = x.created_at.date().isoformat() if getattr(x, 'created_at', None) else None
        except Exception:
            issue_date = None
        valid_until = getattr(x, 'valid_until', None)
        if hasattr(valid_until, 'isoformat'):
            valid_until = valid_until.isoformat()
        items.append({
            'id': x.id,
            'card_number': x.card_number,
            'employee_name': name,
            'userid': getattr(x.employee,'legacy_userid', None) if getattr(x,'employee',None) else None,
            'slot': getattr(x, 'slot', 'additional') or 'additional',
            'status': getattr(x, 'status', 'Active') or 'Active',
            'issue_date': issue_date,
            'valid_until': valid_until,
        })
    return JsonResponse({'items': items})

def issuecards_json_search(request: HttpRequest):
    q = request.GET.get('q','').strip()
    if not q:
        return JsonResponse([], safe=False)
    qs = EmployeeCard.objects.filter(card_number__icontains=q).order_by('id')[:50]
    return JsonResponse([{'id':c.id,'card_number':c.card_number,'slot': getattr(c,'slot','additional')} for c in qs], safe=False)


def _parse_date_yyyy_mm_dd(value: str):
    if not value:
        return None
    try:
        from datetime import date
        return date.fromisoformat(str(value).strip())
    except Exception:
        return None

def issuecard_json_detail(request: HttpRequest, pk: str):
    try:
        c = EmployeeCard.objects.select_related('employee').get(pk=int(pk))
        name = f"{getattr(c.employee,'last_name','')} {getattr(c.employee,'first_name','')}".strip() if getattr(c,'employee',None) else ''
        valid_until = getattr(c, 'valid_until', None)
        if hasattr(valid_until, 'isoformat'):
            valid_until = valid_until.isoformat()
        return JsonResponse({
            'id': c.id,
            'card_number': c.card_number,
            'site_code': getattr(c,'site_code',''),
            'employee': getattr(c.employee,'id', None) if getattr(c,'employee',None) else None,
            'employee_name': name,
            'valid_until': valid_until,
            'slot': getattr(c, 'slot', 'additional') or 'additional',
            'status': getattr(c, 'status', 'Active') or 'Active',
        })
    except Exception:
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
        slot = (payload.get('slot') or 'additional').lower().strip()
        if slot not in ('primary', 'secondary', 'additional'):
            slot = 'additional'

        # Duplicate check across all cards (except the one we might overwrite for primary/secondary)
        existing_slot_card = None
        if slot in ('primary', 'secondary'):
            try:
                existing_slot_card = EmployeeCard.objects.filter(employee=emp, slot=slot).order_by('-created_at').first()
            except Exception:
                existing_slot_card = None

        dup_qs = EmployeeCard.objects.filter(card_number__iexact=num)
        if existing_slot_card is not None:
            dup_qs = dup_qs.exclude(pk=existing_slot_card.pk)
        if dup_qs.exists():
            return JsonResponse({'ok': False,'error':'duplicate card_number'}, status=400)

        valid_until = _parse_date_yyyy_mm_dd(payload.get('valid_until') or '')
        status = (payload.get('status') or 'Active').strip() or 'Active'
        site_code = (payload.get('site_code') or '').strip()

        if existing_slot_card is not None:
            # Overwrite primary/secondary card row instead of creating duplicates
            existing_slot_card.card_number = num
            existing_slot_card.site_code = site_code
            existing_slot_card.status = status
            existing_slot_card.valid_until = valid_until
            existing_slot_card.save()
            c = existing_slot_card
            created_flag = False
        else:
            c = EmployeeCard.objects.create(
                employee=emp,
                card_number=num,
                slot=slot,
                status=status,
                site_code=site_code,
                valid_until=valid_until,
            )
            created_flag = True
        entity_id = c.id

        # Keep Employee primary/secondary fields in sync for backwards compatibility
        try:
            if slot == 'primary':
                emp.card_number = num
                emp.save(update_fields=['card_number'])
            elif slot == 'secondary':
                emp.secondary_card_number = num
                emp.save(update_fields=['secondary_card_number'])
        except Exception:
            pass
        try:
            AuditLog.objects.create(
                module='issuecard',
                action='create' if created_flag else 'update',
                entity_id=entity_id,
                entity_name=num,
                user=getattr(request.user,'username',None),
                details=f"slot={slot}; valid_until={valid_until.isoformat() if valid_until else '-'}",
            )
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
        c = EmployeeCard.objects.select_related('employee').get(pk=int(pk))
        if EmployeeCard.objects.filter(card_number__iexact=num).exclude(pk=c.pk).exists():
            return JsonResponse({'ok': False,'error':'duplicate card_number'}, status=400)

        old_employee = getattr(c, 'employee', None)
        old_number = getattr(c, 'card_number', '')
        old_site_code = getattr(c, 'site_code', '')
        old_valid_until = getattr(c, 'valid_until', None)
        old_status = getattr(c, 'status', 'Active')
        slot = (getattr(c, 'slot', 'additional') or 'additional')

        emp_id = payload.get('employee_id')
        if emp_id:
            try:
                from .models import Employee as AgentEmployee
                new_emp = AgentEmployee.objects.get(pk=int(emp_id))
                c.employee = new_emp
            except Exception:
                return JsonResponse({'ok': False,'error':'employee not found'}, status=400)

        c.card_number = num
        c.site_code = (payload.get('site_code') or '').strip()
        c.valid_until = _parse_date_yyyy_mm_dd(payload.get('valid_until') or '')
        if 'status' in payload:
            c.status = (payload.get('status') or 'Active').strip() or 'Active'
        c.save()
        entity_id = c.id

        # Keep Employee primary/secondary fields in sync
        try:
            from .models import Employee as AgentEmployee
            new_employee = getattr(c, 'employee', None)
            if slot == 'primary':
                if old_employee and getattr(old_employee, 'card_number', None) == old_number:
                    AgentEmployee.objects.filter(pk=old_employee.pk).update(card_number='')
                if new_employee:
                    AgentEmployee.objects.filter(pk=new_employee.pk).update(card_number=num)
            elif slot == 'secondary':
                if old_employee and getattr(old_employee, 'secondary_card_number', None) == old_number:
                    AgentEmployee.objects.filter(pk=old_employee.pk).update(secondary_card_number=None)
                if new_employee:
                    AgentEmployee.objects.filter(pk=new_employee.pk).update(secondary_card_number=num)
        except Exception:
            pass
        try:
            def _fmt(v):
                if not v:
                    return '-'
                if hasattr(v, 'isoformat'):
                    return v.isoformat()
                return str(v)
            details = []
            if old_number != num:
                details.append(f"card_number: {_fmt(old_number)} → {_fmt(num)}")
            if old_site_code != getattr(c, 'site_code', ''):
                details.append(f"site_code: {_fmt(old_site_code)} → {_fmt(getattr(c, 'site_code', ''))}")
            if _fmt(old_valid_until) != _fmt(getattr(c, 'valid_until', None)):
                details.append(f"valid_until: {_fmt(old_valid_until)} → {_fmt(getattr(c, 'valid_until', None))}")
            if old_status != getattr(c, 'status', 'Active'):
                details.append(f"status: {_fmt(old_status)} → {_fmt(getattr(c, 'status', 'Active'))}")
            AuditLog.objects.create(
                module='issuecard',
                action='update',
                entity_id=entity_id,
                entity_name=num,
                user=getattr(request.user,'username',None),
                details='; '.join(details) if details else '',
            )
        except Exception:
            pass
        return JsonResponse({'ok': True})
    except EmployeeCard.DoesNotExist:
        return JsonResponse({'ok': False,'error':'not-found'}, status=404)
    except Exception as e:
        return JsonResponse({'ok': False,'error': str(e)}, status=400)


def issuecard_json_delete(request: HttpRequest, pk: str):
    if request.method != 'POST' or not request.user.is_authenticated or not request.user.is_staff:
        return JsonResponse({'ok': False, 'error': 'unauth'}, status=403)
    try:
        c = EmployeeCard.objects.select_related('employee').get(pk=int(pk))
        num = getattr(c, 'card_number', '')
        slot = (getattr(c, 'slot', 'additional') or 'additional')
        emp = getattr(c, 'employee', None)
        entity_id = c.pk
        c.delete()
        # Keep Employee primary/secondary in sync
        try:
            from .models import Employee as AgentEmployee
            if emp and slot == 'primary' and getattr(emp, 'card_number', None) == num:
                AgentEmployee.objects.filter(pk=emp.pk).update(card_number='')
            if emp and slot == 'secondary' and getattr(emp, 'secondary_card_number', None) == num:
                AgentEmployee.objects.filter(pk=emp.pk).update(secondary_card_number=None)
        except Exception:
            pass
        try:
            AuditLog.objects.create(
                module='issuecard',
                action='delete',
                entity_id=entity_id,
                entity_name=num,
                user=getattr(request.user,'username',None),
                details=f"slot={slot}",
            )
        except Exception:
            pass
        return JsonResponse({'ok': True})
    except EmployeeCard.DoesNotExist:
        return JsonResponse({'ok': False, 'error': 'not-found'}, status=404)
    except Exception as e:
        return JsonResponse({'ok': False, 'error': str(e)}, status=400)

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
        # IMPORTANT: Remote open must be explicit to avoid generating misleading "Remote Opening" events
        # when the controller itself already opened the door after a physical scan.
        remote_open = bool(
            payload.get('remote_open')
            or payload.get('force_remote_open')
            or str(request.GET.get('remote_open') or '').lower() in ('1', 'true', 'yes')
        )
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
        # Attempt door open ONLY when explicitly requested (e.g. Test button), and never return early.
        door_open_ok = None
        src_l = (source or '').strip().lower()
        should_remote_open = (remote_open or src_l == 'test')
        if allowed and should_remote_open and not open_all:
            try:
                # Prevent door command AuditLog spam for evaluate-driven opens.
                setattr(request, '_agent_suppress_door_audit', True)
                if door_pk:
                    resp = door_pk_open(request, int(door_pk))
                elif device_id and door_id:
                    resp = door_open(request, int(device_id), str(door_id))
                else:
                    resp = None
                door_open_ok = bool(resp is None or getattr(resp, 'status_code', 200) < 400)
            except Exception:
                door_open_ok = False
                reasons.append('door_open_failed')
            finally:
                try:
                    delattr(request, '_agent_suppress_door_audit')
                except Exception:
                    pass
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

        # Write a durable access event so Reports -> AccessLog can show real data
        try:
            import json as _json
            from .event_codes import describe_verify_mode as _describe_verify_mode
            door_name = ''
            device_name = ''
            door_id_val = getattr(door, 'id', None)
            try:
                if door:
                    door_name = getattr(door, 'name', '') or ''
                    dev = getattr(door, 'device', None)
                    if dev is not None:
                        device_name = getattr(dev, 'name', None) or getattr(dev, 'device_name', None) or getattr(dev, 'alias', None) or ''
            except Exception:
                pass

            # Derive legacy-like Event Description + Verify Mode
            src_l = (source or '').strip().lower()
            verify_mode_label = 'Only Card'
            if any(k in src_l for k in ('finger', 'ampr', 'fp')):
                verify_mode_label = 'Only Fingerprint'
            elif any(k in src_l for k in ('pin', 'userid', 'id')):
                verify_mode_label = 'Only Pin'
            elif any(k in src_l for k in ('pass', 'parol', 'pwd')):
                verify_mode_label = 'Only Password'
            verify_mode_label = _describe_verify_mode(verify_mode_label)

            legacy_desc = 'Access Granted' if allowed else 'Access Denied'
            if allowed:
                if any(k in src_l for k in ('finger', 'ampr', 'fp')):
                    legacy_desc = 'Normal Fingerprint Open'
                elif any(k in src_l for k in ('exit', 'button')):
                    legacy_desc = 'Exit Button Open'
                else:
                    legacy_desc = 'Normal Punch Open'
            else:
                # Map common denial reasons into legacy strings
                if reasons and reasons[0] == 'no_employee_for_card':
                    legacy_desc = 'Unregistered Card'
                elif reasons and reasons[0] in ('outside_employee_validity', 'employee_inactive'):
                    legacy_desc = 'Card Expired'
                elif reasons and reasons[0] == 'outside_time_segments':
                    legacy_desc = 'Door Inactive Time Zone(Punch Card)'
                elif reasons and reasons[0] in ('holiday_block', 'door_not_in_access_levels', 'no_access_levels'):
                    legacy_desc = 'Access Denied'
                elif reasons and reasons[0] in ('door_not_resolved', 'door_open_failed'):
                    legacy_desc = 'Data Exception'

            # Employee fields expected by legacy report
            employee_pin = None
            department_name = ''
            try:
                if emp is not None:
                    employee_pin = getattr(emp, 'legacy_userid', None)
                    d = getattr(emp, 'dept', None)
                    if d:
                        department_name = getattr(d, 'DeptName', '') or getattr(d, 'deptname', '') or ''
            except Exception:
                employee_pin = employee_pin
                department_name = department_name

            verify_mode_raw = (source or 'unknown').strip()
            details = _json.dumps({
                'card_number': matched_card,
                'employee_id': getattr(emp, 'id', None),
                'employee_pin': employee_pin,
                'employee_name': employee_name,
                'department_name': department_name,
                'door_id': door_id_val,
                'door_name': door_name,
                'device_id': getattr(getattr(door, 'device', None), 'id', None) if door else None,
                'device_name': device_name,
                'allowed': bool(allowed),
                'status_text': status_text,
                'verify_mode': verify_mode_label,
                'verify_mode_raw': verify_mode_raw,
                'event_description': legacy_desc,
                'source': source,
                'open_all': bool(open_all),
                'remote_open': bool(should_remote_open),
                'remote_open_ok': door_open_ok,
                'reasons': reasons,
            }, ensure_ascii=False)
            _audit_log(
                request,
                module='accesslog',
                action=('granted' if allowed else 'denied'),
                entity_id=(getattr(emp, 'id', None) or 0),
                entity_name=(employee_name or matched_card or ''),
                details=details,
            )
        except Exception:
            pass
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
        # Preload DeviceStatus for all devices referenced to minimize queries
        device_ids = [getattr(d.device, 'id', None) for d in qs if getattr(d.device, 'id', None) is not None]
        status_map = {}
        if device_ids:
            for ds in DeviceStatus.objects.filter(device_id__in=device_ids):
                status_map[ds.device_id] = ds
        for d in qs:
            # Map is_open boolean to state string for UI
            state = _door_state_from_cache_or_model(d)
            dev = getattr(d, 'device', None)
            dev_id = getattr(dev, 'id', None) if dev else None
            ds = status_map.get(dev_id)
            items.append({
                'id': d.id,
                'name': d.name or f"Door {d.id}",
                'device_id': dev_id,
                'device_name': getattr(dev, 'name', None) if dev else None,
                'state': state,
                'enabled': bool(d.enabled),
                'device_enabled': bool(getattr(dev, 'enabled', False)) if dev else False,
                'device_online': bool(ds.online) if ds is not None else False,
            })
        return JsonResponse({'items': items})
    except Exception as ex:
        return JsonResponse({'items': [], 'error': str(ex)}, status=500)

def access_logs_list(request: HttpRequest):
    if not request.user.is_authenticated:
        from django.contrib.auth.views import redirect_to_login
        return redirect_to_login(request.get_full_path())
    form = AccessLogFilterForm(request.GET or None)
    qs = None
    using_legacy = bool(LegacyAccessLog)

    if using_legacy:
        qs = LegacyAccessLog.objects.order_by('-timestamp')
        qs = form.filter_queryset(qs)
    else:
        # Fallback: render recent local logs from agent tables so the ACCES->Loguri tab
        # still shows data even when legacy_models isn't available.
        try:
            ev = list(DeviceEventLog.objects.order_by('-created_at')[:400])
        except Exception:
            ev = []
        try:
            rt = list(DeviceRealtimeLog.objects.order_by('-created_at')[:400])
        except Exception:
            rt = []

        rows = []
        for it in ev:
            rows.append({
                'timestamp': getattr(it, 'created_at', None),
                'userid': None,
                'cardno': '',
                'door': None,
                'device': {'device_name': (getattr(it, 'sn', '') or f"device_id={getattr(it, 'device_id', '')}")},
                'event_type': (getattr(it, 'code', '') or 'EVENT'),
                'result': '',
                'info': getattr(it, 'raw_line', '') or '',
            })
        for it in rt:
            rows.append({
                'timestamp': getattr(it, 'created_at', None),
                'userid': None,
                'cardno': '',
                'door': None,
                'device': {'device_name': (getattr(it, 'sn', '') or f"device_id={getattr(it, 'device_id', '')}")},
                'event_type': 'RTLOG',
                'result': '',
                'info': getattr(it, 'raw', '') or '',
            })
        rows.sort(key=lambda r: (r.get('timestamp') is not None, r.get('timestamp')), reverse=True)
        qs = rows
    # export handling
    export = request.GET.get('export')
    if export in ('csv','pdf'):
        if using_legacy:
            # Some schemas store userid as FK (userid__userid), others as plain int.
            try:
                uid_is_rel = bool(getattr(LegacyAccessLog._meta.get_field('userid'), 'is_relation', False))
            except Exception:
                uid_is_rel = False
            uid_field = 'userid__userid' if uid_is_rel else 'userid'
            rows = list(qs.values('timestamp', uid_field, 'cardno', 'door__name', 'device__device_name', 'event_type', 'result', 'info')[:2000])
        else:
            rows = list(qs)[:2000]
        if export == 'csv':
            import csv, io
            buf = io.StringIO(); w = csv.writer(buf)
            w.writerow(['timestamp','userid','cardno','door','device','event_type','result','info'])
            for r in rows:
                if using_legacy:
                    w.writerow([
                        r['timestamp'], r.get(uid_field) if isinstance(r, dict) else '', r['cardno'], r['door__name'],
                        r['device__device_name'], r['event_type'], r['result'], (r['info'] or '')[:120]
                    ])
                else:
                    w.writerow([
                        r.get('timestamp'), '', r.get('cardno',''), '',
                        (r.get('device') or {}).get('device_name',''), r.get('event_type',''), r.get('result',''), (r.get('info') or '')[:120]
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
                    if using_legacy:
                        uid_val = r.get(uid_field) if isinstance(r, dict) else ''
                        line = f"{r['timestamp']} uid={uid_val} door={r['door__name']} ev={r['event_type']} res={r['result']}"
                    else:
                        line = f"{r.get('timestamp')} dev={(r.get('device') or {}).get('device_name','')} ev={r.get('event_type','')}"
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
        if using_legacy:
            try:
                uid_is_rel = bool(getattr(LegacyAccessLog._meta.get_field('userid'), 'is_relation', False))
            except Exception:
                uid_is_rel = False
            uid_field = 'userid__userid' if uid_is_rel else 'userid'
            items = list(qs.values('timestamp', uid_field, 'cardno', 'door__name', 'device__device_name', 'event_type', 'result', 'info')[:200])
            out = []
            for r in items:
                out.append({
                    'datetime': r['timestamp'],
                    'employee': r.get(uid_field),
                    'event': r['event_type'],
                    'details': (r['info'] or '')[:120],
                })
            return JsonResponse({'items': out})

        items = list(qs)[:200]
        out = []
        for r in items:
            out.append({
                'datetime': r.get('timestamp'),
                'employee': '',
                'event': r.get('event_type') or '',
                'details': (r.get('info') or '')[:120],
            })
        return JsonResponse({'items': out})
    per_page = int(request.GET.get('per_page') or 50)
    per_page = max(10, min(per_page, 200))
    page = _paginate(qs, request, per_page=per_page)
    if request.GET.get('embed') == '1':
        return render(request, 'agent/access_logs_embed.html', {'page': page, 'missing': (not using_legacy), 'qs': _qs_without_page(request)})
    return render(request,'agent/access_logs_list.html',{'form': form, 'page': page, 'missing': (not using_legacy)})

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
        # Special: module scopes (aggregate multiple AuditLog.module values)
        if module in ('personnel', 'personal'):
            # ALL logs from PERSONAL module tabs
            qs = qs.filter(module__in=['employee', 'department', 'issuecard'])
        elif module in ('equipment', 'echipamente'):
            # ECHIPAMENTE tabs: device + area + dst + commands
            qs = qs.filter(module__in=['device', 'area', 'dst', 'command'])
        elif module in ('access', 'acces'):
            # CONTROL ACCES tabs: doors + access configuration entities
            qs = qs.filter(module__in=['door', 'access-level', 'time-segment', 'holiday'])
        elif module in ('reports', 'rapoarte'):
            # Report-backed audit sources (best-effort)
            qs = qs.filter(module__in=['accesslog'])
        else:
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
            'issuecard': 'Card',
            'device': 'Dispozitiv',
            'door': 'Ușă',
            'access-level': 'Nivel Acces',
            'time-segment': 'Interval Orar',
            'holiday': 'Sărbătoare',
            'area': 'Zonă Acces',
            'dst': 'Ora de vară',
            'command': 'Comenzi',
            'accesslog': 'AccessLog',
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
    is_modal = (request.GET.get('modal') == '1') or (request.headers.get('x-requested-with') == 'XMLHttpRequest')
    if request.method == 'POST':
        form = AccessLevelForm(request.POST)
        if form.is_valid():
            form.save()
            _broadcast_access_level_change('created', form.instance)
            _audit_log(
                request,
                module='access-level',
                action='create',
                entity_id=form.instance.id,
                entity_name=getattr(form.instance, 'name', '') or '',
            )
            tpl = 'agent/access_level_saved_inner.html' if is_modal else 'agent/access_level_saved.html'
            return render(request, tpl, {'obj': form.instance, 'created': True})
    else: form = AccessLevelForm()
    tpl = 'agent/access_level_form_inner.html' if is_modal else 'agent/access_level_form.html'
    return render(request, tpl, {'form': form})

def access_level_edit(request: HttpRequest, pk: int):
    if not request.user.is_authenticated or not request.user.is_staff:
        from django.contrib.auth.views import redirect_to_login
        return redirect_to_login(request.get_full_path())
    is_modal = (request.GET.get('modal') == '1') or (request.headers.get('x-requested-with') == 'XMLHttpRequest')
    lvl = AccessLevel.objects.get(pk=pk)
    if request.method == 'POST':
        form = AccessLevelForm(request.POST, instance=lvl)
        if form.is_valid():
            form.save()
            _broadcast_access_level_change('updated', form.instance)
            _audit_log(
                request,
                module='access-level',
                action='update',
                entity_id=form.instance.id,
                entity_name=getattr(form.instance, 'name', '') or '',
            )
            tpl = 'agent/access_level_saved_inner.html' if is_modal else 'agent/access_level_saved.html'
            return render(request, tpl, {'obj': form.instance, 'created': False})
    else: form = AccessLevelForm(instance=lvl)
    tpl = 'agent/access_level_form_inner.html' if is_modal else 'agent/access_level_form.html'
    return render(request, tpl, {'form': form, 'obj': lvl})

def access_level_delete(request: HttpRequest, pk: int):
    if not request.user.is_authenticated or not request.user.is_staff or request.method != 'POST': return JsonResponse({'ok': False,'error':'unauthorized'}, status=403)
    try:
        obj = AccessLevel.objects.get(pk=pk)
        obj.delete()
        _broadcast_access_level_change('deleted', obj, deleted=True)
        _audit_log(
            request,
            module='access-level',
            action='delete',
            entity_id=int(pk),
            entity_name=getattr(obj, 'name', '') or '',
        )
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
    # Protect actuations: do not enqueue commands for devices that are disabled
    # or whose persisted DeviceStatus reports offline. This ensures that
    # doors cannot be opened when the centrală is offline/disabled.
    try:
        dev = Device.objects.filter(id=device_id).first()
        if dev is None:
            log.status = 'ERR'
            log.result = 'device-not-found'
            log.save(update_fields=['status','result'])
            return False
        if not getattr(dev, 'enabled', True):
            log.status = 'ERR'
            log.result = 'device-disabled'
            log.save(update_fields=['status','result'])
            return False
        ds = DeviceStatus.objects.filter(device=dev).first()
        if ds is not None and not ds.online:
            log.status = 'ERR'
            log.result = 'device-offline'
            log.save(update_fields=['status','result'])
            return False
        if ds is None:
            # conservative: require an existing DeviceStatus to allow actuations
            log.status = 'ERR'
            log.result = 'device-status-missing'
            log.save(update_fields=['status','result'])
            return False
    except Exception:
        try:
            log.status = 'ERR'
            log.result = 'check-failed'
            log.save(update_fields=['status','result'])
        except Exception:
            pass
        return False
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
            # Use 'auto' driver detection so we don't poll stub data with stale timestamps.
            center = build_and_run_stub(poll_interval=1.0, driver='auto')
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
    if not ok:
        return JsonResponse({"ok": False, "error": "device_unavailable"}, status=409)
    # Update door.is_open state in database
    try:
        door = Door.objects.get(id=door_id)
        door.is_open = True
        door.save(update_fields=['is_open', 'last_state_change'])
        _set_lock_state(door.id, None)
    except Door.DoesNotExist:
        pass
    _persist_and_broadcast_status(device_id, "OPEN")
    try:
        import json as _json
        from .event_codes import describe_door_event_type as _door_desc
        door_obj = Door.objects.filter(id=door_id).select_related('device').first()
        dev = getattr(door_obj, 'device', None) if door_obj else None
        details = _json.dumps({
            'door_id': int(door_id) if str(door_id).isdigit() else door_id,
            'door_name': getattr(door_obj, 'name', '') if door_obj else '',
            'device_id': device_id,
            'device_name': getattr(dev, 'name', '') if dev else '',
            'area_name': getattr(dev, 'area_name', '') if dev else '',
            'event_description': _door_desc('door.open'),
            'status_text': 'OK',
            'verify_mode': 'Others',
        }, ensure_ascii=False)
    except Exception:
        details = ''
    if not getattr(request, '_agent_suppress_door_audit', False):
        _audit_log(
            request,
            module='door',
            action='open',
            entity_id=int(door_id) if str(door_id).isdigit() else 0,
            entity_name=f"door_id={door_id} device_id={device_id}",
            details=details,
        )
    return JsonResponse({"ok": True})

def door_close(request: HttpRequest, device_id: int, door_id: str):
    if not request.user.is_authenticated or not request.user.is_staff:
        return JsonResponse({"ok": False, "error": "unauthorized"}, status=403)
    ok = _enqueue(device_id, f"DOOR_CLOSE:{door_id}")
    if not ok:
        return JsonResponse({"ok": False, "error": "device_unavailable"}, status=409)
    # Update door.is_open state in database
    try:
        door = Door.objects.get(id=door_id)
        door.is_open = False
        door.save(update_fields=['is_open', 'last_state_change'])
        _set_lock_state(door.id, None)
    except Door.DoesNotExist:
        pass
    _persist_and_broadcast_status(device_id, "CLOSED")
    try:
        import json as _json
        from .event_codes import describe_door_event_type as _door_desc
        door_obj = Door.objects.filter(id=door_id).select_related('device').first()
        dev = getattr(door_obj, 'device', None) if door_obj else None
        details = _json.dumps({
            'door_id': int(door_id) if str(door_id).isdigit() else door_id,
            'door_name': getattr(door_obj, 'name', '') if door_obj else '',
            'device_id': device_id,
            'device_name': getattr(dev, 'name', '') if dev else '',
            'area_name': getattr(dev, 'area_name', '') if dev else '',
            'event_description': _door_desc('door.close'),
            'status_text': 'OK',
            'verify_mode': 'Others',
        }, ensure_ascii=False)
    except Exception:
        details = ''
    if not getattr(request, '_agent_suppress_door_audit', False):
        _audit_log(
            request,
            module='door',
            action='close',
            entity_id=int(door_id) if str(door_id).isdigit() else 0,
            entity_name=f"door_id={door_id} device_id={device_id}",
            details=details,
        )
    return JsonResponse({"ok": True})

def door_normal_open(request: HttpRequest, device_id: int, door_id: str):
    if not request.user.is_authenticated or not request.user.is_staff:
        return JsonResponse({"ok": False, "error": "unauthorized"}, status=403)
    ok = _enqueue(device_id, f"DOOR_NORMAL_OPEN:{door_id}")
    if not ok:
        return JsonResponse({"ok": False, "error": "device_unavailable"}, status=409)
    _set_lock_state(door_id, None)
    _persist_and_broadcast_status(device_id, "NORMAL_OPEN")
    try:
        import json as _json
        from .event_codes import describe_door_event_type as _door_desc
        door_obj = Door.objects.filter(id=door_id).select_related('device').first()
        dev = getattr(door_obj, 'device', None) if door_obj else None
        details = _json.dumps({
            'door_id': int(door_id) if str(door_id).isdigit() else door_id,
            'door_name': getattr(door_obj, 'name', '') if door_obj else '',
            'device_id': device_id,
            'device_name': getattr(dev, 'name', '') if dev else '',
            'area_name': getattr(dev, 'area_name', '') if dev else '',
            'event_description': _door_desc('door.normal_open'),
            'status_text': 'OK',
            'verify_mode': 'Others',
        }, ensure_ascii=False)
    except Exception:
        details = ''
    if not getattr(request, '_agent_suppress_door_audit', False):
        _audit_log(
            request,
            module='door',
            action='normal-open',
            entity_id=int(door_id) if str(door_id).isdigit() else 0,
            entity_name=f"door_id={door_id} device_id={device_id}",
            details=details,
        )
    return JsonResponse({"ok": True})

def door_lock(request: HttpRequest, device_id: int, door_id: str):
    if not request.user.is_authenticated or not request.user.is_staff:
        return JsonResponse({"ok": False, "error": "unauthorized"}, status=403)
    ok = _enqueue(device_id, f"DOOR_LOCK:{door_id}")
    if not ok:
        return JsonResponse({"ok": False, "error": "device_unavailable"}, status=409)
    try:
        door = Door.objects.get(id=door_id)
        door.is_open = False
        door.save(update_fields=['is_open', 'last_state_change'])
        _set_lock_state(door.id, 'LOCKED')
    except Door.DoesNotExist:
        _set_lock_state(door_id, 'LOCKED')
    _persist_and_broadcast_status(device_id, "LOCKED")
    try:
        import json as _json
        from .event_codes import describe_door_event_type as _door_desc
        door_obj = Door.objects.filter(id=door_id).select_related('device').first()
        dev = getattr(door_obj, 'device', None) if door_obj else None
        details = _json.dumps({
            'door_id': int(door_id) if str(door_id).isdigit() else door_id,
            'door_name': getattr(door_obj, 'name', '') if door_obj else '',
            'device_id': device_id,
            'device_name': getattr(dev, 'name', '') if dev else '',
            'area_name': getattr(dev, 'area_name', '') if dev else '',
            'event_description': _door_desc('door.lock'),
            'status_text': 'OK',
            'verify_mode': 'Others',
        }, ensure_ascii=False)
    except Exception:
        details = ''
    if not getattr(request, '_agent_suppress_door_audit', False):
        _audit_log(
            request,
            module='door',
            action='lock',
            entity_id=int(door_id) if str(door_id).isdigit() else 0,
            entity_name=f"door_id={door_id} device_id={device_id}",
            details=details,
        )
    return JsonResponse({"ok": True})

def door_unlock(request: HttpRequest, device_id: int, door_id: str):
    if not request.user.is_authenticated or not request.user.is_staff:
        return JsonResponse({"ok": False, "error": "unauthorized"}, status=403)
    ok = _enqueue(device_id, f"DOOR_UNLOCK:{door_id}")
    if not ok:
        return JsonResponse({"ok": False, "error": "device_unavailable"}, status=409)
    try:
        door = Door.objects.get(id=door_id)
        door.save(update_fields=['last_state_change'])
        _set_lock_state(door.id, None)
    except Door.DoesNotExist:
        _set_lock_state(door_id, None)
    _persist_and_broadcast_status(device_id, "UNLOCKED")
    try:
        import json as _json
        from .event_codes import describe_door_event_type as _door_desc
        door_obj = Door.objects.filter(id=door_id).select_related('device').first()
        dev = getattr(door_obj, 'device', None) if door_obj else None
        details = _json.dumps({
            'door_id': int(door_id) if str(door_id).isdigit() else door_id,
            'door_name': getattr(door_obj, 'name', '') if door_obj else '',
            'device_id': device_id,
            'device_name': getattr(dev, 'name', '') if dev else '',
            'area_name': getattr(dev, 'area_name', '') if dev else '',
            'event_description': _door_desc('door.unlock'),
            'status_text': 'OK',
            'verify_mode': 'Others',
        }, ensure_ascii=False)
    except Exception:
        details = ''
    if not getattr(request, '_agent_suppress_door_audit', False):
        _audit_log(
            request,
            module='door',
            action='unlock',
            entity_id=int(door_id) if str(door_id).isdigit() else 0,
            entity_name=f"door_id={door_id} device_id={device_id}",
            details=details,
        )
    return JsonResponse({"ok": True})

def door_cancel_alarm(request: HttpRequest, device_id: int, door_id: str):
    if not request.user.is_authenticated or not request.user.is_staff:
        return JsonResponse({"ok": False, "error": "unauthorized"}, status=403)
    ok = _enqueue(device_id, f"DOOR_CANCEL_ALARM:{door_id}")
    if not ok:
        return JsonResponse({"ok": False, "error": "device_unavailable"}, status=409)
    _persist_and_broadcast_status(device_id, "ALARM_CLEARED")
    try:
        import json as _json
        from .event_codes import describe_door_event_type as _door_desc
        door_obj = Door.objects.filter(id=door_id).select_related('device').first()
        dev = getattr(door_obj, 'device', None) if door_obj else None
        details = _json.dumps({
            'door_id': int(door_id) if str(door_id).isdigit() else door_id,
            'door_name': getattr(door_obj, 'name', '') if door_obj else '',
            'device_id': device_id,
            'device_name': getattr(dev, 'name', '') if dev else '',
            'area_name': getattr(dev, 'area_name', '') if dev else '',
            'event_description': _door_desc('door.cancel_alarm'),
            'status_text': 'OK',
            'verify_mode': 'Others',
        }, ensure_ascii=False)
    except Exception:
        details = ''
    if not getattr(request, '_agent_suppress_door_audit', False):
        _audit_log(
            request,
            module='door',
            action='cancel-alarm',
            entity_id=int(door_id) if str(door_id).isdigit() else 0,
            entity_name=f"door_id={door_id} device_id={device_id}",
            details=details,
        )
    return JsonResponse({"ok": True})


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
                _audit_log(
                    request,
                    module='device',
                    action='toggle',
                    entity_id=int(device_id),
                    entity_name=getattr(dev, 'name', '') or '',
                    details=f"online={bool(ds.online) if ds else bool(target)} updated_at={ua}",
                )
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
        _audit_log(
            request,
            module='device',
            action='toggle',
            entity_id=int(device_id),
            entity_name=getattr(dev, 'name', '') or '',
            details=f"online={bool(ds.online)} updated_at={ua}",
        )
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
            ok = _enqueue(door.device.id, f"DOOR_OPEN:{door.id}", door=door)
            if not ok:
                return JsonResponse({'ok': False, 'error': 'device_unavailable'}, status=409)
            door.is_open = True
            door.save(update_fields=['is_open','last_state_change'])
            _persist_and_broadcast_status(door.device.id, 'OPEN')
        try:
            import json as _json
            from .event_codes import describe_door_event_type as _door_desc
            dev = getattr(door, 'device', None)
            details = _json.dumps({
                'door_id': getattr(door, 'id', pk),
                'door_name': getattr(door, 'name', '') or '',
                'device_id': getattr(dev, 'id', None) or 0,
                'device_name': getattr(dev, 'name', '') if dev else '',
                'area_name': getattr(dev, 'area_name', '') if dev else '',
                'event_description': _door_desc('door.open'),
                'status_text': 'OK',
                'verify_mode': 'Others',
            }, ensure_ascii=False)
        except Exception:
            details = ''
        if not getattr(request, '_agent_suppress_door_audit', False):
            _audit_log(
                request,
                module='door',
                action='open',
                entity_id=int(getattr(door, 'id', 0) or 0),
                entity_name=f"door_id={getattr(door, 'id', pk)} device_id={getattr(getattr(door, 'device', None), 'id', 0) or 0}",
                details=details,
            )
        return JsonResponse({'ok': True})
    except Exception as e:
        return JsonResponse({'ok': False,'error': str(e)}, status=400)

def door_pk_close(request: HttpRequest, pk: int):
    if not request.user.is_authenticated or not request.user.is_staff:
        return JsonResponse({'ok': False,'error':'unauthorized'}, status=403)
    try:
        door = Door.objects.get(pk=pk)
        if door.device:
            ok = _enqueue(door.device.id, f"DOOR_CLOSE:{door.id}", door=door)
            if not ok:
                return JsonResponse({'ok': False, 'error': 'device_unavailable'}, status=409)
            door.is_open = False
            door.save(update_fields=['is_open','last_state_change'])
            _persist_and_broadcast_status(door.device.id, 'CLOSED')
        try:
            import json as _json
            from .event_codes import describe_door_event_type as _door_desc
            dev = getattr(door, 'device', None)
            details = _json.dumps({
                'door_id': getattr(door, 'id', pk),
                'door_name': getattr(door, 'name', '') or '',
                'device_id': getattr(dev, 'id', None) or 0,
                'device_name': getattr(dev, 'name', '') if dev else '',
                'area_name': getattr(dev, 'area_name', '') if dev else '',
                'event_description': _door_desc('door.close'),
                'status_text': 'OK',
                'verify_mode': 'Others',
            }, ensure_ascii=False)
        except Exception:
            details = ''
        if not getattr(request, '_agent_suppress_door_audit', False):
            _audit_log(
                request,
                module='door',
                action='close',
                entity_id=int(getattr(door, 'id', 0) or 0),
                entity_name=f"door_id={getattr(door, 'id', pk)} device_id={getattr(getattr(door, 'device', None), 'id', 0) or 0}",
                details=details,
            )
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


def commands_full_list(request: HttpRequest):
    if not request.user.is_authenticated:
        return JsonResponse({'ok': False, 'error': 'unauthorized'}, status=403)
    limit = min(int(request.GET.get('limit', '200') or 200), 500)
    logs = CommandLog.objects.select_related('device', 'door').order_by('-created_at')[:limit]
    rows = []
    for l in logs:
        rows.append({
            'id': l.id,
            'device': getattr(l.device, 'name', None),
            'serial': getattr(l.device, 'serial_number', ''),
            'door': getattr(l.door, 'name', None),
            'command': l.command,
            'status': l.status,
            'result': l.result,
            'created_at': l.created_at.isoformat(),
            'executed_at': l.executed_at and l.executed_at.isoformat(),
        })
    return JsonResponse({'ok': True, 'items': rows})


def commands_export_csv(request: HttpRequest):
    if not request.user.is_authenticated or not request.user.is_staff:
        return JsonResponse({'ok': False, 'error': 'unauthorized'}, status=403)
    import csv, io
    logs = CommandLog.objects.select_related('device', 'door').order_by('-created_at')[:2000]
    buf = io.StringIO(); w = csv.writer(buf)
    w.writerow(['id','device','serial','door','command','status','result','created_at','executed_at'])
    for l in logs:
        w.writerow([
            l.id,
            getattr(l.device, 'name', ''),
            getattr(l.device, 'serial_number', ''),
            getattr(l.door, 'name', ''),
            l.command,
            l.status,
            l.result,
            l.created_at.isoformat(),
            l.executed_at.isoformat() if l.executed_at else '',
        ])
    resp = HttpResponse(buf.getvalue(), content_type='text/csv')
    resp['Content-Disposition'] = 'attachment; filename=commands.csv'
    return resp


def commands_clear(request: HttpRequest):
    if not request.user.is_authenticated or not request.user.is_staff or request.method != 'POST':
        return JsonResponse({'ok': False, 'error': 'unauthorized'}, status=403)
    deleted, _ = CommandLog.objects.all().delete()
    try:
        _audit_log(
            request,
            module='command',
            action='delete',
            entity_id=0,
            entity_name='CommandLog',
            details=f"deleted={deleted}",
        )
    except Exception:
        pass
    return JsonResponse({'ok': True, 'deleted': deleted})


# ===================== CSV Export/Import (uniform, re-importable) =====================

def _csv_http_response(filename: str, content: str) -> HttpResponse:
    # UTF-8 with BOM for Excel compatibility
    payload = ('\ufeff' + (content or ''))
    resp = HttpResponse(payload, content_type='text/csv; charset=utf-8')
    resp['Content-Disposition'] = f'attachment; filename={filename}'
    return resp


def _parse_bool(val, default=False) -> bool:
    if val is None:
        return bool(default)
    s = str(val).strip().lower()
    if s in ('1', 'true', 'yes', 'y', 'on', 'da'):
        return True
    if s in ('0', 'false', 'no', 'n', 'off', 'nu'):
        return False
    return bool(default)


def _parse_int(val, default=None):
    try:
        if val is None or str(val).strip() == '':
            return default
        return int(str(val).strip())
    except Exception:
        return default


def _parse_time(val):
    from datetime import time
    s = ('' if val is None else str(val)).strip()
    if not s:
        return None
    # accept HH:MM or HH:MM:SS
    try:
        parts = s.split(':')
        hh = int(parts[0]); mm = int(parts[1]) if len(parts) > 1 else 0
        ss = int(parts[2]) if len(parts) > 2 else 0
        return time(hour=hh, minute=mm, second=ss)
    except Exception:
        return None


def _parse_date(val):
    from datetime import date
    s = ('' if val is None else str(val)).strip()
    if not s:
        return None
    # accept YYYY-MM-DD
    try:
        y, m, d = s.split('-')
        return date(int(y), int(m), int(d))
    except Exception:
        return None


def _split_list(val: str):
    s = (val or '').strip()
    if not s:
        return []
    return [x.strip() for x in s.split('|') if x.strip()]


def _read_csv_upload(request: HttpRequest):
    """Return list[dict] rows from uploaded CSV file.

    Accepts delimiter ';' (preferred) or ',' or '\t'.
    """
    if 'file' not in request.FILES:
        return [], 'missing-file'
    f = request.FILES['file']
    try:
        raw = f.read()
        text = raw.decode('utf-8-sig', errors='ignore')
    except Exception:
        return [], 'decode-error'
    import csv, io
    sample = text[:4096]
    delim = ';'
    try:
        sniffer = csv.Sniffer()
        dialect = sniffer.sniff(sample, delimiters=';,\t,')
        delim = getattr(dialect, 'delimiter', ';') or ';'
    except Exception:
        delim = ';'
    reader = csv.DictReader(io.StringIO(text), delimiter=delim)
    rows = []
    for r in reader:
        if not r:
            continue
        # normalize keys
        rr = {}
        for k, v in r.items():
            kk = (k or '').strip().lower()
            if not kk:
                continue
            rr[kk] = (v or '').strip() if isinstance(v, str) else v
        # skip empty lines
        if any((str(v).strip() for v in rr.values())):
            rows.append(rr)
    return rows, None


def csv_export(request: HttpRequest, module: str):
    if not request.user.is_authenticated or not request.user.is_staff:
        return JsonResponse({'ok': False, 'error': 'unauthorized'}, status=403)
    mod = (module or '').lower().strip()

    import csv, io
    buf = io.StringIO(newline='')
    w = csv.writer(buf, delimiter=';')

    if mod in ('door', 'doors'):
        w.writerow(['id', 'name', 'device_serial', 'device_name', 'location', 'normally_open', 'enabled'])
        for d in Door.objects.select_related('device').order_by('name'):
            w.writerow([
                d.id,
                d.name,
                getattr(d.device, 'serial_number', '') if d.device_id else '',
                getattr(d.device, 'name', '') if d.device_id else '',
                d.location or '',
                int(bool(d.normally_open)),
                int(bool(d.enabled)),
            ])
        return _csv_http_response('doors.csv', buf.getvalue())

    if mod in ('time-segment', 'time-segments', 'segment', 'segments'):
        w.writerow(['id', 'name', 'start_time', 'end_time', 'days_mask'])
        for s in TimeSegment.objects.order_by('name'):
            w.writerow([s.id, s.name, s.start_time.isoformat(), s.end_time.isoformat(), int(s.days_mask)])
        return _csv_http_response('time_segments.csv', buf.getvalue())

    if mod in ('holiday', 'holidays'):
        w.writerow(['id', 'date', 'name', 'description'])
        for h in Holiday.objects.order_by('date'):
            w.writerow([h.id, h.date.isoformat(), h.name, h.description or ''])
        return _csv_http_response('holidays.csv', buf.getvalue())

    if mod in ('access-level', 'access-levels', 'level', 'levels'):
        w.writerow(['id', 'name', 'description', 'doors', 'time_segments'])
        qs = AccessLevel.objects.prefetch_related('doors', 'time_segments').order_by('name')
        for lvl in qs:
            doors = '|'.join(lvl.doors.values_list('name', flat=True))
            segs = '|'.join(lvl.time_segments.values_list('name', flat=True))
            w.writerow([lvl.id, lvl.name, lvl.description or '', doors, segs])
        return _csv_http_response('access_levels.csv', buf.getvalue())

    if mod in ('device', 'devices'):
        w.writerow([
            'id', 'name', 'serial_number', 'device_type', 'comm_mode', 'ip_address', 'port',
            'enabled', 'scanner_linked', 'scanner_type',
            'rs485_port', 'rs485_baudrate', 'rs485_address',
            'area_name', 'time_zone'
        ])
        for dev in Device.objects.order_by('name'):
            w.writerow([
                dev.id,
                dev.name,
                dev.serial_number or '',
                dev.device_type or '',
                dev.comm_mode or '',
                dev.ip_address or '',
                int(dev.port or 0),
                int(bool(dev.enabled)),
                int(bool(dev.scanner_linked)),
                dev.scanner_type or '',
                dev.rs485_port or '',
                int(dev.rs485_baudrate or 0),
                '' if dev.rs485_address is None else int(dev.rs485_address),
                dev.area_name or '',
                dev.time_zone or '',
            ])
        return _csv_http_response('devices.csv', buf.getvalue())

    if mod in ('dst', 'dstime'):
        w.writerow([
            'id', 'name',
            'start_month', 'start_week', 'start_weekday', 'start_hour', 'start_minute',
            'end_month', 'end_week', 'end_weekday', 'end_hour', 'end_minute',
            'offset_minutes'
        ])
        for d in DSTime.objects.order_by('name'):
            w.writerow([
                d.id, d.name,
                d.start_month, d.start_week, d.start_weekday, d.start_hour, d.start_minute,
                d.end_month, d.end_week, d.end_weekday, d.end_hour, d.end_minute,
                d.offset_minutes,
            ])
        return _csv_http_response('dst.csv', buf.getvalue())

    if mod in ('area', 'areas'):
        if not LegacyArea:
            return JsonResponse({'ok': False, 'error': 'missing-model'}, status=400)
        try:
            from .models import LegacyAreaMeta
        except Exception:
            LegacyAreaMeta = None  # type: ignore
        areas = list(LegacyArea.objects.order_by('areaname'))
        name_by_id = {int(a.id): (a.areaname or '') for a in areas}
        meta_by_id = {}
        if LegacyAreaMeta is not None:
            try:
                meta_rows = LegacyAreaMeta.objects.filter(legacy_area_id__in=list(name_by_id.keys()))
                meta_by_id = {int(m.legacy_area_id): m for m in meta_rows}
            except Exception:
                meta_by_id = {}
        # export uses parent_code to keep files stable across DBs
        code_by_id = {}
        for aid, m in meta_by_id.items():
            try:
                code_by_id[int(aid)] = (getattr(m, 'code', None) or '').strip()
            except Exception:
                code_by_id[int(aid)] = ''
        w.writerow(['id', 'name', 'code', 'parent_code', 'remarks'])
        for a in areas:
            mid = int(a.id)
            m = meta_by_id.get(mid)
            code = (getattr(m, 'code', None) if m else None) or ''
            remarks = (getattr(m, 'remarks', None) if m else None) or ''
            parent_id = None
            try:
                parent_id = int(getattr(m, 'parent_legacy_area_id', None)) if m and getattr(m, 'parent_legacy_area_id', None) else None
            except Exception:
                parent_id = None
            parent_code = code_by_id.get(parent_id or 0, '') if parent_id else ''
            w.writerow([mid, a.areaname or '', code, parent_code, remarks])
        return _csv_http_response('areas.csv', buf.getvalue())

    if mod in ('command', 'commands'):
        # Export the command log queue (importable to re-create pending commands if needed)
        w.writerow(['id', 'command', 'device_serial', 'device_name', 'door_name'])
        logs = CommandLog.objects.select_related('device', 'door').order_by('-created_at')[:2000]
        for l in logs:
            w.writerow([
                l.id,
                l.command or '',
                getattr(l.device, 'serial_number', '') if l.device_id else '',
                getattr(l.device, 'name', '') if l.device_id else '',
                getattr(l.door, 'name', '') if l.door_id else '',
            ])
        return _csv_http_response('commands_queue.csv', buf.getvalue())

    # ===== PERSONAL MODULES =====
    if mod in ('department', 'departments', 'dept', 'depts'):
        if not Dept:
            return JsonResponse({'ok': False, 'error': 'missing-model:Dept'}, status=400)
        w.writerow(['id', 'name', 'code'])
        for d in Dept.objects.order_by('DeptName'):
            w.writerow([int(d.id), getattr(d, 'DeptName', '') or '', getattr(d, 'code', '') or ''])
        return _csv_http_response('departments.csv', buf.getvalue())

    if mod in ('employee', 'employees'):
        w.writerow([
            'id', 'legacy_userid', 'first_name', 'last_name', 'card_number',
            'dept_id', 'dept_name',
            'mobile_phone', 'gender', 'active', 'acc_startdate', 'acc_enddate'
        ])
        dept_name_by_id = {}
        if Dept:
            try:
                dept_name_by_id = {int(d.id): (getattr(d, 'DeptName', '') or '') for d in Dept.objects.all()}
            except Exception:
                dept_name_by_id = {}
        for e in Employee.objects.order_by('last_name', 'first_name'):
            dept_id = int(e.dept_id) if e.dept_id else ''
            dept_name = dept_name_by_id.get(int(e.dept_id), '') if e.dept_id else ''
            w.writerow([
                int(e.id),
                '' if e.legacy_userid is None else int(e.legacy_userid),
                e.first_name or '',
                e.last_name or '',
                e.card_number or '',
                dept_id,
                dept_name,
                e.mobile_phone or '',
                e.gender or '',
                int(bool(e.active)),
                e.acc_startdate.isoformat() if e.acc_startdate else '',
                e.acc_enddate.isoformat() if e.acc_enddate else '',
            ])
        return _csv_http_response('employees.csv', buf.getvalue())

    if mod in ('issuecard', 'issuecards', 'card', 'cards', 'employee-card', 'employee-cards'):
        w.writerow([
            'id', 'employee_id', 'employee_legacy_userid', 'employee_name',
            'card_number', 'slot', 'status', 'site_code', 'valid_until'
        ])
        qs = EmployeeCard.objects.select_related('employee').order_by('-created_at')
        for c in qs:
            emp = getattr(c, 'employee', None)
            emp_name = ''
            if emp is not None:
                emp_name = f"{getattr(emp,'first_name','') or ''} {getattr(emp,'last_name','') or ''}".strip()
            w.writerow([
                int(c.id),
                int(emp.id) if emp is not None else '',
                '' if (emp is None or emp.legacy_userid is None) else int(emp.legacy_userid),
                emp_name,
                c.card_number or '',
                c.slot or '',
                c.status or '',
                c.site_code or '',
                c.valid_until.isoformat() if c.valid_until else '',
            ])
        return _csv_http_response('employee_cards.csv', buf.getvalue())

    return JsonResponse({'ok': False, 'error': f'unknown-module:{mod}'}, status=400)


def csv_import(request: HttpRequest, module: str):
    if not request.user.is_authenticated or not request.user.is_staff:
        return JsonResponse({'ok': False, 'error': 'unauthorized'}, status=403)
    if request.method != 'POST':
        return JsonResponse({'ok': False, 'error': 'method-not-allowed'}, status=405)
    mod = (module or '').lower().strip()
    rows, err = _read_csv_upload(request)
    if err:
        return JsonResponse({'ok': False, 'error': err}, status=400)

    created = 0
    updated = 0
    failed = 0
    errors = []

    def _fail(i, msg):
        nonlocal failed
        failed += 1
        if len(errors) < 50:
            errors.append({'row': i, 'error': msg})

    # ===== ACCESS MODULES =====
    if mod in ('door', 'doors'):
        for i, r in enumerate(rows, start=2):
            try:
                name = (r.get('name') or '').strip()
                if not name:
                    _fail(i, 'missing-name');
                    continue
                pk = _parse_int(r.get('id'))
                obj = Door.objects.filter(pk=pk).first() if pk else Door.objects.filter(name=name).first()
                is_new = obj is None
                if obj is None:
                    obj = Door(name=name)
                obj.name = name
                obj.location = (r.get('location') or '').strip()
                obj.normally_open = _parse_bool(r.get('normally_open'), False)
                obj.enabled = _parse_bool(r.get('enabled'), True)
                # device resolve
                dev = None
                dev_serial = (r.get('device_serial') or '').strip()
                dev_name = (r.get('device_name') or '').strip()
                if dev_serial:
                    dev = Device.objects.filter(serial_number=dev_serial).first()
                if dev is None and dev_name:
                    dev = Device.objects.filter(name=dev_name).first()
                obj.device = dev
                obj.save()
                if is_new:
                    created += 1
                    _audit_log(request, module='door', action='create', entity_id=int(obj.id), entity_name=obj.name or '')
                else:
                    updated += 1
                    _audit_log(request, module='door', action='update', entity_id=int(obj.id), entity_name=obj.name or '')
            except Exception as ex:
                _fail(i, str(ex))
        return JsonResponse({'ok': True, 'module': mod, 'created': created, 'updated': updated, 'failed': failed, 'errors': errors})

    if mod in ('time-segment', 'time-segments', 'segment', 'segments'):
        for i, r in enumerate(rows, start=2):
            try:
                name = (r.get('name') or '').strip()
                if not name:
                    _fail(i, 'missing-name');
                    continue
                st = _parse_time(r.get('start_time'))
                en = _parse_time(r.get('end_time'))
                if not st or not en:
                    _fail(i, 'missing-start-or-end-time');
                    continue
                dm = _parse_int(r.get('days_mask'), 127)
                pk = _parse_int(r.get('id'))
                obj = TimeSegment.objects.filter(pk=pk).first() if pk else TimeSegment.objects.filter(name=name).first()
                is_new = obj is None
                if obj is None:
                    obj = TimeSegment(name=name)
                obj.name = name
                obj.start_time = st
                obj.end_time = en
                obj.days_mask = int(dm or 127)
                obj.full_clean()
                obj.save()
                if is_new:
                    created += 1
                    _audit_log(request, module='time-segment', action='create', entity_id=int(obj.id), entity_name=obj.name or '')
                else:
                    updated += 1
                    _audit_log(request, module='time-segment', action='update', entity_id=int(obj.id), entity_name=obj.name or '')
            except Exception as ex:
                _fail(i, str(ex))
        return JsonResponse({'ok': True, 'module': mod, 'created': created, 'updated': updated, 'failed': failed, 'errors': errors})

    if mod in ('holiday', 'holidays'):
        for i, r in enumerate(rows, start=2):
            try:
                dt = _parse_date(r.get('date'))
                if not dt:
                    _fail(i, 'missing-date');
                    continue
                name = (r.get('name') or '').strip() or dt.isoformat()
                desc = (r.get('description') or '').strip()
                pk = _parse_int(r.get('id'))
                obj = Holiday.objects.filter(pk=pk).first() if pk else Holiday.objects.filter(date=dt).first()
                is_new = obj is None
                if obj is None:
                    obj = Holiday(date=dt)
                obj.date = dt
                obj.name = name
                obj.description = desc
                obj.save()
                if is_new:
                    created += 1
                    _audit_log(request, module='holiday', action='create', entity_id=int(obj.id), entity_name=obj.name or '')
                else:
                    updated += 1
                    _audit_log(request, module='holiday', action='update', entity_id=int(obj.id), entity_name=obj.name or '')
            except Exception as ex:
                _fail(i, str(ex))
        return JsonResponse({'ok': True, 'module': mod, 'created': created, 'updated': updated, 'failed': failed, 'errors': errors})

    if mod in ('access-level', 'access-levels', 'level', 'levels'):
        for i, r in enumerate(rows, start=2):
            try:
                name = (r.get('name') or '').strip()
                if not name:
                    _fail(i, 'missing-name');
                    continue
                desc = (r.get('description') or '').strip()
                pk = _parse_int(r.get('id'))
                obj = AccessLevel.objects.filter(pk=pk).first() if pk else AccessLevel.objects.filter(name=name).first()
                is_new = obj is None
                if obj is None:
                    obj = AccessLevel(name=name)
                obj.name = name
                obj.description = desc
                obj.save()

                door_names = _split_list(r.get('doors') or '')
                seg_names = _split_list(r.get('time_segments') or '')
                if door_names:
                    doors = list(Door.objects.filter(name__in=door_names))
                    obj.doors.set(doors)
                if seg_names:
                    segs = list(TimeSegment.objects.filter(name__in=seg_names))
                    obj.time_segments.set(segs)

                if is_new:
                    created += 1
                    _audit_log(request, module='access-level', action='create', entity_id=int(obj.id), entity_name=obj.name or '')
                else:
                    updated += 1
                    _audit_log(request, module='access-level', action='update', entity_id=int(obj.id), entity_name=obj.name or '')
            except Exception as ex:
                _fail(i, str(ex))
        return JsonResponse({'ok': True, 'module': mod, 'created': created, 'updated': updated, 'failed': failed, 'errors': errors})

    # ===== PERSONAL MODULES =====
    if mod in ('department', 'departments', 'dept', 'depts'):
        if not Dept:
            return JsonResponse({'ok': False, 'error': 'missing-model:Dept'}, status=400)
        for i, r in enumerate(rows, start=2):
            try:
                name = (r.get('name') or r.get('deptname') or '').strip()
                code = (r.get('code') or '').strip()
                pk = _parse_int(r.get('id'))

                obj = None
                if pk:
                    obj = Dept.objects.filter(pk=int(pk)).first()
                if obj is None and code:
                    obj = Dept.objects.filter(code=code).first()
                if obj is None and name:
                    obj = Dept.objects.filter(DeptName=name).first()

                is_new = obj is None
                if obj is None:
                    if not name:
                        _fail(i, 'missing-name')
                        continue
                    obj = Dept()
                    if pk:
                        try:
                            setattr(obj, 'id', int(pk))
                        except Exception:
                            pass

                if name:
                    obj.DeptName = name
                if code:
                    try:
                        obj.code = code
                    except Exception:
                        pass

                obj.save()
                if is_new:
                    created += 1
                    _audit_log(request, module='department', action='create', entity_id=int(obj.id), entity_name=getattr(obj, 'DeptName', '') or '')
                else:
                    updated += 1
                    _audit_log(request, module='department', action='update', entity_id=int(obj.id), entity_name=getattr(obj, 'DeptName', '') or '')
            except Exception as ex:
                _fail(i, str(ex))
        return JsonResponse({'ok': True, 'module': mod, 'created': created, 'updated': updated, 'failed': failed, 'errors': errors})

    if mod in ('employee', 'employees'):
        dept_by_name = {}
        if Dept:
            try:
                dept_by_name = {str(getattr(d, 'DeptName', '') or '').strip().lower(): int(d.id) for d in Dept.objects.all()}
            except Exception:
                dept_by_name = {}

        for i, r in enumerate(rows, start=2):
            try:
                pk = _parse_int(r.get('id'))
                legacy_userid = _parse_int(r.get('legacy_userid') or r.get('userid'))
                first_name = (r.get('first_name') or '').strip()
                last_name = (r.get('last_name') or '').strip()
                card_number = (r.get('card_number') or '').strip()

                obj = None
                if pk:
                    obj = Employee.objects.filter(pk=int(pk)).first()
                if obj is None and legacy_userid is not None:
                    obj = Employee.objects.filter(legacy_userid=int(legacy_userid)).first()
                if obj is None and card_number:
                    obj = Employee.objects.filter(card_number=card_number).first()
                is_new = obj is None

                if obj is None:
                    if not first_name or not last_name:
                        _fail(i, 'missing-first-or-last-name')
                        continue
                    if not card_number:
                        _fail(i, 'missing-card_number')
                        continue
                    obj = Employee(first_name=first_name, last_name=last_name, card_number=card_number)

                # Avoid clobbering fields with blanks
                if first_name:
                    obj.first_name = first_name
                if last_name:
                    obj.last_name = last_name
                if card_number:
                    other = Employee.objects.filter(card_number=card_number).exclude(pk=obj.pk).first() if obj.pk else Employee.objects.filter(card_number=card_number).first()
                    if other and (not obj.pk or other.pk != obj.pk):
                        _fail(i, f'duplicate-card_number:{card_number}')
                        continue
                    obj.card_number = card_number

                if legacy_userid is not None:
                    other = Employee.objects.filter(legacy_userid=int(legacy_userid)).exclude(pk=obj.pk).first() if obj.pk else Employee.objects.filter(legacy_userid=int(legacy_userid)).first()
                    if other and (not obj.pk or other.pk != obj.pk):
                        _fail(i, f'duplicate-legacy_userid:{legacy_userid}')
                        continue
                    obj.legacy_userid = int(legacy_userid)

                dept_id = _parse_int(r.get('dept_id'))
                if dept_id is None:
                    dept_name = (r.get('dept_name') or '').strip().lower()
                    if dept_name and dept_by_name:
                        dept_id = dept_by_name.get(dept_name)
                if dept_id is not None:
                    obj.dept_id = int(dept_id)

                obj.mobile_phone = (r.get('mobile_phone') or obj.mobile_phone or '').strip()
                obj.gender = (r.get('gender') or obj.gender or '').strip()
                obj.active = _parse_bool(r.get('active'), obj.active if obj.pk else True)
                obj.acc_startdate = _parse_date(r.get('acc_startdate')) or obj.acc_startdate
                obj.acc_enddate = _parse_date(r.get('acc_enddate')) or obj.acc_enddate

                obj.full_clean()
                obj.save()

                if is_new:
                    created += 1
                    _audit_log(request, module='employee', action='create', entity_id=int(obj.id), entity_name=f"{obj.first_name} {obj.last_name}".strip())
                else:
                    updated += 1
                    _audit_log(request, module='employee', action='update', entity_id=int(obj.id), entity_name=f"{obj.first_name} {obj.last_name}".strip())
            except Exception as ex:
                _fail(i, str(ex))
        return JsonResponse({'ok': True, 'module': mod, 'created': created, 'updated': updated, 'failed': failed, 'errors': errors})

    if mod in ('issuecard', 'issuecards', 'card', 'cards', 'employee-card', 'employee-cards'):
        for i, r in enumerate(rows, start=2):
            try:
                pk = _parse_int(r.get('id'))
                card_number = (r.get('card_number') or '').strip()
                if not card_number:
                    _fail(i, 'missing-card_number')
                    continue

                emp = None
                emp_id = _parse_int(r.get('employee_id'))
                emp_legacy = _parse_int(r.get('employee_legacy_userid'))
                if emp_id is not None:
                    emp = Employee.objects.filter(pk=int(emp_id)).first()
                if emp is None and emp_legacy is not None:
                    emp = Employee.objects.filter(legacy_userid=int(emp_legacy)).first()
                if emp is None:
                    _fail(i, 'missing-or-invalid-employee')
                    continue

                obj = None
                if pk:
                    obj = EmployeeCard.objects.filter(pk=int(pk)).first()
                if obj is None and card_number:
                    obj = EmployeeCard.objects.filter(card_number=card_number).first()
                is_new = obj is None
                if obj is None:
                    obj = EmployeeCard(employee=emp, card_number=card_number)

                obj.employee = emp
                # unique card_number enforced by model
                obj.card_number = card_number
                obj.slot = (r.get('slot') or obj.slot or 'additional').strip() or 'additional'
                obj.status = (r.get('status') or obj.status or 'Active').strip() or 'Active'
                obj.site_code = (r.get('site_code') or obj.site_code or '').strip()
                obj.valid_until = _parse_date(r.get('valid_until')) or obj.valid_until
                obj.full_clean()
                obj.save()

                if is_new:
                    created += 1
                    _audit_log(request, module='issuecard', action='create', entity_id=int(obj.id), entity_name=obj.card_number or '')
                else:
                    updated += 1
                    _audit_log(request, module='issuecard', action='update', entity_id=int(obj.id), entity_name=obj.card_number or '')
            except Exception as ex:
                _fail(i, str(ex))
        return JsonResponse({'ok': True, 'module': mod, 'created': created, 'updated': updated, 'failed': failed, 'errors': errors})

    # ===== EQUIPMENT MODULES =====
    if mod in ('device', 'devices'):
        for i, r in enumerate(rows, start=2):
            try:
                name = (r.get('name') or '').strip()
                serial = (r.get('serial_number') or '').strip()
                pk = _parse_int(r.get('id'))
                obj = None
                if pk:
                    obj = Device.objects.filter(pk=pk).first()
                if obj is None and serial:
                    obj = Device.objects.filter(serial_number=serial).first()
                if obj is None and name:
                    obj = Device.objects.filter(name=name).first()
                is_new = obj is None
                if obj is None:
                    if not name:
                        _fail(i, 'missing-name');
                        continue
                    obj = Device(name=name)
                if name:
                    obj.name = name
                if serial:
                    obj.serial_number = serial

                obj.device_type = (r.get('device_type') or obj.device_type or 'access_panel').strip() or 'access_panel'
                obj.comm_mode = (r.get('comm_mode') or obj.comm_mode or 'tcp').strip() or 'tcp'
                obj.ip_address = (r.get('ip_address') or '').strip() or None
                obj.port = _parse_int(r.get('port'), obj.port or 4370) or (obj.port or 4370)
                obj.enabled = _parse_bool(r.get('enabled'), obj.enabled if obj.pk else True)
                obj.scanner_linked = _parse_bool(r.get('scanner_linked'), obj.scanner_linked if obj.pk else False)
                obj.scanner_type = (r.get('scanner_type') or obj.scanner_type or '').strip()
                obj.rs485_port = (r.get('rs485_port') or obj.rs485_port or '').strip()
                obj.rs485_baudrate = _parse_int(r.get('rs485_baudrate'), obj.rs485_baudrate or 9600) or (obj.rs485_baudrate or 9600)
                obj.rs485_address = _parse_int(r.get('rs485_address'), obj.rs485_address)
                obj.area_name = (r.get('area_name') or obj.area_name or '').strip()
                obj.time_zone = (r.get('time_zone') or obj.time_zone or '').strip()
                obj.save()

                if is_new:
                    created += 1
                    _audit_log(request, module='device', action='create', entity_id=int(obj.id), entity_name=obj.name or '')
                else:
                    updated += 1
                    _audit_log(request, module='device', action='update', entity_id=int(obj.id), entity_name=obj.name or '')
            except Exception as ex:
                _fail(i, str(ex))
        return JsonResponse({'ok': True, 'module': mod, 'created': created, 'updated': updated, 'failed': failed, 'errors': errors})

    if mod in ('dst', 'dstime'):
        for i, r in enumerate(rows, start=2):
            try:
                name = (r.get('name') or '').strip()
                if not name:
                    _fail(i, 'missing-name');
                    continue
                pk = _parse_int(r.get('id'))
                obj = DSTime.objects.filter(pk=pk).first() if pk else DSTime.objects.filter(name=name).first()
                is_new = obj is None
                if obj is None:
                    obj = DSTime(name=name)
                obj.name = name
                obj.start_month = _parse_int(r.get('start_month'), 1) or 1
                obj.start_week = (r.get('start_week') or 'last').strip() or 'last'
                obj.start_weekday = _parse_int(r.get('start_weekday'), 0) or 0
                obj.start_hour = _parse_int(r.get('start_hour'), 3) or 3
                obj.start_minute = _parse_int(r.get('start_minute'), 0) or 0
                obj.end_month = _parse_int(r.get('end_month'), 10) or 10
                obj.end_week = (r.get('end_week') or 'last').strip() or 'last'
                obj.end_weekday = _parse_int(r.get('end_weekday'), 0) or 0
                obj.end_hour = _parse_int(r.get('end_hour'), 3) or 3
                obj.end_minute = _parse_int(r.get('end_minute'), 0) or 0
                obj.offset_minutes = _parse_int(r.get('offset_minutes'), 60) or 60
                obj.save()
                if is_new:
                    created += 1
                    _audit_log(request, module='dst', action='create', entity_id=int(obj.id), entity_name=obj.name or '')
                else:
                    updated += 1
                    _audit_log(request, module='dst', action='update', entity_id=int(obj.id), entity_name=obj.name or '')
            except Exception as ex:
                _fail(i, str(ex))
        return JsonResponse({'ok': True, 'module': mod, 'created': created, 'updated': updated, 'failed': failed, 'errors': errors})

    if mod in ('area', 'areas'):
        if not LegacyArea:
            return JsonResponse({'ok': False, 'error': 'missing-model'}, status=400)
        try:
            from .models import LegacyAreaMeta
        except Exception:
            LegacyAreaMeta = None  # type: ignore
        # First pass: build code -> legacy_area_id mapping
        meta_code_map = {}
        if LegacyAreaMeta is not None:
            try:
                for m in LegacyAreaMeta.objects.exclude(code__isnull=True).exclude(code=''):
                    meta_code_map[(m.code or '').strip()] = int(m.legacy_area_id)
            except Exception:
                meta_code_map = {}

        pending_parent_links = []  # (legacy_area_id, parent_code)

        for i, r in enumerate(rows, start=2):
            try:
                name = (r.get('name') or '').strip()
                code = (r.get('code') or '').strip()
                if not name:
                    _fail(i, 'missing-name');
                    continue
                if not code:
                    _fail(i, 'missing-code');
                    continue
                parent_code = (r.get('parent_code') or '').strip()
                remarks = (r.get('remarks') or '').strip()
                pk = _parse_int(r.get('id'))

                obj = None
                if pk:
                    obj = LegacyArea.objects.filter(pk=int(pk)).first()
                if obj is None and code and (code in meta_code_map):
                    obj = LegacyArea.objects.filter(pk=int(meta_code_map[code])).first()
                if obj is None:
                    # fallback by name
                    obj = LegacyArea.objects.filter(areaname=name).first()
                is_new = obj is None
                if obj is None:
                    obj, _ = LegacyArea.objects.get_or_create(areaname=name)
                else:
                    obj.areaname = name
                    obj.save(update_fields=['areaname'])

                # write meta
                if LegacyAreaMeta is not None:
                    try:
                        LegacyAreaMeta.objects.update_or_create(
                            legacy_area_id=int(obj.id),
                            defaults={
                                'code': code,
                                'remarks': remarks,
                                # parent set in second pass
                            },
                        )
                    except Exception:
                        pass
                meta_code_map[code] = int(obj.id)
                if parent_code:
                    pending_parent_links.append((int(obj.id), parent_code))
                if is_new:
                    created += 1
                    _audit_log(request, module='area', action='create', entity_id=int(getattr(obj, 'id', 0) or 0), entity_name=name, details=f"code={code}")
                else:
                    updated += 1
                    _audit_log(request, module='area', action='update', entity_id=int(getattr(obj, 'id', 0) or 0), entity_name=name, details=f"code={code}")
            except Exception as ex:
                _fail(i, str(ex))

        # Second pass: apply parent_code links
        if LegacyAreaMeta is not None and pending_parent_links:
            for (aid, pcode) in pending_parent_links:
                try:
                    pid = meta_code_map.get(pcode)
                    if not pid:
                        continue
                    LegacyAreaMeta.objects.filter(legacy_area_id=int(aid)).update(parent_legacy_area_id=int(pid))
                except Exception:
                    continue

        return JsonResponse({'ok': True, 'module': mod, 'created': created, 'updated': updated, 'failed': failed, 'errors': errors})

    if mod in ('command', 'commands'):
        for i, r in enumerate(rows, start=2):
            try:
                cmd = (r.get('command') or '').strip()
                if not cmd:
                    _fail(i, 'missing-command');
                    continue
                dev_serial = (r.get('device_serial') or '').strip()
                dev_name = (r.get('device_name') or '').strip()
                door_name = (r.get('door_name') or '').strip()
                dev = None
                if dev_serial:
                    dev = Device.objects.filter(serial_number=dev_serial).first()
                if dev is None and dev_name:
                    dev = Device.objects.filter(name=dev_name).first()
                door = Door.objects.filter(name=door_name).first() if door_name else None
                log = CommandLog.objects.create(device=dev, door=door, command=cmd, status='PENDING')
                _broadcast_command(log)
                created += 1
                _audit_log(
                    request,
                    module='command',
                    action='create',
                    entity_id=int(log.id),
                    entity_name=(cmd or '')[:120],
                    details=f"device_id={getattr(dev, 'id', '') or ''} door_id={getattr(door, 'id', '') or ''}",
                )
            except Exception as ex:
                _fail(i, str(ex))
        return JsonResponse({'ok': True, 'module': mod, 'created': created, 'updated': 0, 'failed': failed, 'errors': errors})

    return JsonResponse({'ok': False, 'error': f'unknown-module:{mod}'}, status=400)


def command_manual_create(request: HttpRequest):
    if not request.user.is_authenticated or not request.user.is_staff or request.method != 'POST':
        return JsonResponse({'ok': False, 'error': 'unauthorized'}, status=403)
    import json
    try:
        payload = json.loads(request.body.decode('utf-8'))
    except Exception:
        payload = request.POST.dict()
    cmd = (payload.get('command') or '').strip()
    if not cmd:
        return JsonResponse({'ok': False, 'error': 'missing-command'}, status=400)
    device_id = payload.get('device_id')
    door_id = payload.get('door_id')
    device = Device.objects.filter(pk=device_id).first() if device_id else None
    door = Door.objects.filter(pk=door_id).first() if door_id else None
    log = CommandLog.objects.create(device=device, door=door, command=cmd, status='PENDING')
    _broadcast_command(log)
    try:
        _audit_log(
            request,
            module='command',
            action='create',
            entity_id=int(log.id),
            entity_name=(cmd or '')[:120],
            details=f"device_id={getattr(device, 'id', '') or ''} door_id={getattr(door, 'id', '') or ''}",
        )
    except Exception:
        pass
    return JsonResponse({'ok': True, 'id': log.id})

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
        # Start CommCenter with automatic driver selection (prefer real drivers over stub)
        mcc.ACTIVE_CENTER = build_and_run_stub(poll_interval=1.0, driver='auto')
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

import os
import json
import threading
from types import SimpleNamespace
from typing import Any, Optional, cast
from django.http import JsonResponse, HttpRequest, HttpResponse
from django.views.decorators.csrf import csrf_exempt, ensure_csrf_cookie
from django.shortcuts import render
from django.utils import timezone
from django.db.models import Max
from django.db import transaction

from .models import DeviceRealtimeLog, DeviceEventLog, DeviceStatus, Device, DSTime
from .models import Door, DoorFirstCardRule, DoorMultiCardRule, TimeSegment, Holiday, AccessLevel, Employee
from .models import CommandLog, EmployeeAccessCache, EmployeeCard
try:
    from .models import AuditLog
except ImportError:
    AuditLog = None
from .forms import (DoorForm, DoorFirstCardRuleForm, DoorMultiCardRuleForm, TimeSegmentFormWithDays, HolidayForm, AccessLevelForm,
                    EmployeeForm, EmployeeExtendedForm, DeptForm, AreaForm,
                    AccessLogFilterForm, DeviceExtendedForm, DSTimeForm, WizardDoorDraftForm)
from . import forms as _agent_forms
IssueCardForm = getattr(_agent_forms, 'IssueCardForm', None)
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
    try:
        if AuditLog is None:
            return
        try:
            uname = ''
            if hasattr(request, 'user') and getattr(request.user, 'is_authenticated', False):
                uname = str(getattr(request.user, 'username', '') or '')
        except Exception:
            uname = ''
        try:
            ip_addr = request.META.get('REMOTE_ADDR')
        except Exception:
            ip_addr = None
        AuditLog.objects.create(
            user=uname or None,
            module=(module or '')[:32],
            action=(action or '')[:32],
            entity_id=int(entity_id or 0),
            entity_name=(entity_name or '')[:256] or None,
            details=(details or ''),
            ip_address=ip_addr,
        )
    except Exception:
        return


def _tray_status_path():
    try:
        from pathlib import Path
        from django.conf import settings

        base = Path(getattr(settings, 'BASE_DIR', Path.cwd()))
        return base.parent / 'tray_status.json'
    except Exception:
        from pathlib import Path

        return Path('tray_status.json')


def _readers_cfg_path():
    try:
        from pathlib import Path
        from django.conf import settings

        base = Path(getattr(settings, 'BASE_DIR', Path.cwd()))
        return base.parent / 'scripts' / 'card_readers.json'
    except Exception:
        from pathlib import Path

        return Path('scripts') / 'card_readers.json'


def _read_json_safe(p):
    try:
        from pathlib import Path

        pp = p if isinstance(p, Path) else Path(str(p))
        if pp.exists():
            return json.loads(pp.read_text(encoding='utf-8')) or {}
    except Exception:
        pass
    return {}


def _write_json_safe(p, data) -> bool:
    try:
        from pathlib import Path

        pp = p if isinstance(p, Path) else Path(str(p))
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


def _qs_without_page(request: HttpRequest) -> str:
    try:
        from urllib.parse import urlencode

        q = {}
        try:
            q = dict(getattr(request, 'GET', {}) or {})
        except Exception:
            q = {}
        try:
            q.pop('page', None)
        except Exception:
            pass
        return urlencode(q, doseq=True)
    except Exception:
        return ''


def _payload_get_str(payload: Any, key: str, default: str = '') -> str:
    try:
        if isinstance(payload, dict) and key in payload:
            v = payload.get(key)
            if v is None:
                return default
            return str(v)
    except Exception:
        pass
    return default


def _payload_get_int(payload: Any, key: str, default: int = 0) -> int:
    try:
        if isinstance(payload, dict) and key in payload:
            v = payload.get(key)
            if v is None or str(v).strip() == '':
                return int(default)
            return int(str(v).strip())
    except Exception:
        pass
    try:
        return int(default)
    except Exception:
        return 0


def _get_default_comm_password_cached() -> str:
    """Return the effective default communication password.

    Precedence:
      1) DB (SystemSettings.default_comm_password) if set
      2) settings.ZKACCESS_DEFAULT_COMM_PASSWORD (env-backed) otherwise

    Cached briefly to avoid DB hits on hot endpoints.
    """
    cache_key = 'agent:default_comm_password'
    try:
        cached = cache.get(cache_key)
        if cached is not None:
            return str(cached or '').strip()
    except Exception:
        cached = None

    pw_db = ''
    try:
        from agent.models import SystemSettings

        ss = SystemSettings.get_solo()
        pw_db = str(getattr(ss, 'default_comm_password', '') or '').strip()
    except Exception:
        pw_db = ''

    pw_env = ''
    try:
        from django.conf import settings as _dj_settings

        pw_env = str(getattr(_dj_settings, 'ZKACCESS_DEFAULT_COMM_PASSWORD', '') or '').strip()
    except Exception:
        pw_env = ''

    eff = pw_db or pw_env
    try:
        cache.set(cache_key, eff, timeout=20)
    except Exception:
        pass
    return eff


def health(request: HttpRequest):
    """Dashboard-friendly liveness endpoint.

    Must remain fast but include enough info for access_dashboard health badges.
    """
    payload: dict[str, Any] = {'ok': True}

    try:
        payload['now'] = timezone.now().isoformat()
    except Exception:
        payload['now'] = ''

    # DB reachability check (best-effort)
    try:
        from agent.models import Device

        Device.objects.only('id').first()
        payload['db'] = {'ok': True}
    except Exception as e:
        payload['db'] = {'ok': False, 'error': str(e)}

    # CommCenter heartbeat (best-effort)
    try:
        import agent.modern_comm_center as mcc

        center = getattr(mcc, 'ACTIVE_CENTER', None)
        if center is not None:
            last = getattr(center.heartbeat_backend, 'get', lambda _k: None)('last_cycle')
            backend = getattr(center, 'driver_name', None) or getattr(center, 'driver', None) or 'commcenter'
            payload['heartbeat'] = {'backend': str(backend), 'last_cycle': last}
    except Exception:
        pass

    # Backup status (best-effort): newest .sql under configured backup dir
    try:
        import configparser
        import pathlib

        base_dir = pathlib.Path(__file__).resolve().parent.parent
        ini = base_dir / 'agent_controller.ini'
        backup_dir = base_dir / 'backups'
        configured = False
        if ini.exists():
            cfg = configparser.ConfigParser()
            cfg.read(ini)
            backup_dir = pathlib.Path(cfg.get('controller', 'backup_path', fallback=str(backup_dir)))
            configured = True

        latest_name = None
        latest_age_min = None
        if backup_dir.exists() and backup_dir.is_dir():
            cand = []
            try:
                cand.extend(list(backup_dir.glob('*.sql')))
                cand.extend(list(backup_dir.glob('*.sql.gz')))
            except Exception:
                cand = []
            if cand:
                newest = max(cand, key=lambda p: p.stat().st_mtime)
                latest_name = newest.name
                try:
                    age_s = max(0.0, float(timezone.now().timestamp() - newest.stat().st_mtime))
                    latest_age_min = int(round(age_s / 60.0))
                except Exception:
                    latest_age_min = None

        payload['backup'] = {
            'configured': bool(configured),
            'latest': latest_name,
            'age_minutes': latest_age_min,
        }
    except Exception:
        pass

    return JsonResponse(payload)


def system_comm_password_save(request: HttpRequest):
    """Save default communication password to SystemSettings (DB-backed)."""
    if not request.user.is_authenticated or not request.user.is_staff:
        return JsonResponse({'ok': False, 'error': 'unauthorized'}, status=403)
    if request.method != 'POST':
        return JsonResponse({'ok': False, 'error': 'method_not_allowed'}, status=405)

    from agent.models import SystemSettings

    new_pw = str(request.POST.get('default_comm_password') or '').strip()
    ss = SystemSettings.get_solo()
    try:
        old_has = bool(str(getattr(ss, 'default_comm_password', '') or '').strip())
    except Exception:
        old_has = False

    ss.default_comm_password = new_pw
    ss.save(update_fields=['default_comm_password', 'updated_at'])

    # Bust cache so probes immediately see the new value.
    try:
        cache.delete('agent:default_comm_password')
    except Exception:
        pass

    _audit_log(
        request,
        module='system',
        action='save_default_comm_password',
        entity_id=1,
        entity_name='SystemSettings',
        details='set' if bool(new_pw) else ('cleared' if old_has else 'noop'),
    )
    return JsonResponse({'ok': True, 'data': {'has_password': bool(new_pw)}})


def metrics(request: HttpRequest):
    # Simple JSON metrics endpoint (human/ops friendly).
    try:
        import agent.modern_comm_center as mcc

        center = getattr(mcc, 'ACTIVE_CENTER', None)
        payload: dict[str, Any] = {
            'ok': True,
            'commcenter_active': bool(center),
        }
        if center:
            payload.update({
                'sessions': len(getattr(center, 'sessions', {}) or {}),
                'total_rtlog_lines': int(getattr(center, 'total_rtlog_lines', 0) or 0),
                'total_event_logs': int(getattr(center, 'total_event_logs', 0) or 0),
            })
        return JsonResponse(payload)
    except Exception as e:
        return JsonResponse({'ok': False, 'error': str(e)}, status=500)


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
        'commcenter_driver': st.get('commcenter_driver'),
        'commcenter_backend': st.get('commcenter_backend'),
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
                ds = _DS.objects.filter(device=dev).order_by('-updated_at', '-id').first()
                created = False
                if ds is None:
                    ds = _DS.objects.create(device=dev, online=True, door_state='')
                    created = True
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
                        ua = ds.updated_at.isoformat() if ds.updated_at else ''
                    except Exception:
                        ua = ''
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
                        ua = ds.updated_at.isoformat() if ds.updated_at else ''
                    except Exception:
                        ua = ''
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


def monitor_rtlog_json(request: HttpRequest):
    """Return recent DeviceRealtimeLog rows for polling-based monitor fallback.

    This endpoint exists so Monitorizare live can still show card scans when
    WebSockets/ASGI are unavailable (e.g., running under Django runserver).
    """
    if not request.user.is_authenticated:
        return JsonResponse({'ok': False, 'error': 'unauth'}, status=403)
    try:
        after_id = int(request.GET.get('after_id') or 0)
    except Exception:
        after_id = 0
    try:
        limit = int(request.GET.get('limit') or 200)
    except Exception:
        limit = 200
    limit = max(1, min(limit, 500))

    if after_id:
        qs = DeviceRealtimeLog.objects.filter(id__gt=after_id).order_by('id')[:limit]
    else:
        # On initial load, return only the newest rows (avoid replaying all history).
        newest = list(DeviceRealtimeLog.objects.order_by('-id')[:limit])
        newest.reverse()
        qs = newest

    rows = []
    last_id = after_id
    for r in qs:
        try:
            created = r.created_at.isoformat() if r.created_at else None
        except Exception:
            created = None
        rows.append({
            'id': r.id,
            'device_id': r.device_id,
            'sn': r.sn or '',
            'raw': r.raw or '',
            'created_at': created,
        })
        last_id = r.id
    return JsonResponse({'ok': True, 'rows': rows, 'last_id': last_id})

def status_summary(request: HttpRequest):
    if not request.user.is_authenticated:
        from django.contrib.auth.views import redirect_to_login
        return redirect_to_login(request.get_full_path())
    from django.db.models import OuterRef, Subquery
    from .models import Device, DeviceStatus as _DS
    latest = _DS.objects.filter(device=OuterRef('pk')).order_by('-updated_at', '-id')
    rows = []
    for dev in Device.objects.order_by('id').annotate(
        latest_online=Subquery(latest.values('online')[:1]),
        latest_door_state=Subquery(latest.values('door_state')[:1]),
        latest_updated_at=Subquery(latest.values('updated_at')[:1]),
    ):
        rows.append({
            'id': dev.id,
            'name': dev.name,
            'serial': dev.serial_number,
            'online': bool(getattr(dev, 'latest_online', False)),
            'door_state': getattr(dev, 'latest_door_state', '') or '',
            'updated_at': getattr(dev, 'latest_updated_at', None),
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
        from django.db.models import OuterRef, Subquery
        from .models import Device, DeviceStatus as _DS
        latest = _DS.objects.filter(device=OuterRef('pk')).order_by('-updated_at', '-id')
        for dev in Device.objects.order_by('id').annotate(
            latest_online=Subquery(latest.values('online')[:1]),
            latest_door_state=Subquery(latest.values('door_state')[:1]),
            latest_updated_at=Subquery(latest.values('updated_at')[:1]),
        ):
            updated = getattr(dev, 'latest_updated_at', None)
            iso = None
            try:
                iso = updated.isoformat() if updated is not None else None
            except Exception:
                iso = None
            out.append({
                'id': dev.id,
                'name': dev.name,
                'serial': dev.serial_number,
                'online': bool(getattr(dev, 'latest_online', False)),
                'door_state': getattr(dev, 'latest_door_state', '') or '',
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
    from django.db.models import Prefetch
    door_qs = Door.objects.exclude(door_number__isnull=True).order_by('door_number', 'name')
    qs = Device.objects.order_by('name').annotate(
        latest_online=Subquery(latest.values('online')[:1]),
        latest_updated_at=Subquery(latest.values('updated_at')[:1])
    ).prefetch_related(Prefetch('door_set', queryset=door_qs, to_attr='prefetched_doors'))
    # Filter: all (default) | controllers | new | readers
    flt = (request.GET.get('filter') or 'all').strip().lower()
    if flt == 'controllers':
        qs = qs.filter(device_type__in=['access_panel','door_controller','two_door_panel','multi_door_panel'], scanner_linked=False)
    elif flt == 'readers':
        qs = qs.filter(scanner_linked=True)
    elif flt == 'new':
        qs = qs.filter(scanner_linked=False).exclude(device_type__in=['access_panel','door_controller','two_door_panel','multi_door_panel'])
    page = _paginate(qs, request)

    # Backfill: ensure displayed controllers have their doors (and refresh preview).
    _ensure_controller_doors_for_devices(getattr(page, 'object_list', []) or [])
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
    ports_raw = (request.GET.get('ports') or '').strip()
    quick = (request.GET.get('quick') or '').strip().lower() in ('1', 'true', 'yes', 'y', 'on')
    probe = (request.GET.get('probe') or '').strip().lower() in ('1', 'true', 'yes', 'y', 'on')
    comm_password = (request.GET.get('comm_password') or '').strip()
    if not comm_password:
        comm_password = _get_default_comm_password_cached()
    
    if not ip:
        return JsonResponse({'ok': False, 'error': 'missing-ip'}, status=400)
    
    def _parse_ports(raw: str) -> list[int]:
        out: list[int] = []
        for part in (raw or '').replace(';', ',').replace(' ', ',').split(','):
            p = part.strip()
            if not p:
                continue
            try:
                n = int(p)
            except Exception:
                continue
            if 1 <= n <= 65535 and n not in out:
                out.append(n)
        return out

    # Backward compatible: `port=` works as before; `ports=` enables a sweep.
    ports: list[int]
    if ports_raw:
        ports = _parse_ports(ports_raw)
        if not ports:
            return JsonResponse({'ok': False, 'error': 'invalid-ports'}, status=400)
    else:
        try:
            port = int(port_str)
            if port < 1 or port > 65535:
                return JsonResponse({'ok': False, 'error': 'invalid-port-range'}, status=400)
        except ValueError:
            return JsonResponse({'ok': False, 'error': 'invalid-port-format'}, status=400)
        ports = [port]
    
    import socket
    import select

    # Prefer known ZKTeco SDK/COMM ports when multiple ports are scanned.
    # If a generic web port (80/443) is open, that does NOT mean plcommpro can connect.
    preferred_ports: list[int] = [14370, 4370, 4371, 4372, 5000, 5001, 6000, 8000, 8080]

    def _tcp_connect_code(ip_addr: str, tcp_port: int, timeout_s: float) -> int:
        """Return a stable connect result code (0=open, else OS error code).

        On Windows, sockets with a timeout can yield WSAEWOULDBLOCK (10035)
        during connect_ex; we resolve that into a final status using select + SO_ERROR.
        """
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            sock.setblocking(False)
            try:
                res = int(sock.connect_ex((ip_addr, int(tcp_port))) or 0)
            except Exception:
                res = -1

            if res == 0:
                return 0

            # In-progress / would-block -> wait for completion.
            if res in (10035, 115, 11):
                try:
                    _r, w, e = select.select([], [sock], [sock], float(timeout_s))
                except Exception:
                    return 10060
                if not w and not e:
                    return 10060
                try:
                    err = int(sock.getsockopt(socket.SOL_SOCKET, socket.SO_ERROR) or 0)
                except Exception:
                    err = -1
                return err

            return res
        finally:
            try:
                sock.close()
            except Exception:
                pass
    
    try:
        open_ports: list[int] = []
        results_by_port: dict[int, int] = {}

        # Keep this snappy; callers may pass multiple ports.
        # Use a slightly longer timeout for preferred ports to reduce false negatives.
        sweep_mode = len(ports) > 1

        # Reorder to probe preferred ports first in sweep mode.
        if sweep_mode:
            ports = [p for p in preferred_ports if p in ports] + [p for p in ports if p not in preferred_ports]

        if sweep_mode and quick:
            base_timeout = 0.18
            preferred_timeout = 0.35
        else:
            base_timeout = 0.45 if sweep_mode else 2.0
            preferred_timeout = 1.2 if sweep_mode else 2.0

        for p in ports:
            try:
                result = _tcp_connect_code(
                    ip,
                    p,
                    preferred_timeout if p in preferred_ports else base_timeout,
                )
                results_by_port[p] = result
                if result == 0:
                    open_ports.append(p)
                    # In quick sweep mode, stop early once we hit a preferred open port,
                    # but only if we are NOT doing a deep probe.
                    # When probe is enabled, we may need to continue scanning because a TCP-open
                    # port might not speak the controller protocol.
                    if sweep_mode and quick and (not probe) and p in preferred_ports:
                        break
            except Exception:
                # treat per-port failures as closed/filtered
                results_by_port[p] = -1

        port_open = bool(open_ports)

        # Choose the best open port: prefer known SDK ports, otherwise fall back to first open.
        best_open: int | None = None
        if open_ports:
            for pp in preferred_ports:
                if pp in open_ports:
                    best_open = pp
                    break
            if best_open is None:
                best_open = open_ports[0]
        else:
            best_open = ports[0] if ports else None

        # Optional deep probe (preferred): try a short plcommpro SDK connect.
        # This is the most reliable signal that our actual driver can talk to the controller.
        probe_ports: list[int] = []
        probe_errors: dict[int, str] = {}
        if probe and open_ports:
            try:
                from agent.plcommpro_bridge import PlcommproConnInfo, connect_only

                # Probe preferred ports first.
                probe_order = [p for p in preferred_ports if p in open_ports] + [p for p in open_ports if p not in preferred_ports]
                for pp in probe_order:
                    try:
                        conn = PlcommproConnInfo(
                            ipaddress=str(ip),
                            ip_port=int(pp),
                            password=str(comm_password or ''),
                            timeout=3000,
                            protocol='TCP',
                        )
                        rr = connect_only(conn, process_timeout_s=6 if quick else 10)
                        if isinstance(rr, dict) and bool(rr.get('ok')):
                            probe_ports.append(int(pp))
                            if quick:
                                break
                        else:
                            # Keep it compact for UI, but include a short reason.
                            rres = rr.get('result') if isinstance(rr, dict) else None
                            rle = rr.get('last_error') if isinstance(rr, dict) else None
                            data = str(rr.get('data') or '') if isinstance(rr, dict) else ''
                            data = data.replace('\r', ' ').replace('\n', ' ').strip()
                            if len(data) > 80:
                                data = data[:80] + '…'
                            note = f"sdk:{rres}" + (f":{rle}" if rle is not None else "")
                            if data:
                                note += f":{data}"
                            probe_errors[int(pp)] = note
                    except Exception as ex:
                        probe_errors[int(pp)] = f"exc:{ex}"
            except Exception:
                pass

        # Pick a best port.
        # - Without probing: best is the best TCP-open port.
        # - With probing: best is ONLY a responding port; if none respond, return null
        #   so callers don't accidentally pick a non-protocol port.
        best_open_port: int | None = best_open
        best_responding_port: int | None = int(probe_ports[0]) if probe_ports else None
        best_port: int | None
        if probe:
            best_port = best_responding_port
        else:
            best_port = best_open_port

        # If we are probing and found TCP-open ports but none respond,
        # and quick sweep was requested, try to complete the sweep for remaining ports
        # so callers can see a full picture (e.g. 4370 refused).
        try:
            if probe and sweep_mode and quick and open_ports and (not probe_ports):
                for p in ports:
                    if p in results_by_port:
                        continue
                    try:
                        result = _tcp_connect_code(
                            ip,
                            p,
                            preferred_timeout if p in preferred_ports else base_timeout,
                        )
                        results_by_port[p] = result
                        if result == 0 and p not in open_ports:
                            open_ports.append(p)
                    except Exception:
                        results_by_port[p] = -1
        except Exception:
            pass

        # Best-effort reason for the primary port (helpful in UI/logs).
        reason = None
        try:
            primary = ports[0] if ports else None
            if primary is not None:
                code = results_by_port.get(primary)
                if code == 0:
                    reason = 'open'
                elif code in (10061, 111):
                    reason = 'refused'
                elif code in (10060, 110):
                    reason = 'timeout'
                elif code in (10065, 113):
                    reason = 'no-route'
                elif code == -1:
                    reason = 'error'
                else:
                    reason = f'connect_ex_{code}'
        except Exception:
            reason = None

        return JsonResponse(
            {
                'ok': True,
                'open': port_open,
                'ip': ip,
                # Backward compatible: callers use `port` as the selected port.
                'port': int(best_port or 0) if best_port is not None else None,
                'best_port': int(best_port or 0) if best_port is not None else None,
                'best_open_port': int(best_open_port or 0) if best_open_port is not None else None,
                'best_responding_port': int(best_responding_port or 0) if best_responding_port is not None else None,
                'requested_ports': ports,
                'open_ports': open_ports,
                'results_by_port': results_by_port,
                'probe': bool(probe),
                'probe_ports': probe_ports,
                'probe_errors': probe_errors,
                'reason': reason,
                'status': 'reachable' if port_open else 'unreachable',
                'message': (
                    (
                        f'Port {best_port} responds ✓'
                        if probe_ports
                        else (f'Port {best_open_port} is OPEN but no controller response ✗' if probe else f'Port {best_open_port} is OPEN ✓')
                    )
                    if port_open
                    else f'Ports {ports} are CLOSED, REFUSED or FILTERED ✗'
                ),
            }
        )
    except socket.gaierror:
        return JsonResponse({
            'ok': True,
            'open': False,
            'ip': ip,
            'port': ports[0] if ports else None,
            'error': 'hostname-resolution-failed'
        })
    except socket.timeout:
        return JsonResponse({
            'ok': True,
            'open': False,
            'ip': ip,
            'port': ports[0] if ports else None,
            'error': 'connection-timeout'
        })
    except Exception as e:
        return JsonResponse({'ok': False, 'error': str(e)}, status=500)


def _probe_device_online_plcommpro(dev: "Device") -> tuple[bool, str]:
    """Best-effort plcommpro probe.

    Returns (ok, note). Designed for UI gating where persisted DeviceStatus may be stale.
    Must stay fast and never raise.
    """
    try:
        ip = (getattr(dev, 'ip_address', '') or '').strip()
        if not ip:
            return (False, 'no-ip')
        try:
            port = int(getattr(dev, 'port', None) or 0) or 4370
        except Exception:
            port = 4370

        comm_password = (getattr(dev, 'comm_password', '') or '').strip()
        if not comm_password:
            comm_password = _get_default_comm_password_cached()

        from agent.plcommpro_bridge import PlcommproConnInfo, connect_only

        conn = PlcommproConnInfo(
            ipaddress=str(ip),
            ip_port=int(port),
            password=str(comm_password or ''),
            timeout=2500,
            protocol='TCP',
        )
        rr = connect_only(conn, process_timeout_s=5)
        if isinstance(rr, dict) and bool(rr.get('ok')):
            return (True, 'ok')

        # Compact reason for logs/UI
        if isinstance(rr, dict):
            rres = rr.get('result')
            rle = rr.get('last_error')
            data = str(rr.get('data') or '')
            data = data.replace('\r', ' ').replace('\n', ' ').strip()
            if len(data) > 80:
                data = data[:80] + '…'
            note = f"sdk:{rres}" + (f":{rle}" if rle is not None else "")
            if data:
                note += f":{data}"
            return (False, note)
        return (False, 'probe-failed')
    except Exception as ex:
        return (False, f"exc:{ex}")


def _latest_device_status_row(dev: "Device"):
    """Return the latest DeviceStatus row for a device (or None).

    Important: DeviceStatus is intentionally NOT unique per device in this project,
    so callers must not use `.first()` without ordering.
    """
    try:
        return DeviceStatus.objects.filter(device=dev).order_by('-updated_at', '-id').first()
    except Exception:
        return None


def _maybe_set_device_online_from_probe(dev: "Device") -> bool:
    """Probe controller and persist DeviceStatus if reachable."""
    try:
        ok, _note = _probe_device_online_plcommpro(dev)
        if not ok:
            return False
        ds = _latest_device_status_row(dev)
        if ds is None:
            ds = DeviceStatus.objects.create(device=dev, online=True, door_state='READY')
            return True
        if not ds.online or not (ds.door_state or ''):
            ds.online = True
            if not (ds.door_state or '').strip():
                ds.door_state = 'READY'
            ds.save(update_fields=['online', 'door_state', 'updated_at'])
        return True
    except Exception:
        return False



def device_firewall_allow(request: HttpRequest):
    """Add a Windows Firewall exception to allow connecting to a device port.

    NOTE: This only changes the local Windows firewall. If the port is blocked by the
    controller itself or by network equipment (switch/router ACL), this will not help.

    POST JSON:
      {"ip":"192.168.1.220","port":4370,"direction":"outbound","protocol":"TCP"}
    """
    if not request.user.is_authenticated:
        return JsonResponse({'ok': False, 'error': 'unauth'}, status=403)

    if request.method != 'POST':
        return JsonResponse({'ok': False, 'error': 'method-not-allowed'}, status=405)

    try:
        body = json.loads(request.body.decode('utf-8') or '{}')
    except Exception:
        return JsonResponse({'ok': False, 'error': 'invalid-json'}, status=400)

    ip = str((body or {}).get('ip') or '').strip()
    if not ip:
        return JsonResponse({'ok': False, 'error': 'missing-ip'}, status=400)

    try:
        port = int((body or {}).get('port') or 4370)
        if port < 1 or port > 65535:
            return JsonResponse({'ok': False, 'error': 'invalid-port-range'}, status=400)
    except Exception:
        return JsonResponse({'ok': False, 'error': 'invalid-port-format'}, status=400)

    direction = str((body or {}).get('direction') or 'outbound').strip().lower()
    if direction not in {'outbound', 'inbound'}:
        direction = 'outbound'

    protocol = str((body or {}).get('protocol') or 'TCP').strip().upper()
    if protocol not in {'TCP', 'UDP'}:
        protocol = 'TCP'

    import platform
    import subprocess

    if platform.system() != 'Windows':
        return JsonResponse({'ok': False, 'error': 'unsupported-platform'}, status=400)

    def _is_admin() -> bool:
        try:
            import ctypes

            return bool(ctypes.windll.shell32.IsUserAnAdmin())
        except Exception:
            return False

    display_name = f'ZKAccessB Allow {protocol} {direction} {port} ({ip})'
    group_name = 'ZKAccessB'

    # Keep rules scoped: outbound -> remote ip/port; inbound -> local port (optional for push/ADMS).
    if direction == 'outbound':
        suggested_ps = (
            f'New-NetFirewallRule -DisplayName "{display_name}" -Group "{group_name}" '
            f'-Direction Outbound -Action Allow -Enabled True -Profile Any -Protocol {protocol} '
            f'-RemoteAddress {ip} -RemotePort {port} | Out-Null'
        )
    else:
        suggested_ps = (
            f'New-NetFirewallRule -DisplayName "{display_name}" -Group "{group_name}" '
            f'-Direction Inbound -Action Allow -Enabled True -Profile Any -Protocol {protocol} '
            f'-LocalPort {port} | Out-Null'
        )

    if not _is_admin():
        return JsonResponse(
            {
                'ok': False,
                'error': 'requires-admin',
                'requires_admin': True,
                'ip': ip,
                'port': port,
                'direction': direction,
                'protocol': protocol,
                'display_name': display_name,
                'suggested_powershell_admin': suggested_ps,
                'hint': (
                    'Rule creation requires an elevated process (Run as Administrator). '
                    'If TCP is still blocked afterwards, the device/network is blocking it.'
                ),
            },
            status=200,
        )

    # Create rule idempotently: only if missing.
    ps_script = (
        f'$n = "{display_name}"; '
        f'$r = Get-NetFirewallRule -DisplayName $n -ErrorAction SilentlyContinue; '
        f'if(-not $r){{ {suggested_ps} }}; '
        f'"OK"'
    )

    try:
        proc = subprocess.run(
            ['powershell', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-Command', ps_script],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            timeout=12,
        )
        out = (proc.stdout or '').strip()
        if proc.returncode != 0:
            return JsonResponse(
                {
                    'ok': False,
                    'error': 'firewall-rule-failed',
                    'ip': ip,
                    'port': port,
                    'direction': direction,
                    'protocol': protocol,
                    'display_name': display_name,
                    'output': out[-2000:],
                    'suggested_powershell_admin': suggested_ps,
                },
                status=200,
            )
        return JsonResponse(
            {
                'ok': True,
                'ip': ip,
                'port': port,
                'direction': direction,
                'protocol': protocol,
                'display_name': display_name,
                'output': out[-2000:],
            },
            status=200,
        )
    except Exception as e:
        return JsonResponse(
            {
                'ok': False,
                'error': f'firewall-rule-exception: {e}',
                'ip': ip,
                'port': port,
                'direction': direction,
                'protocol': protocol,
                'display_name': display_name,
                'suggested_powershell_admin': suggested_ps,
            },
            status=200,
        )


def device_admin_test(request: HttpRequest):
    """Test whether a device is administrable via plcommpro (TCP connect + GetDeviceParam).

    This is the practical next step after UDP discovery: UDP can find devices even when
    the SDK pull port is blocked; administration requires a successful plcommpro Connect.

    Usage:
      /agent/devices/admin-test/?ip=192.168.1.220&port=4370&password=0
    """
    if not request.user.is_authenticated:
        return JsonResponse({'ok': False, 'error': 'unauth'}, status=403)

    # Support GET (legacy) and POST (preferred when sending password).
    ip = ''
    password = ''
    protocol_req = ''
    items = ''
    port = 4370

    if request.method == 'POST':
        try:
            import json

            payload = json.loads((request.body or b'').decode('utf-8') or '{}')
        except Exception:
            payload = {}
        ip = str(payload.get('ip') or '').strip()
        try:
            port = int(str(payload.get('port') or '4370').strip() or '4370')
        except Exception:
            port = 4370
        password = str(payload.get('password') or '').strip()
        items = str(
            payload.get('items')
            or 'IPAddress,NetMask,GATEIPAddress,WebServerURL,~SerialNumber,DeviceName,Product'
        ).strip()
        protocol_req = str(payload.get('protocol') or 'AUTO').strip().upper()
    else:
        ip = (request.GET.get('ip') or '').strip()
        if not ip:
            return JsonResponse({'ok': False, 'error': 'missing-ip'}, status=400)

        try:
            port = int((request.GET.get('port') or '4370').strip() or '4370')
        except Exception:
            port = 4370

        password = str(request.GET.get('password') or '').strip()

        # Keep this lightweight and read-only.
        items = str(
            request.GET.get('items')
            or 'IPAddress,NetMask,GATEIPAddress,WebServerURL,~SerialNumber,DeviceName,Product'
        ).strip()

        protocol_req = str(request.GET.get('protocol') or 'AUTO').strip().upper()
    if protocol_req not in {'TCP', 'UDP', 'AUTO'}:
        protocol_req = 'AUTO'

    # If password not provided, try DB-stored password (in-system devices).
    if not password:
        try:
            dev = Device.objects.filter(ip_address=ip).first()
            if dev and (dev.comm_password or '').strip():
                password = str(dev.comm_password or '').strip()
        except Exception:
            pass

    # Final fallback: a configured default comm password (does not persist to DB).
    if not password:
        password = _get_default_comm_password_cached()

    try:
        from .plcommpro_bridge import PlcommproConnInfo, get_device_options

        attempts: list[dict] = []
        protocols = ['TCP', 'UDP'] if protocol_req == 'AUTO' else [protocol_req]
        for proto in protocols:
            conn = PlcommproConnInfo(
                ipaddress=ip,
                ip_port=int(port or 4370),
                password=password,
                timeout=3000,
                protocol=proto,
            )
            resp = get_device_options(conn, items)
            attempts.append(
                {
                    'protocol': proto,
                    'ok': bool(resp.get('ok')),
                    'result': resp.get('result'),
                    'last_error': resp.get('last_error'),
                    'dll_path_used': resp.get('dll_path_used'),
                }
            )
            if resp.get('ok'):
                return JsonResponse(
                    {
                        'ok': True,
                        'ip': ip,
                        'port': port,
                        'protocol': proto,
                        'items': items,
                        'data': resp.get('data') or '',
                        'result': resp.get('result'),
                        'last_error': resp.get('last_error'),
                        'dll_path_used': resp.get('dll_path_used'),
                        'attempts': attempts,
                    }
                )

        # No protocol worked
        return JsonResponse(
            {
                'ok': False,
                'ip': ip,
                'port': port,
                'protocol': protocol_req,
                'error': 'plcommpro-connect-failed',
                'attempts': attempts,
                'hint': (
                    'Nu s-a putut administra centrala nici pe TCP, nici pe UDP (plcommpro). '
                    'Dacă este vizibilă la UDP discovery dar nu răspunde la Connect, verificați: '
                    'setările de comunicare ale centralei (SDK/COMM port), ACL/firewall de rețea, '
                    'și dacă există un server/ADMS activ care ocupă conexiunea.'
                ),
            },
            status=200,
        )
    except Exception as e:
        return JsonResponse({'ok': False, 'ip': ip, 'port': port, 'error': f'admin-test-exception: {e}'}, status=200)


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
        return JsonResponse({'ok': False, 'error': 'unauth'}, status=403)

    def _normalize_base(base_str: str) -> str:
        base_str = (base_str or '').strip()
        if not base_str:
            return ''
        # Remove /24 or similar if provided
        if '/' in base_str:
            base_str = base_str.split('/')[0]
            # If it's a full IP, strip last octet
            if base_str.count('.') == 3:
                base_str = '.'.join(base_str.split('.')[:3])

        # Validate base format (should be XXX.XXX.XXX or XXX.XXX.XXX.0)
        parts = base_str.split('.')
        if len(parts) == 4 and parts[3] == '0':
            return '.'.join(parts[:3])
        if len(parts) != 3:
            raise ValueError('invalid-base-format')
        return base_str

    def _parse_search_device(raw: str) -> list[dict]:
        """Parse plcommpro.SearchDevice output into a list of dicts.

        Format varies across firmware; we keep this permissive.
        """
        import re

        raw = (raw or '').replace('\x00', '')
        raw = raw.strip()
        if not raw:
            return []

        # Split into records (usually \r\n separated)
        records = [r.strip() for r in re.split(r'[\r\n]+', raw) if r.strip()]
        if len(records) == 1 and raw.count('=') > 4 and ',' in raw and raw.count('IPAddress=') > 1:
            # Some firmwares concatenate without newlines; try a softer split.
            records = [r.strip() for r in re.split(r'(?=\b(?:IP|IPAddress|MAC|SN)=)', raw) if r.strip()]

        key_map = {
            'ip': 'ip',
            'ipaddress': 'ip',
            'sn': 'serial_number',
            'serial': 'serial_number',
            'serialnumber': 'serial_number',
            'mac': 'mac',
            'devicename': 'device_name',
            'device': 'device_name',
            'product': 'product',
            'model': 'model',
            # Common legacy/firmware variants for device type/model
            'devicetype': 'model',
            'devicetypename': 'model',
            'deviceclass': 'model',
            'productname': 'model',
            'devicemodel': 'model',
            'fwversion': 'fw_version',
            'firmware': 'fw_version',
            'commport': 'port',
            'port': 'port',
            'netmask': 'netmask',
            'gateipaddress': 'gateway',
            'gateway': 'gateway',
        }

        out: list[dict] = []
        for rec in records:
            parts = [p.strip() for p in re.split(r'[,;\t]+', rec) if p.strip()]
            kv_raw: dict[str, str] = {}
            for p in parts:
                if '=' not in p:
                    continue
                k, v = p.split('=', 1)
                k = (k or '').strip()
                v = (v or '').strip()
                if not k:
                    continue
                kv_raw[k] = v

            normalized: dict[str, object] = {'raw': rec}
            extras: dict[str, str] = {}
            for k, v in kv_raw.items():
                nk = key_map.get(k.strip().lower())
                if nk:
                    if nk == 'port':
                        try:
                            normalized[nk] = int(str(v).strip() or '0') or None
                        except Exception:
                            normalized[nk] = None
                    else:
                        normalized[nk] = v
                else:
                    extras[k] = v

            # Ensure IP key exists when present in raw
            if not normalized.get('ip'):
                ip_guess = kv_raw.get('IP') or kv_raw.get('IPAddress') or kv_raw.get('ip')
                if ip_guess:
                    normalized['ip'] = ip_guess

            if extras:
                normalized['extra'] = extras

            # If firmware provides Product but no explicit Model, use Product as a fallback label.
            try:
                if not str(normalized.get('model') or '').strip():
                    prod = str(normalized.get('product') or '').strip()
                    if prod:
                        normalized['model'] = prod
            except Exception:
                pass
            out.append(normalized)
        return out

    mode = (request.GET.get('mode') or '').strip().lower()
    base_raw = request.GET.get('base', '').strip()
    base = ''
    if base_raw:
        try:
            base = _normalize_base(base_raw)
        except ValueError:
            return JsonResponse(
                {
                    'ok': False,
                    'error': 'invalid-base-format',
                    'example': '100.51.101 or 192.168.1',
                },
                status=400,
            )

    if mode in ('udp', 'legacy', 'broadcast'):
        try:
            from .plcommpro_bridge import search_device_udp
            # Prefer directed broadcast when user provides a subnet.
            # Many networks block 255.255.255.255 but allow 192.168.1.255.
            addr = f"{base}.255" if base else None
            resp = search_device_udp(address=addr)
        except Exception as e:
            return JsonResponse({'ok': False, 'error': f'udp-discover-failed: {e}'}, status=500)

        if not resp.get('ok'):
            hint = None
            try:
                data_s = str(resp.get('data') or '')
                le = resp.get('last_error')
                if '0x8007000B' in data_s:
                    hint = (
                        'plcommpro.dll are arhitectură greșită (x64 vs x86). '\
                        'Setează ZKACCESS_PLCOMMPRO_DLL către un plcommpro.dll x86 (32-bit).'
                    )
                elif le in (-201, -202, -203, 10013, 10051, 10065):
                    hint = (
                        'UDP broadcast pare blocat (firewall/VPN/subrețea greșită). '\
                        'Încearcă „Scan subrețea (ICMP/TCP)”, verifică PC-ul să fie în aceeași subrețea '\
                        'și permite UDP/4370 în Windows Firewall (Private).'
                    )
                elif data_s:
                    hint = data_s
            except Exception:
                hint = None
            return JsonResponse(
                {
                    'ok': False,
                    'error': 'udp-discover-failed',
                    'result': resp.get('result'),
                    'last_error': resp.get('last_error'),
                    'data': resp.get('data', ''),
                    'hint': hint,
                },
                status=500,
            )

        devices = _parse_search_device(str(resp.get('data') or ''))

        # Infer door capacity (Nr. uși) from model/product strings.
        # NOTE: This is a best-effort inference; for some firmwares SearchDevice is sparse.
        try:
            from agent.door_provisioning import infer_controller_door_capacity

            for d in devices:
                try:
                    model_s = str(d.get('model') or d.get('product') or d.get('device_name') or '').strip()
                    if not model_s:
                        d['doors_capacity'] = None
                        continue
                    tmp = Device(
                        device_type='access_panel',
                        scanner_linked=False,
                        name=model_s,
                        hardware_version=model_s,
                        firmware_version=str(d.get('fw_version') or ''),
                    )
                    cap = int(infer_controller_door_capacity(tmp) or 0)
                    d['doors_capacity'] = cap if cap > 0 else None
                except Exception:
                    d['doors_capacity'] = None
        except Exception:
            # If inference fails for any reason, do not break discovery.
            for d in devices:
                try:
                    d['doors_capacity'] = None
                except Exception:
                    pass

        # Annotate each discovered device with whether it already exists in our system.
        # Legacy UX: if already added, hide the Add button.
        try:
            existing_rows = list(
                Device.objects.filter(ip_address__isnull=False)
                .values('id', 'ip_address', 'serial_number')
            )
            # Also include devices that may have SN but no IP in DB.
            existing_rows += list(
                Device.objects.exclude(serial_number__isnull=True)
                .exclude(serial_number='')
                .values('id', 'ip_address', 'serial_number')
            )

            ip_to_id: dict[str, int] = {}
            sn_to_id: dict[str, int] = {}
            for r in existing_rows:
                try:
                    did = int(r.get('id') or 0)
                except Exception:
                    did = 0
                if not did:
                    continue
                ip_s = str(r.get('ip_address') or '').strip()
                sn_s = str(r.get('serial_number') or '').strip()
                if ip_s and ip_s not in ip_to_id:
                    ip_to_id[ip_s] = did
                if sn_s and sn_s not in sn_to_id:
                    sn_to_id[sn_s] = did
        except Exception:
            ip_to_id = {}
            sn_to_id = {}
        for d in devices:
            try:
                dip = str(d.get('ip') or '').strip()
                dsn = str(d.get('serial_number') or '').strip()
                did = 0
                try:
                    if dip and dip in ip_to_id:
                        did = int(ip_to_id.get(dip) or 0)
                    elif dsn and dsn in sn_to_id:
                        did = int(sn_to_id.get(dsn) or 0)
                except Exception:
                    did = 0

                d['in_system'] = bool(did)
                d['device_id'] = did or None
            except Exception:
                d['in_system'] = False
                d['device_id'] = None
        if base:
            devices = [d for d in devices if str(d.get('ip') or '').startswith(base + '.')]
        ips = sorted({str(d.get('ip') or '').strip() for d in devices if str(d.get('ip') or '').strip()})

        return JsonResponse(
            {
                'ok': True,
                'responsive': ips,
                'devices': devices,
                'base': base,
                'method': 'udp',
                'count': len(ips),
            }
        )

    if not base:
        return JsonResponse({'ok': False, 'error': 'missing-base'}, status=400)
    
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
    
    def tcp_port_scan(ip, ports=[14370, 4370, 8080, 80, 22, 23]):
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
    
    responsive_sorted = sorted(results['responsive'])
    try:
        ip_to_id = {
            str(r.get('ip_address') or '').strip(): int(r.get('id') or 0)
            for r in Device.objects.filter(ip_address__isnull=False)
            .values('id', 'ip_address')
        }
        ip_to_id = {k: v for k, v in ip_to_id.items() if k and v}
    except Exception:
        ip_to_id = {}

    devices = []
    for ip in responsive_sorted:
        did = int(ip_to_id.get(str(ip).strip()) or 0)
        devices.append({'ip': ip, 'in_system': bool(did), 'device_id': did or None})

    # Scan mode does not include model info; keep a stable shape for the frontend.
    for d in devices:
        d['doors_capacity'] = None

    return JsonResponse({
        'ok': True,
        'responsive': responsive_sorted,
        'devices': devices,
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
    def _first(v: object) -> object:
        # Some form-style payloads can contain lists; normalize to first scalar.
        if isinstance(v, list) and v:
            return v[0]
        return v

    def _s(key: str, default: str = '') -> str:
        try:
            v = _first(payload.get(key, default))
            return str(v or '').strip()
        except Exception:
            return str(default or '').strip()

    def _i(key: str, default: int = 0) -> int:
        try:
            v = _first(payload.get(key, default))
            return int(str(v or '').strip() or str(default))
        except Exception:
            return int(default)

    action = _s('action')
    action_norm = str(action or '').strip().lower().replace('-', '_')
    ip = _s('ip')
    if not ip:
        return JsonResponse({'ok': False, 'error': 'missing-ip'}, status=400)
    port = _i('port', 4370) or 4370
    name = _s('name', f'Centrală {ip}') or f'Centrală {ip}'
    serial = _s('serial_number')
    device_id = _first(payload.get('device_id'))

    def _to_bool(v: object) -> bool:
        try:
            if isinstance(v, bool):
                return v
            s = str(v or '').strip().lower()
            return s in ('1', 'true', 'yes', 'y', 'on')
        except Exception:
            return False

    comm_password_present = 'comm_password' in payload
    comm_password = _s('comm_password') if comm_password_present else ''
    clear_on_add_present = 'clear_on_add' in payload
    clear_on_add_flag = _to_bool(_first(payload.get('clear_on_add'))) if clear_on_add_present else False

    # Persist discovered model/type into Device.hardware_version (used across UI and door-capacity heuristics).
    hw_present = ('hardware_version' in payload) or ('model' in payload)
    hw_value = ''
    if hw_present:
        hw_value = _s('hardware_version') or _s('model')

    def _guess_net(ip_str: str) -> tuple[str, str]:
        try:
            import ipaddress

            ip_obj = ipaddress.ip_address((ip_str or '').strip())
            if ip_obj.version != 4:
                return ('', '')
            parts = str(ip_obj).split('.')
            if len(parts) != 4:
                return ('', '')
            gw = '.'.join(parts[:3] + ['254'])
            return (gw, '255.255.255.0')
        except Exception:
            return ('', '')

    try:
        from django.db import IntegrityError

        if action_norm == 'modify_ip_udp':
            target_ip = _s('target_ip') or _s('target') or ip
            mac = _s('mac')
            gateway = _s('gateway')
            subnet_mask = _s('subnet_mask')
            if not mac:
                return JsonResponse({'ok': False, 'error': 'missing-mac'}, status=400)
            if not target_ip:
                return JsonResponse({'ok': False, 'error': 'missing-target-ip'}, status=400)

            guess_gw, guess_mask = _guess_net(target_ip)
            if not subnet_mask:
                subnet_mask = guess_mask
            if not gateway:
                gateway = guess_gw
            if not gateway or not subnet_mask:
                return JsonResponse({'ok': False, 'error': 'missing-gateway-or-netmask'}, status=400)

            try:
                from .plcommpro_bridge import modify_ip_udp

                buf = f"MAC={mac},IPAddress={target_ip},GATEIPAddress={gateway},NetMask={subnet_mask}"
                resp = modify_ip_udp(buf)
                if not resp.get('ok'):
                    return JsonResponse(
                        {
                            'ok': False,
                            'error': 'udp-modify-ip-failed',
                            'result': resp.get('result'),
                            'last_error': resp.get('last_error'),
                        },
                        status=500,
                    )
            except Exception as e:
                return JsonResponse({'ok': False, 'error': f'udp-modify-ip-exception: {e}'}, status=500)

            # IMPORTANT: Do NOT auto-add devices to DB when doing IP change from discovery.
            # Only update an existing in-system device record if we can match it.
            dev = None
            if device_id:
                try:
                    dev = Device.objects.filter(pk=int(str(device_id).strip())).first()
                except Exception:
                    dev = None
            if not dev and serial:
                dev = Device.objects.filter(serial_number=serial).first()
            if not dev:
                dev = Device.objects.filter(ip_address=ip).first()

            updated = False
            if dev:
                old_ip_db = dev.ip_address
                dev.ip_address = target_ip
                dev.port = port
                if name:
                    dev.name = name
                if serial:
                    dev.serial_number = serial
                if comm_password_present and (comm_password or not (dev.comm_password or '').strip()):
                    dev.comm_password = comm_password
                if clear_on_add_present:
                    dev.clear_on_add = clear_on_add_flag
                # Persist network fields if present on model.
                if hasattr(dev, 'gateway'):
                    setattr(dev, 'gateway', gateway)
                if hasattr(dev, 'subnet_mask'):
                    setattr(dev, 'subnet_mask', subnet_mask)
                try:
                    update_fields = ['ip_address', 'port', 'name', 'serial_number']
                    if comm_password_present:
                        update_fields.append('comm_password')
                    if clear_on_add_present:
                        update_fields.append('clear_on_add')
                    if hasattr(dev, 'gateway'):
                        update_fields.append('gateway')
                    if hasattr(dev, 'subnet_mask'):
                        update_fields.append('subnet_mask')
                    dev.save(update_fields=update_fields)
                    updated = True
                except IntegrityError as e:
                    return JsonResponse(
                        {
                            'ok': False,
                            'hardware_ok': True,
                            'error': 'db-conflict',
                            'hint': (
                                'IP-ul a fost schimbat pe centrală, dar baza de date are deja un dispozitiv cu acest IP. '
                                'Repornește scanarea și rezolvă conflictul (șterge/unește înregistrările duplicate).'
                            ),
                            'details': str(e),
                            'ip': target_ip,
                        },
                        status=200,
                    )

                _audit_log(
                    request,
                    module='device',
                    action='update',
                    entity_id=dev.id,
                    entity_name=getattr(dev, 'name', '') or '',
                    details=f"udp_modify_ip mac={mac} {old_ip_db} -> {target_ip} gw={gateway} mask={subnet_mask}",
                )
            else:
                _audit_log(
                    request,
                    module='device',
                    action='hardware_only',
                    entity_id=0,
                    entity_name='',
                    details=f"udp_modify_ip mac={mac} {ip} -> {target_ip} gw={gateway} mask={subnet_mask}",
                )

            return JsonResponse({'ok': True, 'ip': target_ip, 'updated': bool(updated), **({'id': dev.id} if dev else {})})

        if action_norm == 'change_ip':
            target_ip = _s('target_ip') or ip
            gateway = _s('gateway')
            subnet_mask = _s('subnet_mask')
            dev = None
            if device_id:
                try:
                    dev = Device.objects.filter(pk=int(str(device_id).strip())).first()
                except Exception:
                    dev = None
            if not dev and serial:
                dev = Device.objects.filter(serial_number=serial).first()
            if not dev:
                dev = Device.objects.filter(ip_address=ip).first()

            # Guess defaults early (legacy screenshot: /24 + gateway .254)
            guess_gw, guess_mask = _guess_net(target_ip or ip)
            if not subnet_mask:
                subnet_mask = guess_mask
            if not gateway:
                gateway = guess_gw
            if not gateway or not subnet_mask:
                return JsonResponse({'ok': False, 'error': 'missing-gateway-or-netmask'}, status=400)

            # Push the change to the hardware first (legacy behavior: SET OPTION ...)
            try:
                from .plcommpro_bridge import PlcommproConnInfo, set_device_options

                pw = ''
                if comm_password_present:
                    pw = str(comm_password or '').strip()
                if (not pw) and dev and (dev.comm_password or '').strip():
                    pw = str(dev.comm_password or '').strip()
                conn = PlcommproConnInfo(
                    ipaddress=str(ip),
                    ip_port=int(port or 4370),
                    password=pw,
                    timeout=3000,
                )
                items = f"IPAddress={target_ip},GATEIPAddress={gateway},NetMask={subnet_mask}"
                hw = set_device_options(conn, items)
                if not hw.get('ok'):
                    return JsonResponse(
                        {
                            'ok': False,
                            'error': 'hardware-change-ip-failed',
                            'result': hw.get('result'),
                            'last_error': hw.get('last_error'),
                        },
                        status=500,
                    )
            except Exception as e:
                return JsonResponse({'ok': False, 'error': f'hardware-change-ip-exception: {e}'}, status=500)

            updated = False
            if dev:
                dev.ip_address = target_ip
                dev.port = port
                if name:
                    dev.name = name
                if serial:
                    dev.serial_number = serial
                if comm_password_present and (comm_password or not (dev.comm_password or '').strip()):
                    dev.comm_password = comm_password
                if clear_on_add_present:
                    dev.clear_on_add = clear_on_add_flag
                if hasattr(dev, 'gateway'):
                    setattr(dev, 'gateway', gateway)
                if hasattr(dev, 'subnet_mask'):
                    setattr(dev, 'subnet_mask', subnet_mask)
                try:
                    update_fields = ['ip_address', 'port', 'name', 'serial_number']
                    if comm_password_present:
                        update_fields.append('comm_password')
                    if clear_on_add_present:
                        update_fields.append('clear_on_add')
                    if hasattr(dev, 'gateway'):
                        update_fields.append('gateway')
                    if hasattr(dev, 'subnet_mask'):
                        update_fields.append('subnet_mask')
                    dev.save(update_fields=update_fields)
                    updated = True
                except IntegrityError as e:
                    return JsonResponse(
                        {
                            'ok': False,
                            'hardware_ok': True,
                            'error': 'db-conflict',
                            'hint': (
                                'IP-ul a fost schimbat pe centrală, dar baza de date are deja un dispozitiv cu acest IP. '
                                'Repornește scanarea și rezolvă conflictul (șterge/unește înregistrările duplicate).'
                            ),
                            'details': str(e),
                            'ip': target_ip,
                        },
                        status=200,
                    )

            _audit_log(
                request,
                module='device',
                action='update',
                entity_id=dev.id,
                entity_name=getattr(dev, 'name', '') or '',
                details=f"change_ip {ip} -> {target_ip} port={port} gw={gateway} mask={subnet_mask}",
            )
            try:
                from legacy_models.models import Device as LegacyDevice  # type: ignore
                legacy = LegacyDevice.objects.filter(sn=dev.serial_number or dev.name).first()
                if legacy:
                    legacy.com_address = target_ip
                    legacy.save(update_fields=['com_address'])
            except Exception:
                pass
            if dev:
                return JsonResponse({'ok': True, 'id': dev.id, 'ip': target_ip, 'updated': bool(updated)})
            return JsonResponse({'ok': True, 'ip': target_ip, 'updated': False})

        # Only explicit add/update operations are allowed to touch DB records.
        # Safety: do NOT auto-add devices for unknown/empty actions.
        if action_norm not in ('add', 'update'):
            return JsonResponse({'ok': False, 'error': f'unknown-action:{action_norm or "(empty)"}'}, status=400)

        # Add/update: create or update existing device by IP/serial
        dev, created = Device.objects.get_or_create(
            ip_address=ip,
            defaults={
                'name': name,
                'serial_number': serial or name,
                'port': port,
                'device_type': 'access_panel',
                'comm_mode': 'tcp',
                'enabled': True,
                **({'hardware_version': hw_value} if (hw_present and hw_value) else {}),
                **({'comm_password': comm_password} if comm_password_present else {}),
                **({'clear_on_add': clear_on_add_flag} if clear_on_add_present else {}),
            }
        )
        if not created:
            dev.name = name or dev.name
            if serial:
                dev.serial_number = serial
            dev.port = port
            dev.enabled = True
            if hw_present and hw_value:
                dev.hardware_version = hw_value
            if comm_password_present and (comm_password or not (dev.comm_password or '').strip()):
                dev.comm_password = comm_password
            if clear_on_add_present:
                dev.clear_on_add = clear_on_add_flag
            update_fields = ['name','serial_number','port','enabled']
            if hw_present and hw_value:
                update_fields.append('hardware_version')
            if comm_password_present:
                update_fields.append('comm_password')
            if clear_on_add_present:
                update_fields.append('clear_on_add')
            dev.save(update_fields=update_fields)

        # Ensure a status row exists immediately after adding/updating a controller,
        # so door allocation/actions won't fail with device-status-missing.
        try:
            from agent.models import DeviceStatus as _DS

            _DS.objects.get_or_create(device=dev)
        except Exception:
            pass

        # Best-effort: if the controller responds to our SDK probe, mark ONLINE now.
        # This avoids the common "all offline" state right after discovery/import.
        try:
            _maybe_set_device_online_from_probe(dev)
        except Exception:
            pass

        # Legacy option: "Clear Data in the Device when Adding".
        # Semantics in legacy iAccess/ZKAccess: clear device data except the event log.
        # We implement this by deleting key non-event tables.
        clear_ok = None
        clear_error = ''
        clear_warning = ''
        if action_norm == 'add' and clear_on_add_present and clear_on_add_flag:
            # Never block the HTTP request on SDK delete operations.
            # Queue a command for CommCenter to execute asynchronously.
            clear_ok = False
            try:
                row = CommandLog.objects.create(device=dev, command='CLEAR_DEVICE_DATA', status='PENDING')
                clear_ok = True
                clear_warning = f"queued:{row.id}"
            except Exception as e:
                clear_ok = False
                clear_error = f"queue_failed:{e}"

        # Time zone policy:
        # - Controllers: keep their configured TZ; default to system TZ only if empty.
        # - Reader devices (scanner-linked): always inherit system TZ.
        try:
            from agent.models import SystemSettings

            tz_name = (SystemSettings.get_solo().time_zone or '').strip()
            if tz_name:
                if getattr(dev, 'scanner_linked', False):
                    if (dev.time_zone or '').strip() != tz_name:
                        dev.time_zone = tz_name
                        dev.save(update_fields=['time_zone'])
                else:
                    if not (dev.time_zone or '').strip():
                        dev.time_zone = tz_name
                        dev.save(update_fields=['time_zone'])
        except Exception:
            pass

        # Auto-provision doors for controllers (1..N) based on type/model.
        prov = None
        try:
            from agent.door_provisioning import ensure_controller_doors

            prov = ensure_controller_doors(dev)
        except Exception:
            prov = None

        _audit_log(
            request,
            module='device',
            action=('create' if created else 'update'),
            entity_id=dev.id,
            entity_name=getattr(dev, 'name', '') or '',
            details=f"discover_apply action={action_norm} ip={ip} port={port} sn={getattr(dev, 'serial_number', '')}",
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

        resp = {'ok': True, 'id': dev.id, 'ip': dev.ip_address, 'created': created}
        if clear_ok is not None:
            resp['clear_ok'] = bool(clear_ok)
            if clear_error:
                resp['clear_error'] = clear_error
            if clear_warning:
                resp['clear_warning'] = clear_warning
        if prov is not None:
            resp['door_capacity'] = getattr(prov, 'capacity', None)
            resp['doors_created'] = getattr(prov, 'created', None)
        return JsonResponse(resp)
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

    # System time zone (used as default + enforced for reader devices).
    system_tz = ''
    system_now_local_str = ''
    try:
        from agent.models import SystemSettings
        from django.utils import timezone

        system_tz = (SystemSettings.get_solo().time_zone or '').strip()
        try:
            system_now_local_str = timezone.localtime(timezone.now()).strftime('%Y-%m-%d %H:%M:%S')
        except Exception:
            system_now_local_str = ''
    except Exception:
        system_tz = ''
        system_now_local_str = ''

    if request.method == 'POST':
        post_data = request.POST
        # For reader devices (ELATEC/APC), force device TZ to system TZ.
        try:
            is_reader = (request.POST.get('scanner_linked') or '').strip().lower() in ('1', 'true', 'yes', 'on')
            if is_reader and system_tz:
                post_data = request.POST.copy()
                post_data['time_zone'] = system_tz
        except Exception:
            post_data = request.POST

        form = DeviceExtendedForm(post_data)
        try:
            dt = (post_data.get('device_type') or '').strip()
            sl = (post_data.get('scanner_linked') or '').strip().lower() in ('1', 'true', 'yes', 'on')
            show_derived_doors = (dt in ('access_panel', 'door_controller', 'two_door_panel', 'multi_door_panel')) and (not sl)
        except Exception:
            show_derived_doors = True
        if form.is_valid():
            obj = form.save()
            # Safety: enforce system TZ for scanners even if the form allowed values.
            try:
                if getattr(obj, 'scanner_linked', False) and system_tz and (obj.time_zone or '').strip() != system_tz:
                    obj.time_zone = system_tz
                    obj.save(update_fields=['time_zone'])
            except Exception:
                pass
            try:
                from agent.door_provisioning import ensure_controller_doors

                ensure_controller_doors(obj)
            except Exception:
                pass

            # Note: do NOT auto-seed "Implicit" access levels. Levels are user-defined.
            # Ensure a baseline status row exists so list UIs don't render OFFLINE on first load.
            try:
                from agent.models import DeviceStatus

                if not DeviceStatus.objects.filter(device=obj).exists():
                    DeviceStatus.objects.create(device=obj, online=True, door_state='CLOSED')
            except Exception:
                pass
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
                        'system_time_zone': system_tz,
                        'system_time_now_local': system_now_local_str,
                        'access_modal': True,
                        'controller_doors': [],
                        'show_derived_doors': show_derived_doors,
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
            return render(request,'agent/device_form.html',{'form': form, 'system_time_zone': system_tz, 'system_time_now_local': system_now_local_str})
    else:
        form = DeviceExtendedForm(initial=({'time_zone': system_tz} if system_tz else {}))
        show_derived_doors = True
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
                    'system_time_zone': system_tz,
                    'system_time_now_local': system_now_local_str,
                    'access_modal': True,
                    'controller_doors': [],
                    'show_derived_doors': show_derived_doors,
                },
            )
    return render(request,'agent/device_form.html',{'form': form, 'next_url': _safe_return_url(), 'system_time_zone': system_tz, 'system_time_now_local': system_now_local_str})

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

    show_derived_doors = False
    try:
        show_derived_doors = bool(obj.is_controller())
    except Exception:
        show_derived_doors = False

    # System time zone (enforced for reader devices).
    system_tz = ''
    system_now_local_str = ''
    try:
        from agent.models import SystemSettings
        from django.utils import timezone

        system_tz = (SystemSettings.get_solo().time_zone or '').strip()
        try:
            system_now_local_str = timezone.localtime(timezone.now()).strftime('%Y-%m-%d %H:%M:%S')
        except Exception:
            system_now_local_str = ''
    except Exception:
        system_tz = ''
        system_now_local_str = ''

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
        post_data = request.POST
        # For reader devices (ELATEC/APC), force device TZ to system TZ.
        try:
            is_reader = (request.POST.get('scanner_linked') or '').strip().lower() in ('1', 'true', 'yes', 'on')
            if is_reader and system_tz:
                post_data = request.POST.copy()
                post_data['time_zone'] = system_tz
        except Exception:
            post_data = request.POST

        form = DeviceExtendedForm(post_data, instance=obj)
        if form.is_valid():
            saved = form.save()
            # Safety: enforce system TZ for scanners even if the form allowed values.
            try:
                if getattr(saved, 'scanner_linked', False) and system_tz and (saved.time_zone or '').strip() != system_tz:
                    saved.time_zone = system_tz
                    saved.save(update_fields=['time_zone'])
            except Exception:
                pass
            try:
                from agent.door_provisioning import ensure_controller_doors

                ensure_controller_doors(saved)
            except Exception:
                pass

            # Note: do NOT auto-seed "Implicit" access levels. Levels are user-defined.
            # Ensure a baseline status row exists (some UIs render OFFLINE if none exists).
            try:
                from agent.models import DeviceStatus

                if not DeviceStatus.objects.filter(device=saved).exists():
                    DeviceStatus.objects.create(device=saved, online=True, door_state='CLOSED')
            except Exception:
                pass
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

                controller_doors = []
                try:
                    from agent.door_provisioning import ensure_controller_doors

                    ensure_controller_doors(obj)
                    try:
                        from django.db.models import F

                        _door_order = [F('door_number').asc(nulls_last=True), 'name']
                    except Exception:
                        _door_order = ['door_number', 'name']
                    from agent.models import Door

                    controller_doors = list(Door.objects.filter(device=obj).order_by(*_door_order))
                except Exception:
                    controller_doors = []

                errors = {k: v[0] if v else '' for k, v in form.errors.items()}
                html = render_to_string(
                    'agent/device_form_modal.html',
                    {
                        'form': form,
                        'obj': obj,
                        'action_url': request.path,
                        'next_url': _safe_return_url(),
                        'mode': 'edit',
                        'system_time_zone': system_tz,
                        'system_time_now_local': system_now_local_str,
                        'access_modal': True,
                        'controller_doors': controller_doors,
                        'show_derived_doors': show_derived_doors,
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
            controller_doors = []
            try:
                from agent.door_provisioning import ensure_controller_doors

                ensure_controller_doors(obj)
                try:
                    from django.db.models import F

                    _door_order = [F('door_number').asc(nulls_last=True), 'name']
                except Exception:
                    _door_order = ['door_number', 'name']
                from agent.models import Door

                controller_doors = list(Door.objects.filter(device=obj).order_by(*_door_order))
            except Exception:
                controller_doors = []
            return render(
                request,
                'agent/device_form_modal.html',
                {
                    'form': form,
                    'obj': obj,
                    'action_url': request.path,
                    'next_url': _safe_return_url(),
                    'mode': 'edit',
                    'system_time_zone': system_tz,
                    'system_time_now_local': system_now_local_str,
                    'access_modal': True,
                    'controller_doors': controller_doors,
                    'show_derived_doors': show_derived_doors,
                },
            )
    # For controller devices, show the derived/provisioned doors in the form UI.
    controller_doors = []
    try:
        from agent.door_provisioning import ensure_controller_doors

        ensure_controller_doors(obj)
        from agent.models import Door

        controller_doors = list(Door.objects.filter(device=obj).exclude(door_number__isnull=True).order_by('door_number'))
    except Exception:
        controller_doors = []

    return render(
        request,
        'agent/device_form.html',
        {
            'form': form,
            'obj': obj,
            'next_url': _safe_return_url(),
            'controller_doors': controller_doors,
            'system_time_zone': system_tz,
            'system_time_now_local': system_now_local_str,
            'show_derived_doors': show_derived_doors,
        },
    )

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
    # For the dashboard page-render we use persisted values from the DB.
    # - Device.last_contact: liveness/heartbeat (updated during successful communication)
    # - DeviceStatus.updated_at: state-change timestamp (online/door_state changes)

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
        # Serialize 'last seen' as ISO string for client-side JSON script.
        # Prefer Device.last_contact (heartbeat). Fall back to DeviceStatus.updated_at.
        ua_iso = None
        try:
            last_seen = getattr(dev, 'last_contact', None) or getattr(ds, 'updated_at', None)
            ua_iso = last_seen.isoformat() if last_seen is not None else None
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

    # Build door payload with cached lock state fallback.
    # Exclude orphan/unassigned Door rows (device is NULL) from live dashboard,
    # because they are not actionable and confuse operators (they show up as "Ușă/USA").
    doors = []
    door_qs = Door.objects.select_related('device').exclude(device__isnull=True).exclude(door_number__isnull=True).all()

    # Preload latest DeviceStatus per device (avoid N+1 and avoid OPEN when offline)
    dev_ids = [getattr(getattr(d, 'device', None), 'id', None) for d in door_qs]
    dev_ids = [i for i in dev_ids if i is not None]
    status_map = {}
    if dev_ids:
        for ds in DeviceStatus.objects.filter(device_id__in=dev_ids).order_by('device_id', '-updated_at', '-id'):
            if ds.device_id not in status_map:
                status_map[ds.device_id] = ds

    for d in door_qs:
        dev = getattr(d, 'device', None)
        dev_id = getattr(dev, 'id', None) if dev else None
        ds = status_map.get(dev_id)
        try:
            setattr(d, '__device_online', bool(ds.online) if ds is not None else False)
        except Exception:
            pass

        state = _door_state_from_cache_or_model(d)
        doors.append({
            'id': d.id,
            'name': d.name,
            'device_id': dev_id,
            'device__name': getattr(dev, 'name', None) if dev else None,
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

    latest = _DS.objects.filter(device=OuterRef('pk')).order_by('-updated_at', '-id')
    qs = Device.objects.order_by('name').annotate(
        latest_online=Subquery(latest.values('online')[:1]),
        latest_door_state=Subquery(latest.values('door_state')[:1]),
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

    # Backfill: ensure displayed controllers have Door rows and attach a fresh preview.
    try:
        _ensure_controller_doors_for_devices(getattr(devices_page, 'object_list', []) or [])
    except Exception:
        pass

    # Lightweight device index for UI actions (e.g., SYNC)
    device_index_json = '{}'
    try:
        import json

        idx = {}
        for d in Device.objects.all().only('id', 'name', 'device_type', 'scanner_linked', 'ip_address', 'port', 'serial_number'):
            try:
                is_phys = bool(d.is_physical_controller())
            except Exception:
                is_phys = False
            idx[int(d.id)] = {
                'name': str(getattr(d, 'name', '') or ''),
                'is_physical': bool(is_phys),
            }
        device_index_json = json.dumps(idx, ensure_ascii=False)
    except Exception:
        device_index_json = '{}'

    # Preload status summary for Monitorizare dispozitive tab (latest-per-device)
    status_rows = []
    try:
        for dev in Device.objects.order_by('name').annotate(
            latest_online=Subquery(latest.values('online')[:1]),
            latest_door_state=Subquery(latest.values('door_state')[:1]),
            latest_updated_at=Subquery(latest.values('updated_at')[:1]),
        ):
            try:
                is_phys = bool(dev.is_physical_controller())
            except Exception:
                is_phys = False
            status_rows.append({
                'id': dev.id,
                'name': dev.name,
                'serial': dev.serial_number,
                'online': bool(getattr(dev, 'latest_online', False)),
                'door_state': getattr(dev, 'latest_door_state', '') or '',
                'updated_at': getattr(dev, 'latest_updated_at', None),
                'is_physical': bool(is_phys),
            })
    except Exception:
        status_rows = []
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
        'device_index_json': device_index_json,
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


def system_options(request: HttpRequest):
    """Legacy-like System Options (global settings).

    Currently exposes the system-wide time zone.
    """
    if not request.user.is_authenticated or not request.user.is_staff:
        from django.contrib.auth.views import redirect_to_login

        return redirect_to_login(request.get_full_path())

    from django.utils import timezone

    msg = ''
    error = ''
    try:
        from agent.models import SystemSettings

        settings_obj = SystemSettings.get_solo()
    except Exception as ex:
        settings_obj = None
        error = f"Settings unavailable: {ex}"

    tz_choices = []
    try:
        from agent.tz_utils import build_time_zone_choice_tuples

        tz_choices = build_time_zone_choice_tuples()
    except Exception:
        tz_choices = []

    if request.method == 'POST' and settings_obj is not None:
        tz_name = (request.POST.get('time_zone') or '').strip()
        if not tz_name:
            error = 'Time zone is required.'
        else:
            try:
                from zoneinfo import ZoneInfo

                ZoneInfo(tz_name)
            except Exception:
                error = 'Invalid time zone. Example: Europe/Bucharest'
            if not error:
                settings_obj.time_zone = tz_name
                try:
                    settings_obj.save(update_fields=['time_zone', 'updated_at'])
                    msg = 'Saved.'
                except Exception as ex:
                    error = str(ex)

    try:
        now_utc = timezone.now()
        now_local = timezone.localtime(now_utc)
    except Exception:
        now_utc = None
        now_local = None

    return render(
        request,
        'agent/system_options.html',
        {
            'settings': settings_obj,
            'msg': msg,
            'error': error,
            'now_utc': now_utc,
            'now_local': now_local,
            'active_tz': getattr(timezone.get_current_timezone(), 'key', None) or str(timezone.get_current_timezone()),
            'tz_choices': tz_choices,
        },
    )


def system_set_time_modal(request: HttpRequest):
    """Modal: queue a SYNC_TIME command to all enabled devices.

    Note: This does not change the server/OS clock; it synchronizes equipment time.
    """
    if not request.user.is_authenticated or not request.user.is_staff:
        return JsonResponse({'ok': False, 'error': 'unauthorized'}, status=403)

    from django.utils import timezone
    from django.utils.dateparse import parse_datetime

    def _coerce_to_utc(dt_any):
        try:
            if timezone.is_naive(dt_any):
                dt_any = timezone.make_aware(dt_any, timezone.get_current_timezone())
            return dt_any.astimezone(timezone.utc)
        except Exception:
            try:
                return dt_any
            except Exception:
                return None

    def _sync_time_cmd_for_device(dev, dt_utc):
        try:
            from zoneinfo import ZoneInfo

            tz_name = (getattr(dev, 'time_zone', '') or '').strip()
            if tz_name:
                tz = ZoneInfo(tz_name)
                dt_local = dt_utc.astimezone(tz)
            else:
                dt_local = timezone.localtime(dt_utc)
        except Exception:
            dt_local = timezone.localtime(dt_utc)
        try:
            ts_local = dt_local.strftime('%Y-%m-%d %H:%M:%S')
        except Exception:
            ts_local = ''
        return (f"SYNC_TIME:{ts_local}" if ts_local else "SYNC_TIME")[:240]

    if request.method == 'POST':
        dt_str = (request.POST.get('local_datetime') or '').strip()
        if not dt_str:
            return JsonResponse({'ok': False, 'error': 'validation', 'errors': {'local_datetime': ['required']}}, status=400)

        dt = parse_datetime(dt_str)
        if dt is None:
            try:
                from datetime import datetime

                dt = datetime.fromisoformat(dt_str)
            except Exception:
                dt = None

        if dt is None:
            return JsonResponse({'ok': False, 'error': 'validation', 'errors': {'local_datetime': ['invalid']}}, status=400)

        dt_utc = _coerce_to_utc(dt)
        if dt_utc is None:
            return JsonResponse({'ok': False, 'error': 'validation', 'errors': {'local_datetime': ['invalid']}}, status=400)

        from agent.models import CommandLog, Device

        queued = 0
        for dev in Device.objects.filter(enabled=True).order_by('id'):
            try:
                cmd = _sync_time_cmd_for_device(dev, dt_utc)
                log = CommandLog.objects.create(device=dev, command=cmd, status='PENDING')
                _broadcast_command(log)
                queued += 1
            except Exception:
                continue

        _audit_log(
            request,
            module='system-time',
            action='sync_time',
            entity_id=0,
            entity_name='SYNC_TIME',
            details=f"local_input={dt_str} devices={queued}",
        )

        return JsonResponse({'ok': True, 'queued': queued})

    # GET
    now_local = timezone.localtime(timezone.now())
    try:
        now_local_input = now_local.strftime('%Y-%m-%dT%H:%M')
    except Exception:
        now_local_input = ''

    tz_key = ''
    try:
        tz_key = getattr(timezone.get_current_timezone(), 'key', None) or str(timezone.get_current_timezone())
    except Exception:
        tz_key = ''

    return render(
        request,
        'agent/system_set_time_modal.html',
        {
            'now_local_input': now_local_input,
            'tz_key': tz_key,
        },
    )


def system_devices_sync_now(request: HttpRequest):
    """Quick sync: queue SYNC_TIME using NOW for each device's configured TZ."""
    # Allow GET to avoid CSRF issues for simple actions in legacy-style UI.
    if not request.user.is_authenticated or not request.user.is_staff or request.method not in ('POST', 'GET'):
        return JsonResponse({'ok': False, 'error': 'unauthorized'}, status=403)

    from django.utils import timezone
    from agent.models import CommandLog, Device

    dt_utc = timezone.now().astimezone(timezone.utc)

    def _cmd_for_dev(dev):
        try:
            from zoneinfo import ZoneInfo

            tz_name = (getattr(dev, 'time_zone', '') or '').strip()
            if tz_name:
                dt_local = dt_utc.astimezone(ZoneInfo(tz_name))
            else:
                dt_local = timezone.localtime(dt_utc)
        except Exception:
            dt_local = timezone.localtime(dt_utc)
        try:
            ts_local = dt_local.strftime('%Y-%m-%d %H:%M:%S')
        except Exception:
            ts_local = ''
        return (f"SYNC_TIME:{ts_local}" if ts_local else "SYNC_TIME")[:240]

    queued = 0
    for dev in Device.objects.filter(enabled=True).order_by('id'):
        try:
            log = CommandLog.objects.create(device=dev, command=_cmd_for_dev(dev), status='PENDING')
            _broadcast_command(log)
            queued += 1
        except Exception:
            continue

    _audit_log(
        request,
        module='system-time',
        action='sync_now',
        entity_id=0,
        entity_name='SYNC_TIME',
        details=f"devices={queued}",
    )
    return JsonResponse({'ok': True, 'queued': queued})


def system_device_sync_now(request: HttpRequest, pk: int):
    """Sync a single device now, using its configured TZ."""
    # Allow GET to avoid CSRF issues for simple actions in legacy-style UI.
    if not request.user.is_authenticated or not request.user.is_staff or request.method not in ('POST', 'GET'):
        return JsonResponse({'ok': False, 'error': 'unauthorized'}, status=403)

    from django.utils import timezone
    from agent.models import CommandLog, Device

    dev = Device.objects.filter(pk=pk).first()
    if not dev:
        return JsonResponse({'ok': False, 'error': 'not-found'}, status=404)

    dt_utc = timezone.now().astimezone(timezone.utc)
    try:
        from zoneinfo import ZoneInfo

        tz_name = (getattr(dev, 'time_zone', '') or '').strip()
        if tz_name:
            dt_local = dt_utc.astimezone(ZoneInfo(tz_name))
        else:
            dt_local = timezone.localtime(dt_utc)
    except Exception:
        dt_local = timezone.localtime(dt_utc)

    try:
        ts_local = dt_local.strftime('%Y-%m-%d %H:%M:%S')
    except Exception:
        ts_local = ''

    cmd = (f"SYNC_TIME:{ts_local}" if ts_local else "SYNC_TIME")[:240]
    try:
        log = CommandLog.objects.create(device=dev, command=cmd, status='PENDING')
        _broadcast_command(log)
    except Exception as ex:
        return JsonResponse({'ok': False, 'error': str(ex)}, status=400)

    _audit_log(
        request,
        module='system-time',
        action='sync_device_now',
        entity_id=int(dev.id),
        entity_name=getattr(dev, 'name', '') or dev.serial_number or str(dev.id),
        details=f"tz={(getattr(dev, 'time_zone', '') or '').strip()} cmd={cmd}",
    )
    return JsonResponse({'ok': True})


@ensure_csrf_cookie
def menu_system(request: HttpRequest):
    """System module: Administrare / Grupuri / Fus Orar / Loguri."""
    if not request.user.is_authenticated or not request.user.is_staff:
        from django.contrib.auth.views import redirect_to_login

        return redirect_to_login(request.get_full_path())

    from django.contrib.auth.models import Group, User
    from django.utils import timezone

    from agent.forms import (
        ROLE_ADMIN,
        ROLE_SUPER_ADMIN,
        ROLE_USER,
        ROLE_VISITOR,
        ROLE_GROUP_PREFIX,
        SystemGroupForm,
        SystemUserForm,
        TimeZoneSettingForm,
    )

    from agent.models import AuditLog, Device, SystemSettings
    try:
        from agent.models import TimeZoneSetting
    except Exception:
        TimeZoneSetting = None  # type: ignore

    # UI prefs + sync limits (stored in SystemSettings)
    ui_date_format = 'ro_short'
    ui_week_start = 'monday'
    sync_limits = None
    default_comm_password_db = ''
    default_comm_password_env = ''
    default_comm_password_effective = ''
    default_comm_password_source = ''
    try:
        ss = SystemSettings.get_solo()
        ui_date_format = (getattr(ss, 'date_format', '') or '').strip() or 'ro_short'
        ui_week_start = (getattr(ss, 'week_start', '') or '').strip() or 'monday'
        default_comm_password_db = str(getattr(ss, 'default_comm_password', '') or '').strip()
        try:
            from django.conf import settings as _dj_settings

            default_comm_password_env = str(getattr(_dj_settings, 'ZKACCESS_DEFAULT_COMM_PASSWORD', '') or '').strip()
        except Exception:
            default_comm_password_env = ''

        # DB wins over env so the in-app tab is authoritative.
        default_comm_password_effective = default_comm_password_db or default_comm_password_env
        default_comm_password_source = 'db' if default_comm_password_db else ('env' if default_comm_password_env else '')
        try:
            from agent.sync_limits import get_sync_personnel_limits

            sync_limits = get_sync_personnel_limits(force_refresh=True)
        except Exception:
            sync_limits = None
    except Exception:
        ui_date_format = 'ro_short'
        ui_week_start = 'monday'
        sync_limits = None
        default_comm_password_db = ''
        try:
            from django.conf import settings as _dj_settings

            default_comm_password_env = str(getattr(_dj_settings, 'ZKACCESS_DEFAULT_COMM_PASSWORD', '') or '').strip()
        except Exception:
            default_comm_password_env = ''
        default_comm_password_effective = default_comm_password_env
        default_comm_password_source = 'env' if default_comm_password_env else ''

    def _fmt_date_ui(dt, fmt: str) -> str:
        try:
            if fmt == 'ro_long':
                months = [
                    'ianuarie', 'februarie', 'martie', 'aprilie', 'mai', 'iunie',
                    'iulie', 'august', 'septembrie', 'octombrie', 'noiembrie', 'decembrie'
                ]
                return f"{dt.day:02d} {months[dt.month-1]} {dt.year:04d}"
            if fmt == 'iso':
                return dt.strftime('%Y-%m-%d')
            # ro_short default
            return dt.strftime('%d.%m.%Y')
        except Exception:
            return ''

    # Current system time (already activated by middleware)
    now_local = None
    now_local_str = ''
    now_date_str = ''
    now_time_str = ''
    active_tz = ''
    try:
        now_local = timezone.localtime(timezone.now())
        now_local_str = now_local.strftime('%Y-%m-%d %H:%M:%S')
        now_date_str = _fmt_date_ui(now_local, ui_date_format)
        now_time_str = now_local.strftime('%H:%M:%S')
        active_tz = getattr(timezone.get_current_timezone(), 'key', None) or str(timezone.get_current_timezone())
    except Exception:
        now_local = None
        now_local_str = ''
        now_date_str = ''
        now_time_str = ''
        active_tz = ''

    # Global system tz name
    system_tz = ''
    try:
        system_tz = (SystemSettings.get_solo().time_zone or '').strip()
    except Exception:
        system_tz = ''

    # USERS
    role_groups = {ROLE_SUPER_ADMIN, ROLE_ADMIN, ROLE_USER, ROLE_VISITOR}
    users_rows = []
    try:
        for u in User.objects.all().prefetch_related('groups').order_by('username'):
            gnames = set(u.groups.values_list('name', flat=True))
            role = None
            for cand in (ROLE_SUPER_ADMIN, ROLE_ADMIN, ROLE_USER, ROLE_VISITOR):
                if cand in gnames:
                    role = cand
                    break
            if not role:
                if u.is_superuser:
                    role = ROLE_SUPER_ADMIN
                elif u.is_staff:
                    role = ROLE_ADMIN
                else:
                    role = ROLE_USER
            role_label = {
                ROLE_SUPER_ADMIN: 'Super Admin',
                ROLE_ADMIN: 'Admin',
                ROLE_USER: 'Utilizator',
                ROLE_VISITOR: 'Vizitator',
            }.get(role, role or '')

            extra_groups = [g for g in sorted(gnames) if g not in role_groups]
            users_rows.append(
                {
                    'id': u.id,
                    'username': u.username,
                    'name': (f"{u.first_name} {u.last_name}").strip(),
                    'email': u.email or '',
                    'role': role,
                    'role_label': role_label,
                    'is_active': bool(u.is_active),
                    'groups': extra_groups,
                    'is_staff': bool(u.is_staff),
                    'is_superuser': bool(u.is_superuser),
                    'last_login': u.last_login,
                }
            )
    except Exception:
        users_rows = []

    # GROUPS
    groups_rows = []
    try:
        for g in Group.objects.all().prefetch_related('permissions').order_by('name'):
            is_role = g.name in role_groups or (g.name or '').startswith(ROLE_GROUP_PREFIX)
            groups_rows.append(
                {
                    'id': g.id,
                    'name': g.name,
                    'perm_count': g.permissions.count(),
                    'user_count': g.user_set.count(),
                    'is_role_group': bool(is_role),
                }
            )
    except Exception:
        groups_rows = []

    # Helper: compute a short GMT label for a tz name at the current moment
    def _fmt_gmt_short(offset_seconds: int) -> str:
        sign = '+' if offset_seconds >= 0 else '-'
        s = abs(int(offset_seconds))
        hh = s // 3600
        mm = (s % 3600) // 60
        if mm:
            return f"GMT{sign}{hh}:{mm:02d}"
        return f"GMT{sign}{hh}"

    def _gmt_for_tz(tz_name: str) -> str:
        try:
            from zoneinfo import ZoneInfo

            tz_name = (tz_name or '').strip()
            if not tz_name:
                return ''
            dt_utc = timezone.now().astimezone(timezone.utc)
            local = dt_utc.astimezone(ZoneInfo(tz_name))
            off = local.utcoffset()
            seconds = int(off.total_seconds()) if off else 0
            return _fmt_gmt_short(seconds)
        except Exception:
            return ''

    # TIME ZONE SETTINGS + device usage
    tz_settings_rows = []
    if TimeZoneSetting is not None:
        try:
            tz_settings_rows = []
            for tz in TimeZoneSetting.objects.all().order_by('-is_active', 'name'):
                tz_name = (getattr(tz, 'time_zone', '') or '').strip()
                tz_settings_rows.append(
                    {
                        'id': tz.id,
                        'is_active': bool(getattr(tz, 'is_active', False)),
                        'name': getattr(tz, 'name', '') or '',
                        'region': getattr(tz, 'region', '') or '',
                        'time_zone': tz_name,
                        'gmt': _gmt_for_tz(tz_name),
                    }
                )
        except Exception:
            tz_settings_rows = []

    devices_rows = []
    try:
        for d in Device.objects.all().order_by('name'):
            tz_name = (d.time_zone or system_tz or '').strip()
            devices_rows.append(
                {
                    'id': d.id,
                    'name': d.name,
                    'ip': getattr(d, 'ip_address', None) or '',
                    'serial': getattr(d, 'serial_number', '') or '',
                    'time_zone': tz_name,
                    'gmt': _gmt_for_tz(tz_name),
                    'system_time': now_local_str,
                }
            )
    except Exception:
        devices_rows = []

    # LOGS
    system_modules = ['system-user', 'system-group', 'system-tz', 'system-time', 'system']
    logs_all = []
    logs_users = []
    logs_groups = []
    logs_tz = []
    try:
        logs_all = list(AuditLog.objects.filter(module__in=system_modules).order_by('-timestamp')[:200])
        logs_users = list(AuditLog.objects.filter(module='system-user').order_by('-timestamp')[:50])
        logs_groups = list(AuditLog.objects.filter(module='system-group').order_by('-timestamp')[:50])
        logs_tz = list(AuditLog.objects.filter(module='system-tz').order_by('-timestamp')[:50])
    except Exception:
        logs_all = []
        logs_users = []
        logs_groups = []
        logs_tz = []

    return render(
        request,
        'agent/menu_system_modern.html',
        {
            'users_rows': users_rows,
            'groups_rows': groups_rows,
            'system_time_zone': system_tz,
            'active_tz': active_tz,
            'system_now_local': now_local_str,
            'system_now_date': now_date_str,
            'system_now_time': now_time_str,
            'tz_settings_rows': tz_settings_rows,
            'devices_rows': devices_rows,
            'ui_date_format': ui_date_format,
            'ui_week_start': ui_week_start,
            'logs_all': logs_all,
            'logs_users': logs_users,
            'logs_groups': logs_groups,
            'logs_tz': logs_tz,
            'user_create_form': SystemUserForm(),
            'group_create_form': SystemGroupForm(),
            'tz_create_form': TimeZoneSettingForm(),
            'sync_limits': sync_limits,
            'default_comm_password_db': default_comm_password_db,
            'default_comm_password_env': default_comm_password_env,
            'default_comm_password_effective': default_comm_password_effective,
            'default_comm_password_source': default_comm_password_source,
        },
    )


def system_sync_limits_save(request: HttpRequest):
    """Save SYNC_PERSONNEL limits to SystemSettings (DB-backed)."""
    if not request.user.is_authenticated or not request.user.is_staff:
        return JsonResponse({'ok': False, 'error': 'unauthorized'}, status=403)

    if request.method != 'POST':
        return JsonResponse({'ok': False, 'error': 'method_not_allowed'}, status=405)

    from agent.models import SystemSettings

    def _parse_int(name: str, default: int) -> int:
        try:
            return int((request.POST.get(name) or '').strip())
        except Exception:
            return default

    def _parse_float(name: str, default: float) -> float:
        try:
            return float((request.POST.get(name) or '').strip())
        except Exception:
            return default

    enabled_raw = (request.POST.get('sync_personnel_enabled') or '').strip()
    enabled = (enabled_raw not in ('0', 'false', 'False', 'no', 'NO'))

    dedupe_s = _parse_int('sync_personnel_dedupe_seconds', 60)
    dedupe_s = max(5, min(600, dedupe_s))

    reassert_s = _parse_int('sync_personnel_reassert_seconds', 21600)
    reassert_s = max(60, min(7 * 24 * 3600, reassert_s))

    batch_size = _parse_int('sync_personnel_batch_size', 200)
    batch_size = max(20, min(2000, batch_size))

    inter_sleep = _parse_float('sync_personnel_inter_batch_sleep', 0.02)
    inter_sleep = max(0.0, min(0.25, inter_sleep))

    max_per_min = _parse_int('sync_personnel_max_per_minute', 0)
    max_per_min = max(0, min(600, max_per_min))

    ss = SystemSettings.get_solo()
    ss.sync_personnel_enabled = bool(enabled)
    ss.sync_personnel_dedupe_seconds = int(dedupe_s)
    ss.sync_personnel_reassert_seconds = int(reassert_s)
    ss.sync_personnel_batch_size = int(batch_size)
    ss.sync_personnel_inter_batch_sleep = float(inter_sleep)
    ss.sync_personnel_max_per_minute = int(max_per_min)
    ss.save(
        update_fields=[
            'sync_personnel_enabled',
            'sync_personnel_dedupe_seconds',
            'sync_personnel_reassert_seconds',
            'sync_personnel_batch_size',
            'sync_personnel_inter_batch_sleep',
            'sync_personnel_max_per_minute',
            'updated_at',
        ]
    )

    try:
        from agent.sync_limits import get_sync_personnel_limits

        eff = get_sync_personnel_limits(force_refresh=True)
        data = {
            'enabled': eff.enabled,
            'dedupe_seconds': eff.dedupe_seconds,
            'reassert_seconds': eff.reassert_seconds,
            'batch_size': eff.batch_size,
            'inter_batch_sleep': eff.inter_batch_sleep,
            'max_per_minute': eff.max_per_minute,
        }
    except Exception:
        data = {
            'enabled': bool(enabled),
            'dedupe_seconds': int(dedupe_s),
            'reassert_seconds': int(reassert_s),
            'batch_size': int(batch_size),
            'inter_batch_sleep': float(inter_sleep),
            'max_per_minute': int(max_per_min),
        }

    _audit_log(
        request,
        module='system',
        action='save_sync_limits',
        entity_id=1,
        entity_name='SystemSettings',
        details=str(data),
    )
    return JsonResponse({'ok': True, 'data': data})


def api_system_now(request: HttpRequest):
    """Return server clock in currently active (system) time zone.

    We return UTC epoch + tz offset so the browser can render correct system time
    independent of the browser's own local time zone.
    """
    if not request.user.is_authenticated:
        return JsonResponse({'ok': False, 'error': 'unauthorized'}, status=403)

    from django.utils import timezone

    now_utc = timezone.now()
    try:
        now_local = timezone.localtime(now_utc)
    except Exception:
        now_local = now_utc

    try:
        offset_td = now_local.utcoffset()
        offset_seconds = int(offset_td.total_seconds()) if offset_td else 0
    except Exception:
        offset_seconds = 0

    tz_key = ''
    try:
        tz_key = getattr(timezone.get_current_timezone(), 'key', None) or str(timezone.get_current_timezone())
    except Exception:
        tz_key = ''

    try:
        formatted = now_local.strftime('%Y-%m-%d %H:%M:%S')
    except Exception:
        formatted = ''

    return JsonResponse(
        {
            'ok': True,
            'epoch_ms_utc': int(now_utc.timestamp() * 1000),
            'offset_seconds': offset_seconds,
            'tz_key': tz_key,
            'tz_label': f"{tz_key} (UTC{_fmt_offset_for_api(offset_seconds)})" if tz_key else f"UTC{_fmt_offset_for_api(offset_seconds)}",
            'formatted': formatted,
        }
    )


def api_system_audit_latest(request: HttpRequest):
    """Return latest system-module audit logs since a given ID.

    This is used by System UI to refresh logs in near real-time, even when
    running under runserver (no WebSockets).
    """
    if not request.user.is_authenticated or not request.user.is_staff:
        return JsonResponse({'ok': False, 'error': 'unauthorized'}, status=403)

    if AuditLog is None:
        return JsonResponse({'ok': True, 'rows': [], 'latest_id': 0})

    try:
        since_id = int((request.GET.get('since_id') or '0').strip() or '0')
    except Exception:
        since_id = 0

    # System module audit stream
    system_modules = ['system-user', 'system-group', 'system-tz', 'system-time', 'system']

    try:
        qs = (
            AuditLog.objects
            .filter(module__in=system_modules, id__gt=int(since_id))
            .order_by('id')
        )
        # Cap incremental delivery
        rows = list(qs[:80])
    except Exception:
        rows = []

    out = []
    latest_id = int(since_id or 0)
    for l in rows:
        try:
            lid = int(getattr(l, 'id'))
        except Exception:
            continue
        latest_id = max(latest_id, lid)
        try:
            ts = getattr(l, 'timestamp', None)
            ts_str = ts.strftime('%Y-%m-%d %H:%M:%S') if ts else ''
        except Exception:
            ts_str = ''
        try:
            details = getattr(l, 'details', '') or ''
        except Exception:
            details = ''
        if len(details) > 2000:
            details = details[:2000]
        out.append(
            {
                'id': lid,
                'timestamp': ts_str,
                'user': (getattr(l, 'user', None) or ''),
                'module': (getattr(l, 'module', None) or ''),
                'action': (getattr(l, 'action', None) or ''),
                'entity': (getattr(l, 'entity_name', None) or '') or str(getattr(l, 'entity_id', '') or ''),
                'details': details,
            }
        )

    return JsonResponse({'ok': True, 'rows': out, 'latest_id': latest_id})


def api_system_time_check(request: HttpRequest):
    """Return drift diagnostics between server clock and DB clock.

    Goal: detect and eliminate discordances between app/server time and DB time
    without relying on browser-local clocks.
    """
    if not request.user.is_authenticated:
        return JsonResponse({'ok': False, 'error': 'unauthorized'}, status=403)

    from django.utils import timezone
    from django.db import connection
    from django.utils.dateparse import parse_datetime
    import datetime as _dt

    now_server_utc = timezone.now()
    try:
        now_server_local = timezone.localtime(now_server_utc)
    except Exception:
        now_server_local = now_server_utc

    # DB current time (best-effort; format depends on backend)
    db_raw = None
    db_epoch_ms_utc = None
    db_error = None
    try:
        vendor = getattr(connection, 'vendor', '')
        sql = 'SELECT CURRENT_TIMESTAMP'
        if vendor == 'sqlite':
            # SQLite CURRENT_TIMESTAMP returns UTC as a string: YYYY-MM-DD HH:MM:SS
            sql = 'SELECT CURRENT_TIMESTAMP'
        cur = connection.cursor()
        cur.execute(sql)
        row = cur.fetchone()
        db_raw = row[0] if row else None

        dt = None
        if isinstance(db_raw, _dt.datetime):
            dt = db_raw
        elif isinstance(db_raw, (int, float)):
            dt = _dt.datetime.fromtimestamp(float(db_raw), tz=_dt.timezone.utc)
        elif db_raw is not None:
            # parse_datetime expects ISO-ish; SQLite uses space separator.
            s = str(db_raw).strip().replace(' ', 'T', 1)
            dt = parse_datetime(s)
            if dt is None:
                # last fallback: try without replacement
                dt = parse_datetime(str(db_raw).strip())

        if dt is not None:
            if timezone.is_naive(dt):
                # Assume UTC for DB timestamps (matches Django storage when USE_TZ=True).
                dt = timezone.make_aware(dt, timezone=timezone.utc)
            db_epoch_ms_utc = int(dt.astimezone(timezone.utc).timestamp() * 1000)
    except Exception as e:
        db_error = str(e)

    server_epoch_ms_utc = int(now_server_utc.timestamp() * 1000)
    drift_seconds = None
    if db_epoch_ms_utc is not None:
        drift_seconds = (db_epoch_ms_utc - server_epoch_ms_utc) / 1000.0

    tz_key = ''
    offset_seconds = 0
    try:
        tz_key = getattr(timezone.get_current_timezone(), 'key', None) or str(timezone.get_current_timezone())
    except Exception:
        tz_key = ''
    try:
        off = now_server_local.utcoffset()
        offset_seconds = int(off.total_seconds()) if off else 0
    except Exception:
        offset_seconds = 0

    return JsonResponse(
        {
            'ok': True,
            'server': {
                'now_utc': now_server_utc.isoformat(),
                'now_local': now_server_local.isoformat(),
                'epoch_ms_utc': server_epoch_ms_utc,
                'tz_key': tz_key,
                'offset_seconds': offset_seconds,
            },
            'db': {
                'vendor': getattr(connection, 'vendor', None),
                'current_timestamp_raw': db_raw,
                'epoch_ms_utc': db_epoch_ms_utc,
                'error': db_error,
            },
            'drift_seconds': drift_seconds,
        }
    )


def _fmt_offset_for_api(offset_seconds: int) -> str:
    sign = '+' if offset_seconds >= 0 else '-'
    s = abs(int(offset_seconds))
    hh = s // 3600
    mm = (s % 3600) // 60
    return f"{sign}{hh:02d}:{mm:02d}"


def system_device_tz_edit(request: HttpRequest, pk: int):
    """Modal to edit a device's time zone."""
    if not request.user.is_authenticated or not request.user.is_staff:
        return JsonResponse({'ok': False, 'error': 'unauthorized'}, status=403)

    from agent.forms import DeviceTimeZoneForm
    from agent.models import Device

    dev = Device.objects.get(pk=pk)
    if request.method == 'POST':
        form = DeviceTimeZoneForm(request.POST, instance=dev)
        if form.is_valid():
            tz_name = (form.cleaned_data.get('time_zone') or '').strip()
            dev.time_zone = tz_name
            dev.save(update_fields=['time_zone'])
            _audit_log(
                request,
                module='system-tz',
                action='device_tz_update',
                entity_id=int(dev.id),
                entity_name=getattr(dev, 'name', '') or dev.serial_number or str(dev.id),
                details=f"device_tz={tz_name}",
            )
            return JsonResponse({'ok': True})
        return JsonResponse({'ok': False, 'error': 'validation', 'errors': form.errors}, status=400)

    form = DeviceTimeZoneForm(instance=dev)
    return render(request, 'agent/system_device_tz_modal.html', {'form': form, 'dev': dev})


def system_options_modal(request: HttpRequest):
    """Modal version of System Options (time zone only)."""
    if not request.user.is_authenticated or not request.user.is_staff:
        return JsonResponse({'ok': False, 'error': 'unauthorized'}, status=403)

    from django.utils import timezone

    from agent.models import SystemSettings

    settings_obj = SystemSettings.get_solo()

    date_format_choices = [
        ('ro_short', 'Zi.Lună.An (22.01.2026)'),
        ('ro_long', 'Zi Luna An (22 ianuarie 2026)'),
        ('iso', 'YYYY-MM-DD (2026-01-22)'),
    ]
    week_start_choices = [
        ('monday', 'Luni (RO)'),
        ('sunday', 'Duminică (US)'),
    ]

    tz_choices = []
    try:
        from agent.tz_utils import build_time_zone_choice_tuples

        tz_choices = build_time_zone_choice_tuples()
    except Exception:
        tz_choices = []

    if request.method == 'POST':
        tz_name = (request.POST.get('time_zone') or '').strip()
        date_format = (request.POST.get('date_format') or '').strip() or (getattr(settings_obj, 'date_format', '') or '').strip() or 'ro_short'
        week_start = (request.POST.get('week_start') or '').strip() or (getattr(settings_obj, 'week_start', '') or '').strip() or 'monday'
        if not tz_name:
            return JsonResponse({'ok': False, 'error': 'validation', 'errors': {'time_zone': ['required']}}, status=400)
        if date_format not in {c[0] for c in date_format_choices}:
            return JsonResponse({'ok': False, 'error': 'validation', 'errors': {'date_format': ['invalid']}}, status=400)
        if week_start not in {c[0] for c in week_start_choices}:
            return JsonResponse({'ok': False, 'error': 'validation', 'errors': {'week_start': ['invalid']}}, status=400)
        try:
            from zoneinfo import ZoneInfo

            ZoneInfo(tz_name)
        except Exception:
            return JsonResponse({'ok': False, 'error': 'validation', 'errors': {'time_zone': ['invalid']}}, status=400)

        settings_obj.time_zone = tz_name
        settings_obj.date_format = date_format
        settings_obj.week_start = week_start
        try:
            settings_obj.save(update_fields=['time_zone', 'date_format', 'week_start', 'updated_at'])
        except Exception as ex:
            return JsonResponse({'ok': False, 'error': str(ex)}, status=400)

        _audit_log(
            request,
            module='system-tz',
            action='system_tz_update',
            entity_id=int(getattr(settings_obj, 'id', 1) or 1),
            entity_name='SystemSettings',
            details=f"time_zone={tz_name} date_format={date_format} week_start={week_start}",
        )
        return JsonResponse({'ok': True})

    active_tz = ''
    try:
        active_tz = getattr(timezone.get_current_timezone(), 'key', None) or str(timezone.get_current_timezone())
    except Exception:
        active_tz = ''

    return render(
        request,
        'agent/system_options_modal.html',
        {
            'settings_id': getattr(settings_obj, 'id', 1) or 1,
            'current_tz': (settings_obj.time_zone or '').strip(),
            'tz_choices': tz_choices,
            'active_tz': active_tz,
            'date_format_choices': date_format_choices,
            'week_start_choices': week_start_choices,
            'current_date_format': (getattr(settings_obj, 'date_format', '') or '').strip() or 'ro_short',
            'current_week_start': (getattr(settings_obj, 'week_start', '') or '').strip() or 'monday',
        },
    )


def system_user_new(request: HttpRequest):
    if not request.user.is_authenticated or not request.user.is_staff:
        return JsonResponse({'ok': False, 'error': 'unauthorized'}, status=403)
    from agent.forms import SystemUserForm

    if request.method == 'POST':
        form = SystemUserForm(request.POST)
        if form.is_valid():
            u = form.save()
            _audit_log(request, module='system-user', action='create', entity_id=int(u.id), entity_name=u.username)
            return JsonResponse({'ok': True})
        return JsonResponse({'ok': False, 'error': 'validation', 'errors': form.errors}, status=400)
    form = SystemUserForm()
    return render(request, 'agent/system_user_form_modal.html', {'form': form, 'mode': 'create'})


def system_user_edit(request: HttpRequest, pk: int):
    if not request.user.is_authenticated or not request.user.is_staff:
        return JsonResponse({'ok': False, 'error': 'unauthorized'}, status=403)
    from django.contrib.auth.models import User
    from agent.forms import SystemUserForm

    u = User.objects.get(pk=pk)
    if request.method == 'POST':
        before = {
            'username': u.username,
            'first_name': u.first_name,
            'last_name': u.last_name,
            'email': u.email,
            'is_active': u.is_active,
            'is_staff': u.is_staff,
            'is_superuser': u.is_superuser,
        }
        form = SystemUserForm(request.POST, instance=u)
        if form.is_valid():
            saved = form.save()
            after = {
                'username': saved.username,
                'first_name': saved.first_name,
                'last_name': saved.last_name,
                'email': saved.email,
                'is_active': saved.is_active,
                'is_staff': saved.is_staff,
                'is_superuser': saved.is_superuser,
            }
            changes = []
            for k, v in before.items():
                if after.get(k) != v:
                    changes.append(f"{k}: {v} -> {after.get(k)}")
            _audit_log(
                request,
                module='system-user',
                action='update',
                entity_id=int(saved.id),
                entity_name=saved.username,
                details='; '.join(changes)[:2000],
            )
            return JsonResponse({'ok': True})
        return JsonResponse({'ok': False, 'error': 'validation', 'errors': form.errors}, status=400)
    form = SystemUserForm(instance=u)
    return render(request, 'agent/system_user_form_modal.html', {'form': form, 'mode': 'edit', 'obj': u})


def system_user_delete(request: HttpRequest, pk: int):
    if not request.user.is_authenticated or not request.user.is_staff or request.method != 'POST':
        return JsonResponse({'ok': False, 'error': 'unauthorized'}, status=403)
    from django.contrib.auth.models import User

    u = User.objects.filter(pk=pk).first()
    if not u:
        return JsonResponse({'ok': False, 'error': 'not-found'}, status=404)
    # Prevent deleting self
    try:
        if request.user.id == u.id:
            return JsonResponse({'ok': False, 'error': 'cannot-delete-self'}, status=400)
    except Exception:
        pass
    name = u.username
    u.delete()
    _audit_log(request, module='system-user', action='delete', entity_id=int(pk), entity_name=name)
    return JsonResponse({'ok': True})


def system_group_new(request: HttpRequest):
    if not request.user.is_authenticated or not request.user.is_staff:
        return JsonResponse({'ok': False, 'error': 'unauthorized'}, status=403)
    from agent.forms import SystemGroupForm

    if request.method == 'POST':
        form = SystemGroupForm(request.POST)
        if form.is_valid():
            g = form.save()
            _audit_log(request, module='system-group', action='create', entity_id=int(g.id), entity_name=g.name)
            return JsonResponse({'ok': True})
        return JsonResponse({'ok': False, 'error': 'validation', 'errors': form.errors}, status=400)
    form = SystemGroupForm()
    return render(request, 'agent/system_group_form_modal.html', {'form': form, 'mode': 'create'})


def system_group_edit(request: HttpRequest, pk: int):
    if not request.user.is_authenticated or not request.user.is_staff:
        return JsonResponse({'ok': False, 'error': 'unauthorized'}, status=403)
    from django.contrib.auth.models import Group
    from agent.forms import ROLE_GROUP_PREFIX, SystemGroupForm

    g = Group.objects.get(pk=pk)
    # Protect role groups
    if (g.name or '').startswith(ROLE_GROUP_PREFIX):
        return JsonResponse({'ok': False, 'error': 'role-group-protected'}, status=400)

    if request.method == 'POST':
        before = {
            'name': g.name,
            'perm_count': g.permissions.count(),
        }
        form = SystemGroupForm(request.POST, instance=g)
        if form.is_valid():
            saved = form.save()
            after = {
                'name': saved.name,
                'perm_count': saved.permissions.count(),
            }
            changes = []
            for k, v in before.items():
                if after.get(k) != v:
                    changes.append(f"{k}: {v} -> {after.get(k)}")
            _audit_log(
                request,
                module='system-group',
                action='update',
                entity_id=int(saved.id),
                entity_name=saved.name,
                details='; '.join(changes)[:2000],
            )
            return JsonResponse({'ok': True})
        return JsonResponse({'ok': False, 'error': 'validation', 'errors': form.errors}, status=400)
    form = SystemGroupForm(instance=g)
    return render(request, 'agent/system_group_form_modal.html', {'form': form, 'mode': 'edit', 'obj': g})


def system_group_delete(request: HttpRequest, pk: int):
    if not request.user.is_authenticated or not request.user.is_staff or request.method != 'POST':
        return JsonResponse({'ok': False, 'error': 'unauthorized'}, status=403)
    from django.contrib.auth.models import Group
    from agent.forms import ROLE_GROUP_PREFIX

    g = Group.objects.filter(pk=pk).first()
    if not g:
        return JsonResponse({'ok': False, 'error': 'not-found'}, status=404)
    if (g.name or '').startswith(ROLE_GROUP_PREFIX):
        return JsonResponse({'ok': False, 'error': 'role-group-protected'}, status=400)
    name = g.name
    g.delete()
    _audit_log(request, module='system-group', action='delete', entity_id=int(pk), entity_name=name)
    return JsonResponse({'ok': True})


def system_tz_new(request: HttpRequest):
    if not request.user.is_authenticated or not request.user.is_staff:
        return JsonResponse({'ok': False, 'error': 'unauthorized'}, status=403)
    from agent.forms import TimeZoneSettingForm
    from agent.models import SystemSettings
    from agent.models import TimeZoneSetting

    date_format_choices = [
        ('ro_short', 'Zi.Lună.An (22.01.2026)'),
        ('ro_long', 'Zi Luna An (22 ianuarie 2026)'),
        ('iso', 'YYYY-MM-DD (2026-01-22)'),
    ]
    week_start_choices = [
        ('monday', 'Luni (RO)'),
        ('sunday', 'Duminică (US)'),
    ]
    ss = None
    try:
        ss = SystemSettings.get_solo()
    except Exception:
        ss = None

    if request.method == 'POST':
        form = TimeZoneSettingForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            date_format = (request.POST.get('date_format') or '').strip() or ((getattr(ss, 'date_format', '') or '').strip() if ss else 'ro_short')
            week_start = (request.POST.get('week_start') or '').strip() or ((getattr(ss, 'week_start', '') or '').strip() if ss else 'monday')
            if date_format not in {c[0] for c in date_format_choices}:
                return JsonResponse({'ok': False, 'error': 'validation', 'errors': {'date_format': ['invalid']}}, status=400)
            if week_start not in {c[0] for c in week_start_choices}:
                return JsonResponse({'ok': False, 'error': 'validation', 'errors': {'week_start': ['invalid']}}, status=400)
            obj = TimeZoneSetting.objects.create(
                name=data.get('name') or 'Time Zone',
                region=(data.get('region') or ''),
                time_zone=data.get('time_zone'),
                is_active=bool(data.get('is_active')),
            )
            if obj.is_active:
                TimeZoneSetting.objects.exclude(pk=obj.pk).update(is_active=False)
                tz_name = (obj.time_zone or '').strip()
                try:
                    ss = SystemSettings.get_solo()
                    ss.time_zone = tz_name
                    ss.date_format = date_format
                    ss.week_start = week_start
                    ss.save(update_fields=['time_zone', 'date_format', 'week_start', 'updated_at'])
                except Exception:
                    pass
            else:
                # Even if preset isn't active, allow updating UI prefs.
                try:
                    if ss is None:
                        ss = SystemSettings.get_solo()
                    ss.date_format = date_format
                    ss.week_start = week_start
                    ss.save(update_fields=['date_format', 'week_start', 'updated_at'])
                except Exception:
                    pass
            _audit_log(request, module='system-tz', action='create', entity_id=int(obj.id), entity_name=obj.name, details=f"region={obj.region} tz={obj.time_zone}")
            return JsonResponse({'ok': True})
        return JsonResponse({'ok': False, 'error': 'validation', 'errors': form.errors}, status=400)
    form = TimeZoneSettingForm()
    return render(
        request,
        'agent/system_tz_form_modal.html',
        {
            'form': form,
            'mode': 'create',
            'date_format_choices': date_format_choices,
            'week_start_choices': week_start_choices,
            'current_date_format': ((getattr(ss, 'date_format', '') or '').strip() if ss else 'ro_short') or 'ro_short',
            'current_week_start': ((getattr(ss, 'week_start', '') or '').strip() if ss else 'monday') or 'monday',
        },
    )


def system_tz_edit(request: HttpRequest, pk: int):
    if not request.user.is_authenticated or not request.user.is_staff:
        return JsonResponse({'ok': False, 'error': 'unauthorized'}, status=403)
    from agent.forms import TimeZoneSettingForm
    from agent.models import SystemSettings
    from agent.models import TimeZoneSetting

    date_format_choices = [
        ('ro_short', 'Zi.Lună.An (22.01.2026)'),
        ('ro_long', 'Zi Luna An (22 ianuarie 2026)'),
        ('iso', 'YYYY-MM-DD (2026-01-22)'),
    ]
    week_start_choices = [
        ('monday', 'Luni (RO)'),
        ('sunday', 'Duminică (US)'),
    ]
    ss = None
    try:
        ss = SystemSettings.get_solo()
    except Exception:
        ss = None

    obj = TimeZoneSetting.objects.get(pk=pk)
    if request.method == 'POST':
        before = {'name': obj.name, 'region': getattr(obj, 'region', ''), 'time_zone': obj.time_zone, 'is_active': obj.is_active}
        form = TimeZoneSettingForm(request.POST, instance=obj)
        if form.is_valid():
            data = form.cleaned_data
            date_format = (request.POST.get('date_format') or '').strip() or ((getattr(ss, 'date_format', '') or '').strip() if ss else 'ro_short')
            week_start = (request.POST.get('week_start') or '').strip() or ((getattr(ss, 'week_start', '') or '').strip() if ss else 'monday')
            if date_format not in {c[0] for c in date_format_choices}:
                return JsonResponse({'ok': False, 'error': 'validation', 'errors': {'date_format': ['invalid']}}, status=400)
            if week_start not in {c[0] for c in week_start_choices}:
                return JsonResponse({'ok': False, 'error': 'validation', 'errors': {'week_start': ['invalid']}}, status=400)
            obj.name = data.get('name') or obj.name
            obj.region = (data.get('region') or '').strip()
            obj.time_zone = data.get('time_zone') or obj.time_zone
            obj.is_active = bool(data.get('is_active'))
            obj.save(update_fields=['name', 'region', 'time_zone', 'is_active', 'updated_at'])
            if obj.is_active:
                TimeZoneSetting.objects.exclude(pk=obj.pk).update(is_active=False)
                tz_name = (obj.time_zone or '').strip()
                try:
                    ss = SystemSettings.get_solo()
                    ss.time_zone = tz_name
                    ss.date_format = date_format
                    ss.week_start = week_start
                    ss.save(update_fields=['time_zone', 'date_format', 'week_start', 'updated_at'])
                except Exception:
                    pass
            else:
                try:
                    if ss is None:
                        ss = SystemSettings.get_solo()
                    ss.date_format = date_format
                    ss.week_start = week_start
                    ss.save(update_fields=['date_format', 'week_start', 'updated_at'])
                except Exception:
                    pass
            after = {'name': obj.name, 'region': getattr(obj, 'region', ''), 'time_zone': obj.time_zone, 'is_active': obj.is_active}
            changes = []
            for k, v in before.items():
                if after.get(k) != v:
                    changes.append(f"{k}: {v} -> {after.get(k)}")
            _audit_log(
                request,
                module='system-tz',
                action='update',
                entity_id=int(obj.id),
                entity_name=obj.name,
                details='; '.join(changes)[:2000],
            )
            return JsonResponse({'ok': True})
        return JsonResponse({'ok': False, 'error': 'validation', 'errors': form.errors}, status=400)
    form = TimeZoneSettingForm(instance=obj)
    return render(
        request,
        'agent/system_tz_form_modal.html',
        {
            'form': form,
            'mode': 'edit',
            'obj': obj,
            'date_format_choices': date_format_choices,
            'week_start_choices': week_start_choices,
            'current_date_format': ((getattr(ss, 'date_format', '') or '').strip() if ss else 'ro_short') or 'ro_short',
            'current_week_start': ((getattr(ss, 'week_start', '') or '').strip() if ss else 'monday') or 'monday',
        },
    )


def system_tz_activate(request: HttpRequest, pk: int):
    if not request.user.is_authenticated or not request.user.is_staff or request.method != 'POST':
        return JsonResponse({'ok': False, 'error': 'unauthorized'}, status=403)
    from agent.models import SystemSettings
    from agent.models import TimeZoneSetting

    obj = TimeZoneSetting.objects.filter(pk=pk).first()
    if not obj:
        return JsonResponse({'ok': False, 'error': 'not-found'}, status=404)
    TimeZoneSetting.objects.exclude(pk=obj.pk).update(is_active=False)
    TimeZoneSetting.objects.filter(pk=obj.pk).update(is_active=True)
    tz_name = (obj.time_zone or '').strip()
    try:
        ss = SystemSettings.get_solo()
        ss.time_zone = tz_name
        ss.save(update_fields=['time_zone', 'updated_at'])
    except Exception:
        pass
    _audit_log(request, module='system-tz', action='activate', entity_id=int(obj.id), entity_name=obj.name, details=tz_name)
    return JsonResponse({'ok': True})


def system_tz_delete(request: HttpRequest, pk: int):
    if not request.user.is_authenticated or not request.user.is_staff or request.method != 'POST':
        return JsonResponse({'ok': False, 'error': 'unauthorized'}, status=403)
    from agent.models import TimeZoneSetting

    obj = TimeZoneSetting.objects.filter(pk=pk).first()
    if not obj:
        return JsonResponse({'ok': False, 'error': 'not-found'}, status=404)
    if obj.is_active:
        return JsonResponse({'ok': False, 'error': 'cannot-delete-active'}, status=400)
    name = obj.name
    obj.delete()
    _audit_log(request, module='system-tz', action='delete', entity_id=int(pk), entity_name=name)
    return JsonResponse({'ok': True})


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
            device_ids_set: set[int] = set()
            for r in rows:
                dev_id = getattr(r, 'device_id', None)
                if dev_id is None:
                    continue
                try:
                    device_ids_set.add(int(dev_id))
                except Exception:
                    continue
            device_ids = sorted(device_ids_set)
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
                door_numbers = []
                for n in names:
                    try:
                        if str(n).strip().isdigit():
                            door_numbers.append(int(str(n).strip()))
                    except Exception:
                        pass
                q = Q(name__in=names)
                if door_numbers:
                    q |= Q(door_number__in=sorted(set(door_numbers)))
                for d in _Door.objects.filter(device_id__in=dids).filter(q).select_related('device'):
                    key = str(getattr(d, 'door_number', None) or getattr(d, 'name', '') or '')
                    if key:
                        door_map[(d.device_id, key)] = d
                    try:
                        if getattr(d, 'name', None) and str(getattr(d, 'name')) != key:
                            door_map[(d.device_id, str(getattr(d, 'name')))] = d
                    except Exception:
                        pass

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
                    device_ids_set: set[int] = set()
                    for r in rows:
                        dev_id = getattr(r, 'device_id', None)
                        if dev_id is None:
                            continue
                        try:
                            device_ids_set.add(int(dev_id))
                        except Exception:
                            continue
                    device_ids = sorted(device_ids_set)
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
                        door_numbers = []
                        for n in names:
                            try:
                                if str(n).strip().isdigit():
                                    door_numbers.append(int(str(n).strip()))
                            except Exception:
                                pass
                        q = Q(name__in=names)
                        if door_numbers:
                            q |= Q(door_number__in=sorted(set(door_numbers)))
                        for d in _Door.objects.filter(device_id__in=dids).filter(q).select_related('device'):
                            key = str(getattr(d, 'door_number', None) or getattr(d, 'name', '') or '')
                            if key:
                                door_map[(d.device_id, key)] = d
                            try:
                                if getattr(d, 'name', None) and str(getattr(d, 'name')) != key:
                                    door_map[(d.device_id, str(getattr(d, 'name')))] = d
                            except Exception:
                                pass

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


def _ensure_controller_doors_for_devices(devices):
    """Ensure controllers have Door rows and attach a fresh `prefetched_doors`.

    This is used to backfill doors for existing devices that were created
    before door provisioning ran (or after device_type/model fields changed).
    """
    try:
        from agent.door_provisioning import ensure_controller_doors
    except Exception:
        ensure_controller_doors = None

    if not devices:
        return

    # Avoid importing Door at module import time for legacy startup paths.
    from .models import Door as _Door
    try:
        from django.db.models import F
        _door_order = [F('door_number').asc(nulls_last=True), 'name']
    except Exception:
        _door_order = ['door_number', 'name']

    for dev in devices:
        if ensure_controller_doors is not None:
            try:
                ensure_controller_doors(dev)
            except Exception:
                pass

        try:
            dev.prefetched_doors = list(
                _Door.objects.filter(device=dev)
                .order_by(*_door_order)
            )
        except Exception:
            dev.prefetched_doors = []

def doors_list(request: HttpRequest):
    if not request.user.is_authenticated:
        from django.contrib.auth.views import redirect_to_login
        return redirect_to_login(request.get_full_path())
    mode = (request.GET.get('mode') or 'monitor').strip().lower()
    if mode in ('doorconfiguration', 'door-configuration', 'door_configuration'):
        mode = 'config'
    is_embed = (request.GET.get('embed') == '1')
    if not is_embed:
        from django.shortcuts import redirect
        tab = 'doorconfig' if mode == 'config' else 'doors'
        return redirect(f'/agent/menu/access/?tab={tab}')
    from django.db.models import Prefetch
    # Device-centric view: each controller is one row, with its doors expandable.
    # IMPORTANT: do not over-filter device_type, because existing DB rows may
    # have older/unknown type strings; we still want them visible and
    # auto-provisioned.
    try:
        from django.db.models import F
        _door_order = [F('door_number').asc(nulls_last=True), 'name']
    except Exception:
        _door_order = ['door_number', 'name']

    device_name = (request.GET.get('device_name') or '').strip()
    door_name = (request.GET.get('door_name') or '').strip()

    # IMPORTANT: include doors even if door_number is missing, so we can
    # show already-registered but not fully configured doors.
    door_qs = (
        Door.objects.select_related('device', 'door_active_time_zone', 'door_passage_mode_time_zone')
        .prefetch_related('first_card_rules', 'multi_card_rules')
        .order_by(*_door_order)
    )
    if door_name:
        door_qs = door_qs.filter(name__icontains=door_name)

    # IMPORTANT (legacy parity): Door Configuration must list ONLY controllers (centrale),
    # never standalone readers (e.g. ACP Demo). Readers are typically either
    # scanner_linked=True or device_type='biometric_reader'.
    dev_qs = Device.objects.filter(scanner_linked=False).exclude(device_type='biometric_reader')
    if device_name:
        dev_qs = dev_qs.filter(name__icontains=device_name)
    if door_name:
        try:
            dev_ids = list(door_qs.values_list('device_id', flat=True).distinct())
            dev_qs = dev_qs.filter(id__in=[i for i in dev_ids if i])
        except Exception:
            pass

    dev_qs = dev_qs.order_by('ip_address', 'name').prefetch_related(
        Prefetch('door_set', queryset=door_qs, to_attr='prefetched_doors')
    )
    page = _paginate(dev_qs, request)

    # Backfill: ensure each controller has its doors, then refresh the list.
    devices = list(getattr(page, 'object_list', []) or [])
    _ensure_controller_doors_for_devices(devices)

    # Attach quick stats used by the template (configured vs unconfigured doors).
    for dev in devices:
        doors = list(getattr(dev, 'prefetched_doors', []) or [])
        dev.doors_total = len(doors)
        dev.doors_configured = sum(1 for d in doors if getattr(d, 'door_number', None))
        dev.doors_unconfigured = max(0, dev.doors_total - dev.doors_configured)
        if mode == 'config':
            try:
                from agent.door_provisioning import infer_controller_door_capacity

                dev.doors_capacity = infer_controller_door_capacity(dev)
            except Exception:
                dev.doors_capacity = None

    # Doors must belong to a controller; do not surface unassigned/orphan doors in UI.
    unassigned_doors = []

    next_tab = 'doorconfig' if mode == 'config' else 'doors'
    tpl = 'agent/access_door_configuration_embed.html' if mode == 'config' else 'agent/access_doors_by_device_embed.html'
    ctx = {
        'page': page,
        'can_edit': bool(getattr(request.user, 'is_staff', False)),
        'unassigned_doors': unassigned_doors,
        'mode': mode,
        'next_tab': next_tab,
        'device_name': device_name,
        'door_name': door_name,
    }
    return render(request, tpl, ctx)


def device_doors_auto_assign(request: HttpRequest, device_id: int):
    """Auto-assign door_number (1..capacity) for doors linked to a device but missing door_number.

    This repairs imported/legacy doors so they appear as proper 1..N doors and can derive readers.
    """
    if not request.user.is_authenticated or not request.user.is_staff:
        return JsonResponse({'ok': False, 'error': 'unauthorized'}, status=403)
    if request.method != 'POST':
        return JsonResponse({'ok': False, 'error': 'method-not-allowed'}, status=405)

    dev = Device.objects.filter(pk=device_id).first()
    if dev is None:
        return JsonResponse({'ok': False, 'error': 'device-not-found'}, status=404)

    try:
        from agent.door_provisioning import infer_controller_door_capacity

        capacity = int(infer_controller_door_capacity(dev) or 4)
    except Exception:
        capacity = 4

    try:
        existing = set(
            Door.objects.filter(device=dev)
            .exclude(door_number__isnull=True)
            .values_list('door_number', flat=True)
        )
    except Exception:
        existing = set()

    available = [n for n in range(1, max(1, capacity) + 1) if n not in existing]
    to_fix = list(Door.objects.filter(device=dev, door_number__isnull=True).order_by('id'))
    if not to_fix:
        return JsonResponse({'ok': True, 'assigned': 0, 'capacity': capacity, 'remaining': 0})

    assigned_ids: list[int] = []
    with transaction.atomic():
        for door, num in zip(to_fix, available):
            door.door_number = num
            door.save(update_fields=['door_number'])
            assigned_ids.append(int(door.id))

    _audit_log(
        request,
        module='door',
        action='auto_assign',
        entity_id=int(dev.id),
        entity_name=getattr(dev, 'name', '') or '',
        details=f'assigned={len(assigned_ids)} capacity={capacity} remaining={max(0, len(to_fix)-len(assigned_ids))}',
    )
    return JsonResponse(
        {
            'ok': True,
            'assigned': len(assigned_ids),
            'capacity': capacity,
            'door_ids': assigned_ids,
            'remaining': max(0, len(to_fix) - len(assigned_ids)),
        }
    )


def device_edit_access(request: HttpRequest, pk: int):
    """Device edit endpoint that returns HTML (not JSON) for the Access module modal."""
    if not request.user.is_authenticated or not request.user.is_staff:
        from django.contrib.auth.views import redirect_to_login
        return redirect_to_login(request.get_full_path())

    obj = Device.objects.get(pk=pk)
    # System time zone (used as reference + enforced for reader devices)
    system_settings = None
    system_tz = ''
    system_now_local_str = ''
    try:
        from agent.models import SystemSettings
        from django.utils import timezone

        system_settings = SystemSettings.get_solo()
        system_tz = (system_settings.time_zone or '').strip()
        try:
            system_now_local_str = timezone.localtime(timezone.now()).strftime('%Y-%m-%d %H:%M:%S')
        except Exception:
            system_now_local_str = ''
    except Exception:
        system_settings = None
        system_tz = ''
        system_now_local_str = ''

    wizard = (request.GET.get('wizard') or '').strip() in ('1', 'true', 'yes', 'on')

    if request.method == 'POST':
        post_data = request.POST
        # For reader devices (ELATEC/APC), force device TZ to system TZ.
        try:
            is_reader = (request.POST.get('scanner_linked') or '').strip().lower() in ('1', 'true', 'yes', 'on')
            if is_reader and system_tz:
                post_data = request.POST.copy()
                post_data['time_zone'] = system_tz
        except Exception:
            post_data = request.POST

        form = DeviceExtendedForm(post_data, instance=obj, wizard=wizard)

        if form.is_valid():
            saved = form.save()
            # Safety: enforce system TZ for scanners.
            try:
                if getattr(saved, 'scanner_linked', False) and system_tz and (saved.time_zone or '').strip() != system_tz:
                    saved.time_zone = system_tz
                    saved.save(update_fields=['time_zone'])
            except Exception:
                pass
            try:
                from agent.door_provisioning import ensure_controller_doors

                ensure_controller_doors(saved)
            except Exception:
                pass

            # Note: do NOT auto-seed "Implicit" access levels. Levels are user-defined.
            _audit_log(
                request,
                module='device',
                action='update',
                entity_id=saved.id,
                entity_name=getattr(saved, 'name', '') or '',
            )
            return render(request, 'agent/device_access_saved_inner.html', {'obj': saved})
    else:
        initial = {}
        try:
            if system_tz and not (getattr(obj, 'time_zone', '') or '').strip():
                initial['time_zone'] = system_tz
        except Exception:
            initial = {}
        form = DeviceExtendedForm(instance=obj, initial=initial, wizard=wizard)

    controller_doors = []
    try:
        from agent.door_provisioning import ensure_controller_doors

        ensure_controller_doors(obj)
        try:
            from django.db.models import F

            _door_order = [F('door_number').asc(nulls_last=True), 'name']
        except Exception:
            _door_order = ['door_number', 'name']
        controller_doors = list(Door.objects.filter(device=obj).order_by(*_door_order))
    except Exception:
        controller_doors = []

    next_tab = (request.GET.get('next_tab') or 'doors').strip().lower()
    if next_tab not in ('doors', 'doorconfig'):
        next_tab = 'doors'

    return render(
        request,
        'agent/device_access_form_inner.html',
        {
            'form': form,
            'obj': obj,
            'action_url': request.path,
            'next_url': f'/agent/menu/access/?tab={next_tab}',
            'controller_doors': controller_doors,
            'system_time_zone': system_tz,
            'system_time_now_local': system_now_local_str,
            'show_derived_doors': True,
            'wizard': wizard,
        },
    )


def device_create_access(request: HttpRequest):
    """Device create endpoint that returns HTML (not JSON) for legacy-like modals.

    Used by Access-style modal wiring (same behavior as door forms).
    """
    if not request.user.is_authenticated or not request.user.is_staff:
        from django.contrib.auth.views import redirect_to_login
        return redirect_to_login(request.get_full_path())

    # System time zone (used as reference + enforced for reader devices)
    system_tz = ''
    system_now_local_str = ''
    try:
        from agent.models import SystemSettings
        from django.utils import timezone

        system_settings = SystemSettings.get_solo()
        system_tz = (system_settings.time_zone or '').strip()
        try:
            system_now_local_str = timezone.localtime(timezone.now()).strftime('%Y-%m-%d %H:%M:%S')
        except Exception:
            system_now_local_str = ''
    except Exception:
        system_tz = ''
        system_now_local_str = ''

    obj = None
    wizard = (request.GET.get('wizard') or '').strip() in ('1', 'true', 'yes', 'on')
    wizard_token = (request.GET.get('wizard_token') or request.POST.get('wizard_token') or '').strip()
    wizard_step = (request.GET.get('wizard_step') or request.POST.get('wizard_step') or '').strip().lower() or 'config'
    if wizard_step not in ('identify', 'config'):
        wizard_step = 'config'

    wants_json = (request.headers.get('X-Requested-With') or '').lower() == 'xmlhttprequest'

    def _wiz_get_store() -> dict:
        try:
            store = request.session.get('wizard_device_drafts')
            return store if isinstance(store, dict) else {}
        except Exception:
            return {}

    def _wiz_set_store(store: dict) -> None:
        try:
            request.session['wizard_device_drafts'] = store
            try:
                request.session.modified = True
            except Exception:
                pass
        except Exception:
            pass

    def _wiz_get_draft(token: str) -> dict:
        if not token:
            return {}
        store = _wiz_get_store()
        d = store.get(token)
        return d if isinstance(d, dict) else {}

    def _wiz_put_draft(token: str, draft: dict) -> None:
        if not token:
            return
        store = _wiz_get_store()
        store[token] = draft if isinstance(draft, dict) else {}
        _wiz_set_store(store)

    def _wiz_update_device_snapshot(token: str, data: dict) -> None:
        if not token:
            return
        draft = _wiz_get_draft(token)
        dev = draft.get('device') if isinstance(draft.get('device'), dict) else {}
        dev = {**dev, **(data or {})}
        draft['device'] = dev
        _wiz_put_draft(token, draft)

    def _wiz_set_meta(token: str, **kwargs) -> None:
        if not token:
            return
        draft = _wiz_get_draft(token)
        for k, v in (kwargs or {}).items():
            draft[k] = v
        _wiz_put_draft(token, draft)

    def _infer_capacity(cleaned: dict) -> int:
        # Prefer discovered capacity stored in wizard draft (from discovery modal).
        try:
            if wizard and wizard_token:
                draft = _wiz_get_draft(wizard_token)
                cap_raw = draft.get('doors_capacity')
                cap = int(cap_raw or 0)
                if cap > 0:
                    return cap
        except Exception:
            pass
        try:
            from agent.door_provisioning import infer_controller_door_capacity

            tmp = Device(
                device_type=cleaned.get('device_type') or 'access_panel',
                comm_mode=cleaned.get('comm_mode') or 'tcp',
                ip_address=cleaned.get('ip_address'),
                port=cleaned.get('port') or 4370,
                hardware_version=cleaned.get('hardware_version') or '',
            )
            cap = int(infer_controller_door_capacity(tmp) or 0)
            return cap if cap > 0 else 0
        except Exception:
            return 0

    def _build_draft_controller_doors(cleaned: dict) -> list:
        try:
            cap = _infer_capacity(cleaned)
            cap = cap if cap > 0 else 1
            ip = str(cleaned.get('ip_address') or '').strip()

            draft = _wiz_get_draft(wizard_token)
            doors = draft.get('doors') if isinstance(draft.get('doors'), dict) else {}

            out = []
            for dn in range(1, cap + 1):
                st = doors.get(str(dn)) if isinstance(doors.get(str(dn)), dict) else {}
                name = str(st.get('name') or f'Ușă {dn}').strip()
                rin = str(st.get('reader_in_custom_name') or (f'{ip}-{dn} In' if ip else '')).strip() or '—'
                rout = str(st.get('reader_out_custom_name') or (f'{ip}-{dn} Out' if ip else '')).strip() or '—'
                out.append(SimpleNamespace(
                    id=dn,
                    door_number=dn,
                    name=name,
                    reader_in_name=rin,
                    reader_out_name=rout,
                ))
            return out
        except Exception:
            return []

    def _wizard_clear_requested_ui() -> bool:
        try:
            if not (wizard and wizard_token):
                return False
            draft = _wiz_get_draft(wizard_token)
            return bool(draft.get('clear_requested_ui')) or bool(draft.get('clear_requested'))
        except Exception:
            return False
    if request.method == 'POST':
        post_data = request.POST
        # For reader devices (ELATEC/APC), force device TZ to system TZ.
        try:
            is_reader = (request.POST.get('scanner_linked') or '').strip().lower() in ('1', 'true', 'yes', 'on')
            if is_reader and system_tz:
                post_data = request.POST.copy()
                post_data['time_zone'] = system_tz
        except Exception:
            post_data = request.POST

        form = DeviceExtendedForm(post_data, wizard=wizard, wizard_step=wizard_step)
        if form.is_valid():
            # Wizard discovery flow: when wizard_token is present, DO NOT create in DB
            # until the final save is validated (doors + optional clear).
            if wizard and wizard_token:
                cleaned = dict(form.cleaned_data or {})

                # Persist wizard meta (e.g., discovered capacity) even on identify step.
                try:
                    cap_post = request.POST.get('doors_capacity')
                    cap = int(str(cap_post).strip() or '0') if cap_post is not None else 0
                    if cap > 0:
                        _wiz_set_meta(wizard_token, doors_capacity=cap)
                except Exception:
                    pass

                # Identify step: only persist snapshot and move to next UI step.
                if wizard_step == 'identify':
                    try:
                        _wiz_update_device_snapshot(wizard_token, {
                            'name': str(cleaned.get('name') or ''),
                            'serial_number': str(cleaned.get('serial_number') or ''),
                            'hardware_version': str(cleaned.get('hardware_version') or ''),
                            'ip_address': str(cleaned.get('ip_address') or ''),
                            'port': int(cleaned.get('port') or 0) or 0,
                            'comm_password': str(cleaned.get('comm_password') or ''),
                        })
                    except Exception:
                        pass

                    clear_ui = bool(cleaned.get('clear_on_add'))
                    try:
                        _wiz_set_meta(wizard_token, clear_requested_ui=clear_ui)
                    except Exception:
                        pass

                    if wants_json:
                        if clear_ui:
                            return JsonResponse({
                                'ok': True,
                                'wizard_step': 'clear',
                                'wizard_token': wizard_token,
                                'device_ip': str(cleaned.get('ip_address') or '').strip(),
                                'device_port': int(cleaned.get('port') or 0) or 4370,
                                'comm_password': str(cleaned.get('comm_password') or '').strip(),
                            })

                        from django.template.loader import render_to_string
                        controller_doors = _build_draft_controller_doors(cleaned)
                        html = render_to_string('agent/device_access_form_inner.html', {
                            'form': form,
                            'obj': None,
                            'action_url': request.path,
                            'next_url': '/agent/menu/device/?tab=devices',
                            'controller_doors': controller_doors,
                            'system_time_zone': system_tz,
                            'system_time_now_local': system_now_local_str,
                            'show_derived_doors': True,
                            'wizard': True,
                            'wizard_token': wizard_token,
                            'wizard_step': 'config',
                            'wizard_doors_capacity': int((_wiz_get_draft(wizard_token) or {}).get('doors_capacity') or 0) or None,
                            'wizard_clear_requested_ui': _wizard_clear_requested_ui(),
                        }, request=request)
                        return JsonResponse({'ok': True, 'html': html, 'wizard_step': 'config'})

                    # Non-AJAX fallback: just render config step.
                    controller_doors = _build_draft_controller_doors(cleaned)
                    return render(request, 'agent/device_access_form_inner.html', {
                        'form': form,
                        'obj': None,
                        'action_url': request.path,
                        'next_url': '/agent/menu/device/?tab=devices',
                        'controller_doors': controller_doors,
                        'system_time_zone': system_tz,
                        'system_time_now_local': system_now_local_str,
                        'show_derived_doors': True,
                        'wizard': True,
                        'wizard_token': wizard_token,
                        'wizard_step': 'config',
                        'wizard_doors_capacity': int((_wiz_get_draft(wizard_token) or {}).get('doors_capacity') or 0) or None,
                        'wizard_clear_requested_ui': _wizard_clear_requested_ui(),
                    })

                # Persist snapshot for door draft editor.
                try:
                    _wiz_update_device_snapshot(wizard_token, {
                        'name': str(cleaned.get('name') or ''),
                        'serial_number': str(cleaned.get('serial_number') or ''),
                        'hardware_version': str(cleaned.get('hardware_version') or ''),
                        'ip_address': str(cleaned.get('ip_address') or ''),
                        'port': int(cleaned.get('port') or 0) or 0,
                    })
                except Exception:
                    pass

                # Validate clear prerequisite if requested.
                draft = _wiz_get_draft(wizard_token)
                clear_required = bool(draft.get('clear_requested')) or bool(draft.get('clear_requested_ui'))
                clear_cmd_id = int(draft.get('clear_cmd_id') or 0) if str(draft.get('clear_cmd_id') or '').strip() else 0
                if clear_required:
                    row = CommandLog.objects.filter(id=clear_cmd_id).first() if clear_cmd_id else None
                    if (not row) or (str(getattr(row, 'status', '')).upper() != 'OK'):
                        form.add_error(None, 'Ștergerea datelor nu este confirmată ca finalizată. Reîncearcă ștergerea și apoi continuă.')
                        controller_doors = _build_draft_controller_doors(cleaned)
                        if wants_json:
                            from django.template.loader import render_to_string

                            html = render_to_string('agent/device_access_form_inner.html', {
                                'form': form,
                                'obj': None,
                                'action_url': request.path,
                                'next_url': '/agent/menu/device/?tab=devices',
                                'controller_doors': controller_doors,
                                'system_time_zone': system_tz,
                                'system_time_now_local': system_now_local_str,
                                'show_derived_doors': True,
                                'wizard': wizard,
                                'wizard_token': wizard_token,
                                'wizard_step': 'config',
                                'wizard_doors_capacity': int((draft or {}).get('doors_capacity') or 0) or None,
                                'wizard_clear_requested_ui': _wizard_clear_requested_ui(),
                            }, request=request)
                            return JsonResponse({'ok': False, 'message': 'Ștergerea datelor nu este confirmată.', 'html': html})
                        return render(request, 'agent/device_access_form_inner.html', {
                            'form': form,
                            'obj': None,
                            'action_url': request.path,
                            'next_url': '/agent/menu/device/?tab=devices',
                            'controller_doors': controller_doors,
                            'system_time_zone': system_tz,
                            'system_time_now_local': system_now_local_str,
                            'show_derived_doors': True,
                            'wizard': wizard,
                            'wizard_token': wizard_token,
                            'wizard_step': 'config',
                            'wizard_doors_capacity': int((draft or {}).get('doors_capacity') or 0) or None,
                            'wizard_clear_requested_ui': _wizard_clear_requested_ui(),
                        })

                # Validate door drafts (all doors for inferred capacity).
                cap = _infer_capacity(cleaned)
                cap = cap if cap > 0 else 1
                need = set(range(1, cap + 1))
                doors = draft.get('doors') if isinstance(draft.get('doors'), dict) else {}
                have = set()
                for k in (doors or {}).keys():
                    try:
                        have.add(int(str(k)))
                    except Exception:
                        continue
                if have != need:
                    form.add_error(None, 'Configurează ușile înainte de a crea centrala (apasă Editează la fiecare ușă).')
                    controller_doors = _build_draft_controller_doors(cleaned)
                    if wants_json:
                        from django.template.loader import render_to_string

                        html = render_to_string('agent/device_access_form_inner.html', {
                            'form': form,
                            'obj': None,
                            'action_url': request.path,
                            'next_url': '/agent/menu/device/?tab=devices',
                            'controller_doors': controller_doors,
                            'system_time_zone': system_tz,
                            'system_time_now_local': system_now_local_str,
                            'show_derived_doors': True,
                            'wizard': wizard,
                            'wizard_token': wizard_token,
                            'wizard_step': 'config',
                            'wizard_doors_capacity': int((draft or {}).get('doors_capacity') or 0) or None,
                            'wizard_clear_requested_ui': _wizard_clear_requested_ui(),
                        }, request=request)
                        return JsonResponse({'ok': False, 'message': 'Ușile nu sunt configurate complet.', 'html': html})
                    return render(request, 'agent/device_access_form_inner.html', {
                        'form': form,
                        'obj': None,
                        'action_url': request.path,
                        'next_url': '/agent/menu/device/?tab=devices',
                        'controller_doors': controller_doors,
                        'system_time_zone': system_tz,
                        'system_time_now_local': system_now_local_str,
                        'show_derived_doors': True,
                        'wizard': wizard,
                        'wizard_token': wizard_token,
                        'wizard_step': 'config',
                        'wizard_doors_capacity': int((draft or {}).get('doors_capacity') or 0) or None,
                        'wizard_clear_requested_ui': _wizard_clear_requested_ui(),
                    })

            saved = form.save()
            # Safety: enforce system TZ for scanners.
            try:
                if getattr(saved, 'scanner_linked', False) and system_tz and (saved.time_zone or '').strip() != system_tz:
                    saved.time_zone = system_tz
                    saved.save(update_fields=['time_zone'])
            except Exception:
                pass
            try:
                from agent.door_provisioning import ensure_controller_doors

                ensure_controller_doors(saved)
            except Exception:
                pass

            # Ensure a baseline status row exists so UI lists (that use latest_online)
            # don't render brand new devices as OFFLINE before CommCenter/tray updates.
            try:
                from agent.models import DeviceStatus

                if not DeviceStatus.objects.filter(device=saved).exists():
                    DeviceStatus.objects.create(device=saved, online=True, door_state='CLOSED')
            except Exception:
                pass

            # Wizard draft flow: apply draft door config onto provisioned doors, then clear draft.
            if wizard and wizard_token:
                try:
                    draft = _wiz_get_draft(wizard_token)
                    doors = draft.get('doors') if isinstance(draft.get('doors'), dict) else {}
                    for k, v in (doors or {}).items():
                        try:
                            dn = int(str(k))
                        except Exception:
                            continue
                        if not isinstance(v, dict):
                            continue
                        d = Door.objects.filter(device=saved, door_number=dn).first()
                        if not d:
                            continue
                        if (v.get('name') or '').strip():
                            d.name = str(v.get('name') or '').strip()[:128]
                        if v.get('reader_in_custom_name') is not None:
                            d.reader_in_custom_name = str(v.get('reader_in_custom_name') or '')[:128]
                        if v.get('reader_out_custom_name') is not None:
                            d.reader_out_custom_name = str(v.get('reader_out_custom_name') or '')[:128]
                        if v.get('normally_open') is not None:
                            d.normally_open = bool(v.get('normally_open'))
                        if v.get('enabled') is not None:
                            d.enabled = bool(v.get('enabled'))

                        # Full legacy-like fields (optional in draft).
                        if v.get('door_active_time_zone') is not None:
                            try:
                                d.door_active_time_zone_id = int(v.get('door_active_time_zone') or 0) or None
                            except Exception:
                                d.door_active_time_zone_id = None
                        if v.get('door_passage_mode_time_zone') is not None:
                            try:
                                d.door_passage_mode_time_zone_id = int(v.get('door_passage_mode_time_zone') or 0) or None
                            except Exception:
                                d.door_passage_mode_time_zone_id = None
                        if v.get('lock_open_duration') is not None:
                            try:
                                d.lock_open_duration = int(v.get('lock_open_duration') or 5)
                            except Exception:
                                pass
                        if v.get('punch_interval') is not None:
                            try:
                                d.punch_interval = int(v.get('punch_interval') or 2)
                            except Exception:
                                pass
                        if v.get('door_sensor_type') is not None:
                            d.door_sensor_type = str(v.get('door_sensor_type') or '')[:20]
                        if v.get('door_status_delay') is not None:
                            try:
                                d.door_status_delay = int(v.get('door_status_delay') or 15)
                            except Exception:
                                pass
                        if v.get('close_and_reverse_state') is not None:
                            d.close_and_reverse_state = bool(v.get('close_and_reverse_state'))
                        if v.get('verify_mode') is not None:
                            d.verify_mode = str(v.get('verify_mode') or '')[:32]
                        if v.get('duress_password') is not None:
                            d.duress_password = str(v.get('duress_password') or '')[:16]
                        if v.get('emergency_password') is not None:
                            d.emergency_password = str(v.get('emergency_password') or '')[:16]

                        d.save(update_fields=[
                            'name',
                            'reader_in_custom_name',
                            'reader_out_custom_name',
                            'door_active_time_zone',
                            'door_passage_mode_time_zone',
                            'lock_open_duration',
                            'punch_interval',
                            'door_sensor_type',
                            'door_status_delay',
                            'close_and_reverse_state',
                            'verify_mode',
                            'duress_password',
                            'emergency_password',
                            'normally_open',
                            'enabled',
                        ])

                    # Remove draft from session (commit completed)
                    store = _wiz_get_store()
                    if wizard_token in store:
                        try:
                            del store[wizard_token]
                        except Exception:
                            pass
                        _wiz_set_store(store)
                except Exception:
                    pass
            _audit_log(
                request,
                module='device',
                action='create',
                entity_id=saved.id,
                entity_name=getattr(saved, 'name', '') or '',
            )
            clear_command_id = None
            clear_requested = False
            try:
                # Wizard-only semantics: queue clear-on-add asynchronously after create.
                # Always surface a command id when the checkbox is set so the UI can block
                # continuation and show progress, even if controller detection is imperfect.
                clear_requested = bool(wizard and bool(getattr(saved, 'clear_on_add', False)))
                if clear_requested:
                    row = CommandLog.objects.create(device=saved, command='CLEAR_DEVICE_DATA', status='PENDING')
                    clear_command_id = int(row.id)
            except Exception:
                clear_command_id = None
            if wants_json:
                from django.template.loader import render_to_string

                html = render_to_string('agent/device_access_saved_inner.html', {
                    'obj': saved,
                    'clear_command_id': clear_command_id,
                    'clear_requested': clear_requested,
                }, request=request)
                return JsonResponse({'ok': True, 'message': 'Centrala a fost creată.', 'html': html, 'device_id': int(saved.id)})

            return render(request, 'agent/device_access_saved_inner.html', {'obj': saved, 'clear_command_id': clear_command_id, 'clear_requested': clear_requested})

        # Invalid form (AJAX): return replacement HTML.
        if wants_json:
            from django.template.loader import render_to_string

            controller_doors = []
            try:
                if wizard and wizard_token:
                    cleaned = dict(getattr(form, 'data', {}) or {})
                    controller_doors = _build_draft_controller_doors(cleaned)
            except Exception:
                controller_doors = []
            html = render_to_string('agent/device_access_form_inner.html', {
                'form': form,
                'obj': None,
                'action_url': request.path,
                'next_url': '/agent/menu/device/?tab=devices',
                'controller_doors': controller_doors,
                'system_time_zone': system_tz,
                'system_time_now_local': system_now_local_str,
                'show_derived_doors': bool(wizard_step == 'config'),
                'wizard': wizard,
                'wizard_token': wizard_token,
                'wizard_step': wizard_step,
                'wizard_doors_capacity': int((_wiz_get_draft(wizard_token) or {}).get('doors_capacity') or 0) or None,
                'wizard_clear_requested_ui': _wizard_clear_requested_ui(),
            }, request=request)
            return JsonResponse({'ok': False, 'message': 'Eroare validare.', 'html': html})
    else:
        initial = {}
        try:
            for k in ('name', 'serial_number', 'hardware_version', 'ip_address', 'comm_password'):
                v = (request.GET.get(k) or '').strip()
                if v:
                    initial[k] = v
            port_raw = (request.GET.get('port') or '').strip()
            if port_raw:
                try:
                    initial['port'] = int(port_raw)
                except Exception:
                    pass
            clear_raw = (request.GET.get('clear_on_add') or '').strip().lower()
            if clear_raw in ('1', 'true', 'yes', 'on'):
                initial['clear_on_add'] = True
        except Exception:
            initial = {}

        # Legacy-like default: prefill device TZ with the system TZ for controllers too.
        try:
            if system_tz and (initial.get('time_zone') is None) and not (initial.get('time_zone') or '').strip():
                initial['time_zone'] = system_tz
        except Exception:
            pass

        form = DeviceExtendedForm(initial=initial, wizard=wizard, wizard_step=wizard_step)

        # If wizard_token is present, merge any session draft snapshot as defaults.
        if wizard and wizard_token:
            try:
                draft = _wiz_get_draft(wizard_token)
                dev = draft.get('device') if isinstance(draft.get('device'), dict) else {}
                for k in ('name', 'serial_number', 'hardware_version', 'ip_address', 'port'):
                    if (not initial.get(k)) and dev.get(k):
                        initial[k] = dev.get(k)
                form = DeviceExtendedForm(initial=initial, wizard=wizard, wizard_step=wizard_step)
            except Exception:
                pass

    # Persist snapshot so door draft editor shows context even before posting.
    if wizard and wizard_token:
        try:
            snap = {
                'name': str((form.initial.get('name') or '')).strip(),
                'serial_number': str((form.initial.get('serial_number') or '')).strip(),
                'hardware_version': str((form.initial.get('hardware_version') or '')).strip(),
                'ip_address': str((form.initial.get('ip_address') or '')).strip(),
                'port': int(form.initial.get('port') or 0) if str(form.initial.get('port') or '').strip() else 0,
            }
            _wiz_update_device_snapshot(wizard_token, snap)
        except Exception:
            pass

        # Store discovered capacity (if provided by discovery modal).
        try:
            cap_raw = (request.GET.get('doors_capacity') or '').strip()
            if cap_raw:
                cap = int(cap_raw)
                if cap > 0:
                    _wiz_set_meta(wizard_token, doors_capacity=cap)
        except Exception:
            pass

    # In create wizard draft mode, build a server-side derived doors list so we can
    # render legacy-like per-door Edit buttons.
    controller_doors = []
    if wizard and wizard_token and wizard_step == 'config':
        try:
            cleaned = dict(getattr(form, 'initial', {}) or {})
            controller_doors = _build_draft_controller_doors(cleaned)
        except Exception:
            controller_doors = []

    wizard_doors_capacity = None
    try:
        if wizard and wizard_token:
            draft = _wiz_get_draft(wizard_token)
            wizard_doors_capacity = int((draft or {}).get('doors_capacity') or 0) or None
    except Exception:
        wizard_doors_capacity = None

    return render(
        request,
        'agent/device_access_form_inner.html',
        {
            'form': form,
            'obj': obj,
            'action_url': request.path,
            # In a modal, cancel is handled via data-modal-close; next_url is a fallback.
            'next_url': '/agent/menu/device/?tab=devices',
            'controller_doors': controller_doors,
            'system_time_zone': system_tz,
            'system_time_now_local': system_now_local_str,
            'show_derived_doors': bool(wizard_step == 'config'),
            'wizard': wizard,
            'wizard_token': wizard_token,
            'wizard_step': wizard_step,
            'wizard_doors_capacity': wizard_doors_capacity,
            'wizard_clear_requested_ui': _wizard_clear_requested_ui(),
        },
    )


@csrf_exempt
def wizard_clear_device(request: HttpRequest):
    """Wizard-only clear operation executed before the Device exists in DB.

    Creates a CommandLog row (device NULL) and updates its status asynchronously.
    """
    if not request.user.is_authenticated or not request.user.is_staff:
        return JsonResponse({'ok': False, 'error': 'unauthorized'}, status=403)
    if request.method != 'POST':
        return JsonResponse({'ok': False, 'error': 'method-not-allowed'}, status=405)

    try:
        payload = json.loads((request.body or b'{}').decode('utf-8') or '{}')
    except Exception:
        payload = {}

    ip = str(payload.get('ip') or '').strip()
    port = int(payload.get('port') or 0) if str(payload.get('port') or '').strip() else 0
    comm_password = str(payload.get('comm_password') or '').strip()
    if not comm_password:
        comm_password = _get_default_comm_password_cached()
    wizard_token = str(payload.get('wizard_token') or '').strip()

    if not ip:
        return JsonResponse({'ok': False, 'error': 'missing-ip'}, status=400)
    if not (port > 0 and port <= 65535):
        return JsonResponse({'ok': False, 'error': 'missing-port'}, status=400)

    row = CommandLog.objects.create(device=None, door=None, command=f'WIZARD_CLEAR_DEVICE {ip}:{port}', status='RUNNING')

    # Link into wizard session so finalize can validate OK.
    try:
        if wizard_token:
            store = request.session.get('wizard_device_drafts')
            if not isinstance(store, dict):
                store = {}
            draft = store.get(wizard_token)
            if not isinstance(draft, dict):
                draft = {}
            draft['clear_requested'] = True
            draft['clear_cmd_id'] = int(row.id)
            store[wizard_token] = draft
            request.session['wizard_device_drafts'] = store
            try:
                request.session.modified = True
            except Exception:
                pass
    except Exception:
        pass

    def _runner(cmd_id: int, ipaddr: str, p: int, pw: str) -> None:
        import time
        from pathlib import Path

        try:
            from django.db import close_old_connections

            close_old_connections()
        except Exception:
            pass

        started = time.time()
        ok = True
        parts: list[str] = []

        def _mark_running() -> None:
            info = (';'.join([x for x in parts if x]) or 'running')[:240]
            try:
                CommandLog.objects.filter(id=int(cmd_id)).update(
                    status='RUNNING',
                    result=info,
                    executed_at=timezone.now(),
                )
            except Exception:
                pass

        # Validate that plcommpro can CONNECT to the controller.
        # We try the user-selected port first, then known controller ports.
        # This avoids common cases where a TCP bridge port is open (e.g. 14370) but does not
        # speak the controller protocol.
        probed_dll: str | None = None
        pw_for_ops = str(pw or '')
        port_for_ops = int(p)
        proto_for_ops = 'TCP'

        # Quick visibility: which common TCP ports are open right now?
        try:
            import socket

            def _tcp_open(port_num: int) -> bool:
                sock: socket.socket | None = None
                try:
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.settimeout(0.4)
                    sock.connect((str(ipaddr), int(port_num)))
                    return True
                except Exception:
                    return False
                finally:
                    try:
                        if sock:
                            sock.close()
                    except Exception:
                        pass

            scan_ports: list[int] = []
            for cp in [int(p), 4370, 4371, 4372, 14370, 443, 80, 8080]:
                try:
                    if cp > 0 and cp <= 65535 and cp not in scan_ports:
                        scan_ports.append(cp)
                except Exception:
                    pass
            open_ports = [cp for cp in scan_ports if _tcp_open(int(cp))]
            if open_ports:
                parts.append('tcpopen=' + ','.join([str(x) for x in open_ports[:8]]))
                _mark_running()
        except Exception:
            pass
        try:
            from agent.plcommpro_bridge import PlcommproConnInfo, connect_only

            # For newer PRO controllers (commonly on TCP 14370), the Standalone SDK bundle
            # tends to be more reliable than older PullSDK builds. Prefer the x86 DLL here:
            # our bridge runner is proven stable for x86 operations (GetDeviceParam/DeleteDeviceData/etc).
            sdk_x86_hint: str | None = None
            try:
                repo_root = Path(__file__).resolve().parents[2]
                cand = repo_root / 'Resurse' / 'Standalone SDK-6.3.1.55' / 'SDK' / 'x86' / 'plcommpro.dll'
                if cand.exists() and cand.is_file():
                    sdk_x86_hint = str(cand)
            except Exception:
                sdk_x86_hint = None

            # Candidate ports: selected + common controller ports.
            cand_ports: list[int] = []
            for cp in [int(p), 4370, 4371, 4372, 14370]:
                try:
                    if cp > 0 and cp <= 65535 and cp not in cand_ports:
                        cand_ports.append(cp)
                except Exception:
                    pass

            rr: dict | None = None
            for try_port in cand_ports:
                port_for_ops = int(try_port)
                for try_proto in ('TCP', 'UDP'):
                    proto_for_ops = str(try_proto)
                    # attempt with provided/default password
                    probe_conn = PlcommproConnInfo(
                        ipaddress=str(ipaddr),
                        ip_port=int(port_for_ops),
                        password=str(pw_for_ops),
                        timeout=1500,
                        protocol=str(proto_for_ops),
                    )
                    rr_try = connect_only(
                        probe_conn,
                        process_timeout_s=8,
                        dll_path=(sdk_x86_hint if int(port_for_ops) == 14370 else None),
                    )
                    if isinstance(rr_try, dict) and bool(rr_try.get('ok')):
                        rr = rr_try
                        break

                    # retry once with blank password (common after reset)
                    if pw_for_ops:
                        try:
                            probe_conn_blank = PlcommproConnInfo(
                                ipaddress=str(ipaddr),
                                ip_port=int(port_for_ops),
                                password='',
                                timeout=1500,
                                protocol=str(proto_for_ops),
                            )
                            rr_blank = connect_only(
                                probe_conn_blank,
                                process_timeout_s=8,
                                dll_path=(sdk_x86_hint if int(port_for_ops) == 14370 else None),
                            )
                            if isinstance(rr_blank, dict) and bool(rr_blank.get('ok')):
                                rr = rr_blank
                                pw_for_ops = ''
                                parts.append('pw=blank')
                                _mark_running()
                                break
                        except Exception:
                            pass

                    rr = rr_try if isinstance(rr_try, dict) else None
                if isinstance(rr, dict) and bool(rr.get('ok')):
                    break

            if not (isinstance(rr, dict) and bool(rr.get('ok'))):
                ok = False
                try:
                    rres = rr.get('result') if isinstance(rr, dict) else 'err'
                    rle = rr.get('last_error') if isinstance(rr, dict) else None
                    data = str(rr.get('data') or '') if isinstance(rr, dict) else ''
                    data = data.replace('\r', ' ').replace('\n', ' ').strip()
                    if len(data) > 120:
                        data = data[:120] + '…'
                    dll_used = str(rr.get('dll_path_used') or '').strip() if isinstance(rr, dict) else ''
                    if dll_used:
                        try:
                            dll_used = os.path.basename(dll_used)
                        except Exception:
                            pass
                    note = f"probe:sdk:fail@{str(proto_for_ops)}:{int(port_for_ops)}:{rres}" + (f":{rle}" if rle is not None else '')
                    if dll_used:
                        note += f":dll={dll_used}"
                    if data:
                        note += f":{data}"
                    parts.append(note)
                except Exception:
                    parts.append(
                        f"probe:sdk:fail@{str(proto_for_ops)}:{int(port_for_ops)}:{rr.get('result') if isinstance(rr, dict) else 'err'}"
                        + (
                            f":{rr.get('last_error')}" if isinstance(rr, dict) and rr.get('last_error') is not None else ''
                        )
                    )
                _mark_running()
            else:
                try:
                    probed_dll = str(rr.get('dll_path_used') or '').strip() or None
                except Exception:
                    probed_dll = None
                parts.append(f'port={int(port_for_ops)}')
                parts.append(f'proto={str(proto_for_ops).lower()}')
                parts.append('probe:sdk:ok')
                _mark_running()
        except Exception as ex:
            ok = False
            parts.append(f'probe:sdk:exc:{ex}')
            _mark_running()

        if not ok:
            info = (';'.join([x for x in parts if x]) or 'err')[:240]
            try:
                CommandLog.objects.filter(id=int(cmd_id)).update(
                    status='ERR',
                    result=info,
                    executed_at=timezone.now(),
                )
            except Exception:
                pass
            return
        try:
            from agent.plcommpro_bridge import (
                PlcommproConnInfo,
                default_plcommpro_dll_path,
                delete_device_data,
                get_device_options,
                query_data,
            )

            conn = PlcommproConnInfo(
                ipaddress=str(ipaddr),
                ip_port=int(port_for_ops),
                password=str(pw_for_ops or ''),
                # Clear runs in background; prefer reliability over short timeouts.
                # C3-Pro controllers can take >60s for some DeleteDeviceData ops.
                timeout=300000,
                protocol=str(proto_for_ops),
            )

            # Determine a working plcommpro.dll once, then pin it for deletes.
            pinned_dll: str | None = None
            try:
                pinned_dll = str(default_plcommpro_dll_path() or '').strip() or None
                if pinned_dll:
                    parts.append('dll:default')
            except Exception:
                pinned_dll = None

            # If the SDK probe already picked a viable DLL, prefer it.
            try:
                if probed_dll:
                    pinned_dll = probed_dll
                    parts.append('dll:probe')
            except Exception:
                pass
            try:
                warm = get_device_options(conn, 'IPAddress', process_timeout_s=15, dll_path=pinned_dll)
                if isinstance(warm, dict) and warm.get('ok'):
                    warm_used = str(warm.get('dll_path_used') or '').strip() or None
                    if warm_used:
                        pinned_dll = warm_used
                        parts.append('dll:ok')
                else:
                    parts.append('dll:skip')
            except Exception:
                parts.append('dll:skip')

            _mark_running()

            def _delete_filtered(table: str, filter_str: str, timeout_s: int) -> tuple[bool, str]:
                try:
                    r = delete_device_data(
                        conn,
                        table,
                        filter_str,
                        process_timeout_s=int(timeout_s),
                        dll_path=pinned_dll,
                    )
                    res = int(r.get('result', -1) or -1)
                    if res >= 0:
                        return True, 'ok'
                    le = r.get('last_error')
                    return False, f'err{res}{":" + str(le) if le is not None else ""}'
                except Exception as e:
                    msg = str(e)
                    if 'timed out' in msg.lower():
                        return False, 'timeout'
                    return False, 'exc'

            _cached_pins: list[str] | None = None

            def _get_user_pins() -> list[str]:
                nonlocal _cached_pins
                if _cached_pins is not None:
                    return _cached_pins
                pins: list[str] = []
                try:
                    qr = query_data(
                        conn,
                        'user',
                        fields='Pin',
                        filter='',
                        option='',
                        buffer_len=256 * 1024,
                        process_timeout_s=120,
                        dll_path=pinned_dll,
                    )
                    if qr.get('ok') and qr.get('data'):
                        raw = str(qr.get('data') or '')
                        # Formats seen in the wild:
                        #  - key=value\tkey=value ...
                        #  - CSV/tabular with header row (e.g. "Pin" then values)
                        lines = [ln.strip() for ln in raw.replace('\r', '\n').split('\n') if ln.strip()]
                        if lines:
                            # Skip header if present.
                            try:
                                if '=' not in lines[0] and str(lines[0]).strip().lower() in ('pin', 'pin,', 'pin;'):
                                    lines = lines[1:]
                            except Exception:
                                pass
                        for ln in lines:
                            if not ln:
                                continue
                            if '=' in ln:
                                for part in ln.split('\t'):
                                    if '=' not in part:
                                        continue
                                    k, v = part.split('=', 1)
                                    if str(k).strip().lower() == 'pin':
                                        pval = str(v or '').strip()
                                        if pval:
                                            pins.append(pval)
                                continue
                            # Plain values (single column)
                            if ',' in ln:
                                ln = ln.split(',', 1)[0].strip()
                            if ln and ln.lower() != 'pin':
                                pins.append(ln)
                except Exception:
                    pins = []
                # De-dupe and keep stable order.
                seen = set()
                out: list[str] = []
                for p in pins:
                    if p in seen:
                        continue
                    seen.add(p)
                    out.append(p)
                _cached_pins = out
                return out

            def _delete_by_pins(table: str, pins: list[str], timeout_s: int, *, batch_size: int = 200) -> tuple[bool, str]:
                if not pins:
                    return True, 'empty'
                total = (len(pins) + batch_size - 1) // batch_size
                for idx in range(total):
                    batch = pins[idx * batch_size : (idx + 1) * batch_size]
                    filt = '\r\n'.join([f'Pin={p}' for p in batch if str(p).strip()])
                    if not filt:
                        continue
                    ok_b, note_b = _delete_filtered(table, filt, timeout_s=int(timeout_s))
                    # Keep only one progress marker per table.
                    try:
                        parts[:] = [pp for pp in parts if not str(pp).startswith(f'{table}:batch:')]
                    except Exception:
                        pass
                    parts.append(f'{table}:batch:{idx + 1}/{total}')
                    _mark_running()
                    if not ok_b:
                        return False, note_b
                return True, 'ok'

            def _del(table: str, timeout_s: int) -> tuple[bool, str]:
                """Attempt a device table delete.

                Returns (ok, note) where note is compact and safe to surface.
                """
                try:
                    r = delete_device_data(
                        conn,
                        table,
                        '',
                        process_timeout_s=int(timeout_s),
                        dll_path=pinned_dll,
                    )
                    res = int(r.get('result', -1) or -1)
                    if res >= 0:
                        return True, 'ok'
                    le = r.get('last_error')
                    dll_used = None
                    try:
                        dll_used = str(r.get('dll_path_used') or '').strip() or None
                        if dll_used:
                            dll_used = os.path.basename(dll_used)
                    except Exception:
                        dll_used = None

                    # Some firmware/SDK combos can return a generic failure code even when
                    # the table is already empty. Treat that as OK to prevent wizard dead-ends.
                    try:
                        from agent.plcommpro_bridge import data_count

                        cnt = data_count(conn, table, process_timeout_s=30)
                        if isinstance(cnt, dict) and cnt.get('ok') and int(cnt.get('result') or 0) == 0:
                            return True, 'ok(empty)'
                    except Exception:
                        pass

                    note = f'err{res}{":" + str(le) if le is not None else ""}'
                    if dll_used:
                        note += f':dll={dll_used}'
                    return False, note
                except Exception as e:
                    msg = str(e)
                    if 'timed out' in msg.lower():
                        return False, 'timeout'
                    return False, 'exc'

            # Required data clear: auth then users.
            # Runs in background; keep a generous but bounded total.
            max_total_s = 900
            required_groups: list[tuple[str, tuple[str, ...], int]] = [
                ('auth', ('userauthorize', 'UserAuthorize', 'USERAUTHORIZE'), 600),
                ('users', ('user', 'User', 'userinfo', 'UserInfo', 'USERINFO'), 600),
            ]

            for label, candidates, timeout_s in required_groups:
                if time.time() - started > max_total_s:
                    ok = False
                    parts.append('err:deadline')
                    _mark_running()
                    break
                chosen = None
                last_note = None
                for t in candidates:
                    ok_t, note = _del(t, timeout_s=int(timeout_s))
                    # Unsupported tables typically return err quickly; keep trying.
                    if ok_t:
                        chosen = t
                        break
                    last_note = note
                    # Fallback: some controllers time out on full-table delete for auth/users.
                    # When that happens, try per-Pin deletes (legacy filter format: one Pin=... per line).
                    try:
                        want_batch = label in ('auth', 'users') and (
                            note in ('timeout', 'exc') or str(note).startswith('err-2') or 'err-2:' in str(note)
                        )
                    except Exception:
                        want_batch = False
                    if want_batch:
                        pins = _get_user_pins()
                        if pins:
                            ok_b, note_b = _delete_by_pins(t, pins, timeout_s=int(timeout_s), batch_size=200)
                            if ok_b:
                                chosen = t
                                break
                            last_note = f'bat:{note_b}'
                    if note in ('timeout', 'exc'):
                        # Likely connectivity/SDK issue rather than a table name variant.
                        break
                if not chosen:
                    ok = False
                    parts.append(f'{label}:err:{last_note or "unknown"}')
                    _mark_running()
                    break
                parts.append(f'{label}:{chosen}:ok')
                _mark_running()

            # Optional tables: best-effort.
            if ok and (time.time() - started) <= max_total_s:
                optional_tables = ('templatev10', 'template', 'usertype', 'UserType')
                for t in optional_tables:
                    if time.time() - started > max_total_s:
                        parts.append('optional:skip:deadline')
                        _mark_running()
                        break
                    ok_t, note = _del(t, timeout_s=20)
                    parts.append(f'{t}:{"ok" if ok_t else "skip"}')
                    _mark_running()
                    if note in ('timeout', 'exc'):
                        break
        except Exception as e:
            ok = False
            parts.append(f'err:{e}')

        info = (';'.join([x for x in parts if x]) or ('ok' if ok else 'err'))[:240]
        try:
            CommandLog.objects.filter(id=int(cmd_id)).update(
                status='OK' if ok else 'ERR',
                result=info,
                executed_at=timezone.now(),
            )
        except Exception:
            pass

    threading.Thread(target=_runner, args=(int(row.id), ip, int(port), comm_password), daemon=True).start()
    return JsonResponse({'ok': True, 'command_id': int(row.id)})


def wizard_door_draft_edit(request: HttpRequest, door_no: int):
    if not request.user.is_authenticated or not request.user.is_staff:
        from django.contrib.auth.views import redirect_to_login
        return redirect_to_login(request.get_full_path())

    wizard_token = (request.GET.get('wizard_token') or request.POST.get('wizard_token') or '').strip()
    if not wizard_token:
        return JsonResponse({'ok': False, 'error': 'missing-wizard-token'}, status=400)

    return_url = (request.GET.get('return_url') or request.POST.get('return_url') or '').strip()

    try:
        dn = int(door_no)
    except Exception:
        dn = 0
    if dn < 1 or dn > 32:
        return JsonResponse({'ok': False, 'error': 'invalid-door'}, status=400)

    store = request.session.get('wizard_device_drafts')
    if not isinstance(store, dict):
        store = {}
    draft = store.get(wizard_token)
    if not isinstance(draft, dict):
        draft = {}

    dev = draft.get('device') if isinstance(draft.get('device'), dict) else {}
    device_name = str((dev or {}).get('name') or '').strip()
    device_ip = str((dev or {}).get('ip_address') or '').strip()

    doors = draft.get('doors') if isinstance(draft.get('doors'), dict) else {}
    door_state = doors.get(str(dn)) if isinstance(doors.get(str(dn)), dict) else {}

    initial = {
        'door_number': dn,
        'name': str(door_state.get('name') or f'Ușă {dn}'),
        'reader_in_custom_name': str(door_state.get('reader_in_custom_name') or ''),
        'reader_out_custom_name': str(door_state.get('reader_out_custom_name') or ''),
        'door_active_time_zone': door_state.get('door_active_time_zone') or None,
        'door_passage_mode_time_zone': door_state.get('door_passage_mode_time_zone') or None,
        'lock_open_duration': door_state.get('lock_open_duration', 5),
        'punch_interval': door_state.get('punch_interval', 2),
        'door_sensor_type': door_state.get('door_sensor_type', 'normal_close'),
        'door_status_delay': door_state.get('door_status_delay', 15),
        'close_and_reverse_state': bool(door_state.get('close_and_reverse_state', False)),
        'verify_mode': door_state.get('verify_mode', 'only_card'),
        'duress_password': str(door_state.get('duress_password') or ''),
        'emergency_password': str(door_state.get('emergency_password') or ''),
        'normally_open': bool(door_state.get('normally_open', True)),
        'enabled': bool(door_state.get('enabled', True)),
    }

    if request.method == 'POST':
        form = WizardDoorDraftForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            doors[str(dn)] = {
                'name': str(cd.get('name') or '').strip(),
                'reader_in_custom_name': str(cd.get('reader_in_custom_name') or '').strip(),
                'reader_out_custom_name': str(cd.get('reader_out_custom_name') or '').strip(),
                'door_active_time_zone': int(getattr(cd.get('door_active_time_zone'), 'id', 0) or 0) or None,
                'door_passage_mode_time_zone': int(getattr(cd.get('door_passage_mode_time_zone'), 'id', 0) or 0) or None,
                'lock_open_duration': int(cd.get('lock_open_duration') or 5),
                'punch_interval': int(cd.get('punch_interval') or 2),
                'door_sensor_type': str(cd.get('door_sensor_type') or 'normal_close'),
                'door_status_delay': int(cd.get('door_status_delay') or 15),
                'close_and_reverse_state': bool(cd.get('close_and_reverse_state')),
                'verify_mode': str(cd.get('verify_mode') or 'only_card'),
                'duress_password': str(cd.get('duress_password') or '').strip(),
                'emergency_password': str(cd.get('emergency_password') or '').strip(),
                'normally_open': bool(cd.get('normally_open')),
                'enabled': bool(cd.get('enabled')),
            }
            draft['doors'] = doors
            store[wizard_token] = draft
            request.session['wizard_device_drafts'] = store
            try:
                request.session.modified = True
            except Exception:
                pass
            return render(request, 'agent/wizard_door_saved_inner.html', {'wizard_token': wizard_token, 'door_number': dn, 'return_url': return_url})
    else:
        form = WizardDoorDraftForm(initial=initial)

    return render(
        request,
        'agent/wizard_door_form_inner.html',
        {
            'form': form,
            'wizard_token': wizard_token,
            'door_number': dn,
            'device_name': device_name,
            'device_ip': device_ip,
            'return_url': return_url,
        },
    )


def device_operation_access(request: HttpRequest, pk: int, op: str):
    """Ultra-compact legacy-like device operation modals (Door Configuration -> More...)."""
    if not request.user.is_authenticated or not request.user.is_staff:
        from django.contrib.auth.views import redirect_to_login
        return redirect_to_login(request.get_full_path())

    dev = Device.objects.get(pk=pk)
    op = (op or '').strip().lower()

    OP_META = {
        'change-ip': {'title': 'Modifică IP'},
        'disable': {'title': 'Dezactivează centrală'},
        'enable': {'title': 'Activează centrală'},
        'toggle-enabled': {'title': 'Activare / Dezactivare centrală'},
        'comm-password': {'title': 'Modifică parola de comunicare'},
        'sync-time': {'title': 'Sincronizează ora', 'command': 'SYNC_TIME'},
        # CommCenter supports DOWN_NEWLOG (immediate download + persist), which
        # matches legacy "Get event entries" behavior better than a noop command.
        'get-events': {'title': 'Preia evenimente', 'command': 'DOWN_NEWLOG'},
        'get-personnel': {'title': 'Preia personal', 'command': 'GET_PERSONNEL'},
        'upgrade-firmware': {'title': 'Upgrade firmware'},
        'disable-dst': {'title': 'Dezactivează ora de vară', 'command': 'DISABLE_DST'},
        'enable-dst': {'title': 'Activează ora de vară', 'command': 'ENABLE_DST'},
        'fp-ident': {'title': 'Identificare amprentă', 'command': 'CHANGE_FP_IDENT'},
    }

    meta = OP_META.get(op)
    if not meta:
        return render(request, 'agent/device_operation_form_inner.html', {
            'dev': dev,
            'op': op,
            'title': 'Operation',
            'error': 'Unknown operation',
            'command_preview': '',
        })

    def _read_recent_device_logs(*, max_items: int = 120) -> dict:
        """Return recent persisted logs and command history for the device.

        Keep it fast and DB-only: does not touch hardware.
        """
        try:
            from agent.models import DeviceEventLog, DeviceRealtimeLog

            event_rows = list(
                DeviceEventLog.objects.filter(device_id=int(dev.id))
                .only('timestamp_str', 'code', 'raw_line', 'created_at')
                .order_by('-created_at')[: max_items]
            )
            rt_rows = list(
                DeviceRealtimeLog.objects.filter(device_id=int(dev.id))
                .only('raw', 'created_at')
                .order_by('-created_at')[: max_items]
            )
        except Exception:
            event_rows, rt_rows = [], []

        try:
            cmd_rows = list(
                CommandLog.objects.filter(device_id=int(dev.id))
                .only('command', 'status', 'result', 'created_at', 'executed_at')
                .order_by('-created_at')[: max_items]
            )
        except Exception:
            cmd_rows = []

        audit_rows = []
        try:
            if AuditLog is not None:
                audit_rows = list(
                    AuditLog.objects.filter(entity_id=int(dev.id), module__in=['device', 'command', 'device-status'])
                    .only('timestamp', 'module', 'action', 'entity_name', 'details', 'user')
                    .order_by('-timestamp')[: max_items]
                )
        except Exception:
            audit_rows = []

        # Unified timeline (best-effort) for the device.
        # Keep it bounded even when the modal is loaded with large limits.
        timeline_limit = int(max_items or 0)
        timeline_limit = max(50, min(10000, timeline_limit))

        from datetime import datetime

        def _safe_dt(v):
            return v if hasattr(v, 'year') else None

        def _parse_event_ts(s: str):
            s = (s or '').strip()
            if not s:
                return None
            # Common formats: "YYYY-MM-DD HH:MM:SS" or ISO-like
            for fmt in ('%Y-%m-%d %H:%M:%S', '%Y/%m/%d %H:%M:%S', '%Y-%m-%dT%H:%M:%S'):
                try:
                    return datetime.strptime(s[:19], fmt)
                except Exception:
                    continue
            return None

        timeline = []
        try:
            for r in (event_rows or [])[:timeline_limit]:
                ts = _parse_event_ts(getattr(r, 'timestamp_str', '') or '')
                ts = ts or _safe_dt(getattr(r, 'created_at', None))
                if not ts:
                    continue
                timeline.append({
                    'ts': ts,
                    'kind': 'EVENT',
                    'summary': f"code={getattr(r, 'code', '') or ''}",
                    'raw': getattr(r, 'raw_line', '') or '',
                })
        except Exception:
            pass

        try:
            for r in (rt_rows or [])[:timeline_limit]:
                ts = _safe_dt(getattr(r, 'created_at', None))
                if not ts:
                    continue
                timeline.append({
                    'ts': ts,
                    'kind': 'RTLOG',
                    'summary': 'rtlog',
                    'raw': getattr(r, 'raw', '') or '',
                })
        except Exception:
            pass

        try:
            for r in (cmd_rows or [])[:timeline_limit]:
                ts = _safe_dt(getattr(r, 'executed_at', None)) or _safe_dt(getattr(r, 'created_at', None))
                if not ts:
                    continue
                cmd = getattr(r, 'command', '') or ''
                status = getattr(r, 'status', '') or ''
                result = getattr(r, 'result', '') or ''
                timeline.append({
                    'ts': ts,
                    'kind': 'CMD',
                    'summary': f"{cmd} ({status})".strip(),
                    'raw': result,
                })
        except Exception:
            pass

        try:
            for a in (audit_rows or [])[:timeline_limit]:
                ts = _safe_dt(getattr(a, 'timestamp', None))
                if not ts:
                    continue
                module = getattr(a, 'module', '') or ''
                action = getattr(a, 'action', '') or ''
                details = getattr(a, 'details', '') or ''
                timeline.append({
                    'ts': ts,
                    'kind': 'AUDIT',
                    'summary': f"{module}:{action}",
                    'raw': details,
                })
        except Exception:
            pass

        try:
            timeline.sort(key=lambda x: x.get('ts'), reverse=True)
        except Exception:
            pass

        timeline_rows = timeline[:timeline_limit]

        counts = {'events': 0, 'rt': 0, 'cmd': 0, 'audit': 0}
        try:
            counts['events'] = int(DeviceEventLog.objects.filter(device_id=int(dev.id)).count())
        except Exception:
            pass
        try:
            counts['rt'] = int(DeviceRealtimeLog.objects.filter(device_id=int(dev.id)).count())
        except Exception:
            pass
        try:
            counts['cmd'] = int(CommandLog.objects.filter(device_id=int(dev.id)).count())
        except Exception:
            pass
        try:
            if AuditLog is not None:
                counts['audit'] = int(
                    AuditLog.objects.filter(entity_id=int(dev.id), module__in=['device', 'command', 'device-status']).count()
                )
        except Exception:
            pass

        return {
            'event_rows': event_rows,
            'rt_rows': rt_rows,
            'cmd_rows': cmd_rows,
            'audit_rows': audit_rows,
            'timeline_rows': timeline_rows,
            'timeline_limit': timeline_limit,
            'counts': counts,
        }

    def _safe_now_local_str() -> str:
        try:
            from datetime import timedelta

            from django.utils import timezone
            return timezone.localtime(timezone.now()).strftime('%Y-%m-%d %H:%M:%S')
        except Exception:
            return ''

    def _parse_plcommpro_rows(raw: str, field_order: list[str]) -> list[dict]:
        """Parse plcommpro GetDeviceData response into a list of dicts.

        Response is typically \r\n separated rows. Columns may be key=value\t...
        or plain delimiter-separated (tab/comma).
        """
        if not raw:
            return []
        rows: list[dict] = []
        lines = [ln.strip() for ln in raw.replace('\r', '\n').split('\n') if ln.strip()]
        if not lines:
            return []

        # Detect header-based CSV/tabular format: first row contains column names.
        header_map: dict[str, int] = {}
        try:
            first = lines[0]
            if '=' not in first:
                delim = '\t' if '\t' in first else ','
                cols = [c.strip() for c in first.split(delim) if c.strip()]
                if cols:
                    want = {str(f).strip().lower() for f in (field_order or []) if str(f).strip()}
                    got = {str(c).strip().lower() for c in cols}
                    if want and len(want & got) >= 1:
                        header_map = {str(c).strip().lower(): idx for idx, c in enumerate(cols)}
                        lines = lines[1:]
        except Exception:
            header_map = {}

        for ln in lines:
            # Most common format: key=value\tkey=value...
            parts = ln.split('\t') if '\t' in ln else ln.split(',')
            kv = {}
            for p in parts:
                p = p.strip()
                if not p:
                    continue
                if '=' in p:
                    k, v = p.split('=', 1)
                    kv[k.strip().lower()] = v.strip()
            if kv:
                out = {}
                for f in field_order:
                    out[f.lower()] = kv.get(f.lower(), '')
                rows.append(out)
                continue

            vals = [p.strip() for p in parts if p.strip()]
            if not vals:
                continue

            out = {}
            # Prefer header-based mapping when available.
            if header_map:
                for f in field_order:
                    idx = header_map.get(str(f).strip().lower())
                    out[str(f).lower()] = vals[idx] if (idx is not None and idx < len(vals)) else ''
                rows.append(out)
                continue

            # Fallback: positional mapping.
            for idx, f in enumerate(field_order):
                out[f.lower()] = vals[idx] if idx < len(vals) else ''
            rows.append(out)
        return rows

    def _decode_door_mask(mask_val: object, doors_by_number: dict[int, object]) -> str:
        try:
            mv = int(str(mask_val).strip() or '0')
        except Exception:
            mv = 0
        if mv <= 0:
            return ''
        nums: list[int] = []
        for n in sorted(doors_by_number.keys()):
            if n <= 0:
                continue
            if mv & (1 << (n - 1)):
                nums.append(int(n))
        # Render as "1,2,4" plus optional names.
        if not nums:
            return ''
        out = []
        for n in nums:
            d = doors_by_number.get(n)
            nm = (getattr(d, 'name', '') or '').strip()
            out.append(f"{n}{(' ' + nm) if nm else ''}".strip())
        return ', '.join(out)

    def _enqueue_tracked(device_id: int, cmd: str) -> tuple[bool, int | None, str]:
        """Create CommandLog and enqueue with LOGID prefix so CommCenter updates status."""
        # De-dupe heavy sync commands to avoid generating high traffic / DoS.
        try:
            if (cmd or '').strip().upper().startswith('SYNC_PERSONNEL'):
                try:
                    from agent.sync_limits import get_sync_personnel_limits

                    dedupe_s = int(get_sync_personnel_limits().dedupe_seconds)
                except Exception:
                    try:
                        import os
                        dedupe_s = int(os.getenv('SYNC_PERSONNEL_DEDUPE_SECONDS', '60'))
                    except Exception:
                        dedupe_s = 60
                    dedupe_s = max(5, min(600, dedupe_s))
                from datetime import timedelta
                from django.utils import timezone as _tz
                cutoff = _tz.now() - timedelta(seconds=dedupe_s)
                existing = (
                    CommandLog.objects.filter(device_id=int(device_id), command__startswith='SYNC_PERSONNEL', status='PENDING', created_at__gte=cutoff)
                    .order_by('-created_at')
                    .first()
                )
                if existing:
                    return (True, int(existing.id), 'already_queued')
        except Exception:
            pass

        try:
            log = CommandLog.objects.create(device_id=int(device_id), command=(cmd or '')[:240], status='PENDING')
        except Exception as e:
            return (False, None, f"commandlog_create_failed:{e}")

        # Similar safety gates as _enqueue()
        try:
            dev0 = Device.objects.filter(id=int(device_id)).first()
            if dev0 is None:
                log.status, log.result = 'ERR', 'device-not-found'
                log.save(update_fields=['status', 'result'])
                return (False, int(log.id), 'device-not-found')
            if not getattr(dev0, 'enabled', True):
                log.status, log.result = 'ERR', 'device-disabled'
                log.save(update_fields=['status', 'result'])
                return (False, int(log.id), 'device-disabled')
            ds0 = DeviceStatus.objects.filter(device=dev0).first()
            if ds0 is not None and not ds0.online:
                log.status, log.result = 'ERR', 'device-offline'
                log.save(update_fields=['status', 'result'])
                return (False, int(log.id), 'device-offline')
        except Exception:
            pass

        try:
            from agent.modern_comm_center import build_and_run_stub  # avoid circular import
            import agent.modern_comm_center as mcc
            center = getattr(mcc, 'ACTIVE_CENTER', None)
            if center is None:
                center = build_and_run_stub(poll_interval=1.0, driver='auto')
                mcc.ACTIVE_CENTER = center
            center.enqueue_command(int(device_id), f"LOGID:{int(log.id)} {cmd}"[:240])
            try:
                _broadcast_command(log)
            except Exception:
                pass
            return (True, int(log.id), 'queued')
        except Exception as e:
            try:
                log.status = 'ERR'
                log.result = 'enqueue-failed'
                log.save(update_fields=['status', 'result'])
            except Exception:
                pass
            return (False, int(log.id), f"enqueue_failed:{e}")

    def _guess_net(ip_str: str) -> tuple[str, str]:
        try:
            import ipaddress

            ip = ipaddress.ip_address((ip_str or '').strip())
            if ip.version != 4:
                return ('', '')
            parts = str(ip).split('.')
            if len(parts) != 4:
                return ('', '')
            gw = '.'.join(parts[:3] + ['254'])
            return (gw, '255.255.255.0')
        except Exception:
            return ('', '')

    ctx_error = None
    if request.method == 'POST':
        error = None
        message = None
        action_state = 'success'
        action_title = 'OK'
        action_message = ''
        close_delay_ms = 250
        try:
            if op == 'change-ip':
                ip_address = (request.POST.get('ip_address') or '').strip()
                port = int(request.POST.get('port') or dev.port or 4370)
                gateway = (request.POST.get('gateway') or '').strip()
                subnet_mask = (request.POST.get('subnet_mask') or '').strip()
                if not ip_address:
                    raise ValueError('Please enter the new IP address.')
                if port < 1 or port > 65535:
                    raise ValueError('Invalid port. Use 1-65535.')

                if not dev.ip_address:
                    raise ValueError('Device has no current IP address saved (original IP missing).')

                # Guess defaults early (legacy screenshot: /24 + gateway .254)
                guess_gw, guess_mask = _guess_net(str(dev.ip_address))
                if not subnet_mask:
                    subnet_mask = guess_mask
                if not gateway:
                    gateway = guess_gw

                # Best-effort: if gateway/mask not provided, try to read from device.
                if not gateway or not subnet_mask:
                    try:
                        from .plcommpro_bridge import PlcommproConnInfo, get_device_options

                        conn = PlcommproConnInfo(
                            ipaddress=str(dev.ip_address),
                            ip_port=int(dev.port or 4370),
                            password=str(dev.comm_password or ''),
                            timeout=3000,
                        )
                        resp = get_device_options(conn, 'NetMask,GATEIPAddress')
                        if resp.get('ok') and resp.get('data'):
                            kv = {}
                            for part in str(resp.get('data') or '').split(','):
                                if '=' in part:
                                    k, v = part.split('=', 1)
                                    kv[k.strip()] = v.strip()
                            if not subnet_mask:
                                subnet_mask = kv.get('NetMask', '') or subnet_mask
                            if not gateway:
                                gateway = kv.get('GATEIPAddress', '') or gateway
                    except Exception:
                        pass

                if not gateway:
                    raise ValueError('Please enter the gateway address.')
                if not subnet_mask:
                    raise ValueError('Please enter the subnet mask.')

                # Push the change to the hardware (legacy behavior: SET OPTION ...)
                try:
                    from .plcommpro_bridge import PlcommproConnInfo, set_device_options

                    conn = PlcommproConnInfo(
                        ipaddress=str(dev.ip_address),
                        ip_port=int(dev.port or 4370),
                        password=str(dev.comm_password or ''),
                        timeout=3000,
                    )
                    items = f"IPAddress={ip_address},GATEIPAddress={gateway},NetMask={subnet_mask}"
                    resp = set_device_options(conn, items)
                    if not resp.get('ok'):
                        raise RuntimeError(
                            f"device rejected change-ip: result={resp.get('result')} last_error={resp.get('last_error')}"
                        )
                except Exception as ex:
                    raise RuntimeError(f"hardware change-ip failed: {ex}")

                old_ip = dev.ip_address
                dev.ip_address = ip_address
                dev.port = port
                dev.save(update_fields=['ip_address', 'port'])
                _audit_log(
                    request,
                    module='device',
                    action='update',
                    entity_id=int(dev.id),
                    entity_name=getattr(dev, 'name', '') or '',
                    details=f"change_ip {old_ip} -> {ip_address} port={port} gw={gateway} mask={subnet_mask}",
                )
                # Best-effort legacy sync
                try:
                    from legacy_models.models import Device as LegacyDevice  # type: ignore
                    legacy = LegacyDevice.objects.filter(sn=dev.serial_number or dev.name).first()
                    if legacy:
                        legacy.com_address = ip_address
                        legacy.save(update_fields=['com_address'])
                except Exception:
                    pass
                message = f"IP changed on device and updated to {ip_address}:{port}"
                action_title = 'MODIFICARE IP'
                action_message = 'Modificare IP realizată cu succes.'

            elif op in ('disable', 'enable'):
                # Legacy: separate menu items.
                dev.enabled = bool(op == 'enable')
                dev.save(update_fields=['enabled'])
                _audit_log(
                    request,
                    module='device',
                    action='toggle_enabled',
                    entity_id=int(dev.id),
                    entity_name=getattr(dev, 'name', '') or '',
                    details=f"enabled={bool(dev.enabled)}",
                )
                if dev.enabled:
                    message = 'Device enabled.'
                    action_state = 'success'
                    action_title = 'ACTIVARE CENTRALĂ'
                    action_message = 'ACTIVARE CENTRALĂ REALIZATĂ CU SUCCES'
                else:
                    message = 'Device disabled.'
                    # Use red palette in the action modal for DISABLE (legacy feel)
                    action_state = 'error'
                    action_title = 'DEZACTIVARE CENTRALĂ'
                    action_message = 'DEZACTIVARE CENTRALĂ REALIZATĂ CU SUCCES'
                close_delay_ms = 900

            elif op == 'toggle-enabled':
                enabled_val = (request.POST.get('enabled') or '').strip()
                dev.enabled = bool(enabled_val in ('1', 'true', 'yes', 'on'))
                dev.save(update_fields=['enabled'])
                _audit_log(
                    request,
                    module='device',
                    action='toggle_enabled',
                    entity_id=int(dev.id),
                    entity_name=getattr(dev, 'name', '') or '',
                    details=f"enabled={bool(dev.enabled)}",
                )
                message = 'Device enabled.' if dev.enabled else 'Device disabled.'

            elif op == 'comm-password':
                comm_password = (request.POST.get('comm_password') or '').strip()
                dev.comm_password = comm_password
                dev.save(update_fields=['comm_password'])
                _audit_log(
                    request,
                    module='device',
                    action='update',
                    entity_id=int(dev.id),
                    entity_name=getattr(dev, 'name', '') or '',
                    details='comm_password updated',
                )
                message = 'Communication password saved.'
                action_title = 'PAROLĂ COMUNICARE'
                action_message = 'Parola de comunicare a fost salvată.'

            elif op == 'upgrade-firmware':
                fw = (request.POST.get('firmware') or '').strip()
                cmd = 'UPGRADE_FIRMWARE'
                if fw:
                    cmd = f"UPGRADE_FIRMWARE:{fw}"[:240]
                else:
                    cmd = cmd[:240]
                ok = _enqueue(int(dev.id), cmd)
                if not ok:
                    raise RuntimeError('Comandă refuzată (centrală offline/dezactivată).')
                _audit_log(
                    request,
                    module='command',
                    action='create',
                    entity_id=int(dev.id),
                    entity_name=cmd,
                    details=f"device_id={dev.id}",
                )
                message = 'Firmware upgrade command queued.'
                action_title = 'FIRMWARE'
                action_message = 'Comanda de upgrade firmware a fost pusă în coadă.'

            elif op == 'sync-time':
                # Legacy behavior: sync device time with server time.
                # Best-effort: if plcommpro bridge is available, push directly;
                # fallback: queue SYNC_TIME for CommCenter.
                ok_direct = False
                direct_err = ''
                try:
                    from .plcommpro_bridge import PlcommproConnInfo, set_device_options, bridge_available

                    if dev.ip_address and bridge_available():
                        conn = PlcommproConnInfo(
                            ipaddress=str(dev.ip_address),
                            ip_port=int(dev.port or 4370),
                            password=str(dev.comm_password or ''),
                            timeout=3000,
                            protocol='TCP',
                        )
                        # Most ZK panels accept SetDeviceOptions with DateTime.
                        # Format: "YYYY-MM-DD HH:MM:SS"
                        now_local = _safe_now_local_str()
                        if now_local:
                            resp = set_device_options(conn, f"DateTime={now_local}")
                            if resp.get('ok'):
                                ok_direct = True
                            else:
                                direct_err = f"result={resp.get('result')} last_error={resp.get('last_error')}"
                except Exception as ex:
                    direct_err = str(ex)

                if ok_direct:
                    _audit_log(
                        request,
                        module='device',
                        action='sync_time',
                        entity_id=int(dev.id),
                        entity_name=getattr(dev, 'name', '') or '',
                        details='direct',
                    )
                    message = 'Time synchronized directly.'
                    action_title = 'SINCRONIZEAZĂ ORA'
                    action_message = 'Timpul a fost sincronizat pe centrală.'
                    close_delay_ms = 900
                else:
                    # Fallback: queue command.
                    cmd = 'SYNC_TIME'
                    try:
                        from django.utils import timezone as _tz
                        from zoneinfo import ZoneInfo

                        now_utc = _tz.now().astimezone(_tz.utc)
                        tz_name = (getattr(dev, 'time_zone', '') or '').strip()
                        if tz_name:
                            now_local = now_utc.astimezone(ZoneInfo(tz_name))
                        else:
                            now_local = _tz.localtime(now_utc)
                        cmd = f"SYNC_TIME:{now_local.strftime('%Y-%m-%d %H:%M:%S')}"
                    except Exception:
                        cmd = 'SYNC_TIME'
                    ok = _enqueue(int(dev.id), (cmd or '')[:240])
                    if not ok:
                        raise RuntimeError('Comandă refuzată (centrală offline/dezactivată).')
                    _audit_log(
                        request,
                        module='command',
                        action='create',
                        entity_id=int(dev.id),
                        entity_name=(cmd or '')[:120],
                        details=f"device_id={dev.id} fallback={direct_err}"[:240],
                    )
                    message = f"Command queued: {cmd}"
                    action_title = 'SINCRONIZEAZĂ ORA'
                    action_message = 'Comanda de sincronizare a fost pusă în coadă.'
                    close_delay_ms = 900

            elif op == 'get-personnel':
                do = (request.POST.get('do') or '').strip().lower()
                if do == 'sync':
                    # Reuse the same safety gates as /api/devices/<id>/sync-personnel/:
                    # - only physical controllers
                    # - require DB to have syncable employees
                    try:
                        if not bool(dev.is_physical_controller()):
                            raise RuntimeError('device-not-physical')
                    except Exception:
                        raise RuntimeError('device-not-physical')

                    try:
                        doors = list(Door.objects.filter(device_id=int(dev.id)).exclude(door_number__isnull=True))
                        levels = list(AccessLevel.objects.filter(doors__in=doors).distinct()) if doors else []
                        emp_qs = Employee.objects.filter(active=True, access_levels__in=levels).distinct() if levels else Employee.objects.none()
                        syncable_count = int(emp_qs.count())
                    except Exception:
                        syncable_count = 0
                    if syncable_count <= 0:
                        raise RuntimeError('no_syncable_employees')

                    ok, cmdlog_id, info = _enqueue_tracked_cmd(int(dev.id), 'SYNC_PERSONNEL')
                    if not ok:
                        raise RuntimeError(f"Comandă refuzată/eroare: {info}")
                    _audit_log(
                        request,
                        module='command',
                        action='create',
                        entity_id=int(dev.id),
                        entity_name='SYNC_PERSONNEL',
                        details=f"device_id={dev.id} cmdlog_id={cmdlog_id} syncable={syncable_count}",
                    )
                    message = 'SYNC_PERSONNEL queued.'
                    action_title = 'SINCRONIZARE PERSONAL'
                    action_message = 'Comanda de sincronizare (server → centrală) a fost pusă în coadă.'
                    close_delay_ms = 900
                else:
                    # Non-destructive default: keep the modal open flow; user can use
                    # "Citește din centrală" (GET) to view data.
                    raise RuntimeError('Alege „SYNC SERVER → CENTRALĂ” sau folosește „CITEȘTE DIN CENTRALĂ”.')

            else:
                cmd = (meta.get('command') or '').strip()
                if not cmd:
                    raise ValueError('missing-command')
                ok = _enqueue(int(dev.id), (cmd or '')[:240])
                if not ok:
                    raise RuntimeError('Comandă refuzată (centrală offline/dezactivată).')
                _audit_log(
                    request,
                    module='command',
                    action='create',
                    entity_id=int(dev.id),
                    entity_name=(cmd or '')[:120],
                    details=f"device_id={dev.id}",
                )
                message = f"Command queued: {cmd}"
                action_title = (meta.get('title') or 'Comandă').upper()
                action_message = 'Comanda a fost pusă în coadă.'
        except Exception as ex:
            error = str(ex)

        if error:
            if op in ('get-events', 'get-personnel', 'sync-time'):
                # Keep modal content visible; show the error inline.
                ctx_error = error
            else:
                gateway_val = (request.POST.get('gateway') or '').strip() if op == 'change-ip' else ''
                subnet_val = (request.POST.get('subnet_mask') or '').strip() if op == 'change-ip' else ''
                new_ip_val = (request.POST.get('ip_address') or '').strip() if op == 'change-ip' else ''
                port_val = (request.POST.get('port') or '').strip() if op == 'change-ip' else ''
                return render(request, 'agent/device_operation_form_inner.html', {
                    'dev': dev,
                    'op': op,
                    'title': meta.get('title') or 'Operation',
                    'error': error,
                    'gateway': gateway_val,
                    'subnet_mask': subnet_val,
                    'new_ip_address': new_ip_val,
                    'new_port': port_val,
                    'command_preview': (meta.get('command') or ''),
                })

        if not error:
            return render(request, 'agent/device_operation_saved_inner.html', {
                'message': message or 'OK',
                'action_state': action_state,
                'action_title': action_title,
                'action_message': action_message or (message or 'OK'),
                'close_delay_ms': close_delay_ms,
            })

    gateway_prefill = ''
    subnet_prefill = ''
    if op == 'change-ip' and dev.ip_address:
        guess_gw, guess_mask = _guess_net(str(dev.ip_address))
        gateway_prefill = guess_gw
        subnet_prefill = guess_mask
        try:
            from .plcommpro_bridge import PlcommproConnInfo, get_device_options

            conn = PlcommproConnInfo(
                ipaddress=str(dev.ip_address),
                ip_port=int(dev.port or 4370),
                password=str(dev.comm_password or ''),
                timeout=3000,
            )
            resp = get_device_options(conn, 'NetMask,GATEIPAddress')
            if resp.get('ok') and resp.get('data'):
                kv = {}
                for part in str(resp.get('data') or '').split(','):
                    if '=' in part:
                        k, v = part.split('=', 1)
                        kv[k.strip()] = v.strip()
                subnet_prefill = kv.get('NetMask', '') or ''
                gateway_prefill = kv.get('GATEIPAddress', '') or ''
        except Exception:
            pass

    ctx = {
        'dev': dev,
        'op': op,
        'title': meta.get('title') or 'Operation',
        'error': ctx_error,
        'gateway': gateway_prefill,
        'subnet_mask': subnet_prefill,
        'new_ip_address': '',
        'new_port': '',
        'command_preview': (meta.get('command') or ''),
    }

    # Make these modals "real" (data-rich) without leaving the page.
    if op in ('get-events', 'get-personnel', 'sync-time'):
        try:
            limit = int((request.GET.get('limit') or '').strip() or '0')
        except Exception:
            limit = 0
        all_flag = (request.GET.get('all') or '').strip() in ('1', 'true', 'yes', 'on')
        if all_flag:
            limit = 20000
        if limit <= 0:
            limit = 5000 if op == 'get-events' else 400
        limit = max(50, min(20000, limit))
        ctx['limit'] = limit
        ctx.update(_read_recent_device_logs(max_items=limit))
        ctx['server_now_local'] = _safe_now_local_str()

        # Best-effort personnel counts (device-side) if bridge is available.
        ctx['personnel_counts'] = None
        ctx['personnel_counts_error'] = ''
        ctx['device_personnel_preview'] = None
        ctx['device_personnel_preview_error'] = ''
        ctx['device_personnel_preview_raw'] = ''
        ctx['device_user_rows'] = None
        ctx['device_userauthorize_rows'] = None
        ctx['device_userauthorize_error'] = ''
        ctx['device_access_rows'] = None
        ctx['show_device_data'] = False
        if op == 'get-personnel':
            try:
                from .plcommpro_bridge import PlcommproConnInfo, data_count, query_data, bridge_available

                show_device = (request.GET.get('device') or '').strip() in ('1', 'true', 'yes', 'on')
                ctx['show_device_data'] = bool(show_device)

                if dev.ip_address and bridge_available():
                    conn = PlcommproConnInfo(
                        ipaddress=str(dev.ip_address),
                        ip_port=int(dev.port or 4370),
                        password=str(dev.comm_password or ''),
                        timeout=3000,
                        protocol='TCP',
                    )
                    # Table names vary by device/SDK; we try the common ones.
                    counts = {}
                    for table in ('user', 'userinfo', 'templatev10', 'template', 'fptemplate', 'holiday', 'timezone', 'acc_timezone'):
                        try:
                            resp = data_count(conn, table)
                            if resp.get('ok'):
                                counts[table] = resp.get('result')
                        except Exception:
                            continue
                    ctx['personnel_counts'] = counts

                    # Best-effort personnel list preview.
                    # Common ZK table is "user". We request only the key fields.
                    try:
                        fields = 'Pin,CardNo,Name'
                        resp = query_data(conn, 'user', fields=fields, filter='', option='', buffer_len=128 * 1024)
                        if resp.get('ok') and resp.get('data'):
                            parsed = _parse_plcommpro_rows(str(resp.get('data') or ''), ['Pin', 'CardNo', 'Name'])
                            if parsed:
                                ctx['device_personnel_preview'] = parsed[:50]
                            else:
                                ctx['device_personnel_preview_raw'] = str(resp.get('data') or '')[:2000]
                        elif resp.get('data'):
                            ctx['device_personnel_preview_raw'] = str(resp.get('data') or '')[:2000]
                    except Exception as ex:
                        ctx['device_personnel_preview_error'] = str(ex)

                    # Optional deeper read: actual device-side personnel + access rights.
                    if show_device:
                        try:
                            from agent.models import Door as DoorModel, TimeSegment as TimeSegmentModel  # type: ignore

                            doors = list(DoorModel.objects.filter(device_id=int(dev.id)).exclude(door_number__isnull=True))
                            doors_by_number = {}
                            for d in doors:
                                try:
                                    dn = int(getattr(d, 'door_number') or 0)
                                    if dn > 0:
                                        doors_by_number[dn] = d
                                except Exception:
                                    continue

                            user_fields = 'Pin,CardNo,Name,Group,Privilege,StartTime,EndTime,Password,SuperAuthorize'
                            ur = query_data(conn, 'user', fields=user_fields, filter='', option='', buffer_len=512 * 1024)
                            if ur.get('ok') and ur.get('data'):
                                ctx['device_user_rows'] = _parse_plcommpro_rows(str(ur.get('data') or ''),
                                                                              ['Pin','CardNo','Name','Group','Privilege','StartTime','EndTime','SuperAuthorize'])
                            else:
                                ctx['device_personnel_preview_error'] = ctx['device_personnel_preview_error'] or (
                                    ur.get('data') or 'device_user_query_failed'
                                )

                            ar = query_data(conn, 'userauthorize', fields='Pin,AuthorizeTimezoneId,AuthorizeDoorId', filter='', option='', buffer_len=512 * 1024)
                            if ar.get('ok') and ar.get('data'):
                                ctx['device_userauthorize_rows'] = _parse_plcommpro_rows(str(ar.get('data') or ''),
                                                                                        ['Pin','AuthorizeTimezoneId','AuthorizeDoorId'])
                            else:
                                ctx['device_userauthorize_error'] = (ar.get('data') or 'device_userauthorize_query_failed')

                            # Build a correlated access view: Pin + Name + dept + timezone + doors
                            tz_names = {}
                            try:
                                for seg in TimeSegmentModel.objects.all().only('id', 'name'):
                                    tz_names[int(seg.id)] = str(getattr(seg, 'name', '') or '')
                            except Exception:
                                tz_names = {}

                            ua_by_pin = {}
                            try:
                                for row in (ctx.get('device_userauthorize_rows') or []):
                                    p = str(row.get('pin') or '').strip()
                                    if p:
                                        ua_by_pin[p] = row
                            except Exception:
                                ua_by_pin = {}

                            access_rows = []
                            for row in (ctx.get('device_user_rows') or [])[:800]:
                                p = str(row.get('pin') or '').strip()
                                ua = ua_by_pin.get(p) or {}
                                tzid = ua.get('authorizetimezoneid') or ''
                                doors_mask = ua.get('authorizedoorid') or ''
                                door_list = _decode_door_mask(doors_mask, doors_by_number)
                                tz_disp = ''
                                try:
                                    tz_int = int(str(tzid).strip() or '0')
                                    tz_disp = tz_names.get(tz_int) or ''
                                except Exception:
                                    tz_disp = ''
                                access_rows.append({
                                    'pin': p,
                                    'name': row.get('name') or '',
                                    'cardno': row.get('cardno') or '',
                                    'dept': row.get('group') or '',
                                    'timezone_id': tzid,
                                    'timezone_name': tz_disp,
                                    'doors_mask': doors_mask,
                                    'doors': door_list,
                                })
                            ctx['device_access_rows'] = access_rows
                        except Exception as ex:
                            ctx['device_userauthorize_error'] = str(ex)
            except Exception as ex:
                ctx['personnel_counts_error'] = str(ex)

            # DB-side: personnel that would be synced to this device (active + access levels on this controller).
            ctx['db_personnel_count'] = 0
            ctx['db_personnel_preview'] = []
            ctx['personnel_diff'] = None
            ctx['personnel_sets_identical'] = False
            ctx['personnel_diff_note'] = ''
            ctx['can_sync_personnel'] = False
            try:
                doors = list(Door.objects.filter(device_id=int(dev.id)).exclude(door_number__isnull=True))
                levels = list(AccessLevel.objects.filter(doors__in=doors).distinct()) if doors else []
                emp_qs = Employee.objects.filter(active=True, access_levels__in=levels).distinct() if levels else Employee.objects.none()
                ctx['db_personnel_count'] = int(emp_qs.count())
                db_preview = []
                for e in emp_qs.select_related(None).only('id', 'first_name', 'last_name', 'card_number').order_by('last_name', 'first_name')[:60]:
                    cardno = str(getattr(e, 'card_number', '') or '').strip()
                    name = (f"{getattr(e, 'last_name', '') or ''} {getattr(e, 'first_name', '') or ''}").strip()
                    db_preview.append({'id': int(e.id), 'cardno': cardno, 'name': name})
                ctx['db_personnel_preview'] = db_preview

                # Diff (CardNo-based) between DB and device.
                try:
                    db_cards = set(
                        [
                            str(x or '').strip()
                            for x in emp_qs.exclude(card_number__isnull=True).exclude(card_number='').values_list('card_number', flat=True)
                        ]
                    )
                except Exception:
                    db_cards = set([str(x.get('cardno') or '').strip() for x in db_preview if str(x.get('cardno') or '').strip()])

                # Device side cards: prefer detailed list if requested; otherwise use preview.
                device_cards = set()
                if ctx.get('show_device_data') and ctx.get('device_user_rows'):
                    for row in (ctx.get('device_user_rows') or []):
                        cno = str((row or {}).get('cardno') or '').strip()
                        if cno:
                            device_cards.add(cno)
                elif ctx.get('device_personnel_preview'):
                    for row in (ctx.get('device_personnel_preview') or []):
                        cno = str((row or {}).get('cardno') or (row or {}).get('CardNo') or '').strip()
                        if cno:
                            device_cards.add(cno)

                missing_on_device = sorted(list(db_cards - device_cards))
                extra_on_device = sorted(list(device_cards - db_cards))
                identical = (db_cards == device_cards) and (len(db_cards) > 0 or len(device_cards) > 0)
                ctx['personnel_sets_identical'] = bool(identical)
                ctx['personnel_diff'] = {
                    'db_count': int(len(db_cards)),
                    'device_count': int(len(device_cards)),
                    'missing_on_device': missing_on_device[:40],
                    'extra_on_device': extra_on_device[:40],
                    'missing_on_device_count': int(len(missing_on_device)),
                    'extra_on_device_count': int(len(extra_on_device)),
                }
                if not ctx.get('show_device_data'):
                    ctx['personnel_diff_note'] = 'Diferențele sunt calculate din preview (apasă „CITEȘTE DIN CENTRALĂ” pentru listă completă).'

                can_sync = False
                try:
                    can_sync = bool(dev.is_physical_controller()) and int(ctx.get('db_personnel_count') or 0) > 0 and not bool(identical)
                except Exception:
                    can_sync = False
                ctx['can_sync_personnel'] = bool(can_sync)
            except Exception:
                # Keep modal usable even if DB-side computation fails.
                pass

    return render(request, 'agent/device_operation_form_inner.html', ctx)

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


def door_first_card_settings(request: HttpRequest, pk: int):
    """First-Card Normal Open settings (legacy-like) for a single door."""
    if not request.user.is_authenticated or not request.user.is_staff:
        from django.contrib.auth.views import redirect_to_login
        return redirect_to_login(request.get_full_path())

    door = Door.objects.select_related('device').filter(pk=pk).first()
    if door is None:
        return HttpResponse('Door not found', status=404)

    msg = ''
    edit_id = (request.GET.get('rule') or '').strip()
    edit_rule = DoorFirstCardRule.objects.filter(pk=edit_id, door=door).first() if edit_id else None

    if request.method == 'POST':
        action = (request.POST.get('_action') or '').strip().lower()
        rid = (request.POST.get('rule_id') or '').strip()
        if action == 'delete' and rid:
            try:
                DoorFirstCardRule.objects.filter(pk=rid, door=door).delete()
                msg = 'Deleted.'
            except Exception as e:
                msg = f'Error: {e}'
            edit_rule = None
        else:
            inst = DoorFirstCardRule.objects.filter(pk=rid, door=door).first() if rid else DoorFirstCardRule(door=door)
            form = DoorFirstCardRuleForm(request.POST, instance=inst)
            if form.is_valid():
                saved = form.save(commit=False)
                saved.door = door
                saved.save()
                form.save_m2m()
                msg = 'Saved.'
                edit_rule = None
            else:
                rules = list(DoorFirstCardRule.objects.filter(door=door).select_related('time_segment').prefetch_related('employees').order_by('-created_at'))
                return render(request, 'agent/door_first_card_modal.html', {'door': door, 'rules': rules, 'form': form, 'msg': msg, 'edit_rule': inst})

    rules = list(DoorFirstCardRule.objects.filter(door=door).select_related('time_segment').prefetch_related('employees').order_by('-created_at'))
    form = DoorFirstCardRuleForm(instance=edit_rule)
    return render(request, 'agent/door_first_card_modal.html', {'door': door, 'rules': rules, 'form': form, 'msg': msg, 'edit_rule': edit_rule})


def door_multi_card_settings(request: HttpRequest, pk: int):
    """Multi-Card Open settings (legacy-like) for a single door."""
    if not request.user.is_authenticated or not request.user.is_staff:
        from django.contrib.auth.views import redirect_to_login
        return redirect_to_login(request.get_full_path())

    door = Door.objects.select_related('device').filter(pk=pk).first()
    if door is None:
        return HttpResponse('Door not found', status=404)

    msg = ''
    edit_id = (request.GET.get('rule') or '').strip()
    edit_rule = DoorMultiCardRule.objects.filter(pk=edit_id, door=door).first() if edit_id else None

    if request.method == 'POST':
        action = (request.POST.get('_action') or '').strip().lower()
        rid = (request.POST.get('rule_id') or '').strip()
        if action == 'delete' and rid:
            try:
                DoorMultiCardRule.objects.filter(pk=rid, door=door).delete()
                msg = 'Deleted.'
            except Exception as e:
                msg = f'Error: {e}'
            edit_rule = None
        else:
            inst = DoorMultiCardRule.objects.filter(pk=rid, door=door).first() if rid else DoorMultiCardRule(door=door)
            form = DoorMultiCardRuleForm(request.POST, instance=inst)
            if form.is_valid():
                saved = form.save(commit=False)
                saved.door = door
                saved.save()
                form.save_m2m()
                msg = 'Saved.'
                edit_rule = None
            else:
                rules = list(DoorMultiCardRule.objects.filter(door=door).prefetch_related('employees').order_by('-created_at'))
                return render(request, 'agent/door_multi_card_modal.html', {'door': door, 'rules': rules, 'form': form, 'msg': msg, 'edit_rule': inst})

    rules = list(DoorMultiCardRule.objects.filter(door=door).prefetch_related('employees').order_by('-created_at'))
    form = DoorMultiCardRuleForm(instance=edit_rule)
    return render(request, 'agent/door_multi_card_modal.html', {'door': door, 'rules': rules, 'form': form, 'msg': msg, 'edit_rule': edit_rule})

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
    try:
        from django.db.models import Prefetch
        from .models import Door, TimeSegment

        qs = qs.prefetch_related(
            Prefetch(
                'doors',
                queryset=(
                    Door.objects.select_related('device', 'door_active_time_zone', 'door_passage_mode_time_zone')
                    .prefetch_related('first_card_rules', 'multi_card_rules')
                    .order_by('device__name', 'door_number', 'name', 'id')
                ),
                to_attr='prefetched_doors',
            ),
            Prefetch(
                'time_segments',
                queryset=TimeSegment.objects.order_by('name', 'id'),
                to_attr='prefetched_time_segments',
            ),
        )
    except Exception:
        pass
    page = _paginate(qs, request)
    return render(request, 'agent/access_levels_embed.html', {'page': page, 'can_edit': bool(getattr(request.user, 'is_staff', False))})


def access_levels_personnel_embed(request: HttpRequest):
    """ACCES -> Nivel Acces personal (legacy-like, ultra-compact).

    Shows access levels on the left and assigned personnel on the right.
    Used ONLY in embedded Access module (menu_access_inner.html) via ?embed=1.
    """
    if not request.user.is_authenticated:
        from django.contrib.auth.views import redirect_to_login
        return redirect_to_login(request.get_full_path())

    is_embed = (request.GET.get('embed') == '1')
    if not is_embed:
        from django.shortcuts import redirect
        return redirect('/agent/menu/access/?tab=personal_levels')

    can_edit = bool(getattr(request.user, 'is_staff', False))

    q = (request.GET.get('q') or '').strip()
    level_id = (request.GET.get('level_id') or '').strip()

    levels_qs = AccessLevel.objects.order_by('name')
    try:
        from django.db.models import Count

        levels_qs = levels_qs.annotate(emp_count=Count('employee'))
    except Exception:
        pass
    if q:
        try:
            from django.db.models import Q
            levels_qs = levels_qs.filter(Q(name__icontains=q) | Q(description__icontains=q))
        except Exception:
            levels_qs = levels_qs.filter(name__icontains=q)

    levels = list(levels_qs)
    selected_level = None
    if level_id:
        try:
            selected_level = AccessLevel.objects.filter(pk=int(level_id)).first()
        except Exception:
            selected_level = None
    if selected_level is None and levels:
        selected_level = levels[0]

    assigned = []
    if selected_level is not None:
        try:
            assigned = list(
                Employee.objects.filter(access_levels=selected_level)
                .order_by('last_name', 'first_name')
                .only('id', 'first_name', 'last_name', 'card_number', 'legacy_userid')
            )
        except Exception:
            assigned = []

    return render(
        request,
        'agent/access_levels_personnel_embed.html',
        {
            'levels': levels,
            'selected_level': selected_level,
            'assigned': assigned,
            'can_edit': can_edit,
            'q': q,
        },
    )


def access_levels_personnel_add(request: HttpRequest, level_id: int):
    if not request.user.is_authenticated or not request.user.is_staff:
        return JsonResponse({'ok': False, 'error': 'unauthorized'}, status=403)
    if request.method != 'POST':
        return JsonResponse({'ok': False, 'error': 'method-not-allowed'}, status=405)

    level = AccessLevel.objects.filter(pk=level_id).first()
    if level is None:
        return JsonResponse({'ok': False, 'error': 'level-not-found'}, status=404)

    emp_id_raw = (request.POST.get('employee_id') or '').strip()
    if not emp_id_raw:
        return JsonResponse({'ok': False, 'error': 'validation', 'message': 'employee_id required'}, status=400)
    try:
        emp_id = int(emp_id_raw)
    except Exception:
        return JsonResponse({'ok': False, 'error': 'validation', 'message': 'employee_id invalid'}, status=400)

    emp = Employee.objects.filter(pk=emp_id).first()
    if emp is None:
        return JsonResponse({'ok': False, 'error': 'employee-not-found'}, status=404)

    try:
        emp.access_levels.add(level)
    except Exception as ex:
        return JsonResponse({'ok': False, 'error': str(ex)}, status=400)

    # Ensure immediate re-evaluation in monitor/API by clearing cached decisions.
    try:
        EmployeeAccessCache.objects.filter(employee=emp).delete()
    except Exception:
        pass

    try:
        _audit_log(
            request,
            module='access-level-personnel',
            action='add',
            entity_id=int(level.id),
            entity_name=getattr(level, 'name', '') or '',
            details=f"employee_id={emp.id} card={getattr(emp, 'card_number', '')}",
        )
    except Exception:
        pass

    return JsonResponse({'ok': True})


def access_levels_personnel_remove(request: HttpRequest, level_id: int):
    if not request.user.is_authenticated or not request.user.is_staff:
        return JsonResponse({'ok': False, 'error': 'unauthorized'}, status=403)
    if request.method != 'POST':
        return JsonResponse({'ok': False, 'error': 'method-not-allowed'}, status=405)

    level = AccessLevel.objects.filter(pk=level_id).first()
    if level is None:
        return JsonResponse({'ok': False, 'error': 'level-not-found'}, status=404)

    emp_ids_raw = request.POST.getlist('employee_ids')
    emp_ids: list[int] = []
    for v in emp_ids_raw:
        try:
            emp_ids.append(int(v))
        except Exception:
            continue
    emp_ids = [i for i in emp_ids if i > 0]
    if not emp_ids:
        return JsonResponse({'ok': False, 'error': 'validation', 'message': 'No employee_ids provided'}, status=400)

    try:
        qs = Employee.objects.filter(pk__in=emp_ids)
        removed = 0
        for emp in qs:
            try:
                emp.access_levels.remove(level)
                removed += 1
            except Exception:
                pass
    except Exception as ex:
        return JsonResponse({'ok': False, 'error': str(ex)}, status=400)

    # Ensure immediate re-evaluation in monitor/API by clearing cached decisions.
    try:
        EmployeeAccessCache.objects.filter(employee_id__in=emp_ids).delete()
    except Exception:
        pass

    try:
        _audit_log(
            request,
            module='access-level-personnel',
            action='remove',
            entity_id=int(level.id),
            entity_name=getattr(level, 'name', '') or '',
            details=f"removed={removed}",
        )
    except Exception:
        pass

    return JsonResponse({'ok': True, 'removed': removed})


def api_access_level_options(request: HttpRequest):
    """JSON helper for UI: list access levels (optionally filtered by a door).

    Used by the live Monitor "➕Acces" action to offer only relevant levels.
    """
    if not request.user.is_authenticated:
        return JsonResponse({'items': []}, status=403)

    door_id = _parse_int((request.GET.get('door_id') or '').strip(), default=None)
    qs = AccessLevel.objects.order_by('name')
    if door_id is not None:
        try:
            qs = qs.filter(doors__id=int(door_id)).distinct()
        except Exception:
            pass
    try:
        items = list(qs.values('id', 'name'))
    except Exception:
        items = []
    return JsonResponse({'items': items})


def employees_search_json(request: HttpRequest):
    """Small JSON endpoint used by ACCES -> Nivel Acces personal for quick searches."""
    if not request.user.is_authenticated:
        return JsonResponse({'items': []}, status=403)

    q = (request.GET.get('q') or '').strip()
    limit_raw = (request.GET.get('limit') or '').strip()
    try:
        limit = max(1, min(50, int(limit_raw or 25)))
    except Exception:
        limit = 25

    qs = Employee.objects.order_by('last_name', 'first_name')
    if q:
        try:
            from django.db.models import Q
            qs = qs.filter(
                Q(first_name__icontains=q)
                | Q(last_name__icontains=q)
                | Q(card_number__icontains=q)
                | Q(secondary_card_number__icontains=q)
            )
        except Exception:
            qs = qs.filter(last_name__icontains=q)

    items = []
    try:
        for e in qs.only('id', 'first_name', 'last_name', 'card_number', 'legacy_userid')[:limit]:
            name = f"{getattr(e, 'last_name', '')} {getattr(e, 'first_name', '')}".strip()
            card = getattr(e, 'card_number', '') or ''
            legacy_uid = getattr(e, 'legacy_userid', None)
            label = name
            if card:
                label = f"{label} — {card}" if label else card
            if legacy_uid is not None:
                label = f"{label} (ID:{legacy_uid})" if label else f"ID:{legacy_uid}"
            items.append({'id': int(e.id), 'label': label, 'card_number': card})
    except Exception as ex:
        return JsonResponse({'items': [], 'error': str(ex)}, status=500)

    return JsonResponse({'items': items})

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
            parent_id = _parse_int(getattr(m, 'parent_legacy_area_id', None), default=None) if m else None
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
    name = _payload_get_str(payload, 'name', '').strip()
    code = _payload_get_str(payload, 'code', '').strip()
    remarks = (_payload_get_str(payload, 'notes', '') or _payload_get_str(payload, 'remarks', '')).strip()
    parent_id_raw = (_payload_get_str(payload, 'parent_id', '') or _payload_get_str(payload, 'parent', '')).strip()
    parent_id = None
    if parent_id_raw:
        try:
            parent_id = int(parent_id_raw)
        except Exception:
            parent_id = None
    pk = _payload_get_str(payload, 'id', '')
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
    name = _payload_get_str(payload, 'name', '').strip()
    if not name:
        return JsonResponse({'ok': False, 'error': 'missing-name'}, status=400)
    try:
        pk = _payload_get_str(payload, 'id', '')
        is_update = bool(pk)
        obj = DSTime.objects.get(pk=int(pk)) if pk else DSTime()
        obj.name = name
        obj.start_month = int(_payload_get_int(payload, 'start_month', 1) or 1)
        obj.start_week = _payload_get_str(payload, 'start_week', 'last') or 'last'
        obj.start_weekday = int(_payload_get_int(payload, 'start_weekday', 0) or 0)
        obj.start_hour = int(_payload_get_int(payload, 'start_hour', 3) or 3)
        obj.start_minute = int(_payload_get_int(payload, 'start_minute', 0) or 0)
        obj.end_month = int(_payload_get_int(payload, 'end_month', 10) or 10)
        obj.end_week = _payload_get_str(payload, 'end_week', 'last') or 'last'
        obj.end_weekday = int(_payload_get_int(payload, 'end_weekday', 0) or 0)
        obj.end_hour = int(_payload_get_int(payload, 'end_hour', 3) or 3)
        obj.end_minute = int(_payload_get_int(payload, 'end_minute', 0) or 0)
        obj.offset_minutes = int(_payload_get_int(payload, 'offset_minutes', 60) or 60)
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

def _set_lock_state(door_id, state: Optional[str]):
    try:
        m = _get_lock_map()
        key = str(door_id)
        if state and str(state).upper() == 'LOCKED':
            m[key] = 'LOCKED'
        else:
            if key in m:
                del m[key]
        cache.set(LOCK_CACHE_KEY, m, timeout=86400)
    except Exception:
        pass

def _door_state_from_cache_or_model(door):
    """Return a UI-friendly door state string.

    IMPORTANT: `door.is_open` is a persisted *simulated* state updated by remote
    commands. It can become stale when the controller is offline/powered down.
    To avoid showing a door stuck as OPEN while the controller is offline, the
    caller may pass `device_online=False` via attribute injection on the door
    instance (see callers below).
    """
    lock_map = _get_lock_map()
    lock_state = lock_map.get(str(getattr(door, 'id', '')))
    if lock_state == 'LOCKED':
        return 'LOCKED'
    # Callers may attach a precomputed `__device_online` attribute to avoid
    # extra DB queries.
    try:
        dev_online = getattr(door, '__device_online')
    except Exception:
        dev_online = None
    if dev_online is False:
        return 'CLOSED'
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
                door_id_s = str(door_id)
                if door_id_s.isdigit():
                    door = Door.objects.filter(device_id=int(device_id), door_number=int(door_id_s)).first()
                    if door is None:
                        door = Door.objects.filter(device_id=int(device_id), name__iexact=door_id_s).first()
                else:
                    door = Door.objects.filter(device_id=int(device_id), name__iexact=door_id_s).first()
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
                door_ids_allowed_raw = set()
                door_ids_allowed = set()
                door_map = {}
                door_schedule_reasons: list[str] = []
                for al in levels:
                    seg_ok = _seg_allows(al)
                    if seg_ok:
                        time_ok_any = True
                    for d in al.doors.all():
                        door_map[d.id] = d
                        if seg_ok:
                            door_ids_allowed_raw.add(d.id)

                # Apply door-level constraints (must be configured and inside its active time zone).
                allowed_doors = []
                for d_id in door_ids_allowed_raw:
                    d_obj = door_map.get(d_id)
                    can_open_now, tz_reason = _door_can_open_now(d_obj)
                    if can_open_now:
                        door_ids_allowed.add(d_id)
                        allowed_doors.append({
                            'id': d_id,
                            'name': getattr(d_obj, 'name', ''),
                            'device_id': getattr(d_obj, 'device_id', None),
                        })
                    else:
                        if tz_reason and tz_reason not in door_schedule_reasons:
                            door_schedule_reasons.append(tz_reason)

                if not time_ok_any:
                    reasons.append('outside_time_segments')

                # If employee has access-level time segments but all doors are blocked by door schedules,
                # surface a meaningful reason.
                if time_ok_any and door_ids_allowed_raw and not door_ids_allowed:
                    if door_schedule_reasons:
                        reasons.append(door_schedule_reasons[0])

                # If door not resolved but employee has allowed doors, pick first
                if door is None and allowed_doors:
                    try:
                        door = door_map.get(allowed_doors[0]['id'])
                    except Exception:
                        door = door

                if door:
                    if door.id not in door_ids_allowed:
                        if door.id not in door_ids_allowed_raw:
                            reasons.append('door_not_in_access_levels')
                        else:
                            # Door is in access levels, but blocked by door constraints.
                            can_open_now, tz_reason = _door_can_open_now(door)
                            reasons.append(tz_reason or 'outside_time_zone')
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
            # Default to the first configured door (assigned + has door_number)
            door = (
                Door.objects.exclude(device__isnull=True)
                .exclude(door_number__isnull=True)
                .order_by('device_id', 'door_number', 'id')
                .first()
            )
    except Exception:
        door = (
            Door.objects.exclude(device__isnull=True)
            .exclude(door_number__isnull=True)
            .order_by('device_id', 'door_number', 'id')
            .first()
        )
    if not door:
        return JsonResponse({'ok': False, 'error': 'no-configured-door', 'card_number': card}, status=400)
    # Call existing evaluator
    try:
        import json
        payload = json.dumps({'card_number': card, 'door_pk': door.id, 'source': 'test', 'open_all': open_all})
        # Build a faux POST request using current request as base
        req = request
        req.method = 'POST'
        cast(Any, req)._body = payload.encode('utf-8')
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
        from .models import Door, DeviceStatus
        include_unassigned = str(request.GET.get('include_unassigned', '') or '').strip().lower() in ('1', 'true', 'yes')
        include_unconfigured = str(request.GET.get('include_unconfigured', '') or '').strip().lower() in ('1', 'true', 'yes')
        include_non_controllers = str(request.GET.get('include_non_controllers', '') or '').strip().lower() in ('1', 'true', 'yes')
        qs = Door.objects.select_related('device').order_by('id')
        if not include_unassigned:
            qs = qs.exclude(device__isnull=True)
        if not include_unconfigured:
            qs = qs.exclude(door_number__isnull=True)
        if not include_non_controllers:
            # Live monitor: doors belong to controllers only; exclude doors linked to readers/scanners.
            qs = qs.exclude(device__scanner_linked=True).exclude(device__device_type='biometric_reader')
        items = []
        # Preload latest DeviceStatus for all devices referenced to minimize queries
        device_ids = [getattr(d.device, 'id', None) for d in qs if getattr(d.device, 'id', None) is not None]
        status_map = {}
        if device_ids:
            for ds in DeviceStatus.objects.filter(device_id__in=device_ids).order_by('device_id', '-updated_at', '-id'):
                if ds.device_id not in status_map:
                    status_map[ds.device_id] = ds
        for d in qs:
            dev = getattr(d, 'device', None)
            dev_id = getattr(dev, 'id', None) if dev else None
            ds = status_map.get(dev_id)
            # Attach precomputed online flag for state helper (avoid OPEN when offline)
            try:
                setattr(d, '__device_online', bool(ds.online) if ds is not None else False)
            except Exception:
                pass
            # Map is_open boolean to state string for UI
            state = _door_state_from_cache_or_model(d)
            items.append({
                'id': d.id,
                'name': d.name or f"Door {d.id}",
                'device_id': dev_id,
                'device_name': getattr(dev, 'name', None) if dev else None,
                'door_number': getattr(d, 'door_number', None),
                'state': state,
                'enabled': bool(d.enabled),
                'lock_open_duration': int(getattr(d, 'lock_open_duration', 5) or 5),
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
        elif module in ('system', 'sistem'):
            # SYSTEM tabs: users + groups + timezone presets
            qs = qs.filter(module__in=['system-user', 'system-group', 'system-tz'])
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

    def _queue_sync_for_device_ids(device_ids: set[int], *, reason: str) -> tuple[int, int]:
        try:
            from datetime import timedelta
            from django.utils import timezone

            from agent.models import CommandLog, Device
            from agent.sync_limits import get_sync_personnel_limits

            limits = get_sync_personnel_limits()
            if not bool(getattr(limits, 'enabled', True)):
                return 0, 0

            dedupe_s = int(getattr(limits, 'dedupe_seconds', 60) or 60)
            cutoff = timezone.now() - timedelta(seconds=max(1, dedupe_s))
        except Exception:
            CommandLog = None  # type: ignore
            Device = None  # type: ignore
            cutoff = None

        queued = 0
        already = 0
        if not device_ids:
            return 0, 0
        try:
            qs = Device.objects.filter(id__in=sorted(device_ids), enabled=True)
        except Exception:
            return 0, 0

        for dev in qs:
            try:
                if cutoff is not None:
                    exists_recent = (
                        CommandLog.objects.filter(
                            device=dev,
                            command__startswith='SYNC_PERSONNEL',
                            created_at__gte=cutoff,
                        )
                        .exclude(status='ERR')
                        .exists()
                    )
                    if exists_recent:
                        already += 1
                        continue
                log = CommandLog.objects.create(device=dev, command='SYNC_PERSONNEL', status='PENDING')
                _broadcast_command(log)
                queued += 1
            except Exception:
                continue
        return queued, already
    if request.method == 'POST':
        form = AccessLevelForm(request.POST)
        if form.is_valid():
            form.save()

            # Sync controllers covered by this level.
            try:
                dev_ids = set(
                    form.instance.doors.exclude(device__isnull=True)
                    .values_list('device_id', flat=True)
                    .distinct()
                )
            except Exception:
                dev_ids = set()
            queued_sync, already_sync = _queue_sync_for_device_ids({int(x) for x in dev_ids if x}, reason='access_level_created')

            _broadcast_access_level_change('created', form.instance)
            _audit_log(
                request,
                module='access-level',
                action='create',
                entity_id=form.instance.id,
                entity_name=getattr(form.instance, 'name', '') or '',
            )
            tpl = 'agent/access_level_saved_inner.html' if is_modal else 'agent/access_level_saved.html'
            return render(request, tpl, {'obj': form.instance, 'created': True, 'queued_sync': queued_sync, 'already_sync': already_sync})
    else: form = AccessLevelForm()
    tpl = 'agent/access_level_form_inner.html' if is_modal else 'agent/access_level_form.html'
    # For modal UI controller picker.
    devices_all = []
    devices_selected = []
    devices_available = []
    try:
        devices_all = list(form.fields['devices'].queryset)
        if form.is_bound:
            raw_ids = list(form.data.getlist('devices'))
        else:
            raw_ids = list(form.initial.get('devices') or [])
        sel_ids = []
        for v in raw_ids:
            try:
                sel_ids.append(int(v))
            except Exception:
                continue
        sel_ids = sorted({int(x) for x in sel_ids if int(x) > 0})
        devices_selected = [d for d in devices_all if int(getattr(d, 'id', 0) or 0) in set(sel_ids)]
        sel_set = {int(getattr(d, 'id', 0) or 0) for d in devices_selected if int(getattr(d, 'id', 0) or 0) > 0}
        devices_available = [d for d in devices_all if int(getattr(d, 'id', 0) or 0) not in sel_set]
    except Exception:
        devices_all = []
        devices_selected = []
        devices_available = []
    return render(request, tpl, {'form': form, 'devices_all': devices_all, 'devices_selected': devices_selected, 'devices_available': devices_available})

def access_level_edit(request: HttpRequest, pk: int):
    if not request.user.is_authenticated or not request.user.is_staff:
        from django.contrib.auth.views import redirect_to_login
        return redirect_to_login(request.get_full_path())
    is_modal = (request.GET.get('modal') == '1') or (request.headers.get('x-requested-with') == 'XMLHttpRequest')
    lvl = AccessLevel.objects.get(pk=pk)

    def _queue_sync_for_device_ids(device_ids: set[int], *, reason: str) -> tuple[int, int]:
        try:
            from datetime import timedelta

            from django.utils import timezone

            from agent.models import CommandLog, Device
            from agent.sync_limits import get_sync_personnel_limits

            limits = get_sync_personnel_limits()
            if not bool(getattr(limits, 'enabled', True)):
                return 0, 0

            dedupe_s = int(getattr(limits, 'dedupe_seconds', 60) or 60)
            cutoff = timezone.now() - timedelta(seconds=max(1, dedupe_s))
        except Exception:
            CommandLog = None  # type: ignore
            Device = None  # type: ignore
            cutoff = None

        queued = 0
        already = 0
        if not device_ids:
            return 0, 0
        try:
            qs = Device.objects.filter(id__in=sorted(device_ids), enabled=True)
        except Exception:
            return 0, 0

        for dev in qs:
            try:
                if cutoff is not None:
                    exists_recent = (
                        CommandLog.objects.filter(
                            device=dev,
                            command__startswith='SYNC_PERSONNEL',
                            created_at__gte=cutoff,
                        )
                        .exclude(status='ERR')
                        .exists()
                    )
                    if exists_recent:
                        already += 1
                        continue
                log = CommandLog.objects.create(device=dev, command='SYNC_PERSONNEL', status='PENDING')
                _broadcast_command(log)
                queued += 1
            except Exception:
                continue
        return queued, already
    if request.method == 'POST':
        try:
            old_dev_ids = set(
                lvl.doors.exclude(device__isnull=True)
                .values_list('device_id', flat=True)
                .distinct()
            )
        except Exception:
            old_dev_ids = set()
        form = AccessLevelForm(request.POST, instance=lvl)
        if form.is_valid():
            form.save()

            try:
                new_dev_ids = set(
                    form.instance.doors.exclude(device__isnull=True)
                    .values_list('device_id', flat=True)
                    .distinct()
                )
            except Exception:
                new_dev_ids = set()
            queued_sync, already_sync = _queue_sync_for_device_ids({int(x) for x in (set(old_dev_ids) | set(new_dev_ids)) if x}, reason='access_level_updated')

            _broadcast_access_level_change('updated', form.instance)
            _audit_log(
                request,
                module='access-level',
                action='update',
                entity_id=form.instance.id,
                entity_name=getattr(form.instance, 'name', '') or '',
            )
            tpl = 'agent/access_level_saved_inner.html' if is_modal else 'agent/access_level_saved.html'
            return render(request, tpl, {'obj': form.instance, 'created': False, 'queued_sync': queued_sync, 'already_sync': already_sync})
    else: form = AccessLevelForm(instance=lvl)
    tpl = 'agent/access_level_form_inner.html' if is_modal else 'agent/access_level_form.html'
    devices_all = []
    devices_selected = []
    devices_available = []
    try:
        devices_all = list(form.fields['devices'].queryset)
        if form.is_bound:
            raw_ids = list(form.data.getlist('devices'))
        else:
            raw_ids = list(form.initial.get('devices') or [])
        sel_ids = []
        for v in raw_ids:
            try:
                sel_ids.append(int(v))
            except Exception:
                continue
        sel_ids = sorted({int(x) for x in sel_ids if int(x) > 0})
        devices_selected = [d for d in devices_all if int(getattr(d, 'id', 0) or 0) in set(sel_ids)]
        sel_set = {int(getattr(d, 'id', 0) or 0) for d in devices_selected if int(getattr(d, 'id', 0) or 0) > 0}
        devices_available = [d for d in devices_all if int(getattr(d, 'id', 0) or 0) not in sel_set]
    except Exception:
        devices_all = []
        devices_selected = []
        devices_available = []
    return render(request, tpl, {'form': form, 'obj': lvl, 'devices_all': devices_all, 'devices_selected': devices_selected, 'devices_available': devices_available})

def access_level_delete(request: HttpRequest, pk: int):
    if not request.user.is_authenticated or not request.user.is_staff or request.method != 'POST': return JsonResponse({'ok': False,'error':'unauthorized'}, status=403)
    try:
        obj = AccessLevel.objects.get(pk=pk)

        # Capture affected devices before delete.
        try:
            dev_ids = set(
                obj.doors.exclude(device__isnull=True)
                .values_list('device_id', flat=True)
                .distinct()
            )
        except Exception:
            dev_ids = set()

        obj.delete()

        # Queue sync so controllers drop the level's authorizations.
        try:
            from datetime import timedelta

            from django.utils import timezone

            from agent.models import CommandLog, Device
            from agent.sync_limits import get_sync_personnel_limits

            limits = get_sync_personnel_limits()
            if bool(getattr(limits, 'enabled', True)):
                dedupe_s = int(getattr(limits, 'dedupe_seconds', 60) or 60)
                cutoff = timezone.now() - timedelta(seconds=max(1, dedupe_s))
                for dev in Device.objects.filter(id__in=sorted({int(x) for x in dev_ids if x}), enabled=True):
                    try:
                        exists_recent = (
                            CommandLog.objects.filter(device=dev, command__startswith='SYNC_PERSONNEL', created_at__gte=cutoff)
                            .exclude(status='ERR')
                            .exists()
                        )
                        if exists_recent:
                            continue
                        log = CommandLog.objects.create(device=dev, command='SYNC_PERSONNEL', status='PENDING')
                        _broadcast_command(log)
                    except Exception:
                        continue
        except Exception:
            pass

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
    log = CommandLog.objects.create(device_id=device_id, door=door, command=(cmd or '')[:240], status='PENDING')
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
        ds = DeviceStatus.objects.filter(device=dev).order_by('-updated_at', '-id').first()

        # Door actuations are blocked when offline/missing status, but we allow
        # a fast best-effort probe to repair stale status (common after discovery).
        if door is not None and (ds is None or (ds is not None and not ds.online)):
            try:
                if _maybe_set_device_online_from_probe(dev):
                    # Refresh local instance
                    try:
                        ds = DeviceStatus.objects.filter(device=dev).order_by('-updated_at', '-id').first()
                    except Exception:
                        ds = ds
            except Exception:
                pass

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
    try:
        import agent.modern_comm_center as mcc
        center = getattr(mcc, 'ACTIVE_CENTER', None)
        # If CommCenter is running in this same process, enqueue via in-memory queue
        # and prefix with LOGID so CommCenter can update this CommandLog row.
        if center is not None:
            try:
                center.enqueue_command(device_id, f"LOGID:{int(log.id)} {cmd}"[:240])
                try:
                    log.status = 'RUNNING'
                    log.result = 'queued'
                    log.save(update_fields=['status', 'result'])
                except Exception:
                    pass
                _broadcast_command(log)
            except Exception:
                # Fallback to DB-only queue (external CommCenter may consume it)
                pass
        return True
    except Exception:
        return True

def _persist_and_broadcast_status(device_id: int, door_state: str, online: bool = True):
    try:
        from channels.layers import get_channel_layer
        from asgiref.sync import async_to_sync

        layer = get_channel_layer()
        ds = None

        # Persist status
        try:
            dev = Device.objects.get(id=device_id)
            ds = _latest_device_status_row(dev)
            if ds is None:
                ds = DeviceStatus.objects.create(device=dev, online=bool(online), door_state=str(door_state or '')[:32])
            else:
                ds.door_state = door_state
                ds.online = online
            ds.save(update_fields=["door_state", "online", "updated_at"])
        except Exception:
            ds = None

        if layer:
            # Include the exact updated_at timestamp so clients can render the true state-change time
            try:
                ua = ds.updated_at.isoformat() if ds and getattr(ds, 'updated_at', None) is not None else None
            except Exception:
                ua = None
            try:
                async_to_sync(layer.group_send)(
                    "monitor",
                    {
                        "type": "monitor_event",
                        "payload": {
                            "type": "device.status",
                            "device_id": int(device_id),
                            "door_state": door_state,
                            "online": bool(online),
                            "updated_at": ua,
                        },
                    },
                )
            except Exception:
                pass
    except Exception:
        pass


def _broadcast_door_event(device_id: int, door_obj, event_type: str, verify_mode: str = '') -> None:
    """Best-effort broadcast for monitor UI so operators always see door open/close lines."""
    try:
        from channels.layers import get_channel_layer
        from asgiref.sync import async_to_sync

        layer = get_channel_layer()
        if not layer:
            return
        door_id_val = int(getattr(door_obj, 'id', 0) or 0) if door_obj is not None else 0
        payload = {
            "type": str(event_type or ''),
            "device_id": int(device_id),
            "door_id": door_id_val,
            "point_id": door_id_val,
            "event_description": str(event_type or ''),
            "verify_mode": str(verify_mode or ''),
        }
        try:
            nm = getattr(door_obj, 'name', '') if door_obj is not None else ''
            if nm:
                payload["door_name"] = nm
        except Exception:
            pass
        async_to_sync(layer.group_send)("monitor", {"type": "monitor_event", "payload": payload})
    except Exception:
        return


def _time_segment_is_active(seg, now_dt) -> bool:
    try:
        if seg is None or now_dt is None:
            return False
        # days_mask: bit 0 = Monday .. bit 6 = Sunday
        wd = int(getattr(now_dt, 'weekday')())
        mask = int(getattr(seg, 'days_mask', 0) or 0)
        if not (mask & (1 << wd)):
            return False
        t = getattr(now_dt, 'time')()
        st = getattr(seg, 'start_time', None)
        en = getattr(seg, 'end_time', None)
        if st is None or en is None:
            return False
        return bool(st <= t < en)
    except Exception:
        return False


def _door_can_open_now(door_obj) -> tuple[bool, str]:
    """Return (ok, reason). Enforces that a door must be assigned and in active time zone."""
    try:
        if door_obj is None:
            return (False, 'door_not_found')
        if getattr(door_obj, 'device_id', None) is None:
            return (False, 'door_unassigned')
        if getattr(door_obj, 'door_number', None) in (None, 0, ''):
            return (False, 'door_not_configured')
        seg = getattr(door_obj, 'door_active_time_zone', None)
        if seg is None:
            return (False, 'door_time_zone_not_set')
        from django.utils import timezone

        now_local = timezone.localtime(timezone.now())
        if not _time_segment_is_active(seg, now_local):
            return (False, 'outside_time_zone')
        return (True, '')
    except Exception:
        return (False, 'schedule_check_failed')


# Best-effort server-side auto-close scheduling.
# Purpose: if a door is configured with lock_open_duration, ensure we always
# transition back to CLOSED and emit a close command/event path for Monitor.
_AUTO_CLOSE_TIMERS = {}


def _schedule_door_auto_close(device_id: int, door_pk: int, cmd_door_arg: str, seconds: int) -> None:
    try:
        seconds = int(seconds or 0)
        if seconds <= 0:
            return
        if int(door_pk or 0) <= 0:
            return
        import threading

        # Cancel previous timer for this door (avoid stacking).
        prev = _AUTO_CLOSE_TIMERS.get(int(door_pk))
        if prev is not None:
            try:
                prev.cancel()
            except Exception:
                pass

        def _fire() -> None:
            try:
                door_obj = Door.objects.filter(pk=int(door_pk)).select_related('device').first()
            except Exception:
                door_obj = None

            # If the door is already closed, do not emit duplicate close commands/events.
            try:
                if door_obj is None or not bool(getattr(door_obj, 'is_open', False)):
                    return
            except Exception:
                return

            # Persist CLOSED in DB so other pages don't keep showing OPEN.
            try:
                from django.utils import timezone

                if door_obj is not None and bool(getattr(door_obj, 'is_open', False)):
                    door_obj.is_open = False
                    door_obj.last_state_change = timezone.now()
                    door_obj.save(update_fields=['is_open', 'last_state_change'])
                    try:
                        _set_lock_state(door_obj.id, None)
                    except Exception:
                        pass
            except Exception:
                pass

            # Enqueue an explicit close so CommCenter can publish `door.close`.
            try:
                _enqueue(int(device_id), f"DOOR_CLOSE:{cmd_door_arg}", door=door_obj)
            except Exception:
                pass

            try:
                _persist_and_broadcast_status(int(device_id), "CLOSED")
            except Exception:
                pass

            # Ensure the monitor shows a real-time close line even if the controller
            # doesn't emit an explicit close event.
            try:
                _broadcast_door_event(int(device_id), door_obj, 'door.close', verify_mode=f'AUTO({int(seconds)}s)')
            except Exception:
                pass

        t = threading.Timer(seconds, _fire)
        t.daemon = True
        _AUTO_CLOSE_TIMERS[int(door_pk)] = t
        t.start()
    except Exception:
        return

def door_open(request: HttpRequest, device_id: int, door_id: str):
    if not request.user.is_authenticated or not request.user.is_staff:
        return JsonResponse({"ok": False, "error": "unauthorized"}, status=403)
    door_obj = None
    try:
        if str(door_id).isdigit():
            door_obj = Door.objects.filter(pk=int(door_id)).first()
            if door_obj is None:
                door_obj = Door.objects.filter(device_id=int(device_id), door_number=int(door_id)).first()
    except Exception:
        door_obj = None

    # Enforce that door belongs to the requested controller and is allowed by schedule
    if door_obj is None:
        return JsonResponse({"ok": False, "error": "door_not_found"}, status=404)
    if int(getattr(door_obj, 'device_id', 0) or 0) != int(device_id):
        return JsonResponse({"ok": False, "error": "door_device_mismatch"}, status=409)
    can_open, reason = _door_can_open_now(door_obj)
    if not can_open:
        return JsonResponse({"ok": False, "error": reason}, status=409)
    cmd_door_arg = str(getattr(door_obj, 'door_number', None) or door_id)
    ok = _enqueue(device_id, f"DOOR_OPEN:{cmd_door_arg}", door=door_obj)
    if not ok:
        return JsonResponse({"ok": False, "error": "device_unavailable"}, status=409)
    # Update door.is_open state in database
    try:
        if door_obj is not None:
            door_obj.is_open = True
            door_obj.save(update_fields=['is_open', 'last_state_change'])
            _set_lock_state(door_obj.id, None)
    except Exception:
        pass
    _persist_and_broadcast_status(device_id, "OPEN")

    # Broadcast a door.open line for real-time monitor log.
    try:
        _broadcast_door_event(int(device_id), door_obj, 'door.open', verify_mode='API')
    except Exception:
        pass

    # Auto-close (server-side): after lock_open_duration seconds, mark CLOSED and
    # enqueue a DOOR_CLOSE to drive a real-time close event in Monitor.
    try:
        secs = int(getattr(door_obj, 'lock_open_duration', 0) or 0)
        if secs > 0 and door_obj is not None:
            _schedule_door_auto_close(int(device_id), int(getattr(door_obj, 'id', 0) or 0), str(cmd_door_arg), secs)
    except Exception:
        pass
    try:
        import json as _json
        from .event_codes import describe_door_event_type as _door_desc
        dev = getattr(door_obj, 'device', None) if door_obj else None
        details = _json.dumps({
            'door_id': int(getattr(door_obj, 'id', 0) or 0) if door_obj else (int(door_id) if str(door_id).isdigit() else door_id),
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
    door_obj = None
    try:
        if str(door_id).isdigit():
            door_obj = Door.objects.filter(pk=int(door_id)).first()
            if door_obj is None:
                door_obj = Door.objects.filter(device_id=int(device_id), door_number=int(door_id)).first()
    except Exception:
        door_obj = None
    cmd_door_arg = str(getattr(door_obj, 'door_number', None) or door_id)
    ok = _enqueue(device_id, f"DOOR_CLOSE:{cmd_door_arg}", door=door_obj)
    if not ok:
        return JsonResponse({"ok": False, "error": "device_unavailable"}, status=409)
    # Update door.is_open state in database
    try:
        if door_obj is not None:
            door_obj.is_open = False
            door_obj.save(update_fields=['is_open', 'last_state_change'])
            _set_lock_state(door_obj.id, None)
    except Exception:
        pass
    _persist_and_broadcast_status(device_id, "CLOSED")

    # Broadcast a door.close line for real-time monitor log.
    try:
        _broadcast_door_event(int(device_id), door_obj, 'door.close', verify_mode='API')
    except Exception:
        pass
    try:
        import json as _json
        from .event_codes import describe_door_event_type as _door_desc
        dev = getattr(door_obj, 'device', None) if door_obj else None
        details = _json.dumps({
            'door_id': int(getattr(door_obj, 'id', 0) or 0) if door_obj else (int(door_id) if str(door_id).isdigit() else door_id),
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
    door_obj = None
    try:
        if str(door_id).isdigit():
            door_obj = Door.objects.filter(pk=int(door_id)).first()
            if door_obj is None:
                door_obj = Door.objects.filter(device_id=int(device_id), door_number=int(door_id)).first()
    except Exception:
        door_obj = None
    cmd_door_arg = str(getattr(door_obj, 'door_number', None) or door_id)
    ok = _enqueue(device_id, f"DOOR_NORMAL_OPEN:{cmd_door_arg}", door=door_obj)
    if not ok:
        return JsonResponse({"ok": False, "error": "device_unavailable"}, status=409)
    try:
        if door_obj is not None:
            _set_lock_state(door_obj.id, None)
        else:
            _set_lock_state(door_id, None)
    except Exception:
        pass
    _persist_and_broadcast_status(device_id, "NORMAL_OPEN")
    try:
        import json as _json
        from .event_codes import describe_door_event_type as _door_desc
        dev = getattr(door_obj, 'device', None) if door_obj else None
        details = _json.dumps({
            'door_id': int(getattr(door_obj, 'id', 0) or 0) if door_obj else (int(door_id) if str(door_id).isdigit() else door_id),
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
    door_obj = None
    try:
        if str(door_id).isdigit():
            door_obj = Door.objects.filter(pk=int(door_id)).first()
            if door_obj is None:
                door_obj = Door.objects.filter(device_id=int(device_id), door_number=int(door_id)).first()
    except Exception:
        door_obj = None

    if door_obj is not None and int(getattr(door_obj, 'device_id', 0) or 0) != int(device_id):
        return JsonResponse({"ok": False, "error": "door_device_mismatch"}, status=409)

    cmd_door_arg = str(getattr(door_obj, 'door_number', None) or door_id)
    ok = _enqueue(device_id, f"DOOR_CANCEL_ALARM:{cmd_door_arg}", door=door_obj)
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
                        ds_link = _DS.objects.filter(device=devlink).order_by('-updated_at', '-id').first()
                        created_ds = False
                        if ds_link is None:
                            ds_link = _DS.objects.create(device=devlink, online=bool(target), door_state='')
                            created_ds = True
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
                            ua = ds2.updated_at.isoformat() if ds2 and ds2.updated_at else ''
                        except Exception:
                            ua = ''
                        try:
                            broadcast_device_status(did, bool(target), updated_at=ua)
                        except Exception:
                            pass
                except Exception:
                    pass
                # Return the status for the specific device_id (if we have a row)
                ds = DeviceStatus.objects.filter(device=dev).order_by('-updated_at', '-id').first()
                ua = ds.updated_at.isoformat() if ds and ds.updated_at else ''
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
        ds = DeviceStatus.objects.filter(device=dev).order_by('-updated_at', '-id').first()
        if ds is None:
            ds = DeviceStatus.objects.create(device=dev, online=bool(target), door_state='')
        else:
            ds.online = bool(target)
            # When forcing offline, clear any persisted OPEN-like state so UIs
            # don't show doors stuck open while the controller is powered down.
            if not bool(target):
                try:
                    ds.door_state = ''
                except Exception:
                    pass
            ds.save(update_fields=['online', 'door_state', 'updated_at'] if not bool(target) else ['online', 'updated_at'])
        # Also clear simulated per-door open state when forcing offline.
        if not bool(target):
            try:
                Door.objects.filter(device=dev).update(is_open=False)
            except Exception:
                pass
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
        if not door.device:
            return JsonResponse({'ok': False, 'error': 'door_unassigned'}, status=409)
        can_open, reason = _door_can_open_now(door)
        if not can_open:
            return JsonResponse({'ok': False, 'error': reason}, status=409)
        if door.device:
            cmd_door_arg = str(getattr(door, 'door_number', None) or getattr(door, 'id', pk))
            ok = _enqueue(door.device.id, f"DOOR_OPEN:{cmd_door_arg}", door=door)
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
            cmd_door_arg = str(getattr(door, 'door_number', None) or getattr(door, 'id', pk))
            ok = _enqueue(door.device.id, f"DOOR_CLOSE:{cmd_door_arg}", door=door)
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
    emp_id = request.GET.get('employee')
    door_id = request.GET.get('door')
    emp_pk = _parse_int(emp_id, default=None)
    door_pk = _parse_int(door_id, default=None)
    if emp_pk is None or door_pk is None:
        return JsonResponse({'ok': False, 'error': 'invalid-args'}, status=400)
    try:
        emp = Employee.objects.get(pk=int(emp_pk))
        door = Door.objects.get(pk=int(door_pk))
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


def _enqueue_tracked_cmd(device_id: int, cmd: str) -> tuple[bool, int | None, str]:
    """Create CommandLog and enqueue with LOGID prefix so CommCenter updates status.

    Starts an in-process CommCenter (driver=auto) if none is active, so UI actions
    remain functional even when tray/daemon isn't running.
    """
    # De-dupe heavy sync commands to avoid generating high traffic / DoS.
    try:
        if (cmd or '').strip().upper().startswith('SYNC_PERSONNEL'):
            try:
                from agent.sync_limits import get_sync_personnel_limits

                dedupe_s = int(get_sync_personnel_limits().dedupe_seconds)
            except Exception:
                try:
                    dedupe_s = int(os.getenv('SYNC_PERSONNEL_DEDUPE_SECONDS', '60'))
                except Exception:
                    dedupe_s = 60
                dedupe_s = max(5, min(600, dedupe_s))
            from datetime import timedelta
            from django.utils import timezone as _tz

            cutoff = _tz.now() - timedelta(seconds=int(dedupe_s))
            existing = (
                CommandLog.objects.filter(
                    device_id=int(device_id),
                    command__startswith='SYNC_PERSONNEL',
                    status='PENDING',
                    created_at__gte=cutoff,
                )
                .order_by('-created_at')
                .first()
            )
            if existing:
                return (True, int(existing.id), 'already_queued')
    except Exception:
        pass

    try:
        log = CommandLog.objects.create(device_id=int(device_id), command=(cmd or '')[:240], status='PENDING')
    except Exception as e:
        return (False, None, f"commandlog_create_failed:{e}")

    # Safety gates
    try:
        dev0 = Device.objects.filter(id=int(device_id)).first()
        if dev0 is None:
            log.status, log.result = 'ERR', 'device-not-found'
            log.save(update_fields=['status', 'result'])
            return (False, int(log.id), 'device-not-found')
        if not getattr(dev0, 'enabled', True):
            log.status, log.result = 'ERR', 'device-disabled'
            log.save(update_fields=['status', 'result'])
            return (False, int(log.id), 'device-disabled')
        ds0 = DeviceStatus.objects.filter(device=dev0).first()
        if ds0 is not None and not ds0.online:
            log.status, log.result = 'ERR', 'device-offline'
            log.save(update_fields=['status', 'result'])
            return (False, int(log.id), 'device-offline')
    except Exception:
        pass

    try:
        import agent.modern_comm_center as mcc

        center = getattr(mcc, 'ACTIVE_CENTER', None)
        if center is None:
            # Best-effort: in web-only mode there may be no active center.
            # We start one so the command can execute without tray/daemon.
            center = getattr(mcc, 'build_and_run_stub')(poll_interval=1.0, driver='auto')
            mcc.ACTIVE_CENTER = center
        center.enqueue_command(int(device_id), f"LOGID:{int(log.id)} {cmd}"[:240])
        try:
            log.status = 'RUNNING'
            log.result = 'queued'
            log.save(update_fields=['status', 'result'])
        except Exception:
            pass
        try:
            _broadcast_command(log)
        except Exception:
            pass
        return (True, int(log.id), 'queued')
    except Exception as e:
        # Keep DB queue as source of truth; external CommCenter/tray can consume.
        try:
            if not (log.result or '').strip():
                log.result = 'queued-db-only'
                log.save(update_fields=['result'])
        except Exception:
            pass
        return (True, int(log.id), f"queued_db_only:{e}")


@csrf_exempt
def device_sync_personnel(request: HttpRequest, device_id: int):
    """Queue SYNC_PERSONNEL for a physical controller and return command id."""
    if not request.user.is_authenticated or not request.user.is_staff:
        return JsonResponse({'ok': False, 'error': 'unauthorized'}, status=403)
    if request.method != 'POST':
        return JsonResponse({'ok': False, 'error': 'method-not-allowed'}, status=405)

    dev = Device.objects.filter(id=int(device_id)).first()
    if dev is None:
        return JsonResponse({'ok': False, 'error': 'not-found'}, status=404)

    try:
        if not bool(dev.is_physical_controller()):
            return JsonResponse({'ok': False, 'error': 'device-not-physical'}, status=400)
    except Exception:
        return JsonResponse({'ok': False, 'error': 'device-not-physical'}, status=400)

    # Ensure DB contains syncable employees for this device (active + access levels on this controller).
    try:
        doors = list(Door.objects.filter(device_id=int(dev.id)).exclude(door_number__isnull=True))
        levels = list(AccessLevel.objects.filter(doors__in=doors).distinct()) if doors else []
        emp_qs = Employee.objects.filter(active=True, access_levels__in=levels).distinct() if levels else Employee.objects.none()
        syncable_count = int(emp_qs.count())
    except Exception:
        syncable_count = 0

    if syncable_count <= 0:
        return JsonResponse({'ok': False, 'error': 'no_syncable_employees'}, status=400)

    ok, cmdlog_id, info = _enqueue_tracked_cmd(int(dev.id), 'SYNC_PERSONNEL')
    if not ok or not cmdlog_id:
        return JsonResponse({'ok': False, 'error': info or 'enqueue-failed'}, status=500)

    try:
        _audit_log(
            request,
            module='command',
            action='create',
            entity_id=int(dev.id),
            entity_name='SYNC_PERSONNEL',
            details=f"device_id={dev.id} cmdlog_id={cmdlog_id} syncable={syncable_count}",
        )
    except Exception:
        pass

    return JsonResponse({'ok': True, 'command_id': int(cmdlog_id), 'info': info, 'syncable_employees': syncable_count})


def command_status(request: HttpRequest, command_id: int):
    if not request.user.is_authenticated:
        return JsonResponse({'ok': False, 'error': 'unauthorized'}, status=403)
    try:
        cid = int(command_id)
    except Exception:
        return JsonResponse({'ok': False, 'error': 'invalid-id'}, status=400)
    try:
        l = CommandLog.objects.get(pk=cid)
    except CommandLog.DoesNotExist:
        return JsonResponse({'ok': False, 'error': 'not-found'}, status=404)
    except Exception as e:
        return JsonResponse({'ok': False, 'error': f'db-error:{e}'}, status=500)

    item = {
        'id': l.id,
        'command': (l.command or '')[:240],
        'status': l.status,
        'result': l.result,
        'device_id': l.device_id,
        'door_id': l.door_id,
        'created_at': l.created_at.isoformat() if l.created_at else None,
        'executed_at': l.executed_at.isoformat() if l.executed_at else None,
    }
    return JsonResponse({'ok': True, 'item': item, **item})


def commands_full_list(request: HttpRequest):
    if not request.user.is_authenticated:
        return JsonResponse({'ok': False, 'error': 'unauthorized'}, status=403)
    limit = min(int(request.GET.get('limit', '200') or 200), 500)
    logs = CommandLog.objects.select_related('device', 'door').order_by('-created_at')[:limit]
    rows = []
    for l in logs:
        rows.append({
            'id': l.id,
            'device_id': l.device_id,
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
        w.writerow(['id', 'name', 'device_serial', 'device_name', 'door_number', 'location', 'normally_open', 'enabled'])
        for d in Door.objects.select_related('device').order_by('device__ip_address', 'device__name', 'door_number', 'name'):
            w.writerow([
                d.id,
                d.name,
                getattr(d.device, 'serial_number', '') if d.device_id else '',
                getattr(d.device, 'name', '') if d.device_id else '',
                getattr(d, 'door_number', '') or '',
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
                parent_id = _parse_int(getattr(m, 'parent_legacy_area_id', None), default=None) if m else None
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
        if Dept is None:
            return JsonResponse({'ok': False, 'error': 'missing-model:Dept'}, status=400)
        DeptModel = cast(Any, Dept)
        w.writerow(['id', 'name', 'code'])
        for d in DeptModel.objects.order_by('DeptName'):
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
                door_number = _parse_int(r.get('door_number'))
                if door_number is not None and door_number not in (1, 2, 3, 4):
                    _fail(i, 'invalid-door_number (allowed: 1..4)')
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
                if dev is None:
                    _fail(i, 'missing-or-unknown-device (device_serial/device_name required)')
                    continue
                try:
                    if not (getattr(dev, 'is_controller', None) and dev.is_controller()):
                        _fail(i, 'invalid-device (not a controller)')
                        continue
                except Exception:
                    _fail(i, 'invalid-device (controller check failed)')
                    continue
                obj.device = dev
                obj.door_number = door_number
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
        if Dept is None:
            return JsonResponse({'ok': False, 'error': 'missing-model:Dept'}, status=400)
        DeptModel = cast(Any, Dept)
        for i, r in enumerate(rows, start=2):
            try:
                name = (r.get('name') or r.get('deptname') or '').strip()
                code = (r.get('code') or '').strip()
                pk = _parse_int(r.get('id'))

                obj = None
                if pk:
                    obj = DeptModel.objects.filter(pk=int(pk)).first()
                if obj is None and code:
                    obj = DeptModel.objects.filter(code=code).first()
                if obj is None and name:
                    obj = DeptModel.objects.filter(DeptName=name).first()

                is_new = obj is None
                if obj is None:
                    if not name:
                        _fail(i, 'missing-name')
                        continue
                    obj = DeptModel()
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
        if Dept is not None:
            try:
                DeptModel = cast(Any, Dept)
                dept_by_name = {str(getattr(d, 'DeptName', '') or '').strip().lower(): int(d.id) for d in DeptModel.objects.all()}
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
                # Universal policy: ignore imported device TZ; inherit system.
                try:
                    from agent.models import SystemSettings

                    tz_name = (SystemSettings.get_solo().time_zone or '').strip()
                    obj.time_zone = tz_name or (obj.time_zone or '').strip()
                except Exception:
                    obj.time_zone = (obj.time_zone or '').strip()
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
    ui = (request.GET.get('ui') or request.POST.get('ui') or '').strip().lower()
    wants_modal = ui in ('modal', '1', 'true', 'yes')
    
    if request.method == 'POST':
        form = EmployeeExtendedForm(request.POST)
        if form.is_valid():
            emp = form.save()
            if is_ajax:
                if wants_modal:
                    # Return HTML so the Personnel modal can behave like Access modal.
                    return render(request, 'agent/employee_modal_saved.html', {'obj': emp, 'created': True})
                return JsonResponse({'ok': True, 'id': emp.id, 'name': str(emp)})
            return render(request,'agent/employee_saved.html',{'obj': emp,'created': True})
        else:
            if is_ajax:
                if wants_modal:
                    resp = render(request, 'agent/employee_form_modal.html', {
                        'form': form,
                        'obj': None,
                        'action_url': '/agent/crud/employees/new/?ui=modal',
                        'available_access_levels': AccessLevel.objects.all(),
                    })
                    resp.status_code = 400
                    return resp
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

    if is_ajax:
        if wants_modal:
            return render(request, 'agent/employee_form_modal.html', {
                'form': form,
                'obj': None,
                'action_url': '/agent/crud/employees/new/?ui=modal',
                'available_access_levels': AccessLevel.objects.all(),
            })
        # Legacy XHR fragment used by Dashboard/Monitor quick-add flows
        return render(request, 'agent/employee_form_fragment.html', {
            'form': form,
            'available_access_levels': AccessLevel.objects.all(),
        })

    # Legacy full-page (archive)
    return render(request, 'agent/employee_form.html', {
        'form': form,
        'available_access_levels': AccessLevel.objects.all(),
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
    
    response_data: dict[str, Any] = {'ok': True}
    
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
        
        response_data: dict[str, Any] = {'ok': True}
        
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
        return JsonResponse({'ok': False, 'error': str(e)}, status=500)

def employee_edit(request: HttpRequest, pk: int):
    if not request.user.is_authenticated or not request.user.is_staff:
        from django.contrib.auth.views import redirect_to_login
        return redirect_to_login(request.get_full_path())
    emp = Employee.objects.get(pk=pk)
    from .forms import EmployeeExtendedForm
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    ui = (request.GET.get('ui') or request.POST.get('ui') or '').strip().lower()
    wants_modal = ui in ('modal', '1', 'true', 'yes')
    if request.method == 'POST':
        form = EmployeeExtendedForm(request.POST, instance=emp)
        if form.is_valid():
            if form.has_changed():
                saved_emp = form.save()
                if is_ajax:
                    if wants_modal:
                        return render(request, 'agent/employee_modal_saved.html', {'obj': saved_emp, 'created': False})
                    return JsonResponse({'ok': True, 'id': saved_emp.id, 'name': str(saved_emp)})

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
                if is_ajax:
                    if wants_modal:
                        return render(request, 'agent/employee_modal_saved.html', {'obj': emp, 'created': False})
                    return JsonResponse({'ok': True, 'id': emp.id, 'name': str(emp)})

                from django.shortcuts import redirect
                return_url = request.POST.get('return_url', '/agent/menu/personnel/')
                return redirect(return_url)
        else:
            if is_ajax:
                if wants_modal:
                    resp = render(request, 'agent/employee_form_modal.html', {
                        'form': form,
                        'obj': emp,
                        'action_url': f'/agent/crud/employees/{pk}/edit/?ui=modal',
                        'available_access_levels': AccessLevel.objects.all(),
                    })
                    resp.status_code = 400
                    return resp
                return JsonResponse({'ok': False, 'errors': form.errors}, status=400)
    else:
        form = EmployeeExtendedForm(instance=emp)

    if is_ajax and wants_modal:
        return render(request, 'agent/employee_form_modal.html', {
            'form': form,
            'obj': emp,
            'action_url': f'/agent/crud/employees/{pk}/edit/?ui=modal',
            'available_access_levels': AccessLevel.objects.all(),
        })

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
    data: dict[str, Any] = {
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

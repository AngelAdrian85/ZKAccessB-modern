from django.shortcuts import render
from django.conf import settings
from django.http import HttpResponseNotFound, HttpResponse
from django.db import IntegrityError
import json
import time
from pathlib import Path

# New: import legacy models if available
try:
    from legacy_models.models import Employee
except Exception:
    Employee = None


def _sample_context(request):
    """Return a context dictionary for legacy templates.

    Prefer using reconstructed ORM models (legacy_models) when available so
    pages render with real DB data. Fall back to lightweight stubs if the
    ORM is unavailable for any reason.
    """
    ctx = {
        "MEDIA_URL": getattr(settings, "MEDIA_URL", "/media/"),
        "LANGUAGE_CODE": getattr(settings, "LANGUAGE_CODE", "en-us"),
        "permissions": {"admin": True},
    }

    # Try to populate devices/employees/doors from ORM if app is present.
    try:
        from legacy_models.models import Device, Employee, Door

        devices_qs = Device.objects.all()[:20]
        employees_qs = Employee.objects.all()[:50]
        doors_qs = Door.objects.all()[:50]

        ctx["devices"] = [
            {"id": d.id, "name": d.device_name or str(d), "ip": None, "sn": d.sn} for d in devices_qs
        ]
        ctx["employees"] = [
            {"id": e.id, "userid": e.userid, "name": f"{e.firstname or ''} {e.lastname or ''}".strip()} for e in employees_qs
        ]
        ctx["doors"] = [{"id": dd.id, "name": dd.name} for dd in doors_qs]
    except Exception:
        # Fall back to simple static stubs
        ctx["devices"] = [
            {"id": 1, "name": "ACPanel-1", "ip": "192.168.1.100"},
            {"id": 2, "name": "ACPanel-2", "ip": "192.168.1.101"},
        ]
        ctx["employees"] = [
            {"id": 1, "name": "Alice"},
            {"id": 2, "name": "Bob"},
        ]
        ctx["doors"] = [
            {"id": 1, "name": "Main Gate"},
            {"id": 2, "name": "Side Door"},
        ]

    # Determine whether to show logs link based on settings and user
    try:
        require_staff = getattr(settings, 'IACCESS_LOG_CSV_REQUIRE_STAFF', True)
    except Exception:
        require_staff = True
    try:
        allowed_groups = getattr(settings, 'IACCESS_LOG_CSV_ALLOWED_GROUPS', []) or []
    except Exception:
        allowed_groups = []

    can_view_logs = False
    try:
        user = getattr(request, 'user', None)
        if not require_staff:
            can_view_logs = True
        elif user and getattr(user, 'is_staff', False):
            can_view_logs = True
        elif user and allowed_groups:
            # check group membership
            try:
                if user.groups.filter(name__in=allowed_groups).exists():
                    can_view_logs = True
            except Exception:
                # defensive fallback
                can_view_logs = False
    except Exception:
        can_view_logs = False
    ctx['show_logs_link'] = can_view_logs

    return ctx


def index(request):
    # Render the most common landing legacy template if available
    candidates = ["Acc_Door_Mng.html", "Acc_Door_Set.html", "Acc_Option.html"]
    for tmpl in candidates:
        try:
            return render(request, tmpl, context={"request": request, **_sample_context(request)})
        except Exception:
            # try next candidate
            continue
    # Fallback: if none of the legacy templates render (missing template
    # libraries or legacy tags), return a small safe HTTP response so the
    # shim remains usable in tests and local dev without requiring legacy
    # template tag libraries to be importable.
    from django.http import HttpResponse
    return HttpResponse("Acc_Door_Mng (fallback)")


def render_page(request, subpath: str = ""):
    # Accept requests like /iaccess/AccDoor_list.html or /iaccess/some/name
    # Map subpath to candidate template names
    candidates = [subpath, f"{subpath}", subpath.replace('/', '_') + '.html']
    # Also try common patterns
    for c in candidates:
        if not c:
            continue
        try:
            return render(request, c, context={"request": request, **_sample_context(request)})
        except Exception:
            continue
    # If not found, render index as fallback
    return index(request)


def employee_list(request):
    """Render a small ORM-backed list of employees.

    This page is intended as an example of migrating a legacy page
    to use the reconstructed `legacy_models.Employee` model.

    Behaviour:
    - If `legacy_models.Employee` is available, query and pass the
      first 200 employees ordered by userid.
    - Else, fall back to an empty list and let template show a stub.
    """
    employees_qs = None
    try:
        # Prefer the reconstructed legacy_models app when present
        from legacy_models.models import Employee as LegacyEmployee
        employees_qs = LegacyEmployee.objects.all().order_by('userid')[:200]
    except Exception:
        employees_qs = []

    context = _sample_context(request)
    context.update({
        'employees': employees_qs,
    })

    return render(request, 'iaccess/employee_list.html', context)


def device_list(request):
    """Render a small ORM-backed list of devices.

    Uses `legacy_models.Device` when present; falls back to an empty list.
    """
    devices_qs = None
    try:
        from legacy_models.models import Device as LegacyDevice
        devices_qs = LegacyDevice.objects.all().order_by('id')[:200]
    except Exception:
        devices_qs = []

    context = _sample_context(request)
    context.update({
        'devices': devices_qs,
    })

    return render(request, 'iaccess/device_list.html', context)


def door_list(request):
    """Render a small ORM-backed list of doors.

    Uses `legacy_models.Door` when present; falls back to stub data.
    """
    doors_qs = None
    try:
        from legacy_models.models import Door as LegacyDoor
        doors_qs = LegacyDoor.objects.all().order_by('id')[:200]
    except Exception:
        doors_qs = []

    context = _sample_context(request)
    # ensure doors override
    context.update({'doors': doors_qs})

    return render(request, 'iaccess/door_list.html', context)


def access_log(request):
    """List access logs with basic filters and CSV export.

    Query params supported (GET):
      - q : text search (userid or cardno)
      - door : door id
      - start : ISO datetime
      - end : ISO datetime
      - page : page number
      - page_size : items per page
      - export : if 'csv', return CSV export of the filtered rows
    """
    from django.core.paginator import Paginator
    from django.http import HttpResponse
    import csv
    from datetime import datetime

    # Try to find a suitable log model in legacy_models
    try:
        from legacy_models.models import AccessLog
    except Exception:
        # If AccessLog missing, show empty page
        AccessLog = None

    q = request.GET.get('q')
    door = request.GET.get('door')
    device = request.GET.get('device')
    event_type = request.GET.get('event_type')
    start = request.GET.get('start')
    end = request.GET.get('end')
    page = int(request.GET.get('page') or 1)
    page_size = int(request.GET.get('page_size') or 50)

    qs = AccessLog.objects.none() if AccessLog is None else AccessLog.objects.all()

    if q:
        # try match userid numeric or cardno substring
        if q.isdigit():
            qs = qs.filter(userid__userid=int(q))
        else:
            qs = qs.filter(cardno__icontains=q)

    if door:
        try:
            qs = qs.filter(door_id=int(door))
        except Exception:
            pass
    
    if device:
        try:
            qs = qs.filter(device_id=int(device))
        except Exception:
            pass

    if event_type:
        qs = qs.filter(event_type__iexact=event_type)

    # Build event_type choices for the template
    event_types = []
    try:
        if AccessLog is not None:
            event_types = list(AccessLog.objects.order_by().values_list('event_type', flat=True).distinct())
            event_types = [e for e in event_types if e]
    except Exception:
        event_types = []

    # Better datetime parsing (accept ISO datetime or date). Make timezone-aware
    from django.utils.dateparse import parse_datetime, parse_date
    from django.utils import timezone as dj_tz

    def _parse_maybe(dt_str):
        if not dt_str:
            return None
        d = parse_datetime(dt_str)
        if d is None:
            dd = parse_date(dt_str)
            if dd is not None:
                # convert to midnight
                d = datetime(dd.year, dd.month, dd.day)
        if d is not None and dj_tz.is_naive(d):
            try:
                d = dj_tz.make_aware(d, dj_tz.get_current_timezone())
            except Exception:
                pass
        return d

    try:
        start_dt = _parse_maybe(start)
        end_dt = _parse_maybe(end)
        if start_dt:
            qs = qs.filter(timestamp__gte=start_dt)
        if end_dt:
            qs = qs.filter(timestamp__lte=end_dt)
    except Exception:
        # ignore parse errors and continue
        pass

    # Export CSV if requested (streaming + auth/limits)
    if request.GET.get('export') == 'csv':
        # Require staff or allowed-group permission to download CSV
        from django.http import StreamingHttpResponse, HttpResponseForbidden
        user = getattr(request, 'user', None)
        allow = False
        try:
            require_staff = getattr(settings, 'IACCESS_LOG_CSV_REQUIRE_STAFF', True)
        except Exception:
            require_staff = True
        try:
            allowed_groups = getattr(settings, 'IACCESS_LOG_CSV_ALLOWED_GROUPS', []) or []
        except Exception:
            allowed_groups = []

        if user and getattr(user, 'is_staff', False):
            allow = True
        elif user and allowed_groups:
            try:
                if user.groups.filter(name__in=allowed_groups).exists():
                    allow = True
            except Exception:
                allow = False
        elif not require_staff:
            allow = True

        if not allow:
            return HttpResponseForbidden('CSV export requires staff privileges or membership in an allowed group')

        # generator for streaming CSV rows
        import io

        def row_generator():
            header = ['timestamp', 'userid', 'cardno', 'door', 'device', 'event_type', 'result', 'info']
            sio = io.StringIO()
            writer = csv.writer(sio)
            writer.writerow(header)
            yield sio.getvalue()
            # iterate using QuerySet.iterator() to stream without loading all rows
            for row in qs.order_by('-timestamp').iterator():
                sio = io.StringIO()
                writer = csv.writer(sio)
                writer.writerow([
                    row.timestamp.isoformat() if row.timestamp else '',
                    row.userid.userid if row.userid else '',
                    row.cardno or '',
                    row.door.name if row.door else '',
                    row.device.device_name if row.device else '',
                    row.event_type or '',
                    row.result or '',
                    (row.info or '')[:1000],
                ])
                yield sio.getvalue()

        resp = StreamingHttpResponse(row_generator(), content_type='text/csv')
        resp['Content-Disposition'] = 'attachment; filename="access_log_export.csv"'
        return resp

    # If the client requested an async export (export=job), enqueue a job and return job id
    if request.GET.get('export') == 'job':
        import uuid
        from django.http import JsonResponse
        job_id = str(uuid.uuid4())
        try:
            jobs_dir = getattr(settings, 'IACCESS_EXPORT_JOB_DIR', 'export_jobs')
            Path(jobs_dir).mkdir(parents=True, exist_ok=True)
            job = {
                'id': job_id,
                'status': 'pending',
                'created_at': time.time(),
                'filters': {
                    'q': q,
                    'door': door,
                    'device': device,
                    'event_type': event_type,
                    'start': start,
                    'end': end,
                },
                'created_by': getattr(request.user, 'username', None),
            }
            job_path = Path(jobs_dir) / f'{job_id}.json'
            job_path.write_text(json.dumps(job), encoding='utf-8')
            return JsonResponse({'job_id': job_id, 'status': 'queued'})
        except Exception:
            return JsonResponse({'error': 'Failed to enqueue export job'}, status=500)

        # generator for streaming CSV rows
        import io

        def row_generator():
            header = ['timestamp', 'userid', 'cardno', 'door', 'device', 'event_type', 'result', 'info']
            sio = io.StringIO()
            writer = csv.writer(sio)
            writer.writerow(header)
            yield sio.getvalue()
            # iterate using QuerySet.iterator() to stream without loading all rows
            for row in qs.order_by('-timestamp').iterator():
                sio = io.StringIO()
                writer = csv.writer(sio)
                writer.writerow([
                    row.timestamp.isoformat() if row.timestamp else '',
                    row.userid.userid if row.userid else '',
                    row.cardno or '',
                    row.door.name if row.door else '',
                    row.device.device_name if row.device else '',
                    row.event_type or '',
                    row.result or '',
                    (row.info or '')[:1000],
                ])
                yield sio.getvalue()

        resp = StreamingHttpResponse(row_generator(), content_type='text/csv')
        resp['Content-Disposition'] = 'attachment; filename="access_log_export.csv"'
        return resp

    paginator = Paginator(qs, page_size)
    page_obj = paginator.get_page(page)

    context = _sample_context(request)
    context.update({
        'logs': page_obj.object_list,
        'page_obj': page_obj,
        'paginator': paginator,
        'filters': {'q': q, 'door': door, 'device': device, 'event_type': event_type, 'start': start, 'end': end},
        'event_types': event_types,
    })

    return render(request, 'iaccess/log_list.html', context)


def export_status(request, job_id: str):
    """Return status for a queued export job and provide download link when ready."""
    from django.http import JsonResponse, FileResponse, HttpResponseNotFound

    jobs_dir = getattr(settings, 'IACCESS_EXPORT_JOB_DIR', 'export_jobs')
    out_dir = getattr(settings, 'IACCESS_EXPORT_OUTPUT_DIR', 'export_outputs')
    job_path = Path(jobs_dir) / f'{job_id}.json'
    if not job_path.exists():
        return HttpResponseNotFound('Job not found')
    try:
        data = json.loads(job_path.read_text(encoding='utf-8'))
    except Exception:
        return JsonResponse({'error': 'could not read job file'}, status=500)

    status = data.get('status')
    if status == 'done' and data.get('output'):
        out_path = Path(data.get('output'))
        if out_path.exists():
            return FileResponse(open(out_path, 'rb'), as_attachment=True, filename=out_path.name)
        else:
            return JsonResponse({'status': 'done', 'output_missing': True})
    return JsonResponse({'status': status, 'job': data})

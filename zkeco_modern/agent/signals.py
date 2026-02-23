"""
Django signals to automatically log CRUD operations on agent.Employee.

These signals capture create/update/delete operations on Employee
and write audit trail entries to AuditLog for the Personnel module Journal.
"""
import json
import os
from django.db.models.signals import post_save, post_delete, pre_save, pre_delete, m2m_changed
from django.dispatch import receiver
from django.core.serializers.json import DjangoJSONEncoder
from django.utils import timezone
from .models import Employee, AuditLog, AccessLevel, TimeSegment, Door


def _dedupe_seconds() -> int:
    try:
        from agent.sync_limits import get_sync_personnel_limits

        return int(get_sync_personnel_limits().dedupe_seconds)
    except Exception:
        try:
            v = int(os.getenv('SYNC_PERSONNEL_DEDUPE_SECONDS', '60'))
        except Exception:
            v = 60
        return max(5, min(600, v))


def _enqueue_sync_personnel_for_devices(device_ids: set[int], reason: str) -> None:
    """Event-driven: server is source-of-truth; mark affected devices to sync.

    We write PENDING CommandLog rows; CommCenter consumes them from DB.
    This avoids large traffic bursts and works even across processes.
    """
    try:
        from .models import CommandLog
    except Exception:
        return

    ids = {int(x) for x in (device_ids or set()) if int(x) > 0}
    if not ids:
        return

    try:
        from agent.sync_limits import get_sync_personnel_limits

        if not get_sync_personnel_limits().enabled:
            return
    except Exception:
        pass

    from datetime import timedelta
    cutoff = timezone.now() - timedelta(seconds=_dedupe_seconds())
    try:
        existing = set(
            CommandLog.objects.filter(
                device_id__in=list(ids),
                command__startswith='SYNC_PERSONNEL',
                status__in=['PENDING', 'RUNNING'],
                created_at__gte=cutoff,
            ).values_list('device_id', flat=True)
        )
    except Exception:
        existing = set()

    todo = sorted(ids - {int(x) for x in existing if x is not None})
    if not todo:
        return

    cmd = 'SYNC_PERSONNEL'
    if reason:
        # Keep the prefix stable for CommCenter parsing and for DB filters.
        cmd = f"SYNC_PERSONNEL:{reason}"[:240]

    try:
        CommandLog.objects.bulk_create(
            [CommandLog(device_id=int(did), command=cmd, status='PENDING') for did in todo],
            ignore_conflicts=False,
        )
    except Exception:
        # Fallback to per-row create
        for did in todo:
            try:
                CommandLog.objects.create(device_id=int(did), command=cmd, status='PENDING')
            except Exception:
                pass


def _devices_for_access_levels(access_levels) -> set[int]:
    try:
        from .models import Door
        dev_ids = set(
            Door.objects.filter(accesslevel__in=access_levels)
            .exclude(device_id__isnull=True)
            .values_list('device_id', flat=True)
            .distinct()
        )
        return {int(x) for x in dev_ids if x is not None}
    except Exception:
        return set()


def _devices_for_employee(emp: Employee) -> set[int]:
    try:
        als = list(emp.access_levels.all())
        return _devices_for_access_levels(als)
    except Exception:
        return set()


# Thread-local storage to track old state for update detection
import threading
_thread_locals = threading.local()


def get_client_ip(request=None):
    """Extract client IP from request if available."""
    if not request:
        return None
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def get_current_user():
    """Get current user from thread-local storage (set by middleware)."""
    return getattr(_thread_locals, 'user', None)


def get_current_request():
    """Get current request from thread-local storage."""
    return getattr(_thread_locals, 'request', None)


def set_current_user(user):
    """Set current user in thread-local storage."""
    _thread_locals.user = user


def set_current_request(request):
    """Set current request in thread-local storage."""
    _thread_locals.request = request


# ==================== Employee Signals ====================

@receiver(pre_save, sender=Employee)
def employee_pre_save(sender, instance, **kwargs):
    """Capture old state before update for change detection."""
    if instance.pk:
        try:
            old_instance = Employee.objects.get(pk=instance.pk)
            _thread_locals.old_employee = old_instance
        except Employee.DoesNotExist:
            _thread_locals.old_employee = None
    else:
        _thread_locals.old_employee = None


@receiver(pre_delete, sender=Employee)
def employee_pre_delete(sender, instance, **kwargs):
    """Capture affected devices before delete (m2m is cleared after)."""
    try:
        _thread_locals.employee_devices_before_delete = _devices_for_employee(instance)
    except Exception:
        _thread_locals.employee_devices_before_delete = set()


@receiver(post_save, sender=Employee)
def employee_post_save(sender, instance, created, **kwargs):
    """Log employee create/update operations."""
    user = get_current_user()
    request = get_current_request()
    
    action = 'create' if created else 'update'
    entity_name = f"{instance.first_name or ''} {instance.last_name or ''}".strip() or f"ID {instance.legacy_userid}"
    
    # Build details
    details = {}
    if created:
        # For creation, log key fields
        details = {
            'legacy_userid': instance.legacy_userid,
            'card_number': instance.card_number,
            'name': entity_name,
            'department': instance.dept.DeptName if instance.dept else None,
        }
    else:
        # For updates, log changed fields
        old_emp = getattr(_thread_locals, 'old_employee', None)
        if old_emp:
            changes = {}
            for field in ['legacy_userid', 'first_name', 'last_name', 'gender', 'card_number',
                         'ssn', 'birthday', 'email', 'phone', 'mobile_phone', 'homeaddress',
                         'hire_date', 'acc_startdate', 'acc_enddate', 'active']:
                old_val = getattr(old_emp, field, None)
                new_val = getattr(instance, field, None)
                if old_val != new_val:
                    changes[field] = {'old': str(old_val) if old_val else None, 
                                     'new': str(new_val) if new_val else None}
            
            # Check department change
            old_dept = old_emp.dept.DeptName if old_emp.dept else None
            new_dept = instance.dept.DeptName if instance.dept else None
            if old_dept != new_dept:
                changes['department'] = {'old': old_dept, 'new': new_dept}
            
            details = {'changes': changes} if changes else {'info': 'No field changes detected'}
    
    AuditLog.objects.create(
        user=user.username if user else 'system',
        module='employee',
        action=action,
        entity_id=instance.legacy_userid or instance.id,  # Use legacy_userid if available
        entity_name=entity_name,
        details=json.dumps(details, cls=DjangoJSONEncoder, ensure_ascii=False),
        ip_address=get_client_ip(request) if request else None
    )

    # Event-driven device sync: employee changes affect devices where the employee has access.
    try:
        dev_ids = _devices_for_employee(instance)
        _enqueue_sync_personnel_for_devices(dev_ids, reason='employee')
    except Exception:
        pass


@receiver(post_delete, sender=Employee)
def employee_post_delete(sender, instance, **kwargs):
    """Log employee deletion."""
    user = get_current_user()
    request = get_current_request()
    
    entity_name = f"{instance.first_name or ''} {instance.last_name or ''}".strip() or f"ID {instance.legacy_userid}"
    
    details = {
        'legacy_userid': instance.legacy_userid,
        'card_number': instance.card_number,
        'name': entity_name,
        'department': instance.dept.DeptName if instance.dept else None,
    }
    
    AuditLog.objects.create(
        user=user.username if user else 'system',
        module='employee',
        action='delete',
        entity_id=instance.legacy_userid or instance.id,
        entity_name=entity_name,
        details=json.dumps(details, cls=DjangoJSONEncoder, ensure_ascii=False),
        ip_address=get_client_ip(request) if request else None
    )

    # Event-driven device sync: deletion affects previously linked devices.
    try:
        dev_ids = getattr(_thread_locals, 'employee_devices_before_delete', None) or set()
        _enqueue_sync_personnel_for_devices(set(dev_ids), reason='employee_delete')
    except Exception:
        pass


# ==================== M2M Signals ====================

@receiver(m2m_changed, sender=Employee.access_levels.through)
def employee_access_levels_changed(sender, instance: Employee, action, reverse, pk_set, **kwargs):
    if action not in ('post_add', 'post_remove', 'post_clear'):
        return
    try:
        dev_ids = _devices_for_employee(instance)
        _enqueue_sync_personnel_for_devices(dev_ids, reason='employee_access')
    except Exception:
        pass


def _devices_for_access_level_obj(al) -> set[int]:
    try:
        from .models import Door
        return set(
            Door.objects.filter(accesslevel=al)
            .exclude(device_id__isnull=True)
            .values_list('device_id', flat=True)
            .distinct()
        )
    except Exception:
        return set()


@receiver(post_save, sender=AccessLevel)
def access_level_post_save(sender, instance, created, **kwargs):
    try:
        dev_ids = _devices_for_access_level_obj(instance)
        _enqueue_sync_personnel_for_devices({int(x) for x in dev_ids if x is not None}, reason='accesslevel')
    except Exception:
        pass


@receiver(post_delete, sender=AccessLevel)
def access_level_post_delete(sender, instance, **kwargs):
    try:
        dev_ids = _devices_for_access_level_obj(instance)
        _enqueue_sync_personnel_for_devices({int(x) for x in dev_ids if x is not None}, reason='accesslevel_delete')
    except Exception:
        pass


@receiver(m2m_changed, sender=AccessLevel.doors.through)
def access_level_doors_changed(sender, instance, action, reverse, pk_set, **kwargs):
    if action not in ('post_add', 'post_remove', 'post_clear'):
        return
    try:
        dev_ids = _devices_for_access_level_obj(instance)
        _enqueue_sync_personnel_for_devices({int(x) for x in dev_ids if x is not None}, reason='accesslevel_doors')
    except Exception:
        pass


@receiver(m2m_changed, sender=AccessLevel.time_segments.through)
def access_level_time_segments_changed(sender, instance, action, reverse, pk_set, **kwargs):
    if action not in ('post_add', 'post_remove', 'post_clear'):
        return
    try:
        dev_ids = _devices_for_access_level_obj(instance)
        _enqueue_sync_personnel_for_devices({int(x) for x in dev_ids if x is not None}, reason='accesslevel_tz')
    except Exception:
        pass


@receiver(post_save, sender=TimeSegment)
def time_segment_post_save(sender, instance, created, **kwargs):
    # Any time segment change can affect userauthorize/timezone on devices.
    try:
        from .models import Door
        dev_ids = set(
            Door.objects.filter(accesslevel__time_segments=instance)
            .exclude(device_id__isnull=True)
            .values_list('device_id', flat=True)
            .distinct()
        )
        _enqueue_sync_personnel_for_devices({int(x) for x in dev_ids if x is not None}, reason='timesegment')
    except Exception:
        pass


@receiver(post_delete, sender=TimeSegment)
def time_segment_post_delete(sender, instance, **kwargs):
    try:
        from .models import Door
        dev_ids = set(
            Door.objects.filter(accesslevel__time_segments=instance)
            .exclude(device_id__isnull=True)
            .values_list('device_id', flat=True)
            .distinct()
        )
        _enqueue_sync_personnel_for_devices({int(x) for x in dev_ids if x is not None}, reason='timesegment_delete')
    except Exception:
        pass


@receiver(post_save, sender=Door)
def door_post_save(sender, instance, created, **kwargs):
    try:
        did = int(getattr(instance, 'device_id', 0) or 0)
        if did > 0:
            _enqueue_sync_personnel_for_devices({did}, reason='door')
    except Exception:
        pass


@receiver(post_delete, sender=Door)
def door_post_delete(sender, instance, **kwargs):
    try:
        did = int(getattr(instance, 'device_id', 0) or 0)
        if did > 0:
            _enqueue_sync_personnel_for_devices({did}, reason='door_delete')
    except Exception:
        pass

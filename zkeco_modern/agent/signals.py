"""
Django signals to automatically log CRUD operations on agent.Employee.

These signals capture create/update/delete operations on Employee
and write audit trail entries to AuditLog for the Personnel module Journal.
"""
import json
from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver
from django.core.serializers.json import DjangoJSONEncoder
from .models import Employee, AuditLog


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

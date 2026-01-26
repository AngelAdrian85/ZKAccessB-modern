"""
Middleware to track current user and request in thread-local storage.

This allows Django signals to access the current user and request context
when logging CRUD operations, even though signals don't have direct access
to the request object.
"""
from agent.signals import set_current_user, set_current_request


def _get_system_time_zone() -> str:
    """Best-effort DB-backed system timezone (no hard dependency during startup)."""
    try:
        from agent.models import SystemSettings

        return (SystemSettings.get_solo().time_zone or '').strip()
    except Exception:
        return ''


def _get_ui_prefs() -> tuple[str, str]:
    """Return (date_format, week_start) from SystemSettings."""
    try:
        from agent.models import SystemSettings

        ss = SystemSettings.get_solo()
        df = (getattr(ss, 'date_format', '') or '').strip() or 'ro_short'
        ws = (getattr(ss, 'week_start', '') or '').strip() or 'monday'
        return df, ws
    except Exception:
        return 'ro_short', 'monday'


class SystemTimeZoneMiddleware:
    """Activate system time zone for each request.

    Keeps the UI and server-side date formatting aligned with the configured
    System Options time zone.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        try:
            from django.utils import timezone

            tz_name = _get_system_time_zone()
            if tz_name:
                try:
                    from zoneinfo import ZoneInfo

                    timezone.activate(ZoneInfo(tz_name))
                except Exception:
                    # Fallback: let Django attempt string-based activation.
                    timezone.activate(tz_name)
        except Exception:
            pass

        # Attach UI preferences (best-effort) for templates/JS.
        try:
            df, ws = _get_ui_prefs()
            request.ui_date_format = df
            request.ui_week_start = ws
            # Native date/datetime input pickers are locale-driven in most browsers.
            # Use RO locale when week starts Monday; otherwise fall back to EN.
            request.ui_lang = 'ro' if ws == 'monday' else 'en'
        except Exception:
            pass

        return self.get_response(request)


class AuditMiddleware:
    """Store current user and request in thread-local storage for audit logging."""
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Set current user and request before processing view
        set_current_user(request.user if request.user.is_authenticated else None)
        set_current_request(request)
        
        response = self.get_response(request)
        
        # Clean up after request (optional but good practice)
        set_current_user(None)
        set_current_request(None)
        
        return response

from django import template
from datetime import datetime

register = template.Library()


@register.filter(name='hasApp')
def has_app(value, arg=None):
    # legacy templates check for apps by name; for demo enable them
    try:
        return bool(value)
    except Exception:
        return True


@register.filter(name='is_zkaccess_att')
def is_zkaccess_att(value, arg=None):
    return True


@register.filter(name='is_zkaccess_5to4')
def is_zkaccess_5to4(value, arg=None):
    # compatibility flag used in many legacy templates; default to False for modern mode
    return False


@register.simple_tag
def get_this_year():
    """Return the current year for legacy copyright templates."""
    return datetime.now().year


@register.filter(name='is_oem')
def is_oem(value, arg=None):
    return False


@register.filter(name='is_contain_att')
def is_contain_att(value, arg=None):
    return False


@register.filter(name='is_english')
def is_english(value, arg=None):
    return False


@register.filter(name='HasPerm')
def has_perm(value, perm=None):
    try:
        if hasattr(value, 'has_perm'):
            if perm is None:
                return getattr(value, 'is_superuser', False)
            return getattr(value, 'is_superuser', False) or value.has_perm(perm)
    except Exception:
        pass
    return True

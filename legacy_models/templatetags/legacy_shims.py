from django import template

register = template.Library()


@register.simple_tag
def legacy_load(name=None):
    """Compatibility shim: used by some legacy templates that expect a 'load' fallback."""
    return ""


@register.filter
def legacy_noop(value, arg=None):
    return value

from django import template

register = template.Library()

@register.filter
def noop(value, arg=None):
    """A permissive no-op filter for legacy templates."""
    return value

@register.filter
def boolean_icon(value):
    return str(value)

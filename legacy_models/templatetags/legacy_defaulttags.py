from django import template

register = template.Library()


@register.simple_tag
def legacy_noop(*args, **kwargs):
    """A permissive no-op tag for legacy templates that expect builtins."""
    return ""

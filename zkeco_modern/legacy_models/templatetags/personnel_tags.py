from django import template

register = template.Library()


@register.simple_tag(takes_context=True)
def personnel_display_name(context, user=None):
    if user is None:
        return ''
    return getattr(user, 'get_full_name', lambda: str(user))()


@register.filter
def personnel_level(level):
    return str(level)

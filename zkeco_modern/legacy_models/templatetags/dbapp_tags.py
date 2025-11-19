from django import template

register = template.Library()


@register.simple_tag(takes_context=True)
def render_dbapp_field(context, *args, **kwargs):
    return ''


@register.filter
def dbapp_bool(val):
    return val

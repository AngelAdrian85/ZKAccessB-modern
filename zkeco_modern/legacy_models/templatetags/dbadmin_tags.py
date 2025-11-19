from django import template

register = template.Library()


@register.simple_tag(takes_context=True)
def dbadmin_link(context, *args, **kwargs):
    return ''


@register.filter
def dbadmin_format(v):
    return str(v)

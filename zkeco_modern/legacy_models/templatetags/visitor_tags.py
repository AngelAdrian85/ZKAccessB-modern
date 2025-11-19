from django import template

register = template.Library()


@register.simple_tag(takes_context=True)
def visitor_badge(context, visitor):
    return ''


@register.filter
def visitor_status(v):
    return str(v)

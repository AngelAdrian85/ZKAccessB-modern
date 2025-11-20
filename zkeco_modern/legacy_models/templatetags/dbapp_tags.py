from django import template

register = template.Library()


# Conservative no-op tags and filters to satisfy legacy templates that
# call `{% load dbapp_tags %}` but expect a variety of helpers. These
# implementations intentionally return neutral values so templates can
# parse and be progressively repaired.


def _noop(*args, **kwargs):
    return ""


@register.simple_tag
def render_table(*args, **kwargs):
    return ""


@register.simple_tag
def render_list(*args, **kwargs):
    return ""


@register.simple_tag
def get_field(*args, **kwargs):
    return ""


@register.simple_tag
def lookup_value(*args, **kwargs):
    return ""


@register.simple_tag
def nop(*args, **kwargs):
    return ""


# Register a handful of likely-used names as simple tags to avoid
# template parse errors; add more if new failing templates report them.
_names = [
    'render_table',
    'render_list',
    'get_field',
    'lookup_value',
    'nop',
]

for _n in _names:
    try:
        register.simple_tag(globals()[_n], name=_n)
    except Exception:
        pass
from django import template

register = template.Library()


@register.simple_tag(takes_context=True)
def render_dbapp_field(context, *args, **kwargs):
    return ''


@register.filter
def dbapp_bool(val):
    return val

from django import template
from django.template import TemplateSyntaxError, Node

register = template.Library()


@register.filter(name="HasPerm")
def HasPerm(value, perm=None):
    try:
        # If `value` looks like a Django user, attempt to call has_perm.
        if hasattr(value, "has_perm"):
            if perm is None:
                return getattr(value, "is_superuser", False)
            return getattr(value, "is_superuser", False) or value.has_perm(perm)
    except Exception:
        pass
    return False


@register.filter(name="hasApp")
def hasApp(value, arg=None):
    # Legacy templates call this as a string membership check like
    # "mysite.att"|hasApp — return True by default for local dev exploration.
    try:
        return bool(value)
    except Exception:
        return False


@register.filter(name="HasPermDefaultGiven")
def HasPermDefaultGiven(value, perm=None):
    # Similar to HasPerm but with a default truthy fallback if permission check fails.
    try:
        if hasattr(value, "has_perm"):
            if perm is None:
                return getattr(value, "is_superuser", False)
            return getattr(value, "is_superuser", False) or value.has_perm(perm)
    except Exception:
        pass
    return True


@register.filter(name="hasAppLicense")
def hasAppLicense(value, arg=None):
    return True


@register.filter
def translate_str(val, arg=None):
    return val


@register.filter
def lescape(val, arg=None):
    return val


@register.filter
def shortTime(val, arg=None):
    return str(val)


@register.filter
def field_as_td_h(val, arg=None):
    return val


@register.filter
def is_zh(val, arg=None):
    return False


@register.filter
def is_zkaccess_5to4(val, arg=None):
    return False


@register.filter
def has_language(val, arg=None):
    return False


@register.filter
def is_zkaccess_att(val, arg=None):
    return False


# Register many legacy filters used across templates as no-ops to allow rendering
_legacy_filter_names = [
    "is_oem",
    "cap",
    "is_contain_att",
    "field_as_td_h_special",
    "field_as_no_td",
    "field_as_label_tag",
    "field_as_td_h_tz",
    "field_as_td_h_asterisk",
    "get_leave_type",
    "dept_tree",
    "user_perms",
    "version",
    "field_as_td_h",
    "field_as_td_h_asterisk",
    "field_as_td_h_special",
    "field_as_label_tag",
    "field_as_no_td",
    "field_as_td_h_tz",
    "is_contain_att",
    "is_oem",
    "has_language",
]


def _make_filter(name):
    def _f(value, arg=None):
        return value

    _f.__name__ = name
    return _f


for _name in _legacy_filter_names:
    try:
        register.filter(_name)(_make_filter(_name))
    except Exception:
        pass

# Simple tags for some block constructs
@register.simple_tag
def dept_tree(*args, **kwargs):
    return ""


@register.simple_tag
def user_perms(*args, **kwargs):
    return ""


# Additional broad no-op filters and simple tags to cover legacy helpers
_extra_filters = [
    "cl",
    "cap",
    "is_oem",
    "is_contain_att",
    "field_as_td_h_special",
    "field_as_no_td",
    "field_as_label_tag",
    "field_as_td_h_tz",
    "field_as_td_h_asterisk",
    "get_leave_type",
    "get_device_types",
    "field_as_label_tag_no_asterisk",
    "field_as_td_h_asterisk",
    "field_as_td_h_special",
    "is_english",
    "cl",
]


for _name in _extra_filters:
    try:
        register.filter(_name)(_make_filter(_name))
    except Exception:
        pass


@register.simple_tag
def get_this_year():
    from datetime import datetime

    return datetime.now().year


@register.tag(name='ifnotequal')
def do_ifnotequal(parser, token):
    bits = token.split_contents()
    if len(bits) != 3:
        raise TemplateSyntaxError('ifnotequal tag requires exactly two arguments')
    var1 = bits[1]
    var2 = bits[2]
    nodelist_true = parser.parse(('else', 'endifnotequal'))
    token = parser.next_token()
    if token.contents == 'else':
        nodelist_false = parser.parse(('endifnotequal',))
        parser.delete_first_token()
    else:
        nodelist_false = None
    # Render true when var1 != var2
    class IfNotEqualNode(Node):
        def __init__(self, v1, v2, t, f=None):
            self.v1 = v1
            self.v2 = v2
            self.t = t
            self.f = f

        def render(self, context):
            v1 = context.get(self.v1, None) if isinstance(self.v1, str) else self.v1
            v2 = context.get(self.v2, None) if isinstance(self.v2, str) else self.v2
            if v1 != v2:
                return self.t.render(context)
            if self.f:
                return self.f.render(context)
            return ''

    return IfNotEqualNode(var1, var2, nodelist_true, nodelist_false)


@register.simple_tag
def version(*args, **kwargs):
    return ""



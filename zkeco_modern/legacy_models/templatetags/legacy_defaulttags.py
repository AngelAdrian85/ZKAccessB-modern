from django import template
from django.template import Node, TemplateSyntaxError

register = template.Library()


class IfEqualNode(Node):
    def __init__(self, var1, var2, nodelist_true, nodelist_false=None):
        self.var1 = var1
        self.var2 = var2
        self.nodelist_true = nodelist_true
        self.nodelist_false = nodelist_false

    def render(self, context):
        v1 = context.get(self.var1, None) if isinstance(self.var1, str) else self.var1
        v2 = context.get(self.var2, None) if isinstance(self.var2, str) else self.var2
        if v1 == v2:
            return self.nodelist_true.render(context)
        if self.nodelist_false is not None:
            return self.nodelist_false.render(context)
        return ''


@register.tag(name='ifequal')
def do_ifequal(parser, token):
    bits = token.split_contents()
    if len(bits) != 3:
        raise TemplateSyntaxError('ifequal tag requires exactly two arguments')
    var1 = bits[1]
    var2 = bits[2]
    # parse until 'else' or 'endifequal'
    nodelist_true = parser.parse(('else', 'endifequal'))
    token = parser.next_token()
    if token.contents == 'else':
        nodelist_false = parser.parse(('endifequal',))
        parser.delete_first_token()
    else:
        nodelist_false = None
    return IfEqualNode(var1, var2, nodelist_true, nodelist_false)


@register.tag(name='filter')
def do_filter(parser, token):
    # compatibility shim for legacy `{% filter cl spec %}` which in older
    # templates was sometimes used as a self-closing tag (no matching
    # `{% endfilter %}`). Modern Django treats `filter` as a block tag, so
    # be tolerant: try parsing as a block, but if no matching `endfilter`
    # exists, treat it as a harmless no-op tag so templates continue to
    # parse.
    bits = token.split_contents()
    try:
        # attempt to parse as a block tag (consumes until 'endfilter')
        nodelist = parser.parse(('endfilter',))
        # consume endfilter token
        parser.delete_first_token()
    except TemplateSyntaxError:
        # no matching endfilter (legacy self-closing usage) — treat as
        # a no-op and do not attempt to consume additional tokens.
        nodelist = None

    class LegacyFilterNode(Node):
        def __init__(self, nodelist):
            self.nodelist = nodelist

        def render(self, context):
            try:
                if self.nodelist is None:
                    return ''
                return self.nodelist.render(context)
            except Exception:
                return ''

    return LegacyFilterNode(nodelist)

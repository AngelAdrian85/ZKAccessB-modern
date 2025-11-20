from django import template

register = template.Library()


class IfEqualNode(template.Node):
    def __init__(self, var1, var2, nodelist_true, nodelist_false=None):
        self.var1 = template.Variable(var1)
        self.var2 = template.Variable(var2)
        self.nodelist_true = nodelist_true
        self.nodelist_false = nodelist_false

    def render(self, context):
        try:
            v1 = self.var1.resolve(context)
        except Exception:
            v1 = getattr(self.var1, 'var', None)
        try:
            v2 = self.var2.resolve(context)
        except Exception:
            v2 = getattr(self.var2, 'var', None)
        if str(v1) == str(v2):
            return self.nodelist_true.render(context)
        if self.nodelist_false is not None:
            return self.nodelist_false.render(context)
        return ""


def ifequal(parser, token):
    bits = token.split_contents()
    if len(bits) != 3:
        raise template.TemplateSyntaxError("ifequal tag takes exactly two arguments")
    var1 = bits[1]
    var2 = bits[2]
    # allow an optional {% else %} inside ifequal
    nodelist_true = parser.parse(('else', 'endifequal'))
    token = parser.next_token()
    nodelist_false = None
    if token.contents == 'else':
        nodelist_false = parser.parse(('endifequal',))
        parser.delete_first_token()
    return IfEqualNode(var1, var2, nodelist_true, nodelist_false)


register.tag('ifequal', ifequal)


class FilterWrapperNode(template.Node):
    def __init__(self, filter_name, filter_arg, nodelist):
        self.filter_name = filter_name
        self.filter_arg = filter_arg
        self.nodelist = nodelist

    def render(self, context):
        content = self.nodelist.render(context)
        if self.filter_arg:
            tpl_str = '{{ value|%s:"%s" }}' % (self.filter_name, self.filter_arg)
        else:
            tpl_str = '{{ value|%s }}' % (self.filter_name,)
        try:
            t = template.Template(tpl_str)
            return t.render(template.Context({'value': content}))
        except Exception:
            return content


def filter_tag(parser, token):
    bits = token.split_contents()
    if len(bits) not in (2, 3):
        raise template.TemplateSyntaxError("filter tag takes one or two args")
    filter_name = bits[1]
    filter_arg = bits[2] if len(bits) == 3 else None
    nodelist = parser.parse(('endfilter', 'endfor'))
    parser.delete_first_token()
    return FilterWrapperNode(filter_name, filter_arg, nodelist)


register.tag('filter', filter_tag)


class WithPassthroughNode(template.Node):
    def __init__(self, nodelist):
        self.nodelist = nodelist

    def render(self, context):
        try:
            return self.nodelist.render(context)
        except Exception:
            return ''


def with_tag(parser, token):
    nodelist = parser.parse(('endwith', 'endif'))
    parser.delete_first_token()
    return WithPassthroughNode(nodelist)


register.tag('with', with_tag)


class TransBlockNode(template.Node):
    def __init__(self, nodelist):
        self.nodelist = nodelist

    def render(self, context):
        try:
            return self.nodelist.render(context)
        except Exception:
            return ''


class SimpleTransNode(template.Node):
    def __init__(self, msg):
        self.msg = msg

    def render(self, context):
        # If it's a variable, resolve; if it's a quoted literal, strip quotes; else return as-is
        try:
            return template.Variable(self.msg).resolve(context)
        except Exception:
            v = self.msg
            if isinstance(v, str) and len(v) >= 2 and ((v[0] == '"' and v[-1] == '"') or (v[0] == "'" and v[-1] == "'")):
                return v[1:-1]
            return v


def trans_tag(parser, token):
    bits = token.split_contents()
    # {% trans 'literal' %} or {% trans variable %} or block form {% trans %}...{% endtrans %}
    if len(bits) == 1:
        nodelist = parser.parse(('endtrans',))
        parser.delete_first_token()
        return TransBlockNode(nodelist)
    if len(bits) == 2:
        return SimpleTransNode(bits[1])
    raise template.TemplateSyntaxError('trans tag takes either one or zero arguments')


register.tag('trans', trans_tag)

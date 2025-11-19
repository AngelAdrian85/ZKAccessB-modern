from pathlib import Path
import re
import glob
from django import template

register = template.Library()

# Conservative list of tags to ignore (Django built-ins and safe names)
_IGNORE = {
    'if', 'endif', 'for', 'endfor', 'else', 'elif', 'empty',
    'block', 'endblock', 'load', 'include', 'extends', 'trans',
    'blocktrans', 'endblocktrans', 'verbatim', 'endverbatim', 'raw',
    'endraw', 'autoescape', 'endautoescape', 'with', 'endwith',
    'comment', 'endcomment', 'filter', 'endfilter', 'csrf_token',
}


def _make_block_tag(name: str):
    """Return a tag function that parses until a matching `end{name}`.

    If no end tag is present (legacy self-closing usage), behave as a
    tolerant no-op that does not consume additional tokens.
    """

    def _tag(parser, token):
        endtag = f'end{name}'
        try:
            nodelist = parser.parse((endtag,))
            # consume the end tag
            parser.delete_first_token()
        except template.TemplateSyntaxError:
            nodelist = None

        class _Node(template.Node):
            def __init__(self, nodelist):
                self.nodelist = nodelist

            def render(self, context):
                try:
                    return self.nodelist.render(context) if self.nodelist else ''
                except Exception:
                    return ''

        return _Node(nodelist)

    return _tag


def _discover_and_register():
    """Scan legacy template files for tag names and register tolerant
    block/no-op tags for any non-built-in names found.
    """
    # Guess repo root relative to this file: go up 4 parents
    repo_root = Path(__file__).resolve().parents[3]
    pattern = str(repo_root / 'zkeco' / 'units' / 'adms' / 'mysite' / '**' / 'templates' / '**' / '*.html')
    tag_names = set()
    corpus_texts = []
    for path in glob.glob(pattern, recursive=True):
        try:
            text = Path(path).read_text(encoding='utf-8', errors='ignore')
        except Exception:
            continue
        corpus_texts.append(text)
        for m in re.finditer(r'{%\s*([A-Za-z_][A-Za-z0-9_]*)', text):
            tag_names.add(m.group(1))

    all_text = "\n".join(corpus_texts)

    # Register forgiving tags for discovered names that are not builtins.
    # If a matching end tag exists anywhere in the corpus, register a
    # tolerant block tag; otherwise register a simple no-op tag to avoid
    # accidental parsing failures for legacy single-token tags.
    for name in sorted(tag_names):
        lname = name.lower()
        if lname in _IGNORE:
            continue
        end_pat = r"{%\s*end" + re.escape(name) + r"\s*%}"
        try:
            found = re.search(end_pat, all_text, flags=re.I) is not None
        except Exception:
            found = False
        try:
            if found:
                register.tag(name, _make_block_tag(name))
            else:
                # register a safe simple_tag no-op
                def _noop(*args, **kwargs):
                    return ''

                register.simple_tag(_noop, name=name)
        except Exception:
            # be tolerant if registration fails for some names
            pass


# Perform discovery on import so the shim becomes effective as a builtin
try:
    _discover_and_register()
except Exception:
    # Be tolerant in case the filesystem layout differs in some environments
    pass

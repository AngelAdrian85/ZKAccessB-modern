"""
Fix templates that use `{% filter name arg %}` by wrapping the arg in a `with` block
so the parser sees a simpler `{% filter name %}` while preserving the argument.

Transforms:
  {% filter cl spec %} ... {% endfilter %}
into:
  {% with __cl_arg="spec" %}{% filter cl %} ... {% endfilter %}{% endwith %}

Creates .bak backups before modifying files.
"""

import re
import os
from pathlib import Path

BASE = Path('..') / 'zkeco' / 'units' / 'adms' / 'mysite' / 'templates'
BASE = BASE.resolve()
if not BASE.exists():
    print('Templates folder not found:', BASE)
    raise SystemExit(2)

OPEN_PAT = re.compile(r"\{%\s*filter\s+([A-Za-z0-9_]+)\s+([^%\s]+)\s*%}\s*", flags=re.IGNORECASE)
END_PAT = re.compile(r"\{%\s*endfilter\s*%}\s*", flags=re.IGNORECASE)

modified = []
for root, dirs, files in os.walk(BASE):
    for fn in files:
        if not fn.lower().endswith('.html'):
            continue
        path = Path(root) / fn
        text = path.read_text(encoding='utf-8', errors='ignore')
        # first pass: replace opening tags
        new_text = OPEN_PAT.sub(lambda m: f"{{% with __cl_arg=\"{m.group(2)}\" %}}{{% filter {m.group(1)} %}}", text)
        # second pass: ensure endfilter closes with endwith
        new_text = END_PAT.sub(r"{% endfilter %}{% endwith %}", new_text)
        if new_text != text:
            backup = str(path) + '.bak'
            if not Path(backup).exists():
                Path(backup).write_text(text, encoding='utf-8')
            path.write_text(new_text, encoding='utf-8')
            rel = os.path.relpath(str(path), str(Path.cwd()))
            modified.append(rel)

print('Wrapped filter-with-arg blocks in files:', len(modified))
for p in modified:
    print(' -', p)

"""
Conservative fixer for old `|cl spec` filter syntax.
Replaces occurrences like `|cl spec` with `|cl:"spec"` inside templates.
Creates `.bak` backups before modifying files.

This is conservative and only targets the specific pattern to make templates
parseable under modern Django's template parser.
"""

import re
import os
from pathlib import Path

BASE = Path('..') / 'zkeco' / 'units' / 'adms' / 'mysite' / 'templates'
BASE = BASE.resolve()
if not BASE.exists():
    print('Templates folder not found:', BASE)
    raise SystemExit(2)

# pattern: a pipe, optional spaces, 'cl', spaces, then an argument token (until space, pipe, or closing brace)
PAT = re.compile(r"(\|\s*cl)\s+([^\s\|\}\)\]]+)")

modified_files = []
for root, dirs, files in os.walk(BASE):
    for fn in files:
        if not fn.lower().endswith('.html'):
            continue
        path = Path(root) / fn
        text = path.read_text(encoding='utf-8', errors='ignore')
        new_text, n = PAT.subn(lambda m: f"{m.group(1)}:\"{m.group(2)}\"", text)
        if n > 0 and new_text != text:
            backup = str(path) + '.bak'
            if not Path(backup).exists():
                Path(backup).write_text(text, encoding='utf-8')
            path.write_text(new_text, encoding='utf-8')
            rel = os.path.relpath(str(path), str(Path.cwd()))
            modified_files.append(rel)

print('Fixed files:', len(modified_files))
for p in modified_files:
    print(' -', p)

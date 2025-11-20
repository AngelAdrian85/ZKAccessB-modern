"""
Cleanup duplicate leading 'EN:' prefixes inside `{% trans %}` occurrences.
Creates `.bak` backups for modified files.
"""

import re
import os
from pathlib import Path

BASE = Path('zkeco') / 'units' / 'adms' / 'mysite' / 'templates'
if not BASE.exists():
    print('Templates folder not found:', BASE)
    raise SystemExit(2)

TRANS_RE = re.compile(r"(\{%\s*trans\s*(['\"]))(.*?)(\2\s*%\})", flags=re.DOTALL)

changed_files = []

for root, dirs, files in os.walk(BASE):
    for fn in files:
        if not fn.lower().endswith('.html'):
            continue
        path = Path(root) / fn
        text = path.read_text(encoding='utf-8', errors='ignore')
        new_text = []
        last = 0
        modified = False
        for m in TRANS_RE.finditer(text):
            new_text.append(text[last:m.start()])
            prefix = m.group(1)
            inner = m.group(3)
            suffix = m.group(4)
            # Normalize multiple leading EN: (with optional spaces) to single 'EN: '
            stripped = re.sub(r'^(?:EN:\s*)+', 'EN: ', inner)
            if stripped != inner:
                modified = True
                new_text.append(prefix + stripped + suffix)
            else:
                new_text.append(m.group(0))
            last = m.end()
        new_text.append(text[last:])
        if modified:
            backup = str(path) + '.bak'
            if not Path(backup).exists():
                Path(backup).write_text(text, encoding='utf-8')
            path.write_text(''.join(new_text), encoding='utf-8')
            rel = os.path.relpath(str(path), str(Path.cwd()))
            changed_files.append(rel)

print('Cleanup complete. Files modified:', len(changed_files))
for p in changed_files:
    print(' -', p)

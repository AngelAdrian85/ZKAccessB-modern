"""translate_chinese_templates.py

Conservative translator for legacy templates.

- Walks template folders under `zkeco/units/adms/mysite/templates` and subfolders.
- Finds `{% trans "..." %}` and `{% trans '...' %}` occurrences containing CJK characters.
- Replaces known phrases using a conservative mapping.
- For unknown Chinese strings, replaces the inner text with `EN: <original>` as a placeholder.
- Writes a `.bak` backup for each modified file and prints a summary of changes.

This script is not used by the running web app; it's a maintenance helper.
"""

from __future__ import annotations

import os
import re
from pathlib import Path


BASE = Path('zkeco') / 'units' / 'adms' / 'mysite' / 'templates'

MAPPING: dict[str, str] = {
    '登录': 'Login',
    '用户登录': 'User Login',
    '口令重设': 'Password reset',
    '更多': 'More',
    '多卡开门人员组列表': 'Multi-card Group List',
    '浏览指定人员组的人员': 'Browse Group Members',
    '联动条件': 'Linkage Conditions',
    '联动动作': 'Linkage Actions',
    '视频联动': 'Video Linkage',
    '录像': 'Record',
    '修改路径:': 'Modify path:',
    '各组开门人数': 'Open Counts per Group',
    '(括号内为该组中当前实际人数)': '(Current counts in parentheses)',
    '时间': 'Time',
    '日期': 'Date',
    '开始时间': 'Start time',
    '结束时间': 'End time',
    '时间区间1': 'Time segment 1',
    '时间区间2': 'Time segment 2',
    '时间区间3': 'Time segment 3',
    'E-mail 地址：': 'E-mail address:',
    '重设我的口令': 'Reset my password',
    '忘记了你的口令？请在下面输入你的 e-mail 地址，我们将重设你的口令并将新口令通过邮件发送给你。': (
        "Forgot your password? Enter your e-mail below and we'll reset your password and send it by email."
    ),
}


TRANS_RE = re.compile(r"(\{%\s*trans\s*['\"])(.*?)(['\"]\s*%\})", flags=re.DOTALL)
CJK_RE = re.compile(r'[\u4e00-\u9fff]')


def main() -> int:
    if not BASE.exists():
        print('Templates folder not found:', BASE)
        return 2

    modified: list[str] = []
    changes: dict[str, list[tuple[str, str]]] = {}

    for root, _dirs, files in os.walk(BASE):
        for fn in files:
            if not fn.lower().endswith('.html'):
                continue
            path = Path(root) / fn
            try:
                text = path.read_text(encoding='utf-8')
            except Exception:
                continue

            parts: list[str] = []
            last = 0
            changed = False

            for m in TRANS_RE.finditer(text):
                parts.append(text[last:m.start()])
                prefix, inner, suffix = m.group(1), m.group(2), m.group(3)
                if not CJK_RE.search(inner):
                    parts.append(m.group(0))
                else:
                    mapped = MAPPING.get(inner) or MAPPING.get(inner.strip()) or ('EN: ' + inner)
                    parts.append(prefix + mapped + suffix)
                    changed = True
                last = m.end()

            parts.append(text[last:])
            new_text = ''.join(parts)

            if not changed or new_text == text:
                continue

            backup = path.with_suffix(path.suffix + '.bak')
            try:
                if not backup.exists():
                    backup.write_text(text, encoding='utf-8')
                path.write_text(new_text, encoding='utf-8')
            except Exception:
                continue

            rel = str(path)
            try:
                rel = str(path.relative_to(Path.cwd()))
            except Exception:
                pass
            modified.append(rel)

            diffs: list[tuple[str, str]] = []
            try:
                for o, n in zip(text.splitlines(), new_text.splitlines()):
                    if o != n and CJK_RE.search(o):
                        diffs.append((o.strip(), n.strip()))
            except Exception:
                diffs = []
            changes[rel] = diffs

    print('Files modified:', len(modified))
    for p in modified:
        print('  -', p)

    print('\nSample changes:')
    for p, diffs in list(changes.items())[:50]:
        print('\nFile:', p)
        for o, n in diffs[:10]:
            print('  ', o, '=>', n)

    if not modified:
        print('No changes made (no trans strings with CJK found under templates).')
    else:
        print('\nBackups saved as .bak next to modified files.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

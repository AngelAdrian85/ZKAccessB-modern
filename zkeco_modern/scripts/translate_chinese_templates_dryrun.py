"""
Dry-run translator for legacy templates (no writes).

Scans templates under `zkeco/units/adms/mysite/templates`, finds `{% trans %}`
strings containing CJK, and reports conservative replacements based on a mapping.
Does not write or modify any files — only prints a preview and sample diffs.
"""

import re
import os
from pathlib import Path

BASE = Path('zkeco') / 'units' / 'adms' / 'mysite' / 'templates'
if not BASE.exists():
    print('Templates folder not found:', BASE)
    raise SystemExit(2)

MAPPING = {
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


def dryrun():
    proposed = {}

    for root, dirs, files in os.walk(BASE):
        for fn in files:
            if not fn.lower().endswith('.html'):
                continue
            path = Path(root) / fn
            try:
                text = path.read_text(encoding='utf-8')
            except Exception:
                # try fallback encoding
                try:
                    text = path.read_text(encoding='latin-1')
                except Exception:
                    print('Could not read', path)
                    continue

            parts = []
            last = 0
            changed = False
            diffs = []
            for m in TRANS_RE.finditer(text):
                prefix, inner, suffix = m.group(1), m.group(2), m.group(3)
                if not CJK_RE.search(inner):
                    continue
                mapped = MAPPING.get(inner) or MAPPING.get(inner.strip()) or ('EN: ' + inner)
                changed = True
                # record a small diff
                original_snip = (prefix + inner + suffix).strip()
                new_snip = (prefix + mapped + suffix).strip()
                diffs.append((original_snip, new_snip))

            if changed:
                rel = os.path.relpath(str(path), str(Path.cwd()))
                proposed[rel] = diffs

    return proposed


def print_preview(proposed):
    if not proposed:
        print('No candidate translations found.')
        return
    print(f'Found {len(proposed)} files with candidate translations.')
    for p, diffs in list(proposed.items())[:200]:
        print('\nFile:', p)
        for o, n in diffs[:20]:
            print(' -', o)
            print('   =>', n)


if __name__ == '__main__':
    proposed = dryrun()
    print_preview(proposed)
    print('\nDry-run complete. No files modified.')

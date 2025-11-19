#!/usr/bin/env python3
"""Heuristic fixer for mismatched Django end-tags.

Reads `remediation_list.json` to pick the top files, finds their `.partial.html`
copies under `scripts/sanitized/`, and attempts a conservative repair:
- balances `if` / `for` blocks by swapping `endif` <-> `endfor` when they
  clearly mismatch the current block stack.

Writes fixed outputs under `scripts/sanitized_fixed/...` and produces
`scripts/sanitized_fixed_report.json` with results.

This is intentionally conservative and intended to be reviewed before
overwriting production templates.
"""
import json
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / 'zkeco_modern' / 'scripts'
SANITIZED_DIR = SCRIPTS / 'sanitized'
FIXED_DIR = SCRIPTS / 'sanitized_fixed'
REMediation = SCRIPTS / 'remediation_list.json'
REPORT_PATH = SCRIPTS / 'sanitized_fixed_report.json'

TAG_RE = re.compile(r"{%-?\s*(\w+)\b([^%}]*)-?%}")

def find_partial_for_basename(basename):
    # Walk the sanitized dir for a file that endswith the basename + '.partial.html'
    for root, _, files in os.walk(SANITIZED_DIR):
        for fn in files:
            if fn.endswith('.partial.html') and fn.endswith(basename + '.partial.html'):
                return Path(root) / fn
    return None

def repair_content(text):
    # Tokenize tags and maintain a simple stack for `if` and `for` blocks.
    out_lines = []
    stack = []

    def push(tag):
        if tag in ('if', 'for'):
            stack.append(tag)

    def pop_expected(expected):
        # pop if top matches expected, otherwise return top (mismatch)
        if not stack:
            return None
        top = stack[-1]
        if top == expected:
            stack.pop()
            return expected
        return top

    for line in text.splitlines(True):
        # find all tags in the line and process in-order
        new_line = line
        for m in reversed(list(TAG_RE.finditer(line))):
            tag = m.group(1)
            span = m.span()
            # closing tags
            if tag in ('endif', 'endfor'):
                expected = 'if' if tag == 'endif' else 'for'
                top = stack[-1] if stack else None
                if top is None:
                    # nothing to close -- leave it alone
                    continue
                if top != expected:
                    # mismatch -> swap to match top
                    replacement = '{% end' + top + ' %}'
                    new_line = new_line[:span[0]] + replacement + new_line[span[1]:]
                    # pop the matched top
                    stack.pop()
                else:
                    stack.pop()
            else:
                # opening tags possibly
                if tag in ('if', 'for'):
                    push(tag)
                # ignore other tags
        out_lines.append(new_line)

    return ''.join(out_lines)

def main():
    if not REMediation.exists():
        print(f"Remediation list not found: {REMediation}")
        sys.exit(2)

    data = json.loads(REMediation.read_text(encoding='utf-8'))
    top = data.get('top_files', []) or data.get('top_files_by_error', [])

    # fallback: if remediation_list.json is a simpler structure, try reading `files` key
    if not top:
        # attempt to pick top filenames from sanitize_report.json instead
        sr = SCRIPTS / 'sanitize_report.json'
        if sr.exists():
            srj = json.loads(sr.read_text(encoding='utf-8'))
            processed = srj.get('processed', [])
            top = [p for p in processed][:10]

    # If `top` is a mapping of error->files, flatten the first group's files
    if isinstance(top, dict):
        # take first key
        first = next(iter(top.values()))
        top = first if isinstance(first, list) else []

    # Ensure we have a plain list of filenames
    if isinstance(top, list) and top and isinstance(top[0], dict):
        # maybe list of {file, count} objects
        top = [item.get('file') for item in top if isinstance(item, dict)]

    # Limit to top 10
    top = [t for t in top if t][:10]

    FIXED_DIR.mkdir(parents=True, exist_ok=True)
    report = {'fixed': [], 'skipped': [], 'errors': {}}

    for fname in top:
        basename = os.path.basename(fname)
        partial = find_partial_for_basename(basename)
        if partial is None:
            report['skipped'].append({'file': fname, 'reason': 'partial not found'})
            continue

        try:
            text = partial.read_text(encoding='utf-8')
        except Exception as e:
            report['errors'][fname] = str(e)
            continue

        fixed = repair_content(text)

        # write to mirrored fixed path
        rel = partial.relative_to(SANITIZED_DIR)
        out_path = FIXED_DIR / rel
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(fixed, encoding='utf-8')

        report['fixed'].append({'file': fname, 'partial': str(partial), 'fixed_partial': str(out_path)})

    REPORT_PATH.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding='utf-8')
    print('Wrote fixed partials and report to', REPORT_PATH)

if __name__ == '__main__':
    main()

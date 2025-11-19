#!/usr/bin/env python3
import glob
import os
import json
import re
from django.template import Template, Context, TemplateSyntaxError
import django

# Ensure Django is configured (pytest-django normally does this for tests)
django.setup()

repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
pattern = os.path.join(repo_root, 'zkeco', 'units', 'adms', 'mysite', '**', 'templates', '**', '*.html')

# replicate sanitize() from the test, minimal copy

def sanitize(src: str) -> str:
    def _html_comment_repl(m):
        body = m.group(1)
        if "{%" in body or "{{" in body:
            safe = body.replace("{{", "&#123;&#123;").replace("{%", "&#123;%")
            return "<!--" + safe + "-->"
        return m.group(0)

    src = re.sub(r'<!--(.*?)-->', _html_comment_repl, src, flags=re.S)
    for _ in range(3):
        new = re.sub(r'{%\s*filter\b[^%]*%}(.*?){%\s*endfilter\s*%}', r"\1", src, flags=re.S)
        if new == src:
            break
        src = new
    src = re.sub(r"(['\"]?\})(\{\{|\{%)", r"\1 \2", src)
    src = re.sub(r"\}(\{)", r"} \1", src)
    src = re.sub(r'{%\s*trans\s+(".*?"|\'.*?\')\s*%}', lambda m: m.group(1), src, flags=re.S)
    src = re.sub(r'\btrans"([^"]+)"', r'trans "\1"', src)
    pattern = re.compile(r"\|([A-Za-z0-9_]+)\s+([^\s\|'\"\)\}\|]+)")
    for _ in range(8):
        new = pattern.sub(r"|\1:'\2'", src)
        if new == src:
            break
        src = new
    pattern2 = re.compile(r"\|([A-Za-z0-9_]+)\s+([^\s\|'\"\)\}\|<>%/.,:-]+)")
    for _ in range(4):
        new = pattern2.sub(r"|\1:'\2'", src)
        if new == src:
            break
        src = new
    src = re.sub(r'\"([^\"]*[\u4e00-\u9fff][^\"]*)\"', '"STR"', src)
    src = re.sub(r"'([^']*[\u4e00-\u9fff][^']*)'", "'STR'", src)
    return src

errors = {}
count = 0
for path in glob.glob(pattern, recursive=True):
    try:
        with open(path, 'r', encoding='utf-8', errors='ignore') as fh:
            src = fh.read()
        src2 = sanitize(src)
        try:
            Template(src2).render(Context({}))
        except TemplateSyntaxError as e:
            msg = str(e)
            errors.setdefault(msg, []).append(path)
            count += 1
    except Exception:
        pass

# trim samples
for k in list(errors.keys()):
    errors[k] = errors[k][:8]

out = {'total_failures': count, 'patterns': errors}
print(json.dumps(out, indent=2, ensure_ascii=False))

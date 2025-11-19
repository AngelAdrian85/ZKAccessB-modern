#!/usr/bin/env python3
import glob
import os
import json
from django.template import Template, Context, TemplateSyntaxError

repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
# Match the same legacy template tree used by the tests
pattern = os.path.join(repo_root, 'zkeco', 'units', 'adms', 'mysite', '**', 'templates', '**', '*.html')

errors = {}
count = 0
for path in glob.glob(pattern, recursive=True):
    try:
        with open(path, 'r', encoding='utf-8', errors='ignore') as fh:
            src = fh.read()
        try:
            Template(src).render(Context({}))
        except TemplateSyntaxError as e:
            msg = str(e)
            errors.setdefault(msg, []).append(path)
            count += 1
    except Exception:
        pass

# trim samples
for k in list(errors.keys()):
    errors[k] = errors[k][:6]

out = {'total_failures': count, 'patterns': errors}
print(json.dumps(out, indent=2, ensure_ascii=False))
